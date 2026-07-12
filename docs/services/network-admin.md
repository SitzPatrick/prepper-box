# Network Admin

Files:
- `services/network-admin/app.py`

Run notes:
- Web UI is exposed on port `5052`.
- The app uses NetworkManager (`nmcli`) on the box to inspect and switch uplinks.
- It expects the AP/uplink connection names defined in the script.
- Restart the service/process after editing the Python app.

Typical update flow:
- edit `app.py`
- copy it to the box
- restart the network-admin process or container, depending on how it is deployed
