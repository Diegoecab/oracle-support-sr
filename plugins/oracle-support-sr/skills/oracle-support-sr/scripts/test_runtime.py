import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import runtime_env as runtime
import run_sr


class RuntimeTests(unittest.TestCase):
    def test_missing_upload_is_reported_before_credentials(self):
        client = type('OldClient', (), {name: lambda: None for name in runtime.REQUIRED_METHODS if name != 'put_attachment'})
        sdk = SimpleNamespace(__version__='2.152.0', cims=SimpleNamespace(IncidentClient=client))
        with self.assertRaisesRegex(RuntimeError, 'put_attachment.*run_sr.py'):
            runtime.require_capabilities(sdk)

    def test_launcher_forwards_all_scope_and_approval_arguments(self):
        args = ['--profile', 'fixture', '--mode', 'MANUAL', 'close', '--key', 'fixture-key',
                '--approval-digest', 'approved-fixture', '--execute']
        with patch.object(run_sr, 'ensure_runtime', return_value=(Path('/isolated/python'), {})), \
             patch.object(run_sr.subprocess, 'call', return_value=7) as call:
            self.assertEqual(run_sr.main(args), 7)
        self.assertEqual(call.call_args.args[0][2:], args)

    def test_failed_setup_never_invokes_sr_helper(self):
        with patch.object(run_sr, 'ensure_runtime', side_effect=RuntimeError('Setup failed')), \
             patch.object(run_sr.subprocess, 'call') as call:
            with self.assertRaisesRegex(RuntimeError, 'Setup failed'):
                run_sr.main(['create', '--execute'])
        call.assert_not_called()

    def test_valid_existing_runtime_is_reused_without_installing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            python = runtime.interpreter(root)
            python.parent.mkdir(parents=True, exist_ok=True)
            python.touch()
            with patch.object(runtime, 'runtime_root', return_value=root), \
                 patch.object(runtime, 'probe', return_value={'put_attachment': True}), \
                 patch.object(runtime.subprocess, 'run') as run:
                actual, _ = runtime.ensure_runtime()
            self.assertEqual(actual, python)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
