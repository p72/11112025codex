#!/usr/bin/env python3
"""Generate an SVG line chart for general account tax revenue to nominal GNI ratio."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "general_account_tax_revenue_vs_gni.csv"
OUTPUT_PATH = ROOT / "output" / "general_account_tax_gni_ratio.svg"


def read_dataset() -> List[Tuple[int, float, float, float]]:
    """Load fiscal year data and compute the tax-to-GNI ratio."""
    rows: List[Tuple[int, float, float, float]] = []
    with DATA_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(row for row in f if not row.lstrip().startswith("#"))
        for row in reader:
            year = int(row["fiscal_year"])
            tax = float(row["tax_revenue_trillion_yen"])
            gni = float(row["nominal_gni_trillion_yen"])
            ratio = (tax / gni) * 100.0
            rows.append((year, tax, gni, ratio))
    return rows


def nice_step(raw_step: float) -> float:
    """Return a human-friendly step size greater than or equal to raw_step."""
    if raw_step <= 0:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(raw_step))
    for multiplier in (1, 2, 2.5, 5, 10):
        step = multiplier * magnitude
        if step >= raw_step:
            return step
    return 10 * magnitude


def compute_y_ticks(values: List[float], target_count: int = 6) -> List[float]:
    """Compute y-axis ticks covering the data range."""
    v_min = min(values)
    v_max = max(values)
    if math.isclose(v_min, v_max):
        return [v_min]
    raw_step = (v_max - v_min) / max(target_count - 1, 1)
    step = nice_step(raw_step)
    tick_start = math.floor(v_min / step) * step
    tick_end = math.ceil(v_max / step) * step
    ticks = []
    current = tick_start
    # protect against infinite loops due to floating point drift
    while current <= tick_end + step * 0.5:
        ticks.append(round(current, 10))
        current += step
    return ticks


def format_number(value: float) -> str:
    """Format a tick label with up to one decimal place without trailing zeros."""
    rounded = round(value, 2)
    if math.isclose(rounded, round(rounded)):
        return f"{int(round(rounded))}"
    return f"{rounded:.1f}"


def build_svg(data: List[Tuple[int, float, float, float]]) -> str:
    width, height = 960, 540
    margin_left, margin_right = 80, 40
    margin_top, margin_bottom = 70, 70

    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom

    years = [row[0] for row in data]
    ratios = [row[3] for row in data]

    min_ratio = min(ratios)
    max_ratio = max(ratios)
    y_ticks = compute_y_ticks(ratios)
    y_min = y_ticks[0]
    y_max = y_ticks[-1]

    def x_coord(index: int) -> float:
        if len(years) == 1:
            return margin_left + chart_width / 2
        return margin_left + (chart_width * index) / (len(years) - 1)

    def y_coord(value: float) -> float:
        if math.isclose(y_max, y_min):
            return margin_top + chart_height / 2
        return margin_top + (y_max - value) * chart_height / (y_max - y_min)

    path_commands = []
    for idx, ratio in enumerate(ratios):
        x = x_coord(idx)
        y = y_coord(ratio)
        command = "M" if idx == 0 else "L"
        path_commands.append(f"{command}{x:.2f},{y:.2f}")
    line_path = " ".join(path_commands)

    x_tick_step = 3
    x_ticks = []
    for idx, year in enumerate(years):
        if idx == 0 or idx == len(years) - 1 or (year - years[0]) % x_tick_step == 0:
            x = x_coord(idx)
            x_ticks.append((x, year))

    svg_parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "  <style>"
        "    text { font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif; fill: #333; }",
        "    .title { font-size: 24px; font-weight: 600; }",
        "    .subtitle { font-size: 16px; fill: #555; }",
        "    .axis text { font-size: 14px; }",
        "    .tick text { font-size: 12px; fill: #444; }",
        "  </style>",
        "  <rect x='0' y='0' width='{width}' height='{height}' fill='#ffffff' />".format(width=width, height=height),
        f"  <text class='title' x='{width/2:.1f}' y='{margin_top - 30:.1f}' text-anchor='middle'>一般会計税収/名目GNI比の推移</text>",
        f"  <text class='subtitle' x='{width/2:.1f}' y='{margin_top - 8:.1f}' text-anchor='middle'>1994年度〜2023年度</text>",
        f"  <line x1='{margin_left}' y1='{margin_top}' x2='{margin_left}' y2='{height - margin_bottom}' stroke='#333' stroke-width='1' />",
        f"  <line x1='{margin_left}' y1='{height - margin_bottom}' x2='{width - margin_right}' y2='{height - margin_bottom}' stroke='#333' stroke-width='1' />",
    ]

    # Horizontal grid lines and y-axis ticks
    for tick in y_ticks:
        y = y_coord(tick)
        svg_parts.append(f"  <line x1='{margin_left}' y1='{y:.2f}' x2='{width - margin_right}' y2='{y:.2f}' stroke='#dddddd' stroke-width='1' />")
        svg_parts.append(
            "  <g class='tick'>"
            f"    <text x='{margin_left - 10}' y='{y + 4:.2f}' text-anchor='end'>{format_number(tick)}</text>"
            "  </g>"
        )

    # X-axis ticks
    for x, year in x_ticks:
        svg_parts.append(f"  <line x1='{x:.2f}' y1='{height - margin_bottom}' x2='{x:.2f}' y2='{height - margin_bottom + 6}' stroke='#333' stroke-width='1' />")
        svg_parts.append(
            "  <g class='tick'>"
            f"    <text x='{x:.2f}' y='{height - margin_bottom + 24}' text-anchor='middle'>{year}</text>"
            "  </g>"
        )

    # Line path
    svg_parts.append(f"  <path d='{line_path}' fill='none' stroke='#1f78b4' stroke-width='2.5' />")

    # Data point markers
    for idx, ratio in enumerate(ratios):
        x = x_coord(idx)
        y = y_coord(ratio)
        svg_parts.append(f"  <circle cx='{x:.2f}' cy='{y:.2f}' r='3.5' fill='#1f78b4' />")

    svg_parts.append(
        f"  <text class='axis' x='{margin_left - 50}' y='{margin_top + chart_height / 2:.1f}' text-anchor='middle' transform='rotate(-90 {margin_left - 50},{margin_top + chart_height / 2:.1f})'>税収/名目GNI（%）</text>"
    )
    svg_parts.append(
        f"  <text class='axis' x='{margin_left + chart_width / 2:.1f}' y='{height - margin_bottom + 50}' text-anchor='middle'>財務省決算ベース税収 ÷ 内閣府SNA名目GNI（年度）</text>"
    )
    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def main() -> None:
    data = read_dataset()
    svg = build_svg(data)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
