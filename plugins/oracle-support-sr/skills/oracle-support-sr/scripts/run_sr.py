#!/usr/bin/env python3
"""Run the SR helper in its persistent, isolated, capability-checked OCI runtime."""
import json
from pathlib import Path
import subprocess
import sys
from runtime_env import ensure_runtime


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    helper = Path(__file__).resolve().with_name('sr.py')
    if args == ['--help']:
        return subprocess.call([sys.executable, str(helper), '--help'])
    python, capabilities = ensure_runtime()
    if args == ['--check-runtime']:
        print(json.dumps(capabilities, indent=2))
        return 0
    # Same helper and arguments: authorization, routing and receipt checks remain intact.
    return subprocess.call([str(python), str(helper), *args])


if __name__ == '__main__':
    raise SystemExit(main())
