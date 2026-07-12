# Paperless-ngx

Files:
- `services/paperless/compose.yaml`

Run notes:
- Paperless is exposed on port `8010`.
- The stack uses Postgres and Redis.
- The compose file expects a local `.env` with `PAPERLESS_DB_PASSWORD`.
- Keep the consume/export/data/media directories on the box, not in git.

Typical update flow:
- edit `compose.yaml`
- update the live `.env` outside the repo
- restart the compose stack
