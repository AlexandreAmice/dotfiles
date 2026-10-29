# Adopted desktop changes

This repository is [AlexandreAmice/dotfiles](https://github.com/AlexandreAmice/dotfiles).
The cross-platform improvements were adapted from
[AlexandreAmice-Arda/dotfiles at 9073208](https://github.com/AlexandreAmice-Arda/dotfiles/tree/9073208),
which branched from `8c56f00`.

The adoption retains Signal and pCloud on Ubuntu and macOS, excludes Cloudflare
WARP, and consolidates Waybar/SwayNC under their standard service names without
masks. It also preserves the local display-layout daemon's bounded retries and
journal-only error reporting. SwayNC actions invoke the focus helper through
`sh -c` so `$HOME` is expanded without hardcoded paths.

## Desktop shortcuts

Both desktop adapters use Super: Windows/Super on Ubuntu, Command on macOS.
AeroSpace previously used Option as its primary modifier. Its shared actions
now follow Sway's chords:

- Super+T opens a plain terminal; Shift adds tmux, Ctrl adds Herdr.
- Super+D opens the application launcher; macOS uses Spotlight.
- Super+/ opens the command palette. The macOS palette reads annotated
  AeroSpace bindings and preserves the original target window when dispatching.
- Super+C opens system controls on Ubuntu; Command+Ctrl+C opens System Settings
  on macOS, preserving Command+C for Copy.
- Super+H/J/K/L focuses windows; Alt moves windows; Ctrl moves whole workspaces
  between monitors.
- Super+E selects tiles or changes their orientation. Super+S/W selects
  vertical/horizontal accordion layouts on macOS.

AeroSpace's explicit split bindings retain single-child containers by disabling
container flattening. These desktop bindings override native Command shortcuts,
including Save, Close, Hide, Find, and New Tab. Native clipboard shortcuts remain
available to applications. Sway's scratchpad, power
menu, lock, and screenshot controls do not have matching AeroSpace bindings.

## Terminal panes

Tmux and Herdr use Ctrl+H/J/K/L for direct pane focus on both platforms. The
previous shared config omitted Ctrl+H, which allowed applications to interpret
it as backspace. Foot and Ghostty already map Ctrl+Backspace separately to
erase the previous word, so Ctrl+H is now bound to left-pane focus.

Ctrl+Alt+B/V splits panes; Ctrl+Alt+H/J/K/L swaps panes; Ctrl+Alt+F zooms.
Alt is Option on macOS. These terminal controls remain distinct from desktop
controls, and the Ctrl+B prefix remains available.

## Workspaces and monitors

Workspaces 1–10 are persistent, rather than a hard maximum. AeroSpace can
create an extra empty workspace when an attached monitor has no assigned
workspace. Moving an existing workspace to that monitor lets the unused empty
workspace disappear. No machine-specific monitor assignment is committed.

## Installation and platform checks

`scripts/install` handles Ubuntu and macOS, reports failures after attempting
independent steps, discovers Homebrew, and installs missing Rust/timezone tools.
Existing pCloud installations are reused; new macOS installs use the official
signed universal package. Signal keeps its startup and workspace integration.
Linux-only helpers and Python caches are excluded from macOS deployment.

`tests/validate-desktop` renders portable Ubuntu, workstation Ubuntu, and macOS
homes and validates their configuration. Installer tests use a closed command
path so installed host tools such as rustup cannot escape the mocks. Native
macOS GUI behavior, extension approval, and physical GPU/display startup still
require checks on those machines; rendering alone does not verify them.

## Minimal macOS terminal appearance

Ghostty follows Foot's shared font family, Tokyo Night palette, selection colors,
padding, 95% opacity, and blinking beam cursor. Blur is disabled and unfocused
Ghostty splits retain full opacity. The macOS title bar is hidden to reduce
terminal chrome; this setting applies to new windows. Scrollback remains at
Ghostty's default byte budget, since Foot's 10,000-line limit has no exact
Ghostty equivalent. Ghostty intentionally uses size 15 while Foot uses size 11;
the native terminals use different sizing and display scaling. The shared
`apply-appearance` command controls machine-local opacity on both platforms.

A macOS-only, idempotent Chezmoi script enables Dock auto-hiding and restarts
Dock only when the preference changes. The Dock still appears when the pointer
reaches its screen edge. Tmux's status bar, AeroSpace configuration, and the
macOS menu bar are unchanged by this appearance update.

## Keeping the configuration current

Use this repository as `origin`. Preserve local edits before integrating changes,
review personal-app declarations, and run `tests/validate-desktop` before
publishing. Review `chezmoi diff` before applying on each machine.

## Shared theme rollout

Theme colors now have one source in `.chezmoidata.yaml`; tmux and Starship are
templates with identical existing output, and Neovim explicitly selects Night.
Bright terminal colors are shared as named tokens. `apply-appearance` now works
on Ubuntu and macOS, with Midnight artwork and 95% opacity as fresh defaults.
The same pinned Ubuntu wallpaper archive is installed on macOS. Saved choices
remain local and survive deployment; solid backgrounds remain optional.

Ghostty reads a local opacity include, and real-home setup restores native
wallpaper, dark mode, and purple accents. This rollout does not change AeroSpace
or tmux layout/controls. Herdr uses its existing built-in theme and VS Code
continues to use Settings Sync. See `wallpapers.md` for controls and platform
limits.

