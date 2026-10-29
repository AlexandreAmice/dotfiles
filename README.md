# Dotfiles

Cross-platform shell and desktop configuration managed by
[chezmoi](https://www.chezmoi.io/). Ubuntu renders a Sway desktop and macOS
renders an AeroSpace desktop from shared Tokyo Night theme, direction, and
workspace data. Supported generation baselines are Ubuntu 24.04+ and macOS
13+.

## Quick Start

1. Install Git, gh, and chezmoi.

   ```sh
   sudo apt install git gh
   sudo snap install chezmoi --classic
   ```

2. Log into GitHub.

   ```sh
   gh auth login
   ```

3. Get the dotfiles and follow the system prompts.

   ```sh
   chezmoi init AlexandreAmice/dotfiles
   ```

4. Navigate to the chezmoi source, install software, and apply chezmoi.

   ```sh
   cd "$(chezmoi source-path)"
   ./scripts/install
   chezmoi diff
   chezmoi apply --verbose
   ```

   Use `./scripts/install --grant-backlight` instead on a laptop with
   a real backlight; omit the flag in a VM or on a desktop.
   Failed installation steps are reported while the remaining steps continue.
   The installer lists failures at the end and exits with a nonzero status if any
   step failed; resolve them and rerun it to finish installation.
   An unfinished Ubuntu package transaction stops the installer before changes.
   Run `sudo dpkg --configure -a`, then `sudo apt-get --fix-broken install`, and
   rerun the installer once both succeed.
   `chezmoi apply` deploys Atuin, `desktop-doctor`, and the managed configuration;
   open a new shell afterward so the commands and Atuin shell integration load.

5. Optionally log into Atuin. This requires the Atuin encryption key.

   ```sh
   atuin login
   ```

6. Check the installation.

   ```sh
   desktop-doctor
   ./tests/validate-desktop
   ```

7. Log out completely and select **Sway** at the login screen.

Atuin credentials, encryption keys, and history are deliberately not deployed.

Choose `portable` for an ordinary machine. Choose `amice-workstation` only on
the original Ubuntu workstation.

The Ubuntu installer updates the existing **Sway** login entry to use the
portable launcher and removes the older Intel trial and dotfiles entries.
Its launcher detects GPU drivers and connected monitors at each login. With
proprietary NVIDIA loaded, it passes `--unsupported-gpu` and orders DRM devices
so a GPU with a connected monitor comes first, while retaining the other GPUs
for additional displays. It prefers Intel/AMD only when a monitor is connected
to them. An explicit `WLR_DRM_DEVICES` setting takes precedence. Other machines
use Sway's normal GPU selection. No workstation profile is needed.

For an existing install, `./scripts/install --sway-session` updates only the
launcher and login entry, without reinstalling software. It needs sudo for the
system files. Startup diagnostics are saved to
`~/.local/state/sway/session.log` (or `$XDG_STATE_HOME/sway/session.log`), with
the previous attempt retained as `session.previous.log`. NVIDIA support remains
experimental; configuration validation does not verify real display startup.

Existing checkouts upgrading to this layout must run `chezmoi init` once to
regenerate the derived `isAmiceWorkstation` config value before applying.

### macOS

Install [Homebrew](https://brew.sh) first. If this is a new checkout, bootstrap
chezmoi and GitHub access before initializing the portable profile:

```sh
brew install git gh chezmoi
gh auth login
chezmoi init AlexandreAmice/dotfiles
```

Install the dependencies, apply, and verify:

```sh
cd "$(chezmoi source-path)"
./scripts/install
chezmoi diff
chezmoi apply --verbose
open -a AeroSpace
open -a Hammerspoon
desktop-doctor
```

Grant AeroSpace permission in System Settings → Privacy & Security →
Accessibility when macOS requests it. Quit and reopen AeroSpace after enabling
permission if its CLI cannot connect. Grant Hammerspoon Accessibility permission
there too for common Ctrl editing/app shortcuts in GUI apps and Ghostty's
Ctrl+scroll font zoom. Open a fresh Ghostty window to
load the managed shell setup.

The installer installs missing Homebrew dependencies without routine package
upgrades. Applications already in `/Applications` may need Homebrew adoption
before rerunning the installer; their data is preserved.

If adopting an existing app requests an administrator password, run the
installer in an interactive terminal. For Slack specifically, run
`brew install --cask --adopt slack`, then rerun the installer.

GitHub credentials, application histories, and caches are deliberately
machine-local.

Signal and pCloud remain part of the personal setup. Ubuntu installs Signal
from its official apt repository and the verified pCloud AppImage on amd64.
macOS installs Signal through Homebrew and pCloud from the official universal
package, checking its signature and Apple's install assessment first. Existing
pCloud installations are reused. Application accounts and sync data stay local.

On macOS, open pCloud after installation and follow its
[Drive setup instructions](https://www.pcloud.com/how-to-install-pcloud-drive-mac-os.html).
Enabling its filesystem extension requires native system approval; the installer
does not change macOS security settings. AeroSpace starts Signal, Slack, and
pCloud; Signal and Slack are assigned to workspace 10. Cloudflare WARP is not
part of this setup.

Codex is installed automatically during the software-install step. Run
`codex` once to sign in and create `~/.codex`; credentials and session state
remain machine-local. Herdr is installed as a pinned external on Linux and
through Homebrew on macOS. After that first Codex launch, install Herdr's
session hook while preserving other Codex hooks:

```sh
cd "$(chezmoi source-path)"
./scripts/install --agent-integrations
```

The installer installs Rust and Cargo through rustup if a working toolchain is
missing. On Ubuntu it also installs pinned `automatic-timezoned` with Cargo for
the Sway timezone service. Cargo commands are available in a new shell after
applying the managed shell configuration.

On Ubuntu, the installer builds pinned Foot 1.28 and fcft 3.3.1 source releases
and installs Foot under `/usr/local`. Ubuntu 24.04's Foot 1.16 duplicates Enter
and Backspace release events when Herdr enables Kitty keyboard reporting. The
apt package remains installed as a system fallback, while the normal
`/usr/local/bin` path selects the fixed version.
Reruns reuse Foot 1.28 or newer when both Foot and footclient are installed
under `/usr/local`. After installing the Signal repository definition, the
installer backs up the legacy Signal-only `signal-xenial.list` as `.list.bak`
to avoid duplicate APT entries.

The Ubuntu installer also installs pinned nwg-displays 0.4.4. Open Displays
from `Super+C` to arrange screens and assign workspaces. Closing the GUI saves
the connected-monitor profile locally and updates the Chezmoi source; later
workspace moves are recorded automatically by the Sway layout service.
Click Apply in the workspace assignment dialog, then close the main Displays
window. The layout controller replaces Sway's workspace output rules and moves
existing workspaces; no session restart is needed. Generated rules live in
`~/.local/state/sway/workspace-outputs.conf` so they also survive a config reload.

## Updating either platform

Both machines follow `main` in `AlexandreAmice/dotfiles`; separate OS
branches are unnecessary. Commit any local source edits before pulling. If a
machine uses a different remote, review it before pulling from this repository.
Do not use `chezmoi update` for this rollout: install dependencies before applying
the new configuration.

Ubuntu:

```sh
cd "$(chezmoi source-path)" &&
git switch main &&
git pull --ff-only origin main &&
chezmoi init &&
./scripts/install &&
./tests/validate-desktop &&
chezmoi diff &&
chezmoi apply --verbose
```

Log out completely, select **Sway** at login, then run
`~/.local/bin/desktop-doctor`. The installer refreshes the system login launcher.
Signal and pCloud installation and startup remain enabled. The standard
`waybar.service` and `swaync.service` names replace the duplicate `sway-*` units;
no services are masked. Notification actions use a shell to resolve `$HOME`.

macOS:

```sh
cd "$(chezmoi source-path)" &&
git switch main &&
git pull --ff-only origin main &&
chezmoi init &&
./scripts/install &&
./tests/validate-desktop &&
chezmoi diff &&
chezmoi apply --verbose &&
open -a AeroSpace &&
open -a Hammerspoon
```

Grant AeroSpace and Hammerspoon Accessibility permission, reload Hammerspoon
from its menu if it was already running, and open a new Ghostty window. Run
`~/.local/bin/desktop-doctor` there. Native macOS GUI behavior and physical
Ubuntu display startup still need verification on each machine; rendering and
automated tests do not exercise those sessions.

Shared configuration keeps Tokyo Night colors, wallpaper choices, workspaces,
tmux, Herdr, Starship, Atuin, and Neovim aligned. Sway/Foot and
AeroSpace/Ghostty remain native adapters. Ghostty's size 15 versus Foot's size
11, macOS clipboard handling, and platform-specific system controls are
intentional differences.

## Validation

Run the clean-room integration validator before committing:

```sh
cd "$(chezmoi source-path)"
./tests/validate-desktop
```

It materializes portable Linux, workstation Linux, and portable macOS homes;
checks profile and platform boundaries; parses rendered configuration; and
runs native validators and ShellCheck when available.

## Daily controls

- `Super+T` on Sway or `Command+T` on AeroSpace opens a plain terminal.
- Add `Shift` to open or resume an independent persistent tmux terminal.
- Add left Ctrl instead to open the agent-aware Herdr workspace. Herdr and
  tmux are separate terminal modes and must not be nested.
- `Super+H/J/K/L` focuses Sway windows; `Super+1` through `Super+0` selects a
  workspace.
- `Super+/` on Sway or `Command+/` on AeroSpace opens the searchable desktop command reference.
- `Super+C` opens Sway system controls; `Super+Shift+X` locks the session.
- `Ctrl+R` searches Atuin history and inserts the result for review.

Starship gives the full untruncated directory its own line, Git state and
command duration the next, and a clean `❯` input marker the final line. SSH
sessions add a separate `user@hostname` line above the directory.

## Appearance

Ubuntu and macOS use the same Tokyo Night palette and pinned wallpaper artwork.
Midnight and 95% terminal opacity are the defaults; saved selections remain
machine-local. Use `apply-appearance --mood midnight` (or `dusk`, `dawn`, `solid`)
and `apply-appearance --opacity 1.00` (or `0.95`, `0.89`). Use `--restore` after
attaching another screen. See [wallpapers.md](docs/wallpapers.md) for native
appearance permissions and reload requirements.

## Documentation

- [Local changes and upstream workflow](docs/local-changes.md)
- [Architecture](docs/architecture.md)
- [Profiles and portability](docs/profiles.md)
- [Keybinding conventions](docs/keybindings.md)
- [Herdr agent workspaces](docs/herdr.md)
- [Wallpaper assets and provenance](docs/wallpapers.md)
- [Roadmap and hardware qualification](docs/roadmap.md)
