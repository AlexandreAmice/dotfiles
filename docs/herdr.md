# Herdr agent workspaces

Herdr is the agent-aware terminal mode. Use it when several Codex sessions or
repositories are active and their working, blocked, done, and idle states need
to be visible together. Plain terminals remain the right entry point for
transparent SSH, and tmux remains the general persistent shell and server
layer.

## Ownership and installation

Linux uses the versioned, checksum-verified Herdr release declared in
`.chezmoiexternal.toml.tmpl`; macOS uses the `Brewfile`. Update those owners
instead of running `herdr update` against the managed installation.

Chezmoi manages only `~/.config/herdr/config.toml`. Herdr's session snapshots,
logs, sockets, plugin state, pane history, and agent session references are
machine-local runtime data and must not be added recursively to the source.
The managed config deliberately disables pane-history persistence because
terminal output can contain prompts, credentials, and command output.

Herdr and tmux both use `Ctrl+B`. Run them in separate terminal windows and do
not nest them. `terminal-agents` enforces that boundary for desktop launches.

Shared pane actions use the same direct chords documented in
`docs/keybindings.md`. Herdr 0.9.1 does not expose pane swaps as native key
fields, so the four swap bindings call its supported `herdr pane swap` CLI.
`Ctrl+Alt+Q` closes the focused pane immediately: Herdr cannot reproduce tmux's
confirmation prompt. The default `Ctrl+B`, then `x` binding remains available.

## Codex integration

Once Codex has created `~/.codex`, install or refresh Herdr's hook:

```sh
chezmoi cd
./scripts/install --agent-integrations
```

The installer asks Herdr to merge its entries with existing Codex hooks, then
verifies that the integration is reported as installed. The hook supplies the
native Codex session identity used by Herdr to resume `codex` after a full
Herdr server restart. Live agent state is detected from the terminal UI.

Check the complete setup with `desktop-doctor`. After editing the managed
config, apply it and run `herdr server reload-config` if a server is active.
