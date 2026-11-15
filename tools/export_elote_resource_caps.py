#!/usr/bin/env python3
"""Export a 2040 resource-cap geofacet for the ELOTE site dashboard.

Usage: python tools/export_elote_resource_caps.py /path/to/Hubs/temoa
Requires matplotlib. Reads the site's existing scenario CSV and the 100% 3P
converter template, whose shared renewable limits match the solved run.
"""
import csv
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

SITE = Path(__file__).resolve().parents[1]
TEMOA = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SITE.parent / "temoa"
YEAR = 2040
SCENARIOS = ("unregulated", "covered_100")
TECHS = ("wind", "solar")
COLORS = {"wind": "#26748b", "solar": "#dda72a"}


def export():
    db = TEMOA / "three_pillars/conus_26z_elote_pct100_conv_template_geo_3360h.sqlite"
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
        caps = {(region, tech): value / 1000 for region, tech, value in conn.execute("""
            SELECT region,
                   CASE WHEN tech_or_group LIKE 'utilitypv_%' THEN 'solar' ELSE 'wind' END,
                   SUM(capacity)
              FROM limit_capacity
             WHERE period = ? AND operator = 'le'
               AND (tech_or_group LIKE 'utilitypv_%'
                 OR tech_or_group LIKE 'landbasedwind_%'
                 OR tech_or_group LIKE 'offshorewind_%')
             GROUP BY region, 2
        """, (YEAR,))}
    with (SITE / "data/elote-regions.csv").open(newline="") as f:
        source = list(csv.DictReader(f))
    rows = []
    for item in source:
        if int(item["year"]) != YEAR or item["scenario"] not in SCENARIOS or item["region"] == "NYCW":
            continue
        for tech in TECHS:
            cap = caps[item["region"], tech]
            used = float(item[f"{tech}_gw"])
            if used > cap + 0.01:
                raise ValueError(f"Capacity exceeds resource cap: {item['region']} {tech} {item['scenario']}")
            rows.append((item["region"], item["scenario"], tech, used, cap, 100 * used / cap))
    regions = sorted({r[0] for r in rows})
    assert len(regions) == 25 and len(rows) == 100
    out = SITE / "data/elote-resource-caps-2040.csv"
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("region", "scenario", "technology", "used_gw", "resource_cap_gw", "cap_used_pct"))
        writer.writerows((z, s, t, f"{u:.5f}", f"{c:.5f}", f"{p:.3f}") for z, s, t, u, c, p in sorted(rows))

    # Compact the project's established geographic tile positions to 5 x 5.
    ordered = (
        "NWPP", "MISW", "PJMC", "NYUP", "ISNE",
        "CANO", "SPPN", "MISC", "MISE", "PJME",
        "BASN", "RMRG", "SPPC", "PJMW", "PJMD",
        "CASO", "SRSG", "SPPS", "MISS", "SRCE",
        "TREW", "TRE", "SRCA", "SRSE", "FRCC",
    )
    assert set(ordered) == set(regions)
    lookup = {(z, s, t): (u, c, p) for z, s, t, u, c, p in rows}
    fig, axes = plt.subplots(5, 5, figsize=(19, 15), dpi=150, facecolor="white")
    for ax, zone in zip(axes.flat, ordered):
        ax.set_title(zone, loc="left", fontsize=12, fontweight="bold", pad=7)
        for i, (tech, scenario) in enumerate((('wind', 'unregulated'), ('wind', 'covered_100'),
                                               ('solar', 'unregulated'), ('solar', 'covered_100'))):
            used, cap, pct = lookup[zone, scenario, tech]
            y = 3 - i
            ax.barh(y, 100, color="#e9eeeb", height=.62, zorder=1)
            ax.barh(y, pct, color=COLORS[tech], alpha=1 if scenario == 'covered_100' else .55,
                    height=.62, zorder=2)
            ax.text(103, y, f"{used:.1f} / {cap:.1f}", va="center", fontsize=8, color="#263733")
        ax.set_yticks([3, 2, 1, 0], ["W · U", "W · 3P", "S · U", "S · 3P"], fontsize=8)
        ax.set_xlim(0, 188)
        ax.set_xticks([0, 50, 100], ["0", "50", "100%"], fontsize=7)
        ax.grid(axis="x", color="#cbd5d0", linewidth=.5)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Wind and solar resource caps used · 2040", x=.065, ha="left", fontsize=19, fontweight="bold")
    fig.text(.065, .938, "Installed capacity / regional resource cap. U = unregulated servers; 3P = 100% New-Build 3P. Values show used / cap in GW.", fontsize=11)
    fig.legend(handles=[Patch(color=COLORS[t], label=t.title()) for t in TECHS],
               loc="upper right", bbox_to_anchor=(.96, .972), ncol=2, frameon=False)
    fig.text(.065, .017, "Wind caps include land-based and offshore wind; cap values sum shared public + server technology limits. NYCW excluded.", fontsize=9, color="#52615c")
    fig.tight_layout(rect=(.04, .035, .97, .92), h_pad=2.0, w_pad=1.0)
    dest = SITE / "data/figures/elote_resource_caps_2040_geofacet.png"
    fig.savefig(dest, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"Wrote {len(rows)} rows to {out} and {dest}")


if __name__ == "__main__":
    export()
