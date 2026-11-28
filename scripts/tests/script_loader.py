"""Import the extensionless scripts/ entry points as modules for testing."""

from importlib import import_module
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from sys import path as SYS_PATH

SCRIPTS_DIR = Path(__file__).resolve().parent.parent

# The scripts import zone_files from their own directory.
if str(SCRIPTS_DIR) not in SYS_PATH:
    SYS_PATH.insert(0, str(SCRIPTS_DIR))


def load_script(name):
    """Import scripts/<name> as a module called name with _ for -."""
    module_name = name.replace("-", "_")
    loader = SourceFileLoader(module_name, str(SCRIPTS_DIR / name))
    spec = spec_from_loader(module_name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_zone_files():
    """Import scripts/zone_files.py, the scripts' shared module."""
    return import_module("zone_files")
