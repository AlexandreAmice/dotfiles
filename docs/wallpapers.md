# Wallpaper assets and provenance

The six Tokyo Night wallpapers were created for this dotfiles project on
2026-09-15 with OpenAI image generation and contain no third-party source
imagery. The public source-of-distribution record is
[AlexandreAmice/dotfiles-assets](https://github.com/AlexandreAmice/dotfiles-assets).

Chezmoi installs this immutable release asset on Ubuntu and macOS:

- Release: `wallpapers-v1`
- Archive: `tokyo-night-wallpapers-v1.tar.gz`
- URL: `https://github.com/AlexandreAmice/dotfiles-assets/releases/download/wallpapers-v1/tokyo-night-wallpapers-v1.tar.gz`
- SHA-256: `266d37158697358a171c66e68e484440348a45800e9b531848da8b11c485b020`
- Layout: one `tokyo-night-wallpapers-v1/` directory containing six PNGs

The external targets `~/.local/share/tokyo-night/wallpapers`, strips that one
top-level component, and uses exact extraction. The repository retains no PNG
copies, avoiding future Git history growth. Runtime mood selection points
`~/.local/state/tokyo-night/wallpaper.png` at one installed file.

## Generation prompts

**Midnight:** A polished abstract 16:10 Tokyo Night wallpaper using deep navy
and ink-purple space, layered geometric ribbons, circles, tiny sparkles, and
subtle grain; a quiet center; navy, blue, cyan, restrained pink, and purple;
no text, logos, recognizable objects, UI, or watermark.

**Dusk:** A companion abstract 16:10 composition with the same geometric
language, softened grain, and quiet center, shifted toward deep plum, warm
violet, restrained magenta, coral, and amber edge accents; no text, logos,
recognizable objects, UI, or watermark.

**Dawn:** A companion abstract 16:10 composition with the same visual language
and calm center, shifted toward lavender-blue, cyan, and pale-yellow highlights
while retaining desktop contrast; no text, logos, recognizable objects, UI,
or watermark.

Each landscape source was re-composed as a native 10:16 portrait image. The
palette, grain, geometric language, and quiet center were preserved while
elements were redistributed for the tall canvas rather than cropped.

## Shared appearance controls

`apply-appearance --mood midnight|dusk|dawn|solid` selects the wallpaper on either
platform. Midnight is the default, and existing machine-local choices survive
deployment. Artwork is identical on Ubuntu and macOS. Portrait artwork is used
for rotated Sway outputs and macOS screens taller than they are wide. Solid is
an optional image generated from the shared background color outside the exact
archive extraction directory.

`apply-appearance --opacity 1.00|0.95|0.89` updates the platform's local terminal
include. New terminal windows use it; existing Ghostty windows need a config
reload. The default remains 95%. `--restore` reapplies the saved choices, which
is also useful after attaching another screen. No hotplug service is installed
on macOS. macOS wallpaper changes apply to currently connected screens, not
every hidden native Space.

Real-home setup applies native dark appearance and purple accents. On macOS,
allow the terminal to control System Events under Privacy & Security →
Automation if requested. Native accent changes may require reopening an app.
Temporary Chezmoi destination homes skip host preference changes.

`--initialize` prepares missing state without requiring downloaded wallpaper
assets. `--no-native` updates wallpaper/opacity state without modifying host
preferences, for diagnostics and tests. Runtime includes and wallpaper choices
are generated locally and are not committed.
