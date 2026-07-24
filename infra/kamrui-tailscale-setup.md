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

`--ssh` enables Tailscale SSH. In practice this was unreliable as a fallback
from macOS clients (see "Access gotchas" below) — don't count on it as the
only way back in; keep a real SSH key authorized too.

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
mesh after the default expiry window (~180 days).

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

**`autoremove --purge` is aggressive here.** On this box it took ~328
packages, including some that were still load-bearing:

- `unattended-upgrades` — security auto-patching. Reinstall:
  `sudo apt-get install -y unattended-upgrades`
- `unzip`, `fdisk` — reinstall if needed: `sudo apt-get install -y unzip fdisk`
- `python3-requests`, `python3-jinja2` — if any fleet script imports these
  under the **system** Python (not a venv), it will break with
  `ModuleNotFoundError` after this step. Verify and restore:
  ```bash
  python3 -c "import requests, jinja2"
  sudo apt-get install -y python3-requests python3-jinja2   # if that failed
  ```

Run the verification in step 8 immediately after this step, before moving on.

## 5. Lock down networking

Disable services a headless worker doesn't need (notably GNOME Remote Desktop,
which was listening on `*:3389/3390`, and avahi/cups):

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

To later restrict SSH to the tailnet only: `sudo ufw delete allow 22/tcp`
(the `tailscale0` rule already covers SSH over the mesh).

## 6. Harden SSH (key-only)

The stock config allowed password auth. Override it (this drop-in beats the
cloud-init default):

```bash
printf 'PasswordAuthentication no\nPermitRootLogin no\n' | sudo tee /etc/ssh/sshd_config.d/99-hardening.conf
sudo systemctl restart ssh
```

**Do this only after a real SSH key is already in `~/.ssh/authorized_keys`.**
Generate a key on the client and add it *before* disabling password auth:

```bash
# on the client machine
ssh-keygen -t ed25519 -C "<user>@kamrui" -N "" -f ~/.ssh/hermes_kamrui_worker
cat ~/.ssh/hermes_kamrui_worker.pub   # copy this line
```

```bash
# on Kamrui, append the copied line
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo '<paste the ssh-ed25519 line here>' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Then confirm the *exact* key/file you authorized is the one you connect with:
`ssh -i ~/.ssh/hermes_kamrui_worker justin@<tailscale-ip>`. If you generate
more than one key while setting this up, it's easy to authorize one and
connect with another — that mismatch produces a bare
`Permission denied (publickey)` with no other clue.

### Access gotchas (from doing this the hard way)

- **`tailscale ssh` failing with "Host key verification failed" / "requested
  strict checking"** on a macOS client is not fixed by editing
  `~/.ssh/config` — `tailscale ssh` manages its own trust store separately.
  Don't chase this; use a real SSH key instead (above).
- **Bracketed-paste corruption at a physical/console terminal**: pasted
  multi-line commands can get `^[[200~` / `^[[201~` markers spliced into the
  first/last line, breaking the command name (e.g. `sudo` becomes
  unrecognized). Fix per-session with `bind 'set enable-bracketed-paste off'`,
  or type single-line commands, or use `tailscale file cp` to transfer a file
  instead of retyping it.
- **A wrong SSH password locks you out of `sudo`, not just login.** If you're
  ever forced into GRUB recovery mode to reset it: Advanced options for
  Ubuntu -> `(recovery mode)` -> `root` shell -> `mount -o remount,rw /` ->
  `passwd <user>` -> `reboot`.

## 7. Verify (run right after step 4, and again after step 6)

```bash
echo "=== target ==="; systemctl get-default
echo "=== gui leftovers (want empty) ==="; dpkg -l | grep -Ei 'ubuntu-desktop|gnome-shell|^ii  xserver-xorg' | awk '{print $2}'
echo "=== ufw ==="; sudo ufw status verbose
echo "=== noise services (want inactive) ==="; systemctl is-active avahi-daemon cups gnome-remote-desktop
echo "=== auto-updates (want ii) ==="; dpkg -l unattended-upgrades | grep '^ii'
echo "=== ssh hardening ==="; sudo sshd -T 2>/dev/null | grep -Ei 'passwordauthentication|permitrootlogin'
echo "=== exposed ports (want only :22 + tailscale) ==="; sudo ss -tulpn | grep -Ev '127\.0\.0|::1'
echo "=== tailscale ==="; tailscale status
```

Expected clean state: `multi-user.target`, no GUI packages, `ufw active`
(default-deny incoming, `tailscale0` + `22/tcp` + `41641/udp` allowed),
avahi/cups/RDP all `inactive`, `unattended-upgrades` present,
`passwordauthentication no` / `permitrootlogin no`, and the only externally
reachable ports are SSH (`:22`) and Tailscale itself.

## 8. Register the node in fleet_state.json

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
