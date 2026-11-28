"""Tests for scripts/check-zone-sync."""

from io import StringIO
from ipaddress import ip_address
from pathlib import Path
from unittest import TestCase, main

from script_loader import load_script, load_zone_files

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
REVERSE_ZONE = "1.168.192.in-addr.arpa."
IPV6_REVERSE_ZONE = "1.0.0.0.5.d.1.6.0.1.0.8.2.0.a.2.ip6.arpa."

check_zone_sync = load_script("check-zone-sync")
zone_files = load_zone_files()


def check(case):
    """Run the check over one fixture directory."""
    zones = zone_files.load_zones(FIXTURES / case)
    return check_zone_sync.check_zones(zones)


class CheckZonesTests(TestCase):
    """Forward and reverse zone comparison over the fixture zones."""

    def test_clean_zones_have_no_errors(self):
        """Matching forward/reverse records and a public address pass."""
        self.assertEqual([], check("clean"))

    def test_missing_ptr_is_reported(self):
        """An internal address in a reverse zone with no PTR is an error."""
        ptr = f"11.{REVERSE_ZONE}"
        expected = f"no PTR for 192.168.1.11 (other.lan.): expected {ptr}"
        self.assertEqual([expected], check("missing_ptr"))

    def test_missing_reverse_zone_is_reported(self):
        """An internal address with no reverse zone covering it is an error."""
        expected = "no reverse zone for 10.0.0.5 (nas.lan.)"
        self.assertEqual([expected], check("missing_reverse_zone"))

    def test_orphan_ptr_is_reported(self):
        """A PTR whose address has no A/AAAA record is an error."""
        expected = (
            f"orphan PTR 99.{REVERSE_ZONE} -> ghost.lan. "
            f"in {REVERSE_ZONE}: no A/AAAA record has this address"
        )
        self.assertEqual([expected], check("orphan_ptr"))

    def test_ptr_target_for_a_different_address_is_reported(self):
        """A PTR naming a host that does not own that address is an error."""
        expected = (
            f"PTR 10.{REVERSE_ZONE} -> other.lan. in {REVERSE_ZONE}: "
            "target has no A/AAAA record for 192.168.1.10 "
            "(expected one of host.lan.)"
        )
        self.assertEqual([expected], check("wrong_target"))

    def test_ipv6_uses_reversed_nibbles(self):
        """IPv6 PTR owners match only when the nibbles are fully reversed."""
        missing_ptr = (
            "no PTR for 2a02:8010:61d5:1::abc (other.lan.): expected "
            f"c.b.a.0.0.0.0.0.0.0.0.0.0.0.0.0.{IPV6_REVERSE_ZONE}"
        )
        orphan_ptr = (
            "orphan PTR "
            f"a.b.c.0.0.0.0.0.0.0.0.0.0.0.0.0.{IPV6_REVERSE_ZONE} "
            f"-> other.lan. in {IPV6_REVERSE_ZONE}: "
            "no A/AAAA record has this address"
        )
        self.assertEqual([missing_ptr, orphan_ptr], check("ipv6"))

    def test_relative_and_absolute_names_resolve(self):
        """Relative, absolute, @, inherited and $ORIGIN names all match."""
        self.assertEqual([], check("relative_absolute"))

    def test_one_ptr_covers_multiple_forward_names(self):
        """Any of several forward names for an address is a valid target."""
        self.assertEqual([], check("multiple_forward_names"))

    def test_ipv6_reverse_name(self):
        """IPv6 addresses reverse to 32 nibbles under ip6.arpa."""
        address = ip_address("2a02:8010:61d5:1::10")
        self.assertEqual(
            f"0.1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.{IPV6_REVERSE_ZONE}",
            check_zone_sync.reverse_name(address),
        )


class MainTests(TestCase):
    """Command line behaviour."""

    def run_main(self, *argv):
        """Run main and capture its exit code and output streams."""
        stdout = StringIO()
        stderr = StringIO()
        code = check_zone_sync.main(list(argv), (stdout, stderr))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_in_sync_exits_zero(self):
        """A clean zone directory exits 0 and reports success."""
        zones = str(FIXTURES / "clean")
        code, stdout, stderr = self.run_main("--zones", zones)
        self.assertEqual(0, code)
        self.assertIn("in sync", stdout)
        self.assertEqual("", stderr)

    def test_mismatch_exits_non_zero_and_lists_each_error(self):
        """Each mismatch is printed on its own line and the exit code is 1."""
        zones = str(FIXTURES / "ipv6")
        code, stdout, stderr = self.run_main("--zones", zones)
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertEqual(2, len(stderr.splitlines()))

    def test_missing_directory_exits_non_zero(self):
        """A zones path that is not a directory is an error."""
        zones = str(FIXTURES / "does-not-exist")
        code, _, stderr = self.run_main("--zones", zones)
        self.assertEqual(1, code)
        self.assertIn("no such directory", stderr)


if __name__ == "__main__":
    main()
