# Jellyfin

Files:
- `services/jellyfin/docker-compose.yml`

Run notes:
- Jellyfin runs on `http://10.1.10.140:8096/`
- the compose file maps `/srv/jellyfin/config` for app data and `/srv/jellyfin/cache` for transcodes/cache
- the media root is `/srv/jellyfin/media`
- the local media folders currently include:
  - `movies`
  - `tv`
  - `music`
  - `audiobooks`
  - `podcasts`
- Intel hardware transcoding is enabled via `/dev/dri`
- the media root is also exported over SMB as the `Jellyfin` share
- the existing `Audiobooks` and `Books` SMB shares remain separate
