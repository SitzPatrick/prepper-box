# Audiobookshelf

Files:
- `services/audiobookshelf/docker-compose.yml`

Run notes:
- Web UI is exposed on port `13378`.
- The container mounts:
  - `/srv/audiobookshelf/config:/config`
  - `/srv/audiobookshelf/audiobooks:/audiobooks`
  - `/srv/audiobookshelf/books:/books`
  - `/srv/audiobookshelf/podcasts:/podcasts`
- Restart the container after changing mounts or image settings.
- The Books library depends on `/books` being mounted inside the container.
