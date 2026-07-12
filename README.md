# prepper-box

Sanitized configuration repo for Patrick's Ubuntu prepper box.

This repo captures the parts of the box that are useful to version control:

- Homepage configuration and theme overrides
- Audiobookshelf compose file
- Samba share compose file for Audiobooks, Books, and Jellyfin media
- Network-admin app code
- Paperless-ngx compose file
- Qdrant compose file
- local arcade launcher notes for MAME
- service-specific docs with short run notes
- a simple backup/restore script for tracked config files

## What is not in git

This repo intentionally excludes:

- passwords, tokens, Wi‑Fi credentials, and other secrets
- databases, caches, logs, and runtime artifacts
- downloaded media, ebooks, and ZIM/PMTiles content
- any machine-local state that would be noisy or unsafe to publish

## Layout

- `services/homepage/` — Homepage dashboard config and styling
- `services/audiobookshelf/` — Audiobookshelf compose file
- `services/samba/` — Samba share compose file
- `services/jellyfin/` — Jellyfin compose file
- `services/network-admin/` — the small network admin web app
- `services/paperless/` — Paperless-ngx compose file
- `services/qdrant/` — Qdrant compose file
- `docs/inventory.md` — what is included and excluded
- `docs/services/README.md` — per-service quick notes and run tips
- `docs/deploy.md` — how to deploy and restore this repo on the box
- `docs/onboarding.md` — how to adapt the repo to your own machine
- `Makefile` — shortcuts for Homepage build/deploy and backup/restore
- `scripts/render-homepage.py` — combines Homepage section fragments
- `arcade/mame/` — local MAME launcher notes and ROM folder layout
- `.env.example` — template for local secrets

## Setup

1. Copy the example env file on the live box or your local test environment:

   cp .env.example .env

2. Fill in the real values for:

   - `PAPERLESS_DB_PASSWORD`
   - `SAMBA_USER`
   - `SAMBA_PASSWORD`

3. Start or update the relevant compose project on the box.

## Arcade / MAME

The Ubuntu prepper box also has a lightweight local arcade setup:

- MAME is installed on the box
- launcher: `/home/patrick/arcade/mame/mame-launcher.py`
- ROM folder: `/home/patrick/arcade/mame/roms`
- the Homepage tile opens `arcade://launch` on the local machine
- the launcher shows cleaned-up game titles and only lists playable sets

## Jellyfin / media shares

The prepper box also runs Jellyfin for local media playback:

- Jellyfin web UI: `http://10.1.10.140:8096/`
- Jellyfin media root: `/srv/jellyfin/media`
- the media root is shared over SMB as `Jellyfin`
- the same Samba container still serves the existing `Audiobooks` and `Books` shares

## Notes

- The compose files reference the live box paths under `/srv/...`.
- The repository is a sanitized snapshot of configuration, not a full backup.
- The live box remains the source of truth for media and application data.
