"""Tests for scripts/check-zone-names."""

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from script_loader import load_script, load_zone_files

SOA = (
    "$TTL 3600\n"
    "@ IN SOA dns-server. admin. (\n"
    "    1       ; serial\n"
    "    900     ; refresh\n"
    "    300     ; retry\n"
    "    604800  ; expire\n"
    "    300     ; minimum TTL\n"
    ")\n"
    "@ IN NS dns-server.\n"
)
# The first record after the header is on this line.
FIRST_LINE = SOA.count("\n") + 2
DNS_LAN = "dns-06 IN A 192.168.42.106\ndns-06 IN AAAA 2a02:8010:61d5:42::106\n"


check_zone_names = load_script("check-zone-names")
zone_files = load_zone_files()


def zone(name, body):
    """Parse a zone made of the standard header plus body."""
    text = f"$ORIGIN {name}.\n{SOA}{body}"
    return zone_files.parse_zone(name, text, f"zones/{name}.db")


def check(**zones):
    """Run the check over zones given as name=body (dots as __)."""
    parsed = [
        zone(name.replace("__", "."), body) for name, body in zones.items()
    ]
    return check_zone_names.check_zones(parsed)


class MultiLabelTests(TestCase):
    """Rule 1: names more than one label deep belong in their own zone."""

    def test_multi_label_owner_is_reported(self):
        """nas-01.storage in lan. names the file, line and fix."""
        errors = check(lan="nas-01.storage IN A 192.168.220.17\n")
        expected = (
            f"zones/lan.db:{FIRST_LINE}: nas-01.storage.lan. is a "
            "multi-label name in the lan. zone; move it to the storage.lan. "
            "zone (zones/storage.lan.db) as nas-01"
        )
        self.assertEqual([expected], errors)

    def test_reported_once_per_name(self):
        """A name with A and AAAA records is one error, on its first line."""
        errors = check(
            lan="x.orchestrator IN A 192.168.170.23\n"
            "x.orchestrator IN AAAA 2a02:8010:61d5:170::17\n"
        )
        self.assertEqual(1, len(errors))
        self.assertIn(f"zones/lan.db:{FIRST_LINE}:", errors[0])

    def test_reported_when_the_sub_zone_exists(self):
        """A name under an existing sub-zone is still in the wrong file."""
        errors = check(
            lan="nas-01.storage IN A 192.168.220.17\n",
            storage__lan="nas-01 IN A 192.168.220.17\n",
        )
        self.assertEqual(1, len(errors))
        self.assertIn("nas-01.storage.lan.", errors[0])

    def test_absolute_and_origin_names_are_resolved(self):
        """An absolute name or a $ORIGIN change is seen as multi-label."""
        errors = check(
            lan="a.b.lan. IN A 192.168.1.1\n"
            "$ORIGIN sub.lan.\n"
            "host IN A 192.168.1.2\n"
        )
        self.assertEqual(2, len(errors))
        self.assertIn("as a", errors[0])
        self.assertIn("move it to the sub.lan. zone", errors[1])

    def test_deeper_names_point_at_the_nearest_zone(self):
        """a.b.c in lan. belongs in b.c.lan. as a."""
        errors = check(lan="a.b.c IN A 192.168.1.1\n")
        self.assertIn("the b.c.lan. zone (zones/b.c.lan.db) as a", errors[0])

    def test_outside_the_zone_is_reported(self):
        """An absolute owner outside the zone is in the wrong file."""
        errors = check(lan="host.example. IN A 192.168.1.1\n")
        self.assertEqual(1, len(errors))
        self.assertIn("host.example. is outside the lan. zone", errors[0])

    def test_single_labels_apex_and_service_labels_pass(self):
        """Hosts, @, continuation lines and _service labels are allowed."""
        errors = check(
            lan='@ IN TXT "v=spf1 -all"\n'
            "host IN A 192.168.1.1\n"
            "     IN AAAA 2a02:8010:61d5:1::1\n"
            "* IN A 192.168.1.2\n"
            "_sip._tcp IN SRV 0 0 5060 host\n"
            "_acme-challenge.host IN TXT token\n"
        )
        self.assertEqual([], errors)

    def test_reverse_zones_are_exempt(self):
        """Reverse zones' PTR owners are legitimately several labels deep."""
        errors = check(
            **{
                "2.4.0.0.5.d.1.6.0.1.0.8.2.0.a.2.ip6.arpa": (
                    "1.0.1.0.0.0.0.0.0.0.0.0.0.0.0.0 IN PTR dns-01.dns.lan.\n"
                )
            }
        )
        self.assertEqual([], errors)


class FlatAliasTests(TestCase):
    """Rule 2: a flat name for a sub-zone host is only a CNAME to it."""

    def test_flat_address_records_are_reported(self):
        """dns-06 A/AAAA in lan. is one error naming the CNAME fix."""
        errors = check(lan=DNS_LAN, dns__lan=DNS_LAN)
        expected = (
            f"zones/lan.db:{FIRST_LINE}: dns-06.lan. has A, AAAA but "
            "dns-06.dns.lan. is a host in zones/dns.lan.db; replace every "
            "dns-06.lan. record with exactly "
            "'dns-06 IN CNAME dns-06.dns.lan.'"
        )
        self.assertEqual([expected], errors)

    def test_cname_to_the_full_name_passes(self):
        """The exact CNAME form, relative or absolute target, is accepted."""
        self.assertEqual(
            [],
            check(lan="dns-06 IN CNAME dns-06.dns.lan.\n", dns__lan=DNS_LAN),
        )
        self.assertEqual(
            [],
            check(lan="dns-06 IN CNAME dns-06.dns\n", dns__lan=DNS_LAN),
        )

    def test_cname_to_another_target_is_reported(self):
        """A CNAME to any other name is an error."""
        errors = check(
            lan="dns-06 IN CNAME dns-05.dns.lan.\n", dns__lan=DNS_LAN
        )
        self.assertEqual(1, len(errors))
        self.assertIn("dns-06.lan. has CNAME", errors[0])

    def test_cname_with_other_records_is_reported(self):
        """A CNAME alongside an address or TXT record is an error."""
        errors = check(
            lan="dns-06 IN CNAME dns-06.dns.lan.\n" "dns-06 IN TXT note\n",
            dns__lan=DNS_LAN,
        )
        self.assertEqual(1, len(errors))
        self.assertIn("dns-06.lan. has CNAME, TXT", errors[0])

    def test_names_only_in_one_zone_pass(self):
        """Hosts only in the parent or only in the sub-zone are fine."""
        errors = check(lan="firewall IN A 192.168.10.1\n", dns__lan=DNS_LAN)
        self.assertEqual([], errors)

    def test_nearest_parent_is_used(self):
        """A sub-sub-zone host is checked against its nearest parent."""
        errors = check(
            lan="dns-06 IN A 192.168.42.106\n",
            dns__lan="dns-06 IN A 192.168.42.106\n",
            a__dns__lan="dns-06 IN A 192.168.42.106\n",
        )
        self.assertEqual(2, len(errors))
        self.assertIn("zones/lan.db", errors[0])
        self.assertIn("zones/dns.lan.db", errors[1])
        self.assertIn("dns-06.a.dns.lan.", errors[1])

    def test_sub_zone_without_parent_is_ignored(self):
        """A service zone with no loaded parent zone has nothing to check."""
        errors = check(proxy__markridgwell__com="01 IN A 192.168.140.250\n")
        self.assertEqual([], errors)


class MainTests(TestCase):
    """Command line behaviour."""

    def run_main(self, files):
        """Write files to a zone directory and run main over it."""
        with TemporaryDirectory() as directory:
            for name, body in files.items():
                text = f"$ORIGIN {name}.\n{SOA}{body}"
                Path(directory, f"{name}.db").write_text(text, "utf-8")
            stdout = StringIO()
            stderr = StringIO()
            code = check_zone_names.main(
                ["--zones", directory], (stdout, stderr)
            )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_clean_zones_exit_zero(self):
        """A compliant zone directory exits 0 and reports success."""
        code, stdout, stderr = self.run_main(
            {"lan": "dns-06 IN CNAME dns-06.dns.lan.\n", "dns.lan": DNS_LAN}
        )
        self.assertEqual(0, code)
        self.assertIn("every name is in its own zone", stdout)
        self.assertEqual("", stderr)

    def test_errors_exit_non_zero_one_line_each(self):
        """Each error is printed on its own line and the exit code is 1."""
        code, stdout, stderr = self.run_main(
            {
                "lan": "nas-01.storage IN A 192.168.220.17\n" + DNS_LAN,
                "dns.lan": DNS_LAN,
            }
        )
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertEqual(2, len(stderr.splitlines()))
        self.assertIn("lan.db:", stderr)

    def test_missing_directory_exits_non_zero(self):
        """A zones path that is not a directory is an error."""
        stderr = StringIO()
        code = check_zone_names.main(
            ["--zones", "/does-not-exist"], (StringIO(), stderr)
        )
        self.assertEqual(1, code)
        self.assertIn("no such directory", stderr.getvalue())


if __name__ == "__main__":
    main()
