# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
"""Match a military occupation code to civilian tech roles using O*NET ratings."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files

SERVICES = {
    "A": "Army",
    "C": "Coast Guard",
    "F": "Air Force",
    "H": "Space Force",
    "M": "Marine Corps",
    "N": "Navy",
}
CATEGORIES = {"E": "enlisted", "O": "officer", "W": "warrant officer"}
TECH_PREFIX = "15-12"  # O*NET computer occupations
IMPORTANT = 3.0  # O*NET importance scale is 1-5; 3 is "important"
ONET_URL = "https://www.onetonline.org/link/summary/"


@dataclass(frozen=True)
class Moc:
    svc: str
    mpc: str
    code: str
    title: str
    active: bool
    onet: tuple[str, ...]


@dataclass(frozen=True)
class Gap:
    element: str
    have: float
    need: float


@dataclass(frozen=True)
class Match:
    onet: str
    title: str
    fit: float  # 0-1, share of the role's important requirements already met
    gaps: tuple[Gap, ...]
    certs: tuple[str, ...]


@cache
def _data() -> tuple[list[Moc], dict, dict[str, list[str]]]:
    root = files("mos2tech") / "onet"
    with (root / "crosswalk.csv").open(encoding="utf-8", newline="") as f:
        mocs = [
            Moc(r["svc"], r["mpc"], r["moc"], r["title"], r["status"] == "A", tuple(r["onet"].split(";")))
            for r in csv.DictReader(f)
        ]
    profiles = json.loads((root / "profiles.json").read_text(encoding="utf-8"))
    certs = json.loads((files("mos2tech") / "certs.json").read_text(encoding="utf-8"))
    return mocs, profiles, certs


def title(onet: str) -> str:
    return _data()[1]["titles"].get(onet, onet)


def lookup(code: str, svc: str | None = None) -> list[Moc]:
    """All crosswalk entries for a code, active ones first."""
    hits = [m for m in _data()[0] if m.code.upper() == code.upper() and svc in (None, m.svc)]
    return sorted(hits, key=lambda m: (not m.active, m.svc))


def source_levels(onet_codes: tuple[str, ...]) -> list[float] | None:
    """Mean skill and knowledge levels across the civilian equivalents O*NET has rated."""
    occupations = _data()[1]["occupations"]
    rated = [occupations[c]["lv"] for c in onet_codes if c in occupations]
    return [sum(col) / len(col) for col in zip(*rated)] if rated else None


def rank(levels: list[float], top: int = 5, gaps: int = 4) -> list[Match]:
    """Tech roles ordered by how much of their important requirements `levels` already meets."""
    _, profiles, certs = _data()
    elements = profiles["elements"]
    out = []
    for code, p in profiles["occupations"].items():
        if not code.startswith(TECH_PREFIX):
            continue
        need = short = 0.0
        found = []
        for name, have, lv, im in zip(elements, levels, p["lv"], p["im"]):
            if im < IMPORTANT:
                continue
            need += im * lv
            miss = max(0.0, lv - have)
            short += im * miss
            if miss > 0:
                found.append((im * miss, Gap(name, round(have, 1), lv)))
        found.sort(key=lambda g: -g[0])
        fit = 1 - short / need if need else 0.0
        out.append(Match(code, title(code), fit, tuple(g for _, g in found[:gaps]), tuple(certs.get(code, []))))
    return sorted(out, key=lambda m: -m.fit)[:top]
