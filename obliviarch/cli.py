"""OBLIVIARCH CLI — Command-line interface for controlled oblivion."""
from __future__ import annotations

import argparse
import json
import sys
import time

from .engine import Obliviarch, ObliviarchConfig


def cmd_start(args):
    """Start the Obliviarch daemon."""
    config = ObliviarchConfig(data_dir=args.data_dir)
    engine = Obliviarch(config=config)
    engine.start()
    print(f"Obliviarch started — data_dir: {args.data_dir}")

    try:
        while True:
            time.sleep(args.interval * 60)
            result = engine.consolidate()
            print(f"[{time.strftime('%H:%M:%S')}] Lethe cycle: "
                  f"+{result['new_schemas']} schemas, "
                  f"+{result['new_archetypes']} archetypes, "
                  f"{result['traces_archived']} archived")
    except KeyboardInterrupt:
        print("\nThe river slows...")
        engine.stop()


def cmd_consolidate(args):
    """Run a single consolidation cycle."""
    engine = Obliviarch(data_dir=args.data_dir)
    engine.start()
    result = engine.consolidate()
    engine.stop()
    print(json.dumps(result, indent=2))


def cmd_stats(args):
    """Show compression statistics."""
    engine = Obliviarch(data_dir=args.data_dir)
    engine.start()
    stats = engine.stats()
    engine.stop()
    print(json.dumps(stats, indent=2))


def cmd_query(args):
    """Query across all memory tiers."""
    engine = Obliviarch(data_dir=args.data_dir)
    engine.start()
    result = engine.query(args.pattern, limit=args.limit)
    engine.stop()
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="obliviarch",
        description="OBLIVIARCH — The Architecture of Controlled Oblivion",
    )
    parser.add_argument("--data-dir", default="data/", help="Data directory")

    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="Start consolidation daemon")
    p_start.add_argument("--interval", type=float, default=30, help="Minutes between cycles")

    sub.add_parser("consolidate", help="Run one Lethe cycle")
    sub.add_parser("stats", help="Show compression stats")

    p_query = sub.add_parser("query", help="Query memory tiers")
    p_query.add_argument("pattern", help="Pattern to search for")
    p_query.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "consolidate":
        cmd_consolidate(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "query":
        cmd_query(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()