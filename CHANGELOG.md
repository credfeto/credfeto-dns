# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Please ADD ALL Changes to the UNRELEASED SECTION and not a specific release
-->

## [Unreleased]
### Security
- Egress firewall moved from the firewalld `dns-egress` policy and `dns-egress-*` ipsets to one nftables table, `inet dns_egress`, built by `scripts/egress` and replaced atomically (`nft -f`, checked with `nft -c` first) by `./update`, `scripts/sync-zones` and `dns-egress-refresh.timer`, so refreshing it never reloads firewalld (a firewalld killed mid-reload leaves its block-everything table loaded). Same allow-list and the same `DNS_EGRESS_ENFORCE` semantics (enforce unless exactly `false`); it is also loaded at boot before Docker starts. `./update` loads and verifies the table before it deletes the old policy and ipsets, with a single firewalld reload. `scripts/refresh-egress-ipsets` is removed.
- The proxies' Servers VLAN addresses (`192.168.150.250`, `192.168.150.251`, `2a02:8010:61d5:150::250`, `2a02:8010:61d5:150::251`) are no longer trusted: `./update` retires their egress (443/tcp) and 538/tcp rules on existing nodes, and `scripts/sync-zones` drops them from `dnsReverseProxyNetworkACL`
- The reverse proxies' DMZ VLAN addresses (`192.168.140.250`, `192.168.140.251`, `2a02:8010:61d5:140::250`, `2a02:8010:61d5:140::251`) are trusted alongside their Servers VLAN addresses: egress allow-list (443/tcp), DNS-over-TCP-PROXY port 538 (`./update`) and `dnsReverseProxyNetworkACL` (`scripts/sync-zones`), so proxy-01/proxy-02 can move to the DMZ one at a time
### Added
- DNS query logs to VictoriaLogs: `scripts/sync-zones` installs the Technitium Log Exporter app (3.1.1) when missing and applies `scripts/log-exporter.json` (RFC 5424 syslog over UDP to monitoring.lan 192.168.150.134:514); `./update` opens 192.168.150.134:514/udp in the egress allow-list. Runs with every full zone import (./update, or when host config changes)
- Egress allow-list: VictoriaLogs on monitoring.lan (`192.168.150.134:9428/tcp`), so the DNS hosts can forward their journal with systemd-journal-upload (credfeto/credfeto-setup-arch-vm#234)
- DNS-over-TCP-PROXY on port 538 for DNS-over-TLS via the proxies (`dns.markridgwell.com`, terminated by Traefik with PROXY protocol v2): `scripts/sync-zones` enables it and trusts only the two proxies in `dnsReverseProxyNetworkACL`, and `./update` opens 538/tcp to the proxy addresses only (new `allow_port_from` helper).
- Added `michelec320.lan` (`192.168.66.11`, the C320 printer's DHCP reservation on the Printers VLAN) to `zones/lan.db`, with its PTR in a new `zones/66.168.192.in-addr.arpa.db`.
- Added `work.lan` (`192.168.90.120`, the work machine's DHCP reservation on the Work VLAN) to `zones/lan.db`, with its PTR in a recreated `zones/90.168.192.in-addr.arpa.db`.
- Daily `Repo: Update GitHub egress ranges` workflow: regenerates `scripts/github-egress-ranges` from https://api.github.com/meta and commits it to main when GitHub publishes new ranges, so the DNS nodes pick them up on the next zone sync. It refuses to commit a list under 50 ranges or more than 20% shorter than the current one.
- `credfeto.orchestrator.lan` (`192.168.150.23`, `2a02:8010:61d5:150::17`) and `funfair-tech.orchestrator.lan` (`192.168.150.24`, `2a02:8010:61d5:150::18`) in `zones/lan.db` with IPv4 and IPv6 PTRs, for the orchestrator split into one VM per owner.
- `scripts/sync-zones` now runs `./update` when pulled commits change host config (`update`, `docker-compose.yml`, `scripts/refresh-egress-ipsets` or its timer) that hasn't been applied yet, so firewall/egress fixes go live on the next 15-minute sync instead of waiting for a manual `./update`. `./update` records the applied commit in `/var/lib/credfeto-adguard-home/applied-head`.
- Egress allow-list: openpgpkey.archlinux.org (HTTPS, WKD) via the dynamic ipsets, so the weekly archlinux-keyring-wkd-sync.timer key refresh stops failing, retrying every 5 minutes (Restart=on-failure) and logging thousands of dns-egress-unmatched drops a day
- Egress allow-list: pkgstats.archlinux.de (HTTPS) via the dynamic ipsets, so the weekly pkgstats.timer submission stops failing, retrying and logging dns-egress-unmatched drops
- Added .ai-instructions and ai/local/index.md from cs-template standard
- Added `dev-upgrader-01.lan` (`192.168.150.20`) to `zones/lan.db`.
- Added `dev-upgrader-02.lan` (`192.168.150.21`) to `zones/lan.db`.
- Added `linux-cache-01.lan` (`192.168.150.200`), `linux-cache-02.lan` (`192.168.150.201`), `defi.lan` (`192.168.150.12`), and `arch-vm-test.lan` (`192.168.150.247`) to `zones/lan.db`.
- DNS record for keys.markridgwell.com pointing to proxy on 192.168.150.250
- DNS record for grafana.markridgwell.com pointing to the proxies (192.168.150.250/.251 and their IPv6 addresses)
- DNS record for cctv.markridgwell.com pointing to proxy on 192.168.150.250
- Support IPv6 (private ranges and 2a02:8010:61d5::/64) in firewall rules
- Added `homepage.lan` (`192.168.150.150`) to `zones/lan.db`.
- Added `gickup.lan` (`192.168.150.13`) to `zones/lan.db`.
- Added `dns-06.lan` / `dns-06.dns.lan` (`192.168.42.106`, `2a02:8010:61d5:42::106`) to `zones/lan.db` and `zones/dns.lan.db`.
- Added `audio-bookshelf.lan` (`192.168.150.16`) to `zones/lan.db`.
- Added `dev-cache-01.lan` (`192.168.150.100`) and `dev-cache-02.lan` (`192.168.150.101`) to `zones/lan.db`.
- Added `development.lan` (`192.168.150.176`) to `zones/lan.db`.
- Added `immich.lan` (`192.168.150.154`) to `zones/lan.db`.
- Added `proxmox-05.lan` (`192.168.86.15`) and `proxmox-06.lan` (`192.168.86.16`) to `zones/lan.db`.
- Added `firewall.lan` (`192.168.10.1`) to `zones/lan.db`.
- Added new `network.lan` zone (`zones/network.lan.db`) with `stairs-01` (`192.168.10.2`) and `bedroom` (`192.168.10.5`); also added flat `stairs-01.lan` and `bedroom.lan` aliases to `zones/lan.db`.
- Added IPv6 AAAA records for public DNS resolvers: 1dot1dot1dot1.cloudflare-dns.com, mozilla.cloudflare-dns.com, security.cloudflare-dns.com, dns.google, and dns.quad9.net.
- Added public DNS resolver zones for Cloudflare Family (family.cloudflare-dns.com), AdGuard DNS (dns.adguard-dns.com), and OpenDNS (dns.opendns.com), each with IPv4 A and IPv6 AAAA records.
- Added dns-06.markridgwell.com zone (192.168.150.250).
- Added fcf757.dns.nextdns.io zone (NextDNS) with A and AAAA records.
- Added be6f94.dns.nextdns.io zone (NextDNS) with A and AAAA records.
- Added AAAA records (2a02:8010:61d5:150::250) for proxy.lan and all 36 services fronted by it, alongside their existing A records.
- Added `stairs-02.lan` (`192.168.10.3`) and `office.lan` (`192.168.10.4`) to `zones/lan.db` and `zones/network.lan.db`.
- DNS record for monitoring.markridgwell.com pointing to proxy on 192.168.150.250
- Added `ap-office.network.lan` (`192.168.10.7`) to `zones/network.lan.db` - Zyxel-Office wireless mesh access point.
- Added `ap-bedroom.network.lan` (`192.168.10.8`) to `zones/network.lan.db` - Zyxel-Bedroom wireless mesh access point.
- Added `ap-stairs.network.lan` (`192.168.10.6`) to `zones/network.lan.db` - Zyxel-Stairs wireless mesh access point.
- Added `ap-garden.network.lan` (`192.168.10.9`) to `zones/network.lan.db` - Zyxel-Garden wireless mesh access point.
- Added `ap-office.lan` (`192.168.10.7`) to `zones/lan.db` - Zyxel-Office wireless mesh access point.
- Added `ap-bedroom.lan` (`192.168.10.8`) to `zones/lan.db` - Zyxel-Bedroom wireless mesh access point.
- Added `ap-stairs.lan` (`192.168.10.6`) to `zones/lan.db` - Zyxel-Stairs wireless mesh access point.
- Added `ap-garden.lan` (`192.168.10.9`) to `zones/lan.db` - Zyxel-Garden wireless mesh access point.
- Added `netgear-proxmox-cluster.network.lan` and `netgear-proxmox-cluster.lan` (`192.168.10.10`) to `zones/network.lan.db` and `zones/lan.db` - NETGEAR GS108Ev3 switch (serial 3UHD1B540039A), the main switch for the Proxmox cluster, on a new DHCP reservation.
- DNS server outbound egress lockdown (firewalld dns-egress policy, inert by default via DNS_EGRESS_ENFORCE)
- Added second proxy node proxy-02.lan (192.168.150.251 / 2a02:8010:61d5:150::251); renamed proxy.lan to proxy-01.lan.
- Added 01.proxy.markridgwell.com and 02.proxy.markridgwell.com records for pinning to a specific proxy node.
- Added reverse DNS (PTR) zones for the internal 192.168.x.0/24 and 2a02:8010:61d5:x::/64 subnets, populated from the existing forward zones
- Added scripts to replace proxy IPs across zone files and check proxy IP consistency (#41)
- Added `scripts/check-zone-sync` and a `zone-sync-check` CI workflow to verify that forward A/AAAA records and reverse PTR zones stay in sync, with unit tests (#43)
- Added `workflow-mcp.markridgwell.com` zone resolving to the reverse-proxy pair (#46)
- Added `memory.lan` (`192.168.150.30`) to `zones/lan.db` with a matching PTR record in `zones/150.168.192.in-addr.arpa.db` (#49)
- Added `memory.markridgwell.com` zone resolving to the reverse-proxy pair (#49)
- Added `wiki.markridgwell.com` zone resolving to the reverse-proxy pair (#49)
- DNS record for logs.markridgwell.com (VictoriaLogs and its MCP server, via Traefik) pointing to the proxies (192.168.150.250/.251 and their IPv6 addresses)
### Fixed
- Egress: serialise runs with a lock and write the resolved-address cache through a unique temp file, so the refresh timer and the firewall sync starting together no longer fail with FileNotFoundError
- Corrected `xerox-b210-wired.lan` from the stale `192.168.86.156` to its Printers VLAN reservation `192.168.66.75`, moving its PTR from `zones/86.168.192.in-addr.arpa.db` to `zones/66.168.192.in-addr.arpa.db`.
- `scripts/github-egress-ranges` regenerated from https://api.github.com/meta: adds `20.64.190.224/28`, `20.254.76.112/28`, `74.158.248.0/28` and `172.130.99.48/28`. github.com resolving into `20.254.76.112/28` was dropped as dns-egress-unmatched, so `sync-zones` git pulls timed out after ~134 s and failed (dns-01 05:17, dns-05 03:45 and 04:45).
- Dropped the `nanoclaw.lan` CNAME from `zones/lan.db`: the zone import only overwrites records of the same type, so the old `nanoclaw` A record stayed and Technitium rejected the CNAME ("a CNAME record cannot exists with other record types"), failing the `lan` import on every DNS server.
- Fixed typo in `zones/lan.db`: `docker-tegistry` renamed to `docker-registry` (`192.168.150.202`).
- Corrected `monitoring.lan` IP in `zones/lan.db` from `192.168.150.135` to `192.168.150.134`.
- Egress ipset refresh no longer flaps on NAT64 spelling differences, and aborted update/refresh runs can no longer strand firewall runtime state behind permanent config
- Added missing reverse DNS (PTR) record for `familiar.lan` in the `150.168.192.in-addr.arpa` zone (`zones/150.168.192.in-addr.arpa.db`)
- Added missing reverse DNS (PTR) records for `netgear-printer` (`192.168.10.11`) and `netgear-office1` (`192.168.10.129`) to `zones/10.168.192.in-addr.arpa.db` (#46)
- Corrected the reverse DNS (PTR) record for `192.168.10.1` in `zones/10.168.192.in-addr.arpa.db` to point at `opnsense.network.lan` instead of `firewall.lan` (#46)
- Added missing reverse DNS zone `zones/2.168.192.in-addr.arpa.db` for `192.168.2.0/24` with PTR records for `stairs-01` (`192.168.2.2`), `stairs-02` (`192.168.2.3`), `office` (`192.168.2.4`) and `bedroom` (`192.168.2.5`) (#46)
### Changed
- proxy-01 moved to the DMZ VLAN: every proxy-fronted zone, `proxy.markridgwell.com` (`01.` included) and `proxy-01.lan` now use `192.168.140.250` / `2a02:8010:61d5:140::250`, with its PTRs in the DMZ reverse zones
- proxy-02 moved to the DMZ VLAN: every proxy-fronted zone, `proxy.markridgwell.com` (`02.` included) and `proxy-02.lan` now use `192.168.140.251` / `2a02:8010:61d5:140::251`; its PTRs moved to the new `140.168.192.in-addr.arpa` and `0.4.1.0.5.d.1.6.0.1.0.8.2.0.a.2.ip6.arpa` zones, and `scripts/check-proxy-ips` defaults follow
- linux-cache-01.lan and linux-cache-02.lan moved to the new LinuxCaches VLAN 21: A `192.168.210.200` / `192.168.210.201` (were 192.168.150.200/201), PTRs in the new `zones/210.168.192.in-addr.arpa.db`
- dev-cache-01.lan and dev-cache-02.lan moved to the new Caches VLAN 20: A `192.168.200.100` / `192.168.200.101` (were 192.168.150.100/101), PTRs in the new `zones/200.168.192.in-addr.arpa.db`
- familiar.lan moved to the new Familiar VLAN 19: A `192.168.190.129` (was `192.168.150.129`), PTR in the new `zones/190.168.192.in-addr.arpa.db`
- dev-upgrader-01.lan moved to the Development VLAN 18: A `192.168.180.20` (was `192.168.150.20`), PTR in `zones/180.168.192.in-addr.arpa.db`. dev-upgrader-02 stays on 192.168.150.21 until it is next powered on and moved
- development.lan moved to the new Development VLAN 18: A `192.168.180.176` (was `192.168.150.176` on the Servers VLAN); its PTR moves to the new `zones/180.168.192.in-addr.arpa.db`
- credfeto.orchestrator.lan and funfair-tech.orchestrator.lan moved to the new Orchestrators VLAN 17: A `192.168.170.23` / `192.168.170.24`, AAAA `2a02:8010:61d5:170::17` / `::18` (were 192.168.150.x and 2a02:8010:61d5:150::x on the Servers VLAN); their PTRs move to the new `zones/170.168.192.in-addr.arpa.db` and `zones/0.7.1.0.5.d.1.6.0.1.0.8.2.0.a.2.ip6.arpa.db`
- monitoring.lan moved to the new Monitoring VLAN 16: A record `192.168.160.134` (was `192.168.150.134` on the Servers VLAN), its PTR moves from `zones/150.168.192.in-addr.arpa.db` to the new `zones/160.168.192.in-addr.arpa.db`, and the egress allow-list rules (VictoriaLogs 9428/tcp, syslog 514/udp) and `scripts/log-exporter.json` now target `192.168.160.134`
- Moved `sql-server.lan` to the new Databases VLAN 13: A record `192.168.130.254` (was `192.168.90.254` on the Work VLAN), its PTR moves from `zones/90.168.192.in-addr.arpa.db` to the new `zones/130.168.192.in-addr.arpa.db`, and the DNS egress allow-list rule for Technitium's Query Logs (SQL Server) app now targets `192.168.130.254:1433`. The old `90.168.192.in-addr.arpa` zone has to be deleted from each DNS server by hand (sync-zones only reports removed zones).
- Removed the legacy repository `hosts` file workflow; zone files in `zones/` are now the source of truth.
- Widened the allowed IPv6 firewall network from 2a02:8010:61d5::/64 to 2a02:8010:61d5::/48 to cover all subnets, not just subnet 0
- Switched Technitium recursion ACL from AllowOnlyForPrivateNetworks to an explicit network ACL including 2a02:8010:61d5::/48, since public IPv6 addresses are never classified as private
- Renumbered dns-01 through dns-04 from 192.168.42.251-254 to 192.168.42.101-104, added dns-05 (192.168.42.105), and added AAAA records (2a02:8010:61d5:42::101-105) for all five in lan.db and dns.lan.db
- Removed stale hagezi block-list URLs from docker-compose - hagezi was deliberately disabled in the live config
- install now runs update at the end so a fresh ./install produces a fully running system
- Egress lockdown is now enforced by default - set DNS_EGRESS_ENFORCE=false for observation mode
- Simplified egress firewall internals - single log-only catch-all with the policy target as the sole enforcement knob (kernel log prefix is now always dns-egress-unmatched:), shared rule helper, conditional reloads
- All 36 services previously fronted by the single proxy now resolve to both proxy-01 and proxy-02 addresses (DNS round-robin), and the internal proxy egress firewall rule allows both.
- Watchtower now removes old images after each update (WATCHTOWER_CLEANUP=true) and its fixed poll interval is replaced by an overridable 6-field cron WATCHTOWER_SCHEDULE, defaulting to hourly at minute 12 (set in .env)
### Deprecated
### Removed
- linux-cache-01.markridgwell.com and linux-cache-02.markridgwell.com zones: their only use was the Traefik route to the old Dozzle log viewer on the caches, now removed. sync-zones only reports removed zones, so delete them from each DNS server by hand (or ask familiar)
- Removed `homepage.lan` (`192.168.150.150`) and its PTR, and the `home.markridgwell.com` zone: the homepage VM (105) is retired and the hostname is no longer routed by the proxies. The zone has to be deleted from each DNS server by hand (sync-zones only reports removed zones).
- Removed the obsolete AdGuard Home `certs/` folder (`adguard.local.crt`, `.key` and `.pem`), which nothing referenced (#46)
### Deployment Changes

<!--
Releases that have at least been deployed to staging, BUT NOT necessarily released to live.  Changes should be moved from [Unreleased] into here as they are merged into the appropriate release branch
-->

## [0.0.0] - Project created