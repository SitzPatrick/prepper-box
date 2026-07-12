#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = 5052
AP_CONN = "prepper-ap"
AP_IFACE = "wlp6s0"
UPLINK_CONN = "prepper-uplink"
UPLINK_IFACE = "wlx00c0cab5aa13"
ETH_CONN = "netplan-enp5s0f0"
ETH_IFACE = "enp5s0f0"


def run(cmd: list[str], check: bool = True) -> str:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or f"command failed: {' '.join(cmd)}").strip())
    return (proc.stdout or "").strip()



def ethernet_device() -> dict[str, str]:
    return next((d for d in device_status() if d["device"] == ETH_IFACE), {})


def switch_to_ethernet() -> None:
    run(["nmcli", "connection", "up", ETH_CONN])
    run(["nmcli", "connection", "down", UPLINK_CONN], check=False)


def switch_to_usb_wifi() -> None:
    run(["nmcli", "radio", "wifi", "on"], check=False)
    run(["nmcli", "connection", "up", UPLINK_CONN])
    run(["nmcli", "connection", "down", ETH_CONN], check=False)


def default_uplink_device() -> str:
    for line in route_lines().splitlines():
        if line.startswith("default "):
            parts = line.split()
            if "dev" in parts:
                idx = parts.index("dev")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    return ""


def nm(fields: list[str], name: str, default: str = "") -> str:
    out = run(["nmcli", "-g", ",".join(fields), "connection", "show", name], check=False)
    lines = [line.strip() for line in out.splitlines()]
    if not lines:
        return default
    if len(fields) == 1:
        return lines[0]
    return "\n".join(lines[: len(fields)])


def conn_value(name: str, field: str, default: str = "") -> str:
    out = run(["nmcli", "-g", field, "connection", "show", name], check=False)
    return out.splitlines()[0].strip() if out.strip() else default


def device_status() -> list[dict[str, str]]:
    out = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"], check=False)
    rows: list[dict[str, str]] = []
    for line in out.splitlines():
        parts = line.split(":", 3)
        if len(parts) == 4:
            rows.append({"device": parts[0], "type": parts[1], "state": parts[2], "connection": parts[3]})
    return rows


def active_connections() -> list[dict[str, str]]:
    out = run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,STATE", "connection", "show", "--active"], check=False)
    rows: list[dict[str, str]] = []
    for line in out.splitlines():
        parts = line.split(":", 3)
        if len(parts) == 4:
            rows.append({"name": parts[0], "type": parts[1], "device": parts[2], "state": parts[3]})
    return rows


def route_lines() -> str:
    return run(["ip", "route"], check=False)


def ip_addr(dev: str) -> str:
    out = run(["ip", "-4", "-o", "addr", "show", "dev", dev], check=False)
    for token in out.split():
        if "/" in token and token[0].isdigit():
            return token
    return ""


def wifi_scan(iface: str) -> list[dict[str, str]]:
    run(["nmcli", "device", "wifi", "rescan", "ifname", iface], check=False)
    out = run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,CHAN", "device", "wifi", "list", "ifname", iface], check=False)
    results: list[dict[str, str]] = []
    for line in out.splitlines():
        parts = line.split(":", 4)
        if len(parts) == 5:
            in_use, ssid, signal, security, chan = parts
            ssid = ssid.replace(r"\:", ":")
            if ssid:
                results.append({
                    "in_use": in_use,
                    "ssid": ssid,
                    "signal": signal,
                    "security": security,
                    "chan": chan,
                })
    return results


def status_snapshot() -> dict:
    ap_ssid = conn_value(AP_CONN, "802-11-wireless.ssid")
    ap_mode = conn_value(AP_CONN, "802-11-wireless.mode")
    ap_band = conn_value(AP_CONN, "802-11-wireless.band")
    ap_channel = conn_value(AP_CONN, "802-11-wireless.channel")
    ap_ipv4 = conn_value(AP_CONN, "ipv4.method")
    ap_iface = conn_value(AP_CONN, "connection.interface-name")
    ap_ip = ip_addr(AP_IFACE)
    eth_state = ethernet_device()
    default_dev = default_uplink_device()

    usb_state = next((d for d in device_status() if d["device"] == UPLINK_IFACE), {})
    usb_conn = usb_state.get("connection", "")
    usb_scan = wifi_scan(UPLINK_IFACE)
    usb_ssid = conn_value(UPLINK_CONN, "802-11-wireless.ssid")
    usb_autoconnect = conn_value(UPLINK_CONN, "connection.autoconnect")
    usb_route_metric = conn_value(UPLINK_CONN, "ipv4.route-metric")

    return {
        "ap": {
            "ssid": ap_ssid,
            "mode": ap_mode,
            "band": ap_band,
            "channel": ap_channel,
            "ipv4_method": ap_ipv4,
            "interface": ap_iface,
            "ip": ap_ip,
        },
        "ethernet": {
            "device": ETH_IFACE,
            "state": eth_state.get("state", ""),
            "connection": eth_state.get("connection", ""),
        },
        "active_uplink": (
            "ethernet" if default_dev == ETH_IFACE else
            "usb" if default_dev == UPLINK_IFACE else
            default_dev
        ),
        "usb": {
            "device": UPLINK_IFACE,
            "state": usb_state.get("state", ""),
            "connection": usb_conn,
            "profile_ssid": usb_ssid,
            "autoconnect": usb_autoconnect,
            "route_metric": usb_route_metric,
            "scan": usb_scan,
        },
        "devices": device_status(),
        "active_connections": active_connections(),
        "routes": route_lines(),
    }


def html_escape(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def set_ap(ssid: str, password: str, band: str, channel: str) -> None:
    if band:
        run(["nmcli", "connection", "modify", AP_CONN, "802-11-wireless.band", band])
    if channel:
        run(["nmcli", "connection", "modify", AP_CONN, "802-11-wireless.channel", channel])
    if ssid:
        run(["nmcli", "connection", "modify", AP_CONN, "802-11-wireless.ssid", ssid])
    if password:
        run(["nmcli", "connection", "modify", AP_CONN, "802-11-wireless-security.key-mgmt", "wpa-psk"])
        run(["nmcli", "connection", "modify", AP_CONN, "802-11-wireless-security.psk", password])
    run(["nmcli", "connection", "down", AP_CONN], check=False)
    run(["nmcli", "connection", "up", AP_CONN])


def set_uplink(ssid: str, password: str, hidden: bool = False) -> None:
    run(["nmcli", "radio", "wifi", "on"], check=False)
    exists = run(["nmcli", "-g", "connection.id", "connection", "show", UPLINK_CONN], check=False).strip() == UPLINK_CONN
    base = [
        "nmcli", "connection", "modify", UPLINK_CONN,
        "connection.interface-name", UPLINK_IFACE,
        "802-11-wireless.mode", "infrastructure",
        "802-11-wireless.ssid", ssid,
        "ipv4.method", "auto",
        "ipv4.route-metric", "600",
        "ipv6.method", "auto",
        "ipv6.route-metric", "600",
        "connection.autoconnect", "yes",
    ]
    if hidden:
        base += ["802-11-wireless.hidden", "yes"]
    if password:
        base += ["802-11-wireless-security.key-mgmt", "wpa-psk", "802-11-wireless-security.psk", password]
    else:
        base += ["802-11-wireless-security.key-mgmt", "", "802-11-wireless-security.psk", ""]

    if exists:
        run(base)
    else:
        create = [
            "nmcli", "connection", "add",
            "type", "wifi",
            "ifname", UPLINK_IFACE,
            "con-name", UPLINK_CONN,
            "ssid", ssid,
            "connection.interface-name", UPLINK_IFACE,
            "802-11-wireless.mode", "infrastructure",
            "ipv4.method", "auto",
            "ipv4.route-metric", "600",
            "ipv6.method", "auto",
            "ipv6.route-metric", "600",
            "connection.autoconnect", "yes",
        ]
        if hidden:
            create += ["802-11-wireless.hidden", "yes"]
        if password:
            create += ["802-11-wireless-security.key-mgmt", "wpa-psk", "802-11-wireless-security.psk", password]
        run(create)
    run(["nmcli", "connection", "down", UPLINK_CONN], check=False)
    run(["nmcli", "connection", "up", UPLINK_CONN])


def disconnect_uplink(delete_profile: bool = False) -> None:
    run(["nmcli", "connection", "down", UPLINK_CONN], check=False)
    if delete_profile and run(["nmcli", "-g", "connection.id", "connection", "show", UPLINK_CONN], check=False).strip() == UPLINK_CONN:
        run(["nmcli", "connection", "delete", UPLINK_CONN], check=False)


def render_page(message: str = "", error: str = "") -> str:
    snap = status_snapshot()
    ap = snap["ap"]
    usb = snap["usb"]
    active_uplink = snap.get("active_uplink", "")

    dev_rows = []
    for d in snap["devices"]:
        dev_rows.append(
            f"<tr><td>{html_escape(d['device'])}</td><td>{html_escape(d['type'])}</td><td>{html_escape(d['state'])}</td><td>{html_escape(d['connection'])}</td></tr>"
        )

    active_rows = []
    for a in snap["active_connections"]:
        active_rows.append(
            f"<tr><td>{html_escape(a['name'])}</td><td>{html_escape(a['type'])}</td><td>{html_escape(a['device'])}</td><td>{html_escape(a['state'])}</td></tr>"
        )

    scan_rows = []
    for s in usb["scan"][:25]:
        badge = "<strong>in use</strong>" if s["in_use"] == "*" else ""
        scan_rows.append(
            f"<tr><td>{badge}</td><td>{html_escape(s['ssid'])}</td><td>{html_escape(s['signal'])}</td><td>{html_escape(s['security'])}</td><td>{html_escape(s['chan'])}</td></tr>"
        )

    banner = ""
    if message:
        banner = f'<div class="banner ok">{html_escape(message)}</div>'
    if error:
        banner = f'<div class="banner err">{html_escape(error)}</div>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Prepper Network Admin</title>
  <style>
    :root {{ color-scheme: light; --bg:#f6f8fb; --card:#ffffff; --text:#1d232f; --muted:#5c677d; --border:#d6dce8; --accent:#2f6fed; --good:#1d7f44; --bad:#b42318; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; background: var(--bg); color: var(--text); }}
    header {{ padding: 24px 28px 8px; }}
    h1 {{ margin: 0 0 6px; font-size: 28px; }}
    .sub {{ color: var(--muted); font-size: 14px; }}
    main {{ padding: 20px 28px 36px; max-width: 1250px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; align-items: start; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 18px; box-shadow: 0 1px 2px rgba(16,24,40,.04); }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    h3 {{ margin: 18px 0 10px; font-size: 15px; color: var(--muted); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .meta {{ display: grid; grid-template-columns: 150px 1fr; gap: 8px 12px; font-size: 14px; }}
    .meta div:nth-child(odd) {{ color: var(--muted); }}
    label {{ display: block; font-size: 13px; font-weight: 600; margin: 0 0 6px; }}
    input, select {{ width: 100%; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; font-size: 14px; background: #fff; }}
    input:focus, select:focus {{ outline: 2px solid color-mix(in srgb, var(--accent) 30%, white); border-color: var(--accent); }}
    .row {{ display: grid; gap: 12px; }}
    .row2 {{ display: grid; gap: 12px; grid-template-columns: 1fr 1fr; }}
    .actions {{ margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }}
    button {{ border: 0; border-radius: 10px; padding: 10px 14px; font-size: 14px; font-weight: 600; cursor: pointer; }}
    .primary {{ background: var(--accent); color: #fff; }}
    .secondary {{ background: #e9eef9; color: #22304a; }}
    .danger {{ background: #ffefee; color: var(--bad); }}
    .banner {{ border-radius: 12px; padding: 12px 14px; margin-bottom: 16px; font-size: 14px; }}
    .ok {{ background: #eaf7ee; color: var(--good); border: 1px solid #c7ead3; }}
    .err {{ background: #fff1f0; color: var(--bad); border: 1px solid #f5c2be; }}
    code {{ background: #f1f4fa; border: 1px solid #e3e8f3; padding: 1px 6px; border-radius: 6px; }}
    .foot {{ color: var(--muted); font-size: 13px; margin-top: 10px; line-height: 1.45; }}
    .tiny {{ color: var(--muted); font-size: 12px; }}
    .table-wrap {{ overflow: auto; border: 1px solid var(--border); border-radius: 12px; }}
    .table-wrap table {{ margin: 0; border: 0; }}
  </style>
</head>
<body>
  <header>
    <h1>Prepper Network Admin</h1>
    <div class="sub">Manage the AP, choose an upstream Wi‑Fi network on the USB adapter, and change SSID/password from one page.</div>
  </header>
  <main>
    {banner}
    <div class="grid">
      <section class="card">
        <h2>Current setup</h2>
        <div class="meta">
          <div>AP SSID</div><div><code>{html_escape(ap['ssid'])}</code></div>
          <div>AP mode</div><div><code>{html_escape(ap['mode'])}</code></div>
          <div>AP band</div><div><code>{html_escape(ap['band'])}</code></div>
          <div>AP channel</div><div><code>{html_escape(ap['channel'])}</code></div>
          <div>AP IPv4</div><div><code>{html_escape(ap['ipv4_method'])}</code></div>
          <div>AP interface</div><div><code>{html_escape(ap['interface'])}</code></div>
          <div>AP address</div><div><code>{html_escape(ap['ip'] or '10.42.0.1/24')}</code></div>
          <div>Ethernet</div><div><code>{html_escape(snap['ethernet']['state'])}</code> <span class="tiny">{html_escape(snap['ethernet']['connection'])}</span></div>
          <div>USB client</div><div><code>{html_escape(usb['state'])}</code></div>
          <div>USB profile</div><div><code>{html_escape(usb['profile_ssid'] or '')}</code></div>
          <div>USB metric</div><div><code>{html_escape(usb['route_metric'] or '')}</code></div>
        </div>
        <div class="foot">Ethernet remains the preferred uplink when present. If Ethernet is unplugged, the USB Wi‑Fi client can provide upstream internet while the AP stays up.</div>
      </section>

      <section class="card">
        <h2>Change AP SSID / password</h2>
        <form method="post" action="/apply-ap">
          <div class="row">
            <div>
              <label for="ap_ssid">SSID</label>
              <input id="ap_ssid" name="ssid" value="{html_escape(ap['ssid'])}" required />
            </div>
            <div>
              <label for="ap_password">Wi‑Fi password</label>
              <input id="ap_password" name="password" type="password" placeholder="Leave blank to keep current password" />
            </div>
            <div class="row2">
              <div>
                <label for="ap_band">Band</label>
                <select id="ap_band" name="band">
                  <option value="">Keep current</option>
                  <option value="bg" {'selected' if ap['band'] == 'bg' else ''}>2.4 GHz (bg)</option>
                  <option value="a" {'selected' if ap['band'] == 'a' else ''}>5 GHz (a)</option>
                </select>
              </div>
              <div>
                <label for="ap_channel">Channel</label>
                <input id="ap_channel" name="channel" value="{html_escape(ap['channel'])}" placeholder="e.g. 6 or 36" />
              </div>
            </div>
          </div>
          <div class="actions">
            <button class="primary" type="submit">Apply and restart AP</button>
          </div>
        </form>
      </section>

<section class="card">
        <h2>Quick uplink switch</h2>
        <div class="foot">One click to prefer Ethernet or the USB Wi‑Fi client. The AP stays up either way.</div>
        <div class="tiny" style="margin-top:6px;">Active uplink: <strong>{'Ethernet' if active_uplink == 'ethernet' else 'USB Wi‑Fi' if active_uplink == 'usb' else html_escape(active_uplink or 'unknown')}</strong></div>
        <form method="post" action="/switch-ethernet">
          <div class="actions">
            <button class="primary" type="submit" {'disabled' if active_uplink == 'ethernet' else ''}>Switch to Ethernet</button>
          </div>
        </form>
        <form method="post" action="/switch-usb" style="margin-top:10px;">
          <div class="actions">
            <button class="secondary" type="submit" {'disabled' if active_uplink == 'usb' else ''}>Switch to USB Wi‑Fi</button>
          </div>
        </form>
      </section>

      <section class="card">
        <h2>USB Wi‑Fi uplink</h2>
        <form method="post" action="/connect-uplink">
          <div class="row">
            <div>
              <label for="uplink_ssid">SSID</label>
              <input id="uplink_ssid" name="ssid" list="known_networks" placeholder="Choose or type a network name" required />
              <datalist id="known_networks">
                {''.join(f'<option value="{html_escape(s["ssid"])}"></option>' for s in usb['scan'][:50])}
              </datalist>
            </div>
            <div>
              <label for="uplink_password">Wi‑Fi password</label>
              <input id="uplink_password" name="password" type="password" placeholder="Blank for open networks" />
            </div>
            <div>
              <label><input type="checkbox" name="hidden" value="yes" style="width:auto; margin-right:8px;">Hidden SSID</label>
            </div>
          </div>
          <div class="actions">
            <button class="primary" type="submit">Connect USB Wi‑Fi</button>
          </div>
        </form>
        <form method="post" action="/disconnect-uplink" style="margin-top:10px;">
          <div class="actions">
            <button class="secondary" type="submit">Disconnect USB Wi‑Fi</button>
            <button class="danger" type="submit" name="delete" value="yes">Forget profile</button>
          </div>
        </form>
        <div class="foot">The USB adapter is kept separate from the AP radio. That lets the box stay on Signal_Beacon while joining another Wi‑Fi network upstream.</div>
      </section>

      <section class="card" style="grid-column: 1 / -1;">
        <h2>Nearby Wi‑Fi networks seen by the USB adapter</h2>
        <div class="tiny">Refreshes automatically whenever the page loads.</div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>In use</th><th>SSID</th><th>Signal</th><th>Security</th><th>Channel</th></tr></thead>
            <tbody>{''.join(scan_rows) if scan_rows else '<tr><td colspan="5">No scan results yet.</td></tr>'}</tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <h2>Device status</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Device</th><th>Type</th><th>State</th><th>Connection</th></tr></thead>
            <tbody>{''.join(dev_rows)}</tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <h2>Active connections</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Type</th><th>Device</th><th>State</th></tr></thead>
            <tbody>{''.join(active_rows)}</tbody>
          </table>
        </div>
      </section>

      <section class="card" style="grid-column: 1 / -1;">
        <h2>Routing</h2>
        <pre style="margin:0;white-space:pre-wrap;font-size:13px;line-height:1.45;background:#f7f9fc;border:1px solid var(--border);border-radius:12px;padding:14px;overflow:auto;">{html_escape(snap['routes'])}</pre>
      </section>
    </div>
  </main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - - [{self.log_date_time_string()}] {fmt % args}")

    def send_html(self, text: str, code: int = 200) -> None:
        data = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, obj: dict, code: int = 200) -> None:
        data = json.dumps(obj, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self.send_json(status_snapshot())
            return
        self.send_html(render_page())

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length).decode("utf-8", "replace")
        form = parse_qs(body)
        try:
            if parsed.path == "/switch-ethernet":
                switch_to_ethernet()
                self.send_html(render_page(message="Switched to Ethernet uplink."))
                return
            if parsed.path == "/switch-usb":
                switch_to_usb_wifi()
                self.send_html(render_page(message="Switched to USB Wi‑Fi uplink."))
                return
            if parsed.path == "/apply-ap":
                set_ap(
                    ssid=(form.get("ssid") or [""])[0].strip(),
                    password=(form.get("password") or [""])[0],
                    band=(form.get("band") or [""])[0].strip(),
                    channel=(form.get("channel") or [""])[0].strip(),
                )
                self.send_html(render_page(message="AP settings applied successfully."))
                return
            if parsed.path == "/connect-uplink":
                set_uplink(
                    ssid=(form.get("ssid") or [""])[0].strip(),
                    password=(form.get("password") or [""])[0],
                    hidden=(form.get("hidden") or [""])[0] == "yes",
                )
                self.send_html(render_page(message="USB Wi‑Fi connected successfully."))
                return
            if parsed.path == "/disconnect-uplink":
                delete_profile = (form.get("delete") or [""])[0] == "yes"
                disconnect_uplink(delete_profile=delete_profile)
                self.send_html(render_page(message="USB Wi‑Fi disconnected."))
                return
            self.send_html(render_page(error="Unknown action."), code=404)
        except Exception as e:
            self.send_html(render_page(error=str(e)))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Prepper Network Admin listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
