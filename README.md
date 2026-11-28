# credfeto-dns

Technitium DNS Server running in Docker with host networking, managed block lists, and version-controlled zone files.

See `CHANGELOG.md` for release history and notable changes.

## Prerequisites

- Docker with Compose plugin
- `firewall-cmd` (firewalld) for the inbound rules
- `nft` (nftables) and `python3` for the egress table
- `systemd`
- Port 53 available on the host — disable the systemd-resolved stub listener if present:

  ```sh
  sudo systemctl disable --now systemd-resolved
  ```

## First-time setup

### 1. Configure the admin password

```sh
cp .env.example .env
# Edit .env and set a strong DNS_ADMIN_PASSWORD
```

Optionally set `WATCHTOWER_SCHEDULE` in `.env` (6-field cron, seconds first) to
override when Watchtower checks for image updates; the default `0 12 * * * *`
runs hourly at minute 12. Old images are cleaned up after each update.

### 2. Install the zone sync timer

```sh
cp scripts/.env.example scripts/.env
# Leave DNS_API_TOKEN blank for now — fill it in after step 4
./install
```

This installs a systemd timer that runs `scripts/sync-zones` every 15 minutes.

### 3. Start the server and apply firewall rules

```sh
./update
```

This creates `/data/technitium/config` and `/data/technitium/logs`, starts the container, and ensures all firewall rules are in place.

### 4. Generate an API token

Open the admin UI at `https://<host-ip>:53443`, log in with the password from `.env`, then go to **Settings → API Keys** and create a token. Paste it into `scripts/.env`:

```sh
DNS_API_TOKEN=your-token-here
```

### 5. Import zones

Paste the API token into `scripts/.env`, then run `./update` again. At the end of `update`, `sync-zones --all` is called automatically and imports every `.db` file in `zones/` into Technitium.

The imported zones are persisted by Technitium in the same directory (as `.zone` files, which are `.gitignore`d).

---

## Day-to-day operations

### Updating

```sh
./update
```

Pulls the latest repo changes, ensures the container is running, applies firewall rules, then imports all zones via `sync-zones --all`.

### Zone changes

Edit zone files in `zones/`, commit, and push. The systemd timer will pick up the changes within 15 minutes and import the updated zones via the Technitium API. Changes to `update` (firewall rules), `docker-compose.yml`, the egress table builder (`scripts/egress`), its units or `scripts/github-egress-ranges` are applied the same way: `sync-zones` runs `./update` when the checkout is ahead of the commit `./update` last applied (recorded in `/var/lib/credfeto-adguard-home/applied-head`). To apply immediately:

```sh
./scripts/sync-zones
```

To import all zones regardless of git state (e.g. after a fresh deploy):

```sh
./scripts/sync-zones --all
```

### Restarting the container

```sh
docker compose restart dns-server
```

---

## Scripts

| Script | Purpose |
| --- | --- |
| `install` | Installs and enables the systemd timer for zone sync |
| `update` | Full update: pull, start container, apply firewall rules |
| `scripts/sync-zones` | Pull latest; import changed zones via API. Refreshes the egress table first. If the pulled commits change host config (`update`, `docker-compose.yml`, `scripts/egress`, its units or `scripts/github-egress-ranges`) that hasn't been applied yet, it runs `./update` instead. `--all` imports every zone. |
| `scripts/egress` | Builds and loads the egress nftables table `inet dns_egress` (installed as `/usr/local/bin/dns-egress`; run by `update`, `sync-zones` and `dns-egress-refresh.timer`). Loads only when the rendered table differs from the loaded one. |
| `scripts/update-github-egress-ranges` | Regenerates `scripts/github-egress-ranges` from <https://api.github.com/meta>. Run by the `Repo: Update GitHub egress ranges` workflow, not on a DNS node. |
| `reset` | Stop and remove containers, then run `update` |
| `scripts/replace-proxy-ip` | Replace a proxy address in every zone's A/AAAA records and bump each changed zone's serial. `--dry-run` lists the files without changing them. |
| `scripts/check-proxy-ips` | Fail if any zone carries some, but not all, of the proxy addresses. Run offline by `scripts/self-test`. |
| `scripts/check-zone-sync` | Fail if any internal A/AAAA record has no matching PTR, or any PTR target has no A/AAAA record for its address. Run by the `PR: Zone Sync Check` workflow. |
| `scripts/check-zone-names` | Fail if a zone holds a name that belongs in a sub-zone, or a parent-zone name for a sub-zone host that isn't a CNAME to it (see [Zone name rules](#zone-name-rules)). Run by the `PR: Zone Lint` workflow. |

## Files

| Path | Purpose |
| --- | --- |
| `.env` | Admin password (not committed) |
| `.env.example` | Template for `.env` |
| `scripts/.env` | API token for zone sync (not committed) |
| `scripts/.env.example` | Template for `scripts/.env` |
| `zones/` | Version-controlled zone files, mounted into the container |
| `docker-compose.yml` | Container definition |

## Data directories

| Host path | Container path | Contents |
| --- | --- | --- |
| `/data/technitium/config` | `/etc/dns` | Technitium configuration (persists across restarts) |
| `/data/technitium/logs` | `/var/log/technitium/dns` | DNS query logs |
| `./zones` | `/etc/dns/config/zones` | Zone files (version-controlled) |

## Zone file layout

Zones are maintained as BIND-format `.db` files in `zones/`. Technitium writes its internal `.zone` files alongside them (`.gitignore`d).

| File | Zone type | Purpose |
| --- | --- | --- |
| `lan.db` | Primary | `.lan` hostnames (Proxmox nodes, servers), plus CNAMEs to sub-zone hosts |
| `dns.lan.db` | Primary | DNS server hostnames |
| `storage.lan.db` | Primary | Storage VLAN hosts (NASes) |
| `proxy.markridgwell.com.db` | Primary | A/AAAA records → `192.168.140.250` (proxy-01) and `192.168.140.251` (proxy-02), plus `01.`/`02.` sub-records pinned to each individually |
| `network.lan.db` | Primary | Network device hostnames (firewall, switches, access points) |
| `orchestrator.lan.db` | Primary | Orchestrator hosts |
| `<service>.markridgwell.com.db` | Override | Per-service A/AAAA → both proxy addresses (round-robin) |
| `<resolver>.db` | Override | DoH resolver IP overrides (Cloudflare, Google, Quad9) |

**Split-brain DNS:** Each `<service>.markridgwell.com` is its own override zone (not a full `markridgwell.com` zone), so Cloudflare remains authoritative for all other names under `markridgwell.com`.

**Adding a new internal service:**

```sh
# Point a new subdomain at the proxy:
cp zones/audiobookshelf.markridgwell.com.db zones/newservice.markridgwell.com.db
# Edit the $ORIGIN line, commit, push — timer will import within 15 min.
```

**Changing a proxy IP:** There is no CNAME chain; each `<service>.markridgwell.com.db` hardcodes both proxy addresses directly, as do `proxy.markridgwell.com.db` and `lan.db`. Use `scripts/replace-proxy-ip` to update them all at once:

```sh
# Preview which zone files would change:
./scripts/replace-proxy-ip --dry-run 192.168.140.250 192.168.140.252
# Replace the address in every A/AAAA record and bump each changed zone's serial by 1:
./scripts/replace-proxy-ip 192.168.140.250 192.168.140.252
# Confirm every zone still carries the complete proxy address set:
./scripts/check-proxy-ips 192.168.140.252 192.168.140.251 2a02:8010:61d5:140::250 2a02:8010:61d5:140::251
```

Both scripts accept `--zones DIR` to work on a directory other than `zones/`. `check-proxy-ips` with no address arguments checks the current default set (`192.168.140.250`, `192.168.140.251`, `2a02:8010:61d5:140::250` and `2a02:8010:61d5:140::251`), which `scripts/self-test` relies on, so update the defaults in the script when a proxy address changes.

`replace-proxy-ip` only changes A/AAAA records. The following still need updating by hand: the reverse PTR records in `140.168.192.in-addr.arpa.db` and `0.4.1.0.5.d.1.6.0.1.0.8.2.0.a.2.ip6.arpa.db` (bump their serials too), the egress allow-list in `scripts/egress`, and `docs/network/egress-whitelist.md`. Grep the repo for the old IP to find every occurrence rather than relying on this list staying exhaustive.

### Zone name rules

`scripts/check-zone-names` enforces two rules over every forward zone in `zones/`:

1. **One label per name.** An owner name is a single label below its zone. A dotted name such as `nas-01.storage` in `lan.db` belongs in its own zone file (`zones/storage.lan.db`, as `nas-01`), whether or not that file exists yet. Leading `_` labels (`_sip._tcp`, `_acme-challenge.www`) don't count. Reverse (`.arpa`) zones are exempt.
2. **Flat aliases are CNAMEs.** When a host has A/AAAA records in a sub-zone, a name for it in the parent zone must be exactly one CNAME to the full sub-zone name and nothing else. For `dns-06.dns.lan`, `lan.db` holds only `dns-06 IN CNAME dns-06.dns.lan.`. PTR records point at the sub-zone name.

Each error names the file, the line and the fix. Run it, with the other zone checks, before pushing a zone change:

```sh
python3 scripts/check-zone-names
python3 scripts/check-zone-sync
python3 -m unittest discover -s scripts/tests
```

The required `PR: Zone Lint` workflow runs these on every pull request, together with BIND's `named-checkzone` over every `zones/*.db` (zone name from the file name), which catches syntax, SOA/NS and CNAME-and-other-data errors.

## Security notes

- The container uses `network_mode: host` — it binds directly to the host's network stack. Firewall rules are the primary access control.
- DHCP ports 67/68 are explicitly rejected at the firewall even though Technitium's DHCP server is inactive by default.
- Outbound traffic is deny-by-default with an explicit allow-list (see [Egress firewall](#egress-firewall)).
- `DNS_SERVER_RECURSION=AllowOnlyForPrivateNetworks` prevents this server from acting as an open resolver.
- The admin UI uses a self-signed certificate on port 53443. Accept the browser warning or add the cert to your trust store.

## Egress firewall

The host's outbound traffic is filtered by one nftables table, `inet dns_egress`, which `scripts/egress` builds and loads. Technitium uses host networking, so its recursion, forwarding, blocklist downloads and log shipping all go through the table's `host_out` chain (the `output` hook). Watchtower, on a Docker bridge, is not filtered by it.

- **Allowed:** DNS (53/tcp+udp) to any destination, since recursive resolution reaches every authoritative server; HTTPS (443/tcp) to the proxies (`192.168.140.250`, `192.168.140.251`, `2a02:8010:61d5:140::250`, `2a02:8010:61d5:140::251`), NextDNS, download.technitium.com, GitHub Pages (Fastly), GitHub's published ranges and the resolved addresses of github.com, cdn-mirror.chaotic.cx, pkgstats.archlinux.de and openpgpkey.archlinux.org; NTP to `192.168.42.1`; SQL Server (1433/tcp) on `192.168.130.254`; VictoriaLogs (9428/tcp) and syslog (514/udp) on `192.168.160.134`; ICMPv6, IGMP and DHCPv6. `scripts/egress` holds the list, and `docs/network/egress-whitelist.md` the reasons.
- **Enforcement:** on by default: unmatched new connections are dropped. Set `DNS_EGRESS_ENFORCE=false` in `.env` for observation mode, where they are accepted. Any other value, or none, enforces. In both modes unmatched connections are logged with the kernel log prefix `dns-egress-unmatched:` (with a trailing space) (at most 30 a minute).
- **Refresh:** `dns-egress-refresh.service` runs `/usr/local/bin/dns-egress` at boot, before Docker starts, and `dns-egress-refresh.timer` runs it every 10 minutes; `sync-zones` runs it before each pull. Each run resolves the names (keeping the last good answer, in `/var/lib/credfeto-adguard-home/egress-resolved.json`, for a name that does not resolve) and reads `/usr/local/share/credfeto-adguard-home/github-egress-ranges`. The table, sets included, is replaced in one `nft -f` transaction, only when it changed, and is checked with `nft -c` first, so a rejected ruleset leaves the loaded one in place. firewalld is never reloaded for egress.
- **Migration:** on a node that still has the firewalld `dns-egress` policy and `dns-egress-*` ipsets, `update` loads and verifies the table first, then deletes the policy and ipsets and activates that with a single `firewall-cmd --reload`.
