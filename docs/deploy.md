# Deploying prepper-box to the box

This repo is the source of truth for the box's configs and helper code.

## Recommended workflow

1. Edit the repo locally.
2. Rebuild the Homepage combined file:

   make homepage-build

3. Deploy the updated Homepage files:

   make deploy-homepage

4. Copy any service files to the live box and restart that service.

## Homepage

Homepage is now split into per-section source files:

- `services/homepage/sections/00-core-apps.yaml`
- `services/homepage/sections/01-offline-reference.yaml`
- `services/homepage/sections/02-references.yaml`
- `services/homepage/sections/03-workflow.yaml`

The generated file that Homepage reads is:

- `services/homepage/services.yaml`

Deploy the Homepage set to:

- `/srv/homepage/`

Files typically copied together:

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
- Target on box: `/srv/audiobookshelf/docker-compose.yml`
- Restart the compose stack after changes.

### Samba
- Source: `services/samba/docker-compose.yml`
- Target on box: wherever you keep the Samba compose project on the box
- Keep secrets in a live `.env`, not in git.

### Paperless-ngx
- Source: `services/paperless/compose.yaml`
- Target on box: `/srv/paperless/compose.yaml`
- Keep the live `.env` and data directories on the box.

### Qdrant
- Source: `services/qdrant/compose.yaml`
- Target on box: `/srv/qdrant/compose.yaml`

### Network Admin
- Source: `services/network-admin/app.py`
- Target on box: `/srv/network-admin/app.py`
- Restart the service or container that runs the app.

## Backup and restore

Use the Makefile shortcuts for tracked repo files:

- `make backup ARCHIVE=/tmp/prepper-box.tar.gz`
- `make restore ARCHIVE=/tmp/prepper-box.tar.gz`
- `make backup-list ARCHIVE=/tmp/prepper-box.tar.gz`

The backup script only includes files tracked by git plus non-ignored working-tree files.
