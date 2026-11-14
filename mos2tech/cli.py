# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .core import CATEGORIES, ONET_URL, SERVICES, lookup, rank, source_levels, title

NAMES = {name.lower().replace(" ", ""): svc for svc, name in SERVICES.items()} | {"marines": "M", "usmc": "M"}


def service(value: str) -> str:
    svc = NAMES.get(value.lower().replace(" ", ""), value.upper())
    if svc not in SERVICES:
        raise argparse.ArgumentTypeError(f"unknown service {value!r}; use one of {', '.join(SERVICES.values())}")
    return svc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mos2tech", description="Military occupation code -> civilian tech roles and skill gaps")
    ap.add_argument("code", help="MOS, AFSC, rating or NEC, e.g. 0631, 25B, 3D0X2")
    ap.add_argument("-s", "--service", type=service, help="army, navy, air force, marine corps, coast guard, space force")
    ap.add_argument("-n", "--top", type=int, default=5, help="number of roles to show (default 5)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    hits = lookup(args.code, args.service)
    if not hits:
        print(f"No crosswalk entry for {args.code!r}. Check the code, or try --service.", file=sys.stderr)
        return 1
    if len({m.svc for m in hits}) > 1:
        print(f"{args.code} exists in more than one service. Re-run with --service:", file=sys.stderr)
        for m in hits:
            print(f"  --service {SERVICES[m.svc].lower().replace(' ', '')!s:<12} {m.title}", file=sys.stderr)
        return 2
    moc = hits[0]
    levels = source_levels(moc.onet)
    matches = rank(levels, args.top) if levels else []

    if args.json:
        print(json.dumps({"moc": asdict(moc), "matches": [asdict(m) for m in matches]}, indent=2))
        return 0

    status = "" if moc.active else ", retired code"
    print(f"{moc.code}  {moc.title}  ({SERVICES[moc.svc]}, {CATEGORIES.get(moc.mpc, 'civilian')}{status})\n")
    print("Civilian equivalents (O*NET military crosswalk):")
    for c in moc.onet:
        print(f"  {c}  {title(c)}\n      {ONET_URL}{c}")
    if not levels:
        print(
            "\nO*NET has no skill ratings for these occupations (military-only and 'All Other'\n"
            "categories aren't surveyed), so a gap can't be calculated from public data."
        )
        return 0
    print("\nClosest tech roles (fit = share of the role's important skill and knowledge levels you already meet):")
    for i, m in enumerate(matches, 1):
        print(f"\n{i}. {m.title}  ({m.onet})  fit {m.fit:.0%}")
        for g in m.gaps:
            print(f"     gap: {g.element}: level {g.have} -> {g.need}")
        if m.certs:
            print(f"     common certs: {', '.join(m.certs)}")
        print(f"     {ONET_URL}{m.onet}")
    print("\nLevels are O*NET 0-7 ratings for the civilian equivalents, not an assessment of you.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
