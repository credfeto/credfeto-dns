# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
Please ADD ALL Changes to the UNRELEASED SECTION and not a specific release
-->

## [Unreleased]
### Security
- Untrusted VLANs are refused the internal and reverse zones, except the TRMNL and HA names
- Egress firewall moved from firewalld policy and ipsets to an atomically replaced nftables table
- The proxies' Servers VLAN addresses are no longer trusted for egress, port 538 or the proxy ACL
- The proxies' DMZ VLAN addresses are trusted for egress, port 538 and the reverse proxy ACL
### Added
- DNS query logs go to VictoriaLogs via the Technitium Log Exporter app over syslog on 514/udp
- Egress allow-list: VictoriaLogs on monitoring.lan (9428/tcp) for systemd-journal-upload
- DNS-over-TCP-PROXY on port 538 for DNS-over-TLS via the proxies, open to the proxies only
- Added `michelec320.lan` (`192.168.66.11`, C320 printer) to `zones/lan.db` with its PTR
- Added `work.lan` (`192.168.90.120`, the work machine) to `zones/lan.db` with its PTR
- Daily workflow regenerates `scripts/github-egress-ranges` from the GitHub meta API
- `credfeto.orchestrator.lan` and `funfair-tech.orchestrator.lan` with IPv4 and IPv6 PTRs
- `scripts/sync-zones` runs `./update` when pulled commits change host config not yet applied
- Egress allow-list: openpgpkey.archlinux.org (HTTPS, WKD) so the weekly keyring sync works
- Egress allow-list: pkgstats.archlinux.de (HTTPS) so the weekly pkgstats submission works
- Added .ai-instructions and ai/local/index.md from cs-template standard
- Added `dev-upgrader-01.lan` (`192.168.150.20`) to `zones/lan.db`.
- Added `dev-upgrader-02.lan` (`192.168.150.21`) to `zones/lan.db`.
- Added `linux-cache-01.lan`, `linux-cache-02.lan`, `defi.lan` and `arch-vm-test.lan` to lan.db
- DNS record for keys.markridgwell.com pointing to proxy on 192.168.150.250
- DNS record for grafana.markridgwell.com pointing to both proxies (IPv4 and IPv6)
- DNS record for cctv.markridgwell.com pointing to proxy on 192.168.150.250
- Support IPv6 (private ranges and 2a02:8010:61d5::/64) in firewall rules
- Added `homepage.lan` (`192.168.150.150`) to `zones/lan.db`.
- Added `gickup.lan` (`192.168.150.13`) to `zones/lan.db`.
- Added `dns-06.lan` / `dns-06.dns.lan` (`192.168.42.106`, `::106`) to the lan and dns.lan zones
- Added `audio-bookshelf.lan` (`192.168.150.16`) to `zones/lan.db`.
- Added `dev-cache-01.lan` (`192.168.150.100`) and `dev-cache-02.lan` (`.101`) to `zones/lan.db`
- Added `development.lan` (`192.168.150.176`) to `zones/lan.db`.
- Added `immich.lan` (`192.168.150.154`) to `zones/lan.db`.
- Added `proxmox-05.lan` (`192.168.86.15`) and `proxmox-06.lan` (`192.168.86.16`) to `zones/lan.db`.
- Added `firewall.lan` (`192.168.10.1`) to `zones/lan.db`.
- New `network.lan` zone with `stairs-01` and `bedroom`, plus flat aliases in `zones/lan.db`
- Added IPv6 AAAA records for the public DNS resolvers (Cloudflare, Google and Quad9)
- Added resolver zones for Cloudflare Family, AdGuard DNS and OpenDNS, with A and AAAA records
- Added dns-06.markridgwell.com zone (192.168.150.250).
- Added fcf757.dns.nextdns.io zone (NextDNS) with A and AAAA records.
- Added be6f94.dns.nextdns.io zone (NextDNS) with A and AAAA records.
- Added AAAA records (2a02:8010:61d5:150::250) for proxy.lan and all 36 services it fronts
- Added `stairs-02.lan` (`192.168.10.3`) and `office.lan` (`192.168.10.4`) to the lan zones
- DNS record for monitoring.markridgwell.com pointing to proxy on 192.168.150.250
- Added `ap-office.network.lan` (`192.168.10.7`), the Zyxel-Office mesh access point
- Added `ap-bedroom.network.lan` (`192.168.10.8`), the Zyxel-Bedroom mesh access point
- Added `ap-stairs.network.lan` (`192.168.10.6`), the Zyxel-Stairs mesh access point
- Added `ap-garden.network.lan` (`192.168.10.9`), the Zyxel-Garden mesh access point
- Added `ap-office.lan` (`192.168.10.7`) to `zones/lan.db` - Zyxel-Office wireless mesh access point.
- Added `ap-bedroom.lan` (`192.168.10.8`) to `zones/lan.db`, the Zyxel-Bedroom access point
- Added `ap-stairs.lan` (`192.168.10.6`) to `zones/lan.db` - Zyxel-Stairs wireless mesh access point.
- Added `ap-garden.lan` (`192.168.10.9`) to `zones/lan.db` - Zyxel-Garden wireless mesh access point.
- Added `netgear-proxmox-cluster` (`192.168.10.10`), the Proxmox cluster's main switch
- DNS server egress lockdown (firewalld dns-egress policy, inert unless DNS_EGRESS_ENFORCE)
- Added second proxy node proxy-02.lan (192.168.150.251); renamed proxy.lan to proxy-01.lan
- Added 01. and 02.proxy.markridgwell.com records for pinning to a specific proxy node
- Added reverse DNS (PTR) zones for the internal subnets, populated from the forward zones
- Added scripts to replace proxy IPs across zone files and check proxy IP consistency (#41)
- Added `scripts/check-zone-sync`, its CI workflow and unit tests to keep PTRs in sync (#43)
- Added `workflow-mcp.markridgwell.com` zone resolving to the reverse-proxy pair (#46)
- Added `memory.lan` (`192.168.150.30`) to `zones/lan.db` with a matching PTR record (#49)
- Added `memory.markridgwell.com` zone resolving to the reverse-proxy pair (#49)
- Added `wiki.markridgwell.com` zone resolving to the reverse-proxy pair (#49)
- DNS record for logs.markridgwell.com (VictoriaLogs and its MCP server) pointing to the proxies
- DNS zone for edge-familiar.markridgwell.com, Familiar's inbound webhook entry point on the proxies
### Fixed
- Query logs self-heal: sync-zones re-applies the Log Exporter config when VictoriaLogs is silent
- The zone query ACL no longer refuses the trusted Databases VLAN (192.168.130.0/24 and its /64)
- Egress runs are serialised with a lock, so concurrent timer and sync runs no longer crash
- Corrected `xerox-b210-wired.lan` to its Printers VLAN address `192.168.66.75` and moved its PTR
- Regenerated `scripts/github-egress-ranges`: four new GitHub ranges, fixing timed-out git pulls
- Dropped the `nanoclaw.lan` CNAME, which clashed with the old A record and failed the lan import
- Fixed typo in `zones/lan.db`: `docker-tegistry` renamed to `docker-registry` (`192.168.150.202`).
- Corrected `monitoring.lan` IP in `zones/lan.db` from `192.168.150.135` to `192.168.150.134`.
- Egress ipset refresh no longer flaps on NAT64 spelling, and aborted runs keep firewall state
- Added the missing PTR record for `familiar.lan` in `zones/150.168.192.in-addr.arpa.db`
- Added missing PTR records for `netgear-printer` and `netgear-office1` in the 10.168.192 zone (#46)
- Corrected the PTR for `192.168.10.1` to `opnsense.network.lan` instead of `firewall.lan` (#46)
- Added the missing reverse zone for `192.168.2.0/24` with PTRs for the four network devices (#46)
### Changed
- proxy-01 moved to the DMZ VLAN (`192.168.140.250`), in every proxy zone and its PTRs
- proxy-02 moved to the DMZ VLAN (`192.168.140.251`), with new DMZ reverse zones for its PTRs
- linux-cache-01/02.lan moved to LinuxCaches VLAN 21 (`192.168.210.200/201`), PTRs in a new zone
- dev-cache-01/02.lan moved to the Caches VLAN 20 (`192.168.200.100/101`), PTRs in a new zone
- familiar.lan moved to the Familiar VLAN 19 (`192.168.190.129`), PTR in a new reverse zone
- dev-upgrader-01.lan moved to Development VLAN 18 (`192.168.180.20`); 02 moves when next on
- development.lan moved to Development VLAN 18 (`192.168.180.176`), PTR in a new reverse zone
- The orchestrator hosts moved to Orchestrators VLAN 17 (`192.168.170.23/24`), PTRs in new zones
- monitoring.lan moved to Monitoring VLAN 16 (`192.168.160.134`), with its PTR and egress rules
- Moved `sql-server.lan` to Databases VLAN 13 (`192.168.130.254`), with its PTR and egress rule
- Removed the legacy repository `hosts` file workflow; the `zones/` files are the source of truth
- Widened the allowed IPv6 firewall network from 2a02:8010:61d5::/64 to the whole ::/48
- Technitium recursion ACL is now an explicit network list including 2a02:8010:61d5::/48
- Renumbered dns-01 to dns-04, added dns-05, and added AAAA records for all five DNS servers
- Removed stale hagezi block-list URLs from docker-compose (disabled in the live config)
- install now runs update at the end so a fresh ./install produces a fully running system
- Egress lockdown is now enforced by default - set DNS_EGRESS_ENFORCE=false for observation mode
- Simplified egress firewall internals: one log-only catch-all; the policy target alone enforces
- All 36 proxy-fronted services resolve to both proxy-01 and proxy-02 (DNS round-robin)
- Watchtower removes old images after updates and polls on an overridable cron schedule
### Deprecated
### Removed
- linux-cache-01/02.markridgwell.com zones, used only by the old Dozzle route; delete by hand
- Removed `homepage.lan`, its PTR and the `home.markridgwell.com` zone (delete it by hand)
- Removed the unreferenced AdGuard Home `certs/` folder (#46)
### Deployment Changes

<!--
Releases that have at least been deployed to staging, BUT NOT necessarily released to live.  Changes should be moved from [Unreleased] into here as they are merged into the appropriate release branch
-->

## [0.0.0] - Project created