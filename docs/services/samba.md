# Samba

Files:
- `services/samba/docker-compose.yml`

Run notes:
- Samba exposes shares over ports `139` and `445`.
- The compose file reads credentials from `.env`.
- Shares currently cover:
  - `Audiobooks`
  - `Books`
- Update the `.env` outside git before bringing the stack up on a real box.
