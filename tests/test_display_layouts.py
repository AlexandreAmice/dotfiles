#!/usr/bin/env python3
"""Unit tests for the Sway display layout controller."""

from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SOURCE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SOURCE_ROOT / "private_dot_local/bin/executable_display-layouts"
SPEC = importlib.util.spec_from_loader(
    "display_layouts", SourceFileLoader("display_layouts", str(SCRIPT))
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {SCRIPT}")
display_layouts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(display_layouts)


class DisplayLayoutsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.original_state = display_layouts.STATE_PATH
        self.original_lock = display_layouts.LOCK_PATH
        self.original_workspaces = display_layouts.NWG_WORKSPACES_PATH
        self.original_rules = display_layouts.WORKSPACE_RULES_PATH
        display_layouts.STATE_PATH = root / "display-layouts.json"
        display_layouts.LOCK_PATH = root / "display-layouts.lock"
        display_layouts.NWG_WORKSPACES_PATH = root / "workspaces"
        display_layouts.WORKSPACE_RULES_PATH = root / "workspace-outputs.conf"

    def tearDown(self) -> None:
        display_layouts.STATE_PATH = self.original_state
        display_layouts.LOCK_PATH = self.original_lock
        display_layouts.NWG_WORKSPACES_PATH = self.original_workspaces
        display_layouts.WORKSPACE_RULES_PATH = self.original_rules
        self.temp_dir.cleanup()

    def test_missing_daemon_dependency_fails_without_notifications(self) -> None:
        with (
            patch.dict(sys.modules, {"i3ipc": None}),
            patch.object(sys, "argv", ["display-layouts", "daemon"]),
            patch.object(sys, "stderr", new_callable=io.StringIO) as stderr,
            patch.object(display_layouts, "notify") as notify,
            patch.object(display_layouts, "apply_profile") as apply_profile,
        ):
            self.assertEqual(display_layouts.main(), os.EX_CONFIG)
        notify.assert_not_called()
        apply_profile.assert_not_called()
        self.assertIn("sudo apt install python3-i3ipc", stderr.getvalue())

    def test_other_daemon_failures_are_logged_without_notifications(self) -> None:
        with (
            patch.object(sys, "argv", ["display-layouts", "daemon"]),
            patch.object(sys, "stderr", new_callable=io.StringIO) as stderr,
            patch.object(display_layouts, "notify") as notify,
            patch.object(
                display_layouts, "daemon",
                side_effect=display_layouts.LayoutError("Sway is unavailable"),
            ),
        ):
            self.assertEqual(display_layouts.main(), 1)
        notify.assert_not_called()
        self.assertIn("Sway is unavailable", stderr.getvalue())

    def test_interactive_failures_still_notify(self) -> None:
        with (
            patch.object(sys, "argv", ["display-layouts", "gui"]),
            patch.object(sys, "stderr", new_callable=io.StringIO),
            patch.object(display_layouts, "notify") as notify,
            patch.object(
                display_layouts, "run_gui",
                side_effect=display_layouts.LayoutError("nwg-displays is unavailable"),
            ),
        ):
            self.assertEqual(display_layouts.main(), 1)
        notify.assert_called_once_with(
            "Display layout error", "nwg-displays is unavailable", critical=True,
        )

    def test_identity_prefers_description_with_serial(self) -> None:
        output = {
            "name": "DP-7",
            "make": "Acer Technologies",
            "model": "R271",
            "serial": "T60AA0012411",
        }
        self.assertEqual(
            display_layouts.output_identity(output),
            "description:Acer Technologies R271 T60AA0012411",
        )

    def test_identity_falls_back_to_connector_without_serial(self) -> None:
        output = {
            "name": "eDP-1",
            "make": "Sharp Corporation",
            "model": "0x1518",
            "serial": "Unknown",
        }
        self.assertEqual(
            display_layouts.output_identity(output),
            "connector:eDP-1:Sharp Corporation 0x1518",
        )

    def test_profile_match_requires_exact_monitor_set(self) -> None:
        state = {
            "version": 1,
            "profiles": {
                "dock": {"monitors": ["connector:eDP-1", "description:Dock 1"]}
            },
        }
        key, _ = display_layouts.find_profile(
            state, ["connector:eDP-1", "description:Dock 1"]
        )
        self.assertEqual(key, "dock")
        key, profile = display_layouts.find_profile(state, ["connector:eDP-1"])
        self.assertIsNone(key)
        self.assertIsNone(profile)

    def test_state_update_is_atomic_and_idempotent(self) -> None:
        def add_profile(state: dict) -> bool:
            state["profiles"]["mobile"] = {"monitors": ["connector:eDP-1"]}
            return True

        original_sync = display_layouts.sync_to_chezmoi
        display_layouts.sync_to_chezmoi = lambda: None
        try:
            self.assertTrue(display_layouts.update_state(add_profile))
        finally:
            display_layouts.sync_to_chezmoi = original_sync
        state = json.loads(display_layouts.STATE_PATH.read_text())
        self.assertEqual(state["profiles"]["mobile"]["monitors"], ["connector:eDP-1"])
        leftovers = list(display_layouts.STATE_PATH.parent.glob(".display-layouts.json.*"))
        self.assertEqual(leftovers, [])

    def test_nwg_workspace_parser_resolves_names_and_descriptions(self) -> None:
        display_layouts.NWG_WORKSPACES_PATH.write_text(
            "workspace 1 output DP-7\n"
            "workspace 2 output 'Dell Inc. DELL U3011 PH5NY1BH326L'\n"
        )
        outputs = [
            {
                "name": "DP-7",
                "make": "Acer",
                "model": "R271",
                "serial": "ABC",
            },
            {
                "name": "DP-8",
                "make": "Dell Inc.",
                "model": "DELL U3011",
                "serial": "PH5NY1BH326L",
            },
        ]
        self.assertEqual(
            display_layouts.parse_nwg_workspaces(outputs),
            {
                "1": "description:Acer R271 ABC",
                "2": "description:Dell Inc. DELL U3011 PH5NY1BH326L",
            },
        )

    def test_seed_profiles_assign_all_ten_workspaces(self) -> None:
        state = json.loads(
            (SOURCE_ROOT / "private_dot_config/sway/private_display-layouts.json").read_text()
        )
        display_layouts.validate_state(state)
        self.assertTrue(
            {"Office", "Home", "Mobile"}
            <= {profile["label"] for profile in state["profiles"].values()},
        )
        for profile in state["profiles"].values():
            self.assertEqual(set(profile["workspaces"]), set(display_layouts.WORKSPACE_NAMES))
            self.assertTrue(set(profile["workspaces"].values()) <= set(profile["monitors"]))

    def test_unknown_monitor_set_is_not_applied(self) -> None:
        display_layouts.STATE_PATH.write_text('{"version": 1, "profiles": {}}\n')
        output = {
            "name": "DP-1",
            "make": "Example",
            "model": "Panel",
            "serial": "123",
            "non_desktop": False,
        }
        original_outputs = display_layouts.connected_outputs
        original_command = display_layouts.sway_command
        display_layouts.connected_outputs = lambda: [output]
        display_layouts.sway_command = lambda _command: self.fail(
            "unknown monitor set issued a Sway command"
        )
        try:
            self.assertFalse(display_layouts.apply_profile())
        finally:
            display_layouts.connected_outputs = original_outputs
            display_layouts.sway_command = original_command

    def test_saved_profile_applies_output_and_workspace_rules(self) -> None:
        identity = "description:Example Panel 123"
        profile = {
            "label": "Test",
            "monitors": [identity],
            "outputs": [
                {
                    "identity": identity,
                    "enabled": True,
                    "mode": "1920x1080@60Hz",
                    "position": [10, 20],
                    "scale": 1.0,
                    "transform": "normal",
                    "scale_filter": "smart",
                    "adaptive_sync": False,
                    "dpms": True,
                }
            ],
            "workspaces": {name: identity for name in display_layouts.WORKSPACE_NAMES},
        }
        display_layouts.STATE_PATH.write_text(
            json.dumps({"version": 1, "profiles": {"test": profile}})
        )
        output = {
            "name": "DP-1",
            "make": "Example",
            "model": "Panel",
            "serial": "123",
            "active": True,
            "non_desktop": False,
        }
        commands: list[str] = []
        original_outputs = display_layouts.connected_outputs
        original_command = display_layouts.sway_command
        original_json = display_layouts.sway_json
        original_hook = display_layouts.run_output_hook
        original_sleep = display_layouts.time.sleep
        display_layouts.connected_outputs = lambda: [output]
        display_layouts.sway_command = commands.append
        display_layouts.sway_json = lambda _message_type: []
        display_layouts.run_output_hook = lambda: None
        display_layouts.time.sleep = lambda _seconds: None
        try:
            self.assertTrue(display_layouts.apply_profile())
        finally:
            display_layouts.connected_outputs = original_outputs
            display_layouts.sway_command = original_command
            display_layouts.sway_json = original_json
            display_layouts.run_output_hook = original_hook
            display_layouts.time.sleep = original_sleep
        self.assertIn(
            'output "DP-1" enable mode 1920x1080@60Hz pos 10 20 '
            "transform normal scale 1 scale_filter smart adaptive_sync off dpms on",
            commands,
        )
        self.assertIn("reload", commands)
        self.assertEqual(
            len(display_layouts.WORKSPACE_RULES_PATH.read_text().splitlines()), 11
        )

    def test_reassignment_replaces_old_output_priority_and_survives_reload(self) -> None:
        live = {
            "laptop": {"name": "eDP-1", "active": True},
            "monitor": {"name": "DP-12", "active": True},
        }
        # Model Sway 1.9: output commands append; reload clears the old rules.
        priorities: list[str] = []

        def command(value: str) -> None:
            if value == "reload":
                priorities.clear()
                for line in display_layouts.WORKSPACE_RULES_PATH.read_text().splitlines():
                    if line.startswith("workspace "):
                        command(line)
            elif value.startswith('workspace "4" output '):
                priorities.append(json.loads(value.split(" output ", 1)[1]))

        with patch.object(display_layouts, "sway_command", side_effect=command) as send:
            display_layouts.replace_workspace_rules({"workspaces": {"4": "laptop"}}, live)
            display_layouts.replace_workspace_rules({"workspaces": {"4": "monitor"}}, live)
            self.assertEqual(priorities, ["DP-12"])
            command("reload")
            self.assertEqual(priorities, ["DP-12"])
            send.reset_mock()
            display_layouts.replace_workspace_rules({"workspaces": {"4": "monitor"}}, live)
            send.assert_not_called()

    def test_reassignment_moves_existing_workspace_and_restores_focus(self) -> None:
        live = {"monitor": {"name": "DP-12", "active": True}}
        with (
            patch.object(display_layouts, "sway_json", return_value=[
                {"name": "4", "output": "eDP-1", "focused": True},
            ]),
            patch.object(display_layouts, "sway_command") as send,
        ):
            display_layouts.apply_workspace_profile({"workspaces": {"4": "monitor"}}, live)
        self.assertEqual([call.args[0] for call in send.call_args_list], [
            "reload",
            'workspace --no-auto-back-and-forth number "4"; move workspace to output "DP-12"',
            'workspace --no-auto-back-and-forth "4"',
        ])

    def test_gui_assignment_wins_over_current_workspace_location(self) -> None:
        outputs = [
            {"name": "eDP-1", "make": "Laptop", "model": "Panel", "active": True},
            {"name": "DP-12", "make": "Acer", "model": "Panel", "serial": "123", "active": True},
        ]
        target = display_layouts.output_identity(outputs[1])

        def edit_workspaces(*_args, **_kwargs):
            # The workspace Apply button saves this file before the GUI exits.
            display_layouts.NWG_WORKSPACES_PATH.write_text("workspace 4 output DP-12\n")
            return type("Result", (), {"returncode": 0})()

        with (
            patch.object(display_layouts.shutil, "which", return_value="nwg-displays"),
            patch.object(display_layouts, "connected_outputs", return_value=outputs),
            patch.object(display_layouts, "sway_json", return_value=[
                {"name": "4", "output": "eDP-1", "focused": True},
            ]),
            patch.object(display_layouts, "NWG_OUTPUTS_PATH", Path(self.temp_dir.name) / "outputs"),
            patch.object(display_layouts.subprocess, "run", side_effect=edit_workspaces),
            patch.object(display_layouts, "sway_command") as send,
            patch.object(display_layouts, "sync_to_chezmoi"),
            patch.object(display_layouts, "notify"),
        ):
            self.assertEqual(display_layouts.run_gui(), 0)
        _, profile = display_layouts.find_profile(
            display_layouts.load_state(), display_layouts.monitor_set(outputs)
        )
        self.assertEqual(profile["workspaces"]["4"], target)
        self.assertIn('workspace "4" output "DP-12"', display_layouts.WORKSPACE_RULES_PATH.read_text())
        send.assert_any_call(
            'workspace --no-auto-back-and-forth number "4"; move workspace to output "DP-12"'
        )


if __name__ == "__main__":
    unittest.main()
