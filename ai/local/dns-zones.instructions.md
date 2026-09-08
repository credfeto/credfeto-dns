# DNS zone maintenance

[Back to Local AI Memory Index](index.md)

## Reverse zone naming

* Only create reverse zones for private subnets that actually have A/AAAA records in the forward zones — not the full RFC1918/ULA space.
* IPv4: one zone per `/24` actually in use, named `<3rd-octet>.<2nd-octet>.<1st-octet>.in-addr.arpa`, file `zones/<that-name>.db`.
  e.g. `192.168.42.0/24` -> `zones/42.168.192.in-addr.arpa.db`.
* IPv6: one zone per `/64` actually in use, named by reversing the nibbles of the first 64 bits + `.ip6.arpa`, file `zones/<that-name>.db`.
  e.g. `2a02:8010:61d5:42::/64` -> `zones/2.4.0.0.5.d.1.6.0.1.0.8.2.0.a.2.ip6.arpa.db`.
* PTR record names are the remaining octets/nibbles (reversed, dot-separated for IPv6).
* Every zone file name (forward or reverse) is also its zone name — `sync-zones` derives the zone to import via `basename .db`, so a new reverse zone slots into that existing mechanism with no script changes.

## Choosing the PTR target name

A single IP must resolve to exactly one PTR name, even when several forward zones define an A/AAAA record for it:

* If a host's IP appears in both a flat zone (`lan.`) and a more specific child zone (`dns.lan.`, `network.lan.`), the PTR uses the **more specific zone's name** (e.g. `dns-01.dns.lan.`, not `dns-01.lan.`).
* If an IP's owning node has its own dedicated zone with per-node sub-records (e.g. `zones/proxy.markridgwell.com.db`'s `01`/`02` records for the two reverse-proxy nodes), the PTR uses `<sub-label>.<owning-zone>.` from that dedicated zone (e.g. `01.proxy.markridgwell.com.`) — never the flat `lan.` name, and never one of the many other zones that merely copy the same address (e.g. the public-facing `*.markridgwell.com` service zones that all resolve to the proxy pair).
* If a new ambiguous case comes up that isn't covered by the rules above, ask before picking a name rather than guessing.

## Keeping reverse zones in sync (MANDATORY)

* Whenever an A or AAAA record is added, changed, or removed in any forward zone file, update the matching reverse zone's PTR record in the same commit, applying the "Choosing the PTR target name" rule above.
* If the address falls in a subnet that has no reverse zone yet, create one following the "Reverse zone naming" convention above as part of that same commit.
* If removing a forward record leaves a reverse zone with no PTR records other than the SOA/NS, leave the (now-empty) reverse zone file in place rather than deleting it, unless asked to remove it.
