# Deploying prepper-box to the box

This repo is the source of truth for the box configs and helper code.

## Quick workflow

1. Edit the repo locally.
2. Rebuild the combined Homepage file:

   make homepage-build

3. Deploy Homepage to the box:

   make deploy-homepage

4. Copy any non-Homepage service files to the live box.
5. Restart the relevant service or container.

## Homepage

Homepage uses per-section source fragments in this repo:

- `services/homepage/sections/00-core-apps.yaml`
- `services/homepage/sections/01-offline-reference.yaml`
- `services/homepage/sections/02-references.yaml`
- `services/homepage/sections/03-workflow.yaml`

The generated file that Homepage reads is:

- `services/homepage/services.yaml`

`make homepage-build` rebuilds that generated file from the fragments.
`make deploy-homepage` then syncs the Homepage config set to:

- `/srv/homepage/`

It copies these files:

- `services.yaml`
- `bookmarks.yaml`
- `settings.yaml`
- `widgets.yaml`
- `custom.css`
- `custom.js`
- `docker.yaml`
- `kubernetes.yaml`
- `proxmox.yaml`

## Other services

### Audiobookshelf
- Source: `services/audiobookshelf/docker-compose.yml`
- Live path: `/srv/audiobookshelf/docker-compose.yml`
- Restart the compose stack after changing mounts, ports, or image settings.

### Samba
- Source: `services/samba/docker-compose.yml`
- Live path: wherever the Samba compose project lives on the box
- Keep secrets in the live `.env`, not in git.

### Paperless-ngx
- Source: `services/paperless/compose.yaml`
- Live path: `/srv/paperless/compose.yaml`
- Keep the live `.env` and data directories on the box.

### Qdrant
- Source: `services/qdrant/compose.yaml`
- Live path: `/srv/qdrant/compose.yaml`

### Network Admin
- Source: `services/network-admin/app.py`
- Live path: `/srv/network-admin/app.py`
- Restart the service or container that runs the app after edits.

## Backup and restore

Use the Makefile shortcuts for tracked repo files and unignored working-tree files:

- `make backup ARCHIVE=/tmp/prepper-box.tar.gz`
- `make restore ARCHIVE=/tmp/prepper-box.tar.gz`
- `make backup-list ARCHIVE=/tmp/prepper-box.tar.gz`

Notes:
- The backup archive is a tar.gz.
- The backup helper only includes repo files and non-ignored working-tree files.
- Restore extracts the archive into the target directory you provide.
