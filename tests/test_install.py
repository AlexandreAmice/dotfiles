"""Exercise installer failure handling without downloads or system changes."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def run_installer(self, failures, component=None, platform="Linux", rust_available=True,
                      arguments=(), rustup_available=False, pcloud_installed=False,
                      architecture="amd64", package_audit="", legacy_signal=None,
                      foot_version=None, footclient_installed=True, legacy_foot=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            shutil.copy2(SOURCE_ROOT / "scripts/install", scripts)
            # Simulated installs must not inspect the host's OS, apps, or sources.
            os_release = root / "os-release"
            os_release.write_text('ID=ubuntu\nVERSION_ID="24.04"\nVERSION_CODENAME=noble\n')
            signal_source = root / "signal-xenial.list"
            if legacy_signal is not None:
                signal_source.write_text(legacy_signal)
            installer = scripts / "install"
            installer.write_text(installer.read_text().replace("/etc/os-release", str(os_release))
                                 .replace("/Applications/", str(root / "Applications") + "/")
                                 .replace("/etc/apt/sources.list.d/signal-xenial.list", str(signal_source))
                                 .replace("/usr/local/bin/foot", str(root / "local/bin/foot")))
            shutil.copytree(SOURCE_ROOT / "packages", root / "packages")
            shutil.copy2(SOURCE_ROOT / ".chezmoidata.yaml", root)
            mock_bin = root / "bin"
            mock_bin.mkdir()
            if pcloud_installed:
                (root / "Applications/pCloud Drive.app").mkdir(parents=True)
                binary = root / ".local/opt/pcloud/pCloud.AppImage"
                binary.parent.mkdir(parents=True)
                binary.touch(mode=0o755)
            log = root / "commands.log"
            log.touch()
            mock = mock_bin / "mock"
            mock.write_text(f"#!{sys.executable}\n" + '''
import fnmatch
import json
import os
from pathlib import Path
import sys
name = Path(sys.argv[0]).name
args = sys.argv[1:]
if name == "sh" and args[:3] == ["-eu", "-s", "--"]:
    name = "install-" + args[3]
    args = []
command = " ".join([name, *args])
with open(os.environ["INSTALL_TEST_LOG"], "a") as log:
    log.write(command + "\\n")
if any(fnmatch.fnmatchcase(command, pattern)
       for pattern in os.environ["INSTALL_TEST_FAILURES"].split("\\n")):
    sys.exit(7)
if name in ("cargo", "rustc") and args == ["--version"]:
    ready = Path(os.environ["HOME"]) / ".rust-ready"
    if os.environ["INSTALL_TEST_RUST_AVAILABLE"] != "1" and not ready.exists():
        sys.exit(1)
    print(name + " 1.90.0")
elif (name == "sh" and "--no-modify-path" in args) or name == "rustup":
    (Path(os.environ["HOME"]) / ".rust-ready").touch()
elif name == "cargo" and args[0] == "install":
    binary = Path(os.environ["HOME"]) / ".cargo/bin/automatic-timezoned"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.symlink_to(Path(sys.argv[0]).resolve())
elif name == "automatic-timezoned":
    print("automatic-timezoned 2.0.160")
elif name == "uname":
    print(os.environ["INSTALL_TEST_PLATFORM"])
elif name == "dpkg" and args == ["--print-architecture"]:
    print(os.environ["INSTALL_TEST_ARCH"])
elif name == "dpkg" and args[0] == "--compare-versions":
    version = lambda text: tuple(int(part) for part in text.split("."))
    sys.exit(0 if version(args[1]) >= version(args[3]) else 1)
elif name == "sudo" and args == ["dpkg", "--audit"]:
    print(os.environ["INSTALL_TEST_PACKAGE_AUDIT"], end="")
elif name == "foot" and args == ["--version"]:
    print("foot version: " + os.environ["INSTALL_TEST_FOOT_VERSION"])
elif name == "dpkg-query":
    print("ii ")
elif name == "getent":
    print("video:x:44:")
elif name == "curl" and "getpublinkdownload" in command:
    print(json.dumps(dict(result=0, hosts=["downloads.example.invalid"], path="/pcloud", dwltag="test")))
elif name == "pkgutil":
    print("1. Developer ID Installer: PCLOUD LTD (KSTWHH4JHP)")
elif name == "snap":
    sys.exit(1)
''')
            mock.chmod(0o755)
            for name in ("uname", "dpkg", "sudo", "wget", "gpg", "curl",
                         "sha256sum", "install", "snap", "find", "getent", "sh", "dpkg-query", "brew", "cargo", "rustc", "pkgutil", "spctl", "installer"):
                (mock_bin / name).symlink_to(mock)
            if rustup_available:
                (mock_bin / "rustup").symlink_to(mock)
            if foot_version is not None:
                foot_bin = root / "local/bin"
                foot_bin.mkdir(parents=True)
                (foot_bin / "foot").symlink_to(mock)
                if footclient_installed:
                    (foot_bin / "footclient").symlink_to(mock)
            if legacy_foot:
                old_install = root / ".local/opt/foot-1.21.0"
                (old_install / "bin").mkdir(parents=True)
                (old_install / "bin/foot").touch(mode=0o755)
                (root / ".local/bin").mkdir(parents=True)
                for name in ("foot", "footclient"):
                    (root / ".local/bin" / name).symlink_to(old_install / "bin/foot")
            # A closed PATH prevents any unmocked installer from escaping to
            # host rustup, package managers, or network tools.
            for name in ("dirname", "id", "awk", "sed", "grep", "mktemp", "rm", "cat", "cut", "tr", "readlink", "mkdir", "tar", "jq"):
                (mock_bin / name).symlink_to(shutil.which(name))
            for name in ("check-ubuntu",):
                (scripts / name).symlink_to(mock)
            env = os.environ.copy()
            # Keep host-installed Rust and nwg-displays out of component tests.
            env.update(PATH=str(mock_bin), HOME=str(root), USER="installer-test",
                       INSTALL_TEST_LOG=str(log), INSTALL_TEST_FAILURES="\n".join(failures),
                       INSTALL_TEST_PLATFORM=platform, INSTALL_TEST_ARCH=architecture, CARGO_HOME=str(root / ".cargo"),
                       RUSTUP_HOME=str(root / ".rustup"),
                       INSTALL_TEST_PACKAGE_AUDIT=package_audit,
                       INSTALL_TEST_FOOT_VERSION=foot_version or "",
                       INSTALL_TEST_RUST_AVAILABLE="1" if rust_available else "0")
            if component is None:
                result = subprocess.run(["/bin/sh", str(scripts / "install"), *arguments],
                                        env=env, capture_output=True, text=True)
            else:
                marker = component.upper().replace("-", "_") + "_INSTALL"
                body = (scripts / "install").read_text().split(
                    f"<<'{marker}'\n", 1)[1].split(f"\n{marker}\n", 1)[0]
                result = subprocess.run(["/bin/sh", "-eu", "-s"], input=body,
                                        env=env, capture_output=True, text=True)
            if legacy_foot and result.returncode == 0:
                self.assertFalse(old_install.exists())
                for name in ("foot", "footclient"):
                    self.assertFalse((root / ".local/bin" / name).is_symlink())
            return result, log.read_text().splitlines()

    def test_success(self):
        result, commands = self.run_installer([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Software installation complete.", result.stdout)
        self.assertEqual(commands[-1], "check-ubuntu")
        self.assertLess(commands.index("sudo dpkg --audit"), commands.index("sudo apt-get update"))

    def test_unfinished_package_transaction_stops_before_changes(self):
        result, commands = self.run_installer([], package_audit="linux-headers-test is half-installed\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("linux-headers-test is half-installed", result.stderr)
        self.assertIn("sudo dpkg --configure -a", result.stderr)
        self.assertIn("sudo apt-get --fix-broken install", result.stderr)
        self.assertEqual([command for command in commands if command.startswith("sudo ")],
                         ["sudo dpkg --audit"])
        self.assertFalse(any(command.startswith(("wget ", "install-", "check-ubuntu"))
                             for command in commands))

    def test_failed_package_audit_stops_before_changes(self):
        result, commands = self.run_installer(["sudo dpkg --audit"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Could not inspect dpkg state", result.stderr)
        self.assertEqual(commands[-1], "sudo dpkg --audit")

    def test_personal_apps_are_installed_without_warp(self):
        result, commands = self.run_installer([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sudo apt-get install -y signal-desktop", commands)
        self.assertIn("install-pcloud-linux", commands)
        self.assertFalse(any("cloudflare" in command for command in commands))

    def test_failed_child_and_check_are_reported_after_later_steps(self):
        result, commands = self.run_installer(["install-foot", "install-nwg-displays", "check-ubuntu"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("install-codex", commands)
        self.assertEqual(commands[-1], "check-ubuntu")
        self.assertIn("3 failed step(s)", result.stderr)
        self.assertIn("Install nwg-displays (exit 7)", result.stderr)
        self.assertNotIn("Software installation complete.", result.stdout)

    def test_failed_package_update_continues(self):
        result, commands = self.run_installer(["sudo apt-get update"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("install-nwg-displays", commands)
        self.assertEqual(commands[-1], "check-ubuntu")
        self.assertIn("2 failed step(s)", result.stderr)

    def test_sway_session_is_registered_by_normal_install(self):
        result, commands = self.run_installer([])
        self.assertEqual(result.returncode, 0, result.stderr)
        launcher = next(i for i, command in enumerate(commands)
                        if command.endswith(" /usr/local/bin/start-sway"))
        session = next(i for i, command in enumerate(commands)
                       if command.endswith(" /usr/share/wayland-sessions/sway.desktop"))
        self.assertLess(launcher, session)

    def test_session_only_updates_sway_and_removes_duplicates(self):
        result, commands = self.run_installer([], arguments=('--sway-session',))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(command.endswith(' /usr/share/wayland-sessions/sway.desktop')
                            for command in commands))
        self.assertIn('sudo rm -f -- /usr/share/wayland-sessions/sway-dotfiles.desktop '
                      '/usr/share/wayland-sessions/sway-intel.desktop', commands)
        self.assertFalse(any('apt-get' in command or command.startswith('install-')
                             for command in commands))
        self.assertNotIn("sudo dpkg --audit", commands)

    def test_failed_sway_launcher_install_skips_session_entry(self):
        result, commands = self.run_installer(["sudo install */usr/local/bin/start-sway"])
        self.assertEqual(result.returncode, 1)
        self.assertFalse(any(command.endswith(" /usr/share/wayland-sessions/sway.desktop")
                             for command in commands))
        self.assertIn("Register Sway login session (exit 7)", result.stderr)
        self.assertEqual(commands[-1], "check-ubuntu")

    def test_failed_repository_download_skips_dependent_commands(self):
        result, commands = self.run_installer(["wget *microsoft.asc *"])
        self.assertEqual(result.returncode, 1)
        self.assertFalse(any("microsoft.gpg" in command for command in commands))
        self.assertFalse(any("vscode.sources" in command for command in commands))
        self.assertTrue(any("signal-desktop.sources" in command for command in commands))
        self.assertIn("install-nwg-displays", commands)
        self.assertIn("Configure VS Code repository (exit 7)", result.stderr)

    def test_nwg_component_download_failure_stops_before_install(self):
        result, commands = self.run_installer(["curl *"], component="nwg-displays")
        self.assertEqual(result.returncode, 7)
        self.assertTrue(any(command.startswith("curl ") for command in commands))
        self.assertFalse(any(command.startswith("sudo ") for command in commands))

    def test_signal_repository_precedes_manifest_install(self):
        result, commands = self.run_installer([])
        self.assertEqual(result.returncode, 0, result.stderr)
        repository = next(i for i, command in enumerate(commands)
                          if command.endswith(" /etc/apt/sources.list.d/signal-desktop.sources"))
        refresh = commands.index("sudo apt-get update", repository)
        packages = next(i for i, command in enumerate(commands)
                        if command.startswith("sudo apt-get install -y sway "))
        self.assertLess(repository, refresh)
        self.assertLess(refresh, packages)
        self.assertLess(refresh, commands.index("sudo apt-get install -y signal-desktop"))

    def test_signal_key_failure_skips_repository_install(self):
        for failure in ("wget *signal.asc *", "gpg *signal.asc"):
            with self.subTest(failure=failure):
                result, commands = self.run_installer([failure])
                self.assertEqual(result.returncode, 1)
                self.assertFalse(any(command.startswith("sudo install ") and "signal-desktop" in command
                                     for command in commands))
                self.assertIn("install-codex", commands)
                self.assertIn("Configure Signal repository (exit 7)", result.stderr)

    def test_legacy_signal_source_is_backed_up_after_replacement(self):
        source = ("# Signal Desktop\n\n"
                  "deb [arch=amd64 signed-by=/usr/share/keyrings/signal-desktop-keyring.gpg] "
                  "https://updates.signal.org/desktop/apt xenial main\n")
        result, commands = self.run_installer([], legacy_signal=source)
        self.assertEqual(result.returncode, 0, result.stderr)
        repository = next(i for i, command in enumerate(commands)
                          if command.endswith(" /etc/apt/sources.list.d/signal-desktop.sources"))
        backup = next(i for i, command in enumerate(commands)
                      if command.startswith("sudo mv --backup=numbered -- ")
                      and command.endswith("signal-xenial.list.bak"))
        self.assertLess(repository, backup)
        self.assertLess(backup, commands.index("sudo apt-get update", repository))

    def test_signal_replacement_failure_preserves_legacy_source(self):
        for failure in ("wget *signal.asc *", "gpg *signal.asc",
                        "sudo install */usr/share/keyrings/signal-desktop-keyring.gpg",
                        "sudo install */etc/apt/sources.list.d/signal-desktop.sources"):
            with self.subTest(failure=failure):
                result, commands = self.run_installer([failure], legacy_signal=
                    "deb https://updates.signal.org/desktop/apt xenial main\n")
                self.assertEqual(result.returncode, 1)
                self.assertFalse(any(command.startswith("sudo mv ") for command in commands))

    def test_signal_custom_source_is_preserved(self):
        result, commands = self.run_installer([], legacy_signal=
            "deb https://updates.signal.org/desktop/apt xenial main\n"
            "deb https://example.invalid/custom stable main\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Custom entries", result.stderr)
        self.assertFalse(any(command.startswith("sudo mv ") for command in commands))

    def test_signal_without_legacy_source_needs_no_migration(self):
        result, commands = self.run_installer([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(command.startswith("sudo mv ") for command in commands))

    def test_foot_component_checksum_failure_stops_before_build(self):
        result, commands = self.run_installer(["sha256sum *"], component="foot")
        self.assertEqual(result.returncode, 7)
        self.assertFalse(any(command.startswith("sudo ") for command in commands))

    def test_current_or_newer_foot_is_reused_and_legacy_override_removed(self):
        for version in ("1.28.0", "1.29.0"):
            with self.subTest(version=version):
                result, commands = self.run_installer([], component="foot", foot_version=version,
                                                      legacy_foot=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"Foot {version} is already installed", result.stdout)
                self.assertFalse(any(command.startswith(("curl ", "sudo ", "dpkg-query "))
                                     for command in commands))

    def test_old_or_incomplete_foot_still_downloads_replacement(self):
        for version, client in (("1.21.0", True), ("1.28.0", False)):
            with self.subTest(version=version, client=client):
                result, commands = self.run_installer(["sha256sum *"], component="foot",
                    foot_version=version, footclient_installed=client)
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertTrue(any(command.startswith("curl ") for command in commands))

    def test_macos_installs_homebrew_and_codex_without_ubuntu_packages(self):
        result, commands = self.run_installer([], platform="Darwin")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(command.startswith("brew bundle install ") for command in commands))
        self.assertIn("install-codex", commands)
        self.assertNotIn("install-foot", commands)
        self.assertIn("install-pcloud-macos", commands)
        self.assertFalse(any(command.startswith("sudo apt-get ") for command in commands))
        self.assertNotIn("sudo dpkg --audit", commands)

    def test_macos_brew_failure_still_attempts_codex(self):
        result, commands = self.run_installer(["brew bundle install *"], platform="Darwin")
        self.assertEqual(result.returncode, 1)
        self.assertIn("install-codex", commands)
        self.assertIn("Install Homebrew dependencies (exit 7)", result.stderr)

    def test_existing_working_rust_is_reused(self):
        result, commands = self.run_installer([], component="rust")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("cargo --version", commands)
        self.assertIn("rustc --version", commands)
        self.assertFalse(any(command.startswith("curl ") for command in commands))

    def test_missing_rust_installs_toolchain_without_editing_shell_files(self):
        result, commands = self.run_installer([], component="rust", rust_available=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any("https://sh.rustup.rs" in command for command in commands))
        self.assertTrue(any("--no-modify-path" in command for command in commands))
        self.assertEqual(commands[-2:], ["cargo --version", "rustc --version"])

    def test_failed_rust_download_never_runs_installer(self):
        result, commands = self.run_installer(["curl *"], component="rust", rust_available=False)
        self.assertEqual(result.returncode, 7)
        self.assertFalse(any("--no-modify-path" in command for command in commands))

    def test_timezone_daemon_is_installed_at_service_path(self):
        result, commands = self.run_installer([], component="automatic-timezoned")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(command.startswith("cargo install --locked --version 2.0.160 --root ")
                            and command.endswith(" automatic-timezoned") for command in commands))
        self.assertEqual(commands[-1], "automatic-timezoned --version")

    def test_failed_rust_steps_do_not_stop_other_installations(self):
        result, commands = self.run_installer(["install-rust", "install-automatic-timezoned"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("install-nwg-displays", commands)
        self.assertEqual(commands[-1], "check-ubuntu")
        self.assertIn("2 failed step(s)", result.stderr)

    def test_existing_rustup_repairs_missing_toolchain(self):
        result, commands = self.run_installer([], component="rust", rust_available=False,
                                              rustup_available=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rustup default stable", commands)
        self.assertFalse(any(command.startswith("curl ") for command in commands))

    def test_unsupported_linux_arch_skips_personal_binaries(self):
        result, commands = self.run_installer([], architecture="arm64")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("install-pcloud-linux", commands)
        self.assertFalse(any("signal-desktop" in command for command in commands))

    def test_pcloud_existing_installations_are_reused(self):
        for component in ("pcloud-linux", "pcloud-macos"):
            with self.subTest(component=component):
                result, commands = self.run_installer([], component=component, pcloud_installed=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(any(command.startswith(("curl ", "sudo ", "install "))
                                     for command in commands))

    def test_pcloud_verification_failure_never_installs(self):
        for component, failure in (("pcloud-linux", "sha256sum *"),
                                   ("pcloud-macos", "pkgutil *"),
                                   ("pcloud-macos", "spctl *")):
            with self.subTest(component=component, failure=failure):
                result, commands = self.run_installer([failure], component=component)
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertFalse(any(command.startswith(("sudo installer ", "install "))
                                     for command in commands))

    def test_pcloud_macos_verifies_before_installing(self):
        result, commands = self.run_installer([], component="pcloud-macos")
        self.assertEqual(result.returncode, 0, result.stderr)
        signature = next(i for i, command in enumerate(commands) if command.startswith("pkgutil "))
        assessment = next(i for i, command in enumerate(commands) if command.startswith("spctl "))
        installation = next(i for i, command in enumerate(commands) if command.startswith("sudo installer "))
        self.assertLess(signature, assessment)
        self.assertLess(assessment, installation)


if __name__ == "__main__":
    unittest.main()
