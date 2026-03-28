"""
Developer entry point.  Runs lute on a dev server.

This script _always_ uses the config at /lute/config/config.yml.

You can run with:

inv start
python -m devstart

If you want to run this with "python", then for some _extremely odd_
reason, you must run this with the full path to the file.
Ref https://stackoverflow.com/questions/37650208/flask-cant-find-app-file

e.g.:

python /Users/jeff/Documents/Projects/lute_v3/devstart.py
python `pwd`/devstart.py
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

load_dotenv()
from lute import __version__
from lute.app_factory import create_app, data_initialization
from lute.config.app_config import AppConfig
from lute.db import db

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


def _check_language_defs():
    """
    Check if language_defs submodule is initialized.
    Exits with helpful message if not.
    """
    thisdir = os.path.dirname(os.path.realpath(__file__))
    langdefs_dir = os.path.join(thisdir, "lute", "db", "language_defs")
    
    # Check if directory exists and has any definition.yaml files
    if not os.path.exists(langdefs_dir):
        print("\n" + "=" * 70)
        print("ERROR: language_defs directory is missing!")
        print("=" * 70)
        print("\nThe language_defs submodule has not been initialized.")
        print("\nPlease run:")
        print("  git submodule update --init --recursive")
        print("\nOr use the setup task:")
        print("  invoke setup")
        print("=" * 70 + "\n")
        sys.exit(1)
    
    # Check if directory is empty (submodule not initialized)
    has_defs = any(
        os.path.exists(os.path.join(langdefs_dir, d, "definition.yaml"))
        for d in os.listdir(langdefs_dir)
        if os.path.isdir(os.path.join(langdefs_dir, d)) and not d.startswith(".")
    )
    
    if not has_defs:
        print("\n" + "=" * 70)
        print("ERROR: language_defs directory is empty!")
        print("=" * 70)
        print("\nThe language_defs submodule has not been initialized.")
        print("\nPlease run:")
        print("  git submodule update --init --recursive")
        print("\nOr use the setup task:")
        print("  invoke setup")
        print("=" * 70 + "\n")
        sys.exit(1)


def start(port):
    """
    Start the dev server with reloads on port.
    """
    # Check submodules early to provide helpful error message
    _check_language_defs()

    def dev_print(s):
        "Print info on first load only."
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            # https://stackoverflow.com/questions/25504149/
            #  why-does-running-the-flask-dev-server-run-itself-twice
            # Reloading, do nothing.
            return
        print(s, flush=True)

    config_file = AppConfig.default_config_filename()
    dev_print("")
    app = create_app(config_file, output_func=dev_print)
    with app.app_context():
        data_initialization(db.session, dev_print)

    ac = AppConfig(config_file)
    dev_print(f"\nversion {__version__}")
    dev_print(f"db name: {ac.dbname}")
    dev_print(f"data: {ac.datapath}")
    dev_print(f"Running at: http://localhost:{port}\n")

    app.run(debug=True, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start dev server lute.")
    parser.add_argument(
        "--port", type=int, default=5001, help="Port number (default: 5001)"
    )
    args = parser.parse_args()
    start(args.port)
