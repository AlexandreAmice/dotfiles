"""Exercise SwayNC's command boundary without touching the live desktop."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class NotificationFocusTests(unittest.TestCase):
    def test_action_expands_home_and_preserves_notification_environment(self):
        config = json.loads((SOURCE_ROOT / "private_dot_config/swaync/config.json").read_text())
        action = config["scripts"]["focus-application-on-action"]
        self.assertEqual(action["run-on"], "action")
        with tempfile.TemporaryDirectory(prefix="notification home ") as directory:
            home = Path(directory)
            helper = home / ".local/bin/focus-notification-app"
            helper.parent.mkdir(parents=True)
            helper.write_text('#!/bin/sh\nprintf "%s\\n" "$SWAYNC_APP_NAME" "$SWAYNC_DESKTOP_ENTRY"\n')
            helper.chmod(0o755)
            env = dict(os.environ, HOME=str(home), SWAYNC_APP_NAME="Signal Desktop",
                       SWAYNC_DESKTOP_ENTRY="signal.desktop")
            # SwayNC 0.9's Script.run_script uses exec.split(" "), preserving
            # quote characters. A shell parser here would hide broken commands.
            result = subprocess.run(action["exec"].split(" "), env=env, cwd="/",
                                    capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.splitlines(), ["Signal Desktop", "signal.desktop"])

    def test_notification_matches_wayland_and_xwayland_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            swaymsg = root / "swaymsg"
            tree = {"nodes": [
                {"type": "con", "id": 9, "app_id": "signal", "focused": False},
                {"type": "con", "id": 10, "window_properties": {"class": "pcloud"}},
                {"type": "con", "id": 11, "app_id": "foot", "focused": True},
            ]}
            swaymsg.write_text("#!/bin/sh\ncat <<'TREE'\n" + json.dumps(tree) + "\nTREE\n")
            swaymsg.chmod(0o755)
            for app, desktop, expected in (("Signal", "signal.desktop", "9"),
                                            ("pCloud", "", "10"), ("Missing", "", "")):
                with self.subTest(app=app):
                    env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                               SWAYNC_APP_NAME=app, SWAYNC_DESKTOP_ENTRY=desktop,
                               FOCUS_HELPER_DRY_RUN="1")
                    result = subprocess.run([str(SOURCE_ROOT / "private_dot_local/bin/executable_focus-notification-app")],
                                            env=env, capture_output=True, text=True, check=True)
                    self.assertEqual(result.stdout.strip(), expected)

    def test_pcloud_uses_installed_appimage_without_personal_launcher(self):
        with tempfile.TemporaryDirectory(prefix="pcloud home ") as directory:
            root = Path(directory)
            binary = root / ".local/opt/pcloud/pCloud.AppImage"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            mocks = root / "bin"
            mocks.mkdir()
            scripts = {
                "setsid": '#!/bin/sh\nprintf "%s\\n" "$2" > "$HOME/launched"\n',
                "sleep": "#!/bin/sh\nexit 0\n",
                "swaymsg": '''#!/bin/sh
if [ "$2" = --type ]; then
    if [ -f "$HOME/launched" ]; then
        printf '%s\n' '{"type":"con","id":10,"window_properties":{"class":"pcloud"}}'
    else
        printf '%s\n' '{"type":"root"}'
    fi
else
    printf '%s\n' "$*" > "$HOME/focused"
fi
''',
            }
            for name, content in scripts.items():
                path = mocks / name
                path.write_text(content)
                path.chmod(0o755)
            env = dict(os.environ, HOME=str(root), PATH=str(mocks) + os.pathsep + os.environ["PATH"])
            subprocess.run([str(SOURCE_ROOT / "private_dot_local/bin/executable_focus-pcloud")],
                           env=env, check=True, timeout=5)
            self.assertEqual((root / "launched").read_text().strip(), str(binary))
            self.assertIn("[con_id=10] focus", (root / "focused").read_text())


if __name__ == "__main__":
    unittest.main()
