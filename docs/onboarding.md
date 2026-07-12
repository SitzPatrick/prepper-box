# Using prepper-box on your own machine

This repo was built for Patrick's Ubuntu prepper box, but it can be adapted to another similar machine.

## What to change first

Before you deploy anything, search for machine-specific values and replace them with your own:

- IP address: `10.1.10.140`
- hostname/display name: `Patrick Mini PC`
- SSH user/host references: `patrick@10.1.10.140`
- Samba credentials in `.env.example`
- any service paths under `/srv/...`

A quick way to find the machine-specific strings is:

```bash
rg -n "10\.1\.10\.140|Patrick Mini PC|patrick@10\.1\.10\.140|/srv/" .
```

## Recommended setup flow

1. Clone the repo.
2. Copy `.env.example` to `.env` and fill in real secrets.
3. Update the Homepage links, compose files, and service paths for your box.
4. Run `make homepage-build` to regenerate `services/homepage/services.yaml`.
5. Copy the service files to the live machine.
6. Restart the affected containers or services.
7. Verify the live UI and mounts before you consider the change done.

## Files most likely to need edits

- `README.md`
- `docs/deploy.md`
- `Makefile`
- `services/homepage/sections/*.yaml`
- `services/homepage/bookmarks.yaml`
- `services/audiobookshelf/docker-compose.yml`
- `services/samba/docker-compose.yml`
- `services/paperless/compose.yaml`
- `services/network-admin/app.py`
- `.env.example`

## Secrets and data

Do not commit:

- real passwords
- tokens
- Wi-Fi credentials
- databases
- downloaded media
- scan caches or runtime state

Keep those in the live machine's working directories or in a private secret manager.

## Helpful shortcuts

- `make homepage-build` — rebuild the Homepage combined services file
- `make deploy-homepage` — sync Homepage files to the live box
- `make backup ARCHIVE=/tmp/prepper-box.tar.gz` — create a snapshot of repo files
- `make restore ARCHIVE=/tmp/prepper-box.tar.gz DEST=/tmp/restore-target` — restore a snapshot

## If you are starting from scratch

If you want to use this as a template, rename the project and update the docs to match your own machine name. The layout is intentionally small and readable so you can keep only the services you actually run.
