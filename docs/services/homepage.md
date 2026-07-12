# Homepage

Files:
- `services/homepage/sections/*.yaml` (source fragments)
- `services/homepage/services.yaml` (generated combined file)
- `services/homepage/bookmarks.yaml`
- `services/homepage/settings.yaml`
- `services/homepage/widgets.yaml`
- `services/homepage/custom.css`
- `services/homepage/custom.js`
- `services/homepage/docker.yaml`
- `services/homepage/kubernetes.yaml`
- `services/homepage/proxmox.yaml`

Run notes:
- Dashboard is exposed on port `3001`.
- Restart the container after config changes.
- Build `services.yaml` from the fragments before deploying.

Typical update flow:
- edit one or more files under `services/homepage/sections/`
- run `make homepage-build`
- copy the generated `services.yaml` and companion files to the live box
- restart Homepage
