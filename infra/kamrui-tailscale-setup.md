# Kamrui: Tailscale mesh + always-on setup

Runbook for bringing the Kamrui mini PC (Ubuntu, sandboxed untrusted-code node)
onto the home-lab Tailscale mesh, keeping it awake 24/7, and registering it in
the fleet state.

Run the commands below directly on the Kamrui box (SSH or local console).

## 1. Join the Tailscale mesh

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled
sudo tailscale up --hostname=kamrui --ssh --advertise-tags=tag:sandbox
```

- `--ssh` enables Tailscale SSH to this node going forward.
- `--advertise-tags=tag:sandbox` only applies if the tailnet ACLs use tags to
  isolate the untrusted-code node — drop it if tags aren't configured.

## 2. Prevent sleep/suspend

Headless-safe, works regardless of desktop environment:

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# if it has a lid or a GUI session:
sudo sed -i 's/^#\?HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sudo sed -i 's/^#\?HandleLidSwitchDocked=.*/HandleLidSwitchDocked=ignore/' /etc/systemd/logind.conf
sudo systemctl restart systemd-logind
```

## 3. Disable Tailscale key expiry

In the Tailscale admin console (login.tailscale.com/admin/machines), find
`kamrui` → `⋯` menu → **Disable key expiry**. Without this the node silently
drops off the mesh after the default expiry window (~180 days).

## 4. Register the node in fleet_state.json

On the machine holding the canonical fleet state
(`~/Documents/Audit/hermes-fleet/fleet_state.json`), add an entry for Kamrui,
e.g.:

```json
"nodes": {
  "kamrui": {
    "role": "sandbox-untrusted-code",
    "tailscale_hostname": "kamrui",
    "os": "ubuntu",
    "always_on": true
  }
}
```

Adjust the schema to match whatever the current `fleet_state.json` actually
looks like — the snippet above is a starting point, not a fixed format.
