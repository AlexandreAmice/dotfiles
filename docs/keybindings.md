# Keybinding conventions

This page is intentionally not an exhaustive shortcut list. Annotated `#@`
entries in `private_dot_config/sway/conf.d/50-keybindings.conf.tmpl` are the
source of truth. On a running Sway session, `Super+/` renders those annotations
as the complete searchable reference and can execute entries that carry a
Sway command. Rows show the category and action first, followed by the shortcut.
Search for familiar terms such as `screenshot`, `snip`, `monitor`, `workspace`,
`volume`, or `brightness`; monitor actions also include `screen` and `output`.
The palette matches each space-separated search term as a substring, ignoring
case and word order: `snip` finds the region screenshot, and `workspace right`
finds workspace movement to the right monitor. Shortcuts are searchable too.
Entries marked `[reference only]` describe terminal shortcuts and do not run
when selected. `Palette only` means the action runs from the palette but has
no dedicated shortcut. Enter selects an entry; Escape closes the palette.

Every bound Sway action must have an executable annotation. Alternate keys for
the same action can share an entry. `tests/validate-desktop` checks coverage
and verifies command dispatch against the rendered Linux configurations.

Both desktops use Super as the window-manager modifier: the Windows/Super key
on Ubuntu and Command on macOS. Desktop bindings take precedence over native
macOS app shortcuts, including Command+H and Command+T. Native clipboard
shortcuts remain available to applications.

On macOS, Hammerspoon translates common Ctrl shortcuts for GUI applications.
It sends the translated events directly to the active app so AeroSpace does
not intercept Save, Find, New Tab, Close Tab, or numbered tab selection.
The physical Command shortcuts above still operate the desktop.

| Ctrl shortcut | macOS app receives / usual action |
| --- | --- |
| Ctrl+A/C/V/X | Command+A/C/V/X: select all, copy, paste, cut |
| Ctrl+Z | Command+Z: undo |
| Ctrl+Y or Ctrl+Shift+Z | Command+Shift+Z: redo |
| Ctrl+S/O/N/P/Q | Command equivalents: save, open, new, print, quit |
| Ctrl+F/G | Command equivalents: find / next match |
| Ctrl+T/W/L/R/D | Command equivalents: new tab, close tab, address bar, reload, bookmark |
| Ctrl+B/I/U/K | Command equivalents: bold, italic, underline, link where supported |
| Ctrl+1–9 | Command+1–9: select tab where supported |
| Ctrl+plus/minus/0 | Command equivalents: zoom in/out/reset |
| Ctrl+/ | Command+/: comment toggle where supported |
| Ctrl+Shift+F/G/N/O/P/R/S/T/V/W/Z | Command+Shift equivalents, including reopen tab and save as |
| Ctrl+Left/Right, optionally Shift | Option+Left/Right, optionally Shift: move/select by word |
| Ctrl+Backspace/Delete, optionally Shift | Option equivalents: delete by word |
| Ctrl+Home/End, optionally Shift | Command+Up/Down, optionally Shift: document start/end or selection |

Actions follow each app's macOS bindings; not every app implements every action.
Ghostty, Terminal, iTerm2, Kitty, Alacritty, WezTerm, Warp, and Hyper are excluded
so their Ctrl shortcuts retain terminal behavior. Combinations including
Option or Command, and unlisted Ctrl shortcuts, pass through unchanged.
Word navigation and deletion modify the original events so holding a key
continues to repeat normally.

VS Code is also excluded from Hammerspoon: its managed macOS
`~/Library/Application Support/Code/User/keybindings.json` supplies native
Ctrl editing shortcuts with terminal-aware conditions. Ctrl+C always interrupts
in its integrated terminal, even with text selected. Ctrl+Shift+C copies the
selection, Ctrl+Shift+V pastes, and Ctrl+Backspace sends the shell's erase-word
control character. Holding Ctrl+Backspace repeats in both the editor and terminal.
Other editors' or browsers' embedded terminals still need their own configuration.

Directional operations follow H/J/K/L. A plain direction focuses, adding Alt
moves a window, and adding left Ctrl moves the whole workspace to an
adjacent monitor. Number keys select workspaces; Shift routes the focused window.

Important chords:

- `Super+T` / `Command+T`: plain terminal, suitable for transparent SSH use.
- Add `Shift`: independent persistent local tmux terminal.
- Add left Ctrl instead: agent-aware Herdr workspace.
- `Super+/`: searchable desktop command palette and shortcut reference.
- `Super+D`: application launcher (Spotlight on macOS).
- `Super+C` on Ubuntu / `Command+Ctrl+C` on macOS: system controls.
- `Super+P`: lock and power menu.
- `Super+Shift+X`: lock immediately.
- `Super+R`: enter resize mode; use H/J/K/L and Escape to exit.
- `Print Screen`: copy a screenshot of all screens to the clipboard.
- `Shift+Print Screen`: select a region and copy its screenshot to the clipboard.

Screenshot actions copy an image for pasting; they do not save a file. Volume,
microphone mute, media playback, brightness, and individual resize actions
are also available directly from the palette.

The Displays entry under `Super+C` opens nwg-displays for both monitor geometry
and workspace placement. Close the GUI after applying changes to save the
active monitor-set profile; subsequent whole-workspace moves are saved
automatically.

The Kinesis Advantage2 places Super, Space, and Enter in one thumb cluster, so
Sway deliberately defines no Super+Space or Super+Return chord. Tmux uses its
existing prefix-free pane controls plus the ordinary `Ctrl+B` prefix for
window and persistence operations. Herdr also uses `Ctrl+B`, but only in its
own terminal windows; do not nest either multiplexer inside the other. Each
tool's own configuration is authoritative for its internal bindings.

Tmux and Herdr share these direct pane controls:

- `Ctrl+H/J/K/L`: focus left/down/up/right. Foot and Ghostty map
  Ctrl+Backspace separately to erase the previous word.
- `Ctrl+Alt+H/J/K/L` or `Ctrl+Alt+Arrow`: swap with the neighboring pane.
- `Ctrl+Alt+B/V`: split side-by-side / top-to-bottom. Herdr calls these
  operations `split_vertical` / `split_horizontal`, respectively.
- `Ctrl+Alt+Shift+Arrow`: resize in that direction.
- `Ctrl+Alt+F`: toggle pane zoom.
- `Ctrl+Alt+Q`: close the pane.

The close shortcut is not perfectly equivalent: tmux confirms before killing
the pane, while Herdr 0.9.1 closes it immediately. Herdr's safer prefix form
(`Ctrl+B`, then `x`) remains available alongside the direct shortcut.

On macOS, `Super+/` opens an fzf command palette in a temporary Ghostty window.
Its actions and shortcut labels come directly from the annotated AeroSpace
bindings, and window actions target the window that was focused before the
palette opened. `Super+E` selects tiles or toggles their orientation; `Super+S`
and `Super+W` select vertical and horizontal accordion layouts. AeroSpace has
no direct Sway scratchpad equivalent. Lock/power and screenshot shortcuts above
remain Sway-specific; macOS uses its native controls for those actions.
