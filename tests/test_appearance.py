import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / 'private_dot_local/bin/executable_apply-appearance.tmpl'
loader = importlib.machinery.SourceFileLoader('appearance', str(source))
spec = importlib.util.spec_from_loader(loader.name, loader)
appearance = importlib.util.module_from_spec(spec)
loader.exec_module(appearance)


class AppearanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name)
        env = patch.dict(os.environ, {'HOME': str(self.home), 'CHEZMOI_DEST_DIR': str(self.home), 'XDG_STATE_HOME': str(self.home / '.local/state'),
                                     'XDG_DATA_HOME': str(self.home / '.local/share')})
        env.start()
        self.addCleanup(env.stop)

    def invoke(self, *args, system='Darwin'):
        with patch('sys.argv', ['apply-appearance', *args]), patch.object(appearance.platform, 'system', return_value=system):
            appearance.main()

    def test_initialization_preserves_saved_choices(self):
        state, data, _, _ = appearance.initialize('Darwin')
        (state / 'mood').write_text('dusk\n')
        (state / 'opacity').write_text('0.89\n')
        (state / 'ghostty-opacity.conf').unlink()
        _, _, mood, opacity = appearance.initialize('Darwin')
        self.assertEqual((mood, opacity), ('dusk', '0.89'))
        self.assertEqual((state / 'ghostty-opacity.conf').read_text(), 'background-opacity = 0.89\n')

    def test_solid_and_platform_opacity(self):
        with patch.object(appearance, 'BACKGROUND', '1a1b26'):
            for system, filename, expected in [('Darwin', 'ghostty-opacity.conf', 'background-opacity = 1.00\n'),
                                                ('Linux', 'foot-opacity.ini', '[colors-dark]\nalpha=1.00\n')]:
                self.invoke('--mood', 'solid', '--opacity', '1.00', '--no-native', '--quiet', system=system)
                state, data = appearance.paths()
                self.assertEqual((state / filename).read_text(), expected)
                self.assertEqual((state / 'wallpaper.png').resolve(), (data / 'solid.png').resolve())
                self.assertTrue(((data / 'solid.png').resolve()).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))

    def test_artwork_modes_and_portrait_fallback(self):
        state, data, _, _ = appearance.initialize('Darwin')
        (data / 'wallpapers').mkdir(parents=True)
        for mood in ('midnight', 'dusk', 'dawn'):
            image = data / 'wallpapers' / (mood + '.png')
            image.write_bytes(b'fixture')
            with patch.object(appearance, 'native_apply') as native:
                self.invoke('--mood', mood, '--quiet')
                native.assert_called_once_with('Darwin', image, image)
            self.assertEqual((state / 'mood').read_text().strip(), mood)

    def test_missing_artwork_does_not_apply_native_settings(self):
        with patch.object(appearance, 'native_apply') as native:
            with self.assertRaisesRegex(RuntimeError, 'Missing wallpaper'):
                self.invoke('--mood', 'dawn')
            native.assert_not_called()

    def test_temporary_destination_never_changes_host(self):
        with patch.dict(os.environ, {'CHEZMOI_DEST_DIR': '/another/home'}), \
                patch.object(appearance, 'BACKGROUND', '1a1b26'), patch.object(appearance, 'native_apply') as native:
            self.invoke('--mood', 'solid', '--quiet')
            native.assert_not_called()

    def test_sway_rotated_screens_choose_portrait(self):
        outputs = [{'name': 'wide', 'active': True, 'transform': 'normal'},
                   {'name': 'tall', 'active': True, 'transform': '90'}]
        with patch.dict(os.environ, {'SWAYSOCK': 'fixture'}), \
                patch.object(appearance.shutil, 'which', side_effect=lambda cmd: cmd == 'swaymsg'), \
                patch.object(appearance.subprocess, 'check_output', return_value=json.dumps(outputs)), \
                patch.object(appearance.subprocess, 'run') as run:
            appearance.native_apply('Linux', Path('/wide.png'), Path('/tall.png'))
            self.assertEqual(run.call_args_list[0].args[0][-2], '/wide.png')
            self.assertEqual(run.call_args_list[1].args[0][-2], '/tall.png')

    def test_mac_permission_error_is_actionable(self):
        with patch.object(appearance.subprocess, 'run') as run:
            run.side_effect = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1, '', ''),
                               subprocess.CompletedProcess([], 1, '', 'not authorized')]
            with self.assertRaisesRegex(RuntimeError, 'Automation > System Events'):
                appearance.native_apply('Darwin', Path('/wide.png'), Path('/tall.png'))

    def test_existing_dark_mode_skips_automation(self):
        with patch.object(appearance.subprocess, 'run') as run:
            run.side_effect = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0, 'Dark\n'),
                               subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0)]
            appearance.native_apply('Darwin', Path('/wide.png'), Path('/tall.png'))
            self.assertEqual(sum(call.args[0][0] == 'osascript' for call in run.call_args_list), 1)


if __name__ == '__main__':
    unittest.main()
