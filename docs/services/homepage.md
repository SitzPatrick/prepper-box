# Homepage

Files:
- `services/homepage/services.yaml`
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
- Keep widget/provider YAML files aligned with the live services in the box.

Typical update flow:
- edit the YAML/CSS/JS files in this repo
- copy them to the live box
- restart Homepage
