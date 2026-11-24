"""Shared, isolated OCI runtime for Codex and Claude; no credentials are read here."""
import json
import os
from pathlib import Path
import subprocess
import sys

SDK_VERSION = '2.177.0'
REQUIRED_METHODS = ('validate_user', 'list_incidents', 'get_incident',
                    'create_incident', 'update_incident', 'put_attachment')


def require_capabilities(oci):
    missing = [name for name in REQUIRED_METHODS
               if not callable(getattr(oci.cims.IncidentClient, name, None))]
    if missing:
        raise RuntimeError('OCI SDK ' + getattr(oci, '__version__', 'unknown') +
            ' in ' + sys.executable + ' lacks ' + ', '.join(missing) +
            '. Use python scripts/run_sr.py with the same arguments. No SR write sent.')


def runtime_root():
    override = os.environ.get('ORACLE_SUPPORT_SR_RUNTIME')
    if override:
        return Path(override).expanduser().resolve()
    # A home-relative path also avoids Windows Store Python's LOCALAPPDATA
    # virtualization, which can leave subprocesses unable to find pyvenv.cfg.
    return Path.home() / '.local' / 'share' / 'oracle-support-sr' / 'runtime'


def interpreter(root):
    return root / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def probe(python):
    code = ('import json,sys,oci; from runtime_env import require_capabilities; '
            'require_capabilities(oci); print(json.dumps({"python":sys.executable,'
            '"sdk_version":oci.__version__,"put_attachment":True}))')
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent))
    result = subprocess.run([str(python), '-c', code], env=env, capture_output=True,
                            text=True, timeout=45)
    if result.returncode:
        return None
    return json.loads(result.stdout)


def ensure_runtime():
    root = runtime_root()
    python = interpreter(root)
    if python.is_file():
        ready = probe(python)
        if ready:
            return python, ready
    root.parent.mkdir(parents=True, exist_ok=True)
    lock = root.parent / (root.name + '.setup.lock')
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RuntimeError('Another runtime setup is in progress: ' + str(lock) +
                           '. Wait for it; no SR write sent.') from None
    os.close(fd)
    try:
        # A second process may have completed setup before we acquired the lock.
        if python.is_file():
            ready = probe(python)
            if ready:
                return python, ready
        if not python.is_file():
            subprocess.run([sys.executable, '-m', 'venv', str(root)], check=True,
                           stdout=sys.stderr)
        subprocess.run([str(python), '-m', 'pip', '--disable-pip-version-check',
                        'install', 'oci==' + SDK_VERSION], check=True, stdout=sys.stderr)
        ready = probe(python)
        if not ready:
            raise RuntimeError('Runtime setup failed capability validation; no SR write sent.')
        return python, ready
    finally:
        lock.unlink()
