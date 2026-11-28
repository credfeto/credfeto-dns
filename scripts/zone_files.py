"""Shared zone file parsing and command line plumbing for the zone checks."""

from dataclasses import dataclass
from pathlib import Path
from sys import stderr as STDERR
from sys import stdout as STDOUT

CLASSES = frozenset({"IN", "CH", "HS"})
# Record types whose first data field is a domain name.
NAME_DATA_TYPES = frozenset({"CNAME", "DNAME", "NS", "PTR"})


@dataclass(frozen=True)
class Record:
    """One resource record with its owner and any name data made absolute."""

    owner: str
    rtype: str
    data: str
    line: int = 0


@dataclass(frozen=True)
class Zone:
    """The records parsed from one zone file."""

    name: str
    records: tuple
    path: str = ""


def absolute_name(name, origin):
    """Resolve a zone file name against the current origin."""
    if name == "@":
        return origin
    if name.endswith("."):
        return name.lower()
    return f"{name}.{origin}".lower()


def logical_lines(text):
    """Yield (line number, starts_with_owner, tokens) for each entry.

    Lines inside parentheses are joined into a single entry, numbered by
    the line it starts on.
    """
    pending = []
    owner_present = True
    start = 0
    depth = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(";", 1)[0]
        if not pending:
            owner_present = bool(line) and not line[0].isspace()
            start = number
        depth += line.count("(") - line.count(")")
        pending.extend(line.replace("(", " ").replace(")", " ").split())
        if depth <= 0 and pending:
            yield start, owner_present, pending
            pending = []
            depth = 0


def is_ttl_or_class(field):
    """Whether a field is a TTL or a class."""
    return field.isdigit() or field.upper() in CLASSES


def strip_ttl_and_class(fields):
    """Drop the optional TTL and class, which may appear in either order."""
    remaining = list(fields)
    while remaining and is_ttl_or_class(remaining[0]):
        remaining.pop(0)
    return remaining


def parse_zone(name, text, path=""):
    """Parse the zone file text for the zone called name."""
    zone_name = f"{name.rstrip('.')}.".lower()
    origin = zone_name
    owner = origin
    records = []
    for number, owner_present, tokens in logical_lines(text):
        if tokens[0].upper() == "$ORIGIN":
            origin = absolute_name(tokens[1], origin)
            continue
        if tokens[0].startswith("$"):
            continue
        if owner_present:
            owner = absolute_name(tokens[0], origin)
            tokens = tokens[1:]
        fields = strip_ttl_and_class(tokens)
        if len(fields) < 2:
            continue
        rtype = fields[0].upper()
        data = fields[1]
        if rtype in NAME_DATA_TYPES:
            data = absolute_name(data, origin)
        records.append(Record(owner, rtype, data, number))
    return Zone(zone_name, tuple(records), path)


def display_path(path):
    """A path relative to the working directory when it is below it."""
    try:
        return str(path.resolve().relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def load_zones(zones_dir):
    """Parse every *.db file in zones_dir.

    The zone name is the file name minus .db.
    """
    return [
        parse_zone(
            path.name[: -len(".db")],
            path.read_text(encoding="utf-8"),
            display_path(path),
        )
        for path in sorted(Path(zones_dir).glob("*.db"))
    ]


def is_reverse_zone(zone):
    """Whether the zone is an in-addr.arpa or ip6.arpa reverse zone."""
    return zone.name.endswith(".arpa.")


def default_zones_dir():
    """The zones directory next to the scripts directory."""
    return Path(__file__).resolve().parent.parent / "zones"


def colour(code, text, stream):
    """Wrap text in an ANSI colour when writing to a terminal."""
    return f"\033[{code}m{text}\033[0m" if stream.isatty() else text


def fail(name, message, stream):
    """Print a red failure line for the check called name."""
    print(colour("31", f"✗ {name}: {message}", stream), file=stream)


def run_check(parser, check_zones, success, argv=None, streams=None):
    """Parse --zones, run check_zones over them and report.

    streams is (stdout, stderr), defaulting to the process's own. Returns
    the process exit code: 0 with the success message, or 1 with one line
    per error.
    """
    out, err = streams or (STDOUT, STDERR)
    parser.add_argument(
        "--zones",
        type=Path,
        default=default_zones_dir(),
        help="zone directory",
    )
    args = parser.parse_args(argv)
    if not args.zones.is_dir():
        fail(parser.prog, f"no such directory: {args.zones}", err)
        return 1
    errors = check_zones(load_zones(args.zones))
    for error in errors:
        fail(parser.prog, error, err)
    if errors:
        return 1
    print(colour("32", f"✓ {parser.prog}: {success}", out), file=out)
    return 0
