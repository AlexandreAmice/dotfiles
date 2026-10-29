import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


source = Path(__file__).resolve().parents[1] / 'private_dot_local/bin/executable_desktop-commands'
loader = importlib.machinery.SourceFileLoader('desktop_commands', str(source))
spec = importlib.util.spec_from_loader(loader.name, loader)
palette = importlib.util.module_from_spec(spec)
loader.exec_module(palette)


class PaletteDispatchTests(unittest.TestCase):
    def test_window_action_preserves_original_target(self):
        with patch.object(palette, 'catalog', return_value={'Close window': 'close'}), \
                patch('sys.argv', ['desktop-commands', '--select', '75', '1']), \
                patch.dict(os.environ, {'AEROSPACE_WORKSPACE': '2'}), \
                patch.object(palette.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, 'Close window\n')
            palette.main()
            self.assertEqual(run.call_args_list[1].args[0], ['aerospace', 'focus', '--window-id', '75'])
            self.assertEqual(run.call_args_list[2].args[0], ['aerospace', 'eval', 'close'])
            self.assertEqual(os.environ['AEROSPACE_WINDOW_ID'], '75')
            self.assertNotIn('AEROSPACE_WORKSPACE', os.environ)

    def test_cancel_does_not_dispatch(self):
        with patch.object(palette, 'catalog', return_value={'Close window': 'close'}), \
                patch('sys.argv', ['desktop-commands', '--select', '75', '1']), \
                patch.object(palette.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 130, '')
            palette.main()
            self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
