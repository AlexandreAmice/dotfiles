"""Check GPU selection with synthetic sysfs and a recording compositor."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class SwaySessionTests(unittest.TestCase):
    def launch(self, drivers, override=None, connected=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            drm = root / "drm"
            drm.mkdir()
            for card, driver in drivers.items():
                device = drm / card / "device"
                device.mkdir(parents=True)
                target = root / "drivers" / driver
                target.mkdir(parents=True, exist_ok=True)
                (device / "driver").symlink_to(target)
            for card in connected:
                connector = drm / (card + '-DP-1')
                connector.mkdir()
                (connector / 'status').write_text('connected\n')
            # A connector must never become a DRM device in the selected list.
            (drm / "card0-HDMI-A-1").mkdir()
            compositor = root / "sway"
            compositor.write_text(
                "#!/usr/bin/python3\nimport json, os, sys\n"
                "print(json.dumps({'args': sys.argv[1:], "
                "'devices': os.environ.get('WLR_DRM_DEVICES'), "
                "'desktop': os.environ.get('XDG_CURRENT_DESKTOP')}))\n")
            compositor.chmod(0o755)
            launcher = root / "start-sway"
            source = (SOURCE_ROOT / "private_dot_local/bin/executable_start-sway").read_text()
            launcher.write_text(source.replace('/sys/class/drm', str(drm))
                               .replace('/usr/bin/sway', str(compositor)))
            env = os.environ.copy()
            env.pop('WLR_DRM_DEVICES', None)
            env['XDG_STATE_HOME'] = str(root / 'state')
            if override is not None:
                env['WLR_DRM_DEVICES'] = override
            result = subprocess.run(['/bin/sh', str(launcher), '--test'],
                                    env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, '')
            return json.loads((root / 'state/sway/session.log').read_text())

    def test_non_nvidia_and_nouveau_keep_default_gpu_selection(self):
        for drivers in ({}, {'card3': 'i915'}, {'card2': 'amdgpu'}, {'card0': 'nouveau'}):
            with self.subTest(drivers=drivers):
                self.assertEqual(self.launch(drivers),
                                 {'args': ['--debug', '--test'], 'devices': None, 'desktop': 'sway'})

    def test_hybrid_gpu_selection_does_not_depend_on_pci_or_card_number(self):
        result = self.launch({'card7': 'nvidia', 'card4': 'i915', 'card9': 'amdgpu'}, connected=('card4', 'card9'))
        self.assertEqual(result['args'], ['--debug', '--unsupported-gpu', '--test'])
        self.assertEqual(result['devices'], '/dev/dri/card4:/dev/dri/card9:/dev/dri/card7')

    def test_nvidia_only_keeps_its_device(self):
        result = self.launch({'card2': 'nvidia'})
        self.assertEqual(result['args'], ['--debug', '--unsupported-gpu', '--test'])
        self.assertEqual(result['devices'], '/dev/dri/card2')

    def test_monitor_on_nvidia_with_disconnected_intel(self):
        result = self.launch({'card1': 'i915', 'card2': 'nvidia'}, connected=('card2',))
        self.assertEqual(result['devices'], '/dev/dri/card2:/dev/dri/card1')

    def test_monitors_on_both_gpus_keep_both_available(self):
        result = self.launch({'card1': 'i915', 'card2': 'nvidia'}, connected=('card1', 'card2'))
        self.assertEqual(result['devices'], '/dev/dri/card1:/dev/dri/card2')

    def test_explicit_device_selection_is_preserved(self):
        result = self.launch({'card2': 'nvidia', 'card1': 'i915'}, '/dev/dri/card2')
        self.assertEqual(result['devices'], '/dev/dri/card2')
        self.assertIn('--unsupported-gpu', result['args'])


if __name__ == '__main__':
    unittest.main()
