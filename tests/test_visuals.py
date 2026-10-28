import xml.etree.ElementTree as ET

import pytest

from founder_engine.visuals import CATEGORICAL, column_chart_svg, fmt_value, line_chart_svg, load_tokens, nice_ticks


def test_number_formatting():
    assert fmt_value(129850, "£") == "£129.8K" or fmt_value(129850, "£") == "£129.9K"
    assert fmt_value(45, "%") == "45%"
    assert fmt_value(4200) == "4,200"
    assert fmt_value(31200) == "31.2K"
    assert fmt_value(3_400_000) == "3.4M"


def test_nice_ticks_cover_max():
    for vmax in (7, 38, 31200, 0.9):
        ticks = nice_ticks(vmax)
        assert ticks[0] == 0 and ticks[-1] >= vmax and len(ticks) <= 7


def test_svgs_are_valid_and_use_brand_colours():
    t = load_tokens()
    col = column_chart_svg(["a", "b", "c"], [1, 5, 3], t, highlight=1)
    ET.fromstring(col)
    assert t["iris-400"] in col and t["iris-600"] in col
    line = line_chart_svg(["Jan", "Feb"], {"A": [1, 2], "B": [2, 3]}, t, "%")
    ET.fromstring(line)
    assert t[CATEGORICAL[0]] in line and t[CATEGORICAL[1]] in line


def test_guards():
    t = load_tokens()
    with pytest.raises(ValueError):
        column_chart_svg(["a"], [-1], t)
    with pytest.raises(ValueError):
        line_chart_svg(["x"], {str(i): [1] for i in range(5)}, t)
