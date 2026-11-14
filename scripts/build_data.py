#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
"""Rebuild mos2tech/onet/ from the public O*NET downloads.

    python scripts/build_data.py <military_crosswalk.csv> <db_XX_X_text dir>

Inputs: the Military Crosswalk CSV and the O*NET text database, both from
https://www.onetcenter.org (see README for links and licenses).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "mos2tech" / "onet"
SERVICES = "ACFHMNP"  # the occupation codes themselves; skill identifiers and civilian series are left out
RATING_FILES = ("Essential Skills.txt", "Transferable Skills.txt", "Knowledge.txt")


def build_crosswalk(src: Path) -> int:
    rows = set()
    with src.open(encoding="latin-1", newline="") as f:
        for r in csv.DictReader(f):
            codes = [r[f"ONET{i}"] for i in "1234" if r[f"ONET{i}"]]
            if r["SVC"] in SERVICES and codes:
                rows.add((r["SVC"], r["MPC"], r["MOC"], r["MOC_TITLE"], r["STATUS"], ";".join(codes)))
    with (OUT / "crosswalk.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["svc", "mpc", "moc", "title", "status", "onet"])
        w.writerows(sorted(rows))
    return len(rows)


def build_profiles(db: Path) -> int:
    with (db / "Occupation Data.txt").open(encoding="utf-8") as f:
        titles = {r["O*NET-SOC Code"]: r["Title"] for r in csv.DictReader(f, delimiter="\t")}
    elements: list[str] = []
    ratings: dict[str, dict[str, dict[str, float]]] = {}
    for name in RATING_FILES:
        with (db / name).open(encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["Element Name"] not in elements:
                    elements.append(r["Element Name"])
                occ = ratings.setdefault(r["O*NET-SOC Code"], {"LV": {}, "IM": {}})
                occ[r["Scale ID"]][r["Element Name"]] = float(r["Data Value"])
    occupations = {
        code: {"lv": [v["LV"].get(e, 0.0) for e in elements], "im": [v["IM"].get(e, 1.0) for e in elements]}
        for code, v in sorted(ratings.items())
    }
    doc = {"elements": elements, "titles": titles, "occupations": occupations}
    (OUT / "profiles.json").write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    return len(occupations)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    OUT.mkdir(parents=True, exist_ok=True)
    print("crosswalk rows:", build_crosswalk(Path(sys.argv[1])))
    print("occupation profiles:", build_profiles(Path(sys.argv[2])))
