import sys

# import pytest

from organizer.cli import main as cli_main


def test_cli_runs(monkeypatch):
    # Simulate command line args, e.g. "organizer organize test_dir"
    test_args = ["organizer", "organize", "test_dir"]
    monkeypatch.setattr(sys, "argv", test_args)

    # Call cli main() – it should not crash
    try:
        cli_main()
    except SystemExit as e:
        # argparse normally calls sys.exit → we accept exit code 0
        assert e.code == 0
