"""Install the same private marketplace plugin in Codex and/or Claude Code."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=('codex', 'claude', 'both'), default='both')
    parser.add_argument('--dry-run', action='store_true', help='Print the native commands without changing agent configuration')
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error('This pilot requires Python 3.11 or newer')
    agents = ('codex', 'claude') if args.agent == 'both' else (args.agent,)
    commands = []
    for agent in agents:
        binary = shutil.which(agent + '.cmd') if sys.platform == 'win32' else shutil.which(agent)
        binary = binary or shutil.which(agent)
        if not binary:
            parser.error(f'{agent} CLI is missing from PATH; install the intended client first')
        commands.append([binary, 'plugin', 'marketplace', 'add', 'Diegoecab/oracle-support-sr'])
        action = 'add' if agent == 'codex' else 'install'
        install = [binary, 'plugin', action, 'oracle-support-sr@diego-oci-support']
        if agent == 'claude':
            install.extend(['--scope', 'user'])
        commands.append(install)
    if args.dry_run:
        print(json.dumps({'state': 'dry_run', 'commands': commands}, indent=2))
        return 0
    try:
        version = importlib.metadata.version('oci')
        version_tuple = tuple(int(p) for p in version.split('.')[:3])
    except importlib.metadata.PackageNotFoundError:
        version_tuple = (0,)
    if version_tuple < (2, 177, 0):
        requirements = Path(__file__).resolve().parent / 'plugins/oracle-support-sr/skills/oracle-support-sr/requirements.txt'
        parser.error(f'Install the OCI SDK in your approved Python environment first: python -m pip install -r "{requirements}"')
    for command in commands:
        print(json.dumps({'running': command}), flush=True)
        subprocess.run(command, check=True)
    print('Plugin installed. Start a new agent session and use the Python environment with the OCI SDK. OCI credentials and permissions are configured separately.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
