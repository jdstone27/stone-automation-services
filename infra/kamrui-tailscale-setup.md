# Kamrui: fleet worker / model host provisioning

Runbook for the Kamrui mini PC (Ubuntu 24.04 LTS). Role in the fleet:
**fleet worker / model host** — runs `ollama` for local inference plus the
agent supervisor and Docker workloads, always-on, reachable over the Tailscale
mesh.

> Note: earlier fleet notes described Kamrui as a "sandboxed node for untrusted
> code." That is not its role — it holds fleet credentials and control code and
> is an active worker, so it is not a place to run untrusted code. If an
> untrusted-code sandbox is needed, use a separate node (or a host-secret-free
> Docker/qemu boundary on this one).

Run the commands below directly on the Kamrui box (SSH or Tailscale SSH).

## 1. Join the Tailscale mesh

```bash
curl -fsSL https://tailscale.com/install.sh -o ts.sh
sudo sh ts.sh
sudo tailscale up --hostname=kamrui --ssh
```

`--ssh` enables Tailscale SSH, which is the reliable fallback if OpenSSH is
ever locked out (see hardening below).

## 2. Keep it awake 24/7

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

If it has a lid or a GUI session, also set `HandleLidSwitch=ignore` and
`HandleLidSwitchDocked=ignore` in `/etc/systemd/logind.conf` and restart
`systemd-logind`.

## 3. Disable Tailscale key expiry

In the Tailscale admin console (login.tailscale.com/admin/machines): find
`kamrui` -> `...` menu -> **Disable key expiry**, or the node drops off the
mesh after the default expiry window (~180 days). *(Done.)*

## 4. Headless strip (remove the desktop)

This box shipped as a full Ubuntu desktop. For a headless worker, remove the
GUI to cut attack surface and free resources:

```bash
sudo systemctl set-default multi-user.target
sudo apt-get purge -y ubuntu-desktop-minimal gnome-shell gdm3 xserver-xorg xserver-xorg-core gnome-remote-desktop
sudo apt-get autoremove --purge -y
sudo snap remove --purge firefox snap-store snapd-desktop-integration gtk-common-themes gnome-46-2404 gnome-42-2204 mesa-2404
sudo apt-get clean
sudo journalctl --vacuum-time=7d
```

`ollama`, `docker`/`containerd`, `qemu-kvm`, and `ttyd` are intentionally kept
— they are the worker's job.

## 5. Lock down networking

Disable services a headless worker doesn't need (notably GNOME Remote Desktop,
which was listening on `*:3389/3390`):

```bash
sudo systemctl disable --now gnome-remote-desktop.service avahi-daemon avahi-daemon.socket cups cups.socket cups-browsed bluetooth ModemManager
```

Enable the firewall — add allow rules *before* enabling so SSH can't lock out:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow in on tailscale0
sudo ufw allow 41641/udp   # tailscale direct connections
sudo ufw allow 22/tcp      # LAN SSH fallback; tighten to tailscale-only later
sudo ufw --force enable
```

## 6. Harden SSH (key-only)

The stock config allowed password auth. Override it (this drop-in beats the
cloud-init default):

```bash
printf 'PasswordAuthentication no\nPermitRootLogin no\n' | sudo tee /etc/ssh/sshd_config.d/99-hardening.conf
sudo systemctl restart ssh
```

Tailscale SSH (`tailscale ssh justin@kamrui` from another tailnet device) is the
guaranteed fallback if key auth ever fails.

## 7. Register the node in fleet_state.json

On the machine holding the canonical fleet state
(`~/Documents/Audit/hermes-fleet/fleet_state.json`), add an entry for Kamrui.
Match the file's actual schema; the shape below is a starting point:

```json
"nodes": {
  "kamrui": {
    "role": "fleet-worker",
    "tailscale_hostname": "kamrui",
    "tailscale_ip": "100.106.133.47",
    "os": "ubuntu-24.04",
    "always_on": true,
    "services": ["ollama", "docker"]
  }
}
```
