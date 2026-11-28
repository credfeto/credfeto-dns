"""Tests for scripts/zone_files.py, the shared zone file parser."""

from unittest import TestCase, main

from script_loader import load_zone_files

zone_files = load_zone_files()


class ParseZoneTests(TestCase):
    """Zone file parsing."""

    def test_names_are_made_absolute(self):
        """Owners and name data resolve against the current origin."""
        zone = zone_files.parse_zone(
            "lan",
            "@ IN A 192.168.1.1\n"
            "host IN A 192.168.1.2\n"
            "Abs.Example. IN A 192.168.1.3\n"
            "$ORIGIN sub.lan.\n"
            "ptr IN PTR target\n"
            "alias IN CNAME host\n",
        )
        self.assertEqual("lan.", zone.name)
        self.assertEqual(
            [
                ("lan.", "A", "192.168.1.1"),
                ("host.lan.", "A", "192.168.1.2"),
                ("abs.example.", "A", "192.168.1.3"),
                ("ptr.sub.lan.", "PTR", "target.sub.lan."),
                ("alias.sub.lan.", "CNAME", "host.sub.lan."),
            ],
            [(rec.owner, rec.rtype, rec.data) for rec in zone.records],
        )

    def test_parenthesised_records_and_comments(self):
        """A multi-line SOA parses as one record and comments are ignored."""
        zone = zone_files.parse_zone(
            "lan",
            "@ IN SOA ns. admin. ( ; start\n"
            "    1 ; serial\n"
            "    300 )\n"
            "; host IN A 192.168.1.9\n"
            "host IN A 192.168.1.2 ; trailing\n",
        )
        self.assertEqual(
            [("lan.", "SOA", 1), ("host.lan.", "A", 5)],
            [(rec.owner, rec.rtype, rec.line) for rec in zone.records],
        )


if __name__ == "__main__":
    main()
