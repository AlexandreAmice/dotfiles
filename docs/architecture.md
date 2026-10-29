# Architecture

## Deployment model

Chezmoi owns deployment. This repository remains destination-shaped: source
names such as `private_dot_config` map directly into the target home. Shared
data in `.chezmoidata.yaml` renders native adapters rather than attempting to
make both platforms run the same desktop stack:

- Ubuntu uses Sway, Foot, Waybar, SwayNC, Wofi, wlogout, and GTKLock.
- macOS uses AeroSpace, Ghostty, and native macOS facilities.
- Shell configuration, Tokyo Night colors, H/J/K/L directions, workspaces,
  tmux, Herdr, Starship, Atuin, fzf, and zoxide are shared where their behavior
  truly aligns.

Sway's entry point stays short. Ordered fragments under
`~/.config/sway/conf.d` separate theme, session, inputs, workspaces, bindings,
and rules. The numeric order is intentional and must remain stable.

Package declarations are separate from repository tooling. The root
`Brewfile` is the macOS manifest and `packages/ubuntu.txt` is the Ubuntu
manifest. `scripts/install` selects the platform, installs its manifest and
Codex, and continues independent steps after failures. On Ubuntu it also
configures vendor repositories for VS Code and Signal, installs the verified
pCloud AppImage, and installs Slack through its supported Snap. It registers the
existing system-wide Sway session with a launcher that detects GPU drivers
and connected displays at login, retaining both GPUs on hybrid machines.
Older custom Sway entries are removed during installation.
Both platform setup paths use
OpenAI's official standalone installer for Codex; authentication and session
state remain local. Installers live in `scripts/`, integration checks in
`tests/`, and durable explanations in `docs/`; chezmoi ignores all three
tooling/document trees so they never appear in a rendered home.

## Executable ownership

Use the narrowest stable interface:

- `~/.local/bin` contains commands a person may call and commands shared by
  multiple components, such as `desktop-doctor`, `terminal-main`, and session
  actions.
- `~/.local/libexec` contains private implementations owned by one component.
  Waybar's temperature probe is therefore
  `~/.local/libexec/waybar/desktop-temperature`.
- `~/.config/sway/scripts` contains Sway session integration. `start-waybar`
  remains here as the session service launcher. Waybar uses the shared
  configuration on every connected screen without an output restriction.

Do not move scripts broadly merely for symmetry; ownership and call surface
decide the location.

## External assets and runtime state

Pinned release archives in `.chezmoiexternal.toml.tmpl` fill Linux package
gaps and carry large binary assets. Every archive uses a versioned URL and a
SHA-256 checksum. Wallpaper PNGs are installed from the public assets release,
not Git history; see [wallpapers.md](wallpapers.md).

Runtime state is not source state. Atuin accounts and history, editor caches,
terminal session data, pCloud credentials, selected wallpaper mood, and
terminal opacity remain local. VS Code settings and ordinary extensions belong
to VS Code and Settings Sync. The retired unpublished Sway extension is removed
only by its exact installed directory through `.chezmoiremove.tmpl`.

Display layout state is the deliberate exception: `display-layouts` stores one
profile per exact connected-monitor set and immediately imports its managed
JSON file into the Chezmoi source. The local save remains authoritative if that
import fails, while Git commit and synchronization stay manual. The companion
Sway service reapplies matching output geometry after hotplug and records
workspace-to-output moves without treating automatic moves during unplug as
user choices.

Long-running Sway components are supervised by systemd user units and tied to
the Sway session target. Small scripts connect components without embedding
procedural behavior in compositor configuration.

Chezmoi manages normal user units named `waybar.service` and `swaync.service`.
Both Sway and distribution graphical-session activation resolve to those same
units, so each component has one process. The units require an imported
`SWAYSOCK` and stop with `sway-session.target`. Waybar retains the monitor-aware
launcher, and SwayNC retains D-Bus notification ownership. A migration hook
stops the old `sway-waybar`/`sway-swaync` units before starting their replacements;
no vendor services are masked or globally disabled.

## Prompt and terminal decisions

Native terminal windows begin with a plain shell so an SSH session is never
silently nested inside local tmux. The shifted terminal shortcut explicitly
resumes a detached numbered session or creates the next one; `terminal-main
--shared` is the deliberate shared-session escape hatch.

Herdr is a separate, explicit agent-workspace layer rather than a replacement
for general tmux sessions. The Ctrl-modified terminal shortcut starts its
background server/client, while tmux remains on Shift. `terminal-agents`
rejects launches from inside either multiplexer so their shared Ctrl+B prefix
and overlapping pane ownership never become ambiguous. Only Herdr's
`config.toml` is source state; agent sessions, logs, sockets, and pane contents
remain local runtime state.

Starship stays on both platforms with a compact multiline prompt. The full,
untruncated directory has its own line, Git branch/status and command duration
share the next, and the final line is the clean `❯` character. SSH sessions
conditionally add a separate `user@hostname` line above the directory. Time
and project-language modules are intentionally omitted.

## Shared appearance

`.chezmoidata.yaml` owns theme colors, including bright terminal colors and the
subdued tmux text token. Foot, Ghostty, Starship, tmux, and Neovim render these
tokens. Neovim explicitly uses `tokyonight-night`; Herdr retains its built-in
`tokyo-night` approximation. GTK and macOS use native dark/purple styles rather
than exact recoloring of system chrome. VS Code remains under Settings Sync.

The shared `apply-appearance` command writes machine-local opacity includes and
wallpaper selections, then applies native appearance through Sway/GTK or a
macOS AppKit adapter. Ghostty loads its optional runtime opacity include after
its managed config. Setup initializes only missing values and restores them
after deployment; temporary destinations never change the host desktop.
