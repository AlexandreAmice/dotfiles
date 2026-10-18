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


if __name__ == "__main__":
    unittest.main()
