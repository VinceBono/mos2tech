# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
import json

from mos2tech.cli import main
from mos2tech.core import _data, lookup, rank, source_levels


def test_lookup_finds_marine_network_administrator():
    (moc,) = lookup("0631", "M")
    assert moc.title == "Network Administrator" and moc.onet == ("15-1244.00",)


def test_lookup_is_case_insensitive_and_puts_active_first():
    hits = lookup("2841", "M")
    assert [m.active for m in hits] == sorted((m.active for m in hits), reverse=True)
    assert lookup("25b", "A") == lookup("25B", "A")


def test_military_only_occupation_has_no_levels():
    assert source_levels(("55-3016.00",)) is None


def test_role_fits_itself_perfectly_and_ranks_first():
    best = rank(source_levels(("15-1244.00",)), top=1)[0]
    assert best.onet == "15-1244.00" and best.fit == 1.0 and best.gaps == ()


def test_zero_levels_fit_nothing_and_gaps_are_real_shortfalls():
    n = len(_data()[1]["elements"])
    for m in rank([0.0] * n):
        assert m.fit == 0.0 and all(g.need > g.have for g in m.gaps)


def test_cli_text_json_and_errors(capsys):
    assert main(["0631", "-s", "marines"]) == 0
    assert "Network and Computer Systems Administrators" in capsys.readouterr().out
    assert main(["0631", "-s", "M", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["matches"][0]["onet"] == "15-1244.00"
    assert main(["0311", "-s", "M"]) == 0
    assert "can't be calculated" in capsys.readouterr().out
    assert main(["ZZZZ9"]) == 1
