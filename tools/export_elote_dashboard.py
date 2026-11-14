#!/usr/bin/env python3
"""Export the four ELOTE scenarios as a small static CSV for the site.

Run with a Python environment containing pandas and openpyxl:
  python tools/export_elote_dashboard.py /path/to/Hubs/temoa
"""
import csv
import re
import sys
from pathlib import Path

import pandas as pd

SITE = Path(__file__).resolve().parents[1]
TEMOA = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SITE.parent / "temoa"
RUNS = {
    "no_servers": ("lulo_no_dc_duals_3360h", "conus_myopic_lulo_no_dc_duals.xlsx"),
    "unregulated": ("lulo_geo_baseline_duals_3360h", "conus_myopic_lulo_geo_baseline_duals.xlsx"),
    "covered_50": ("elote_pct50_fixconv_geo_3360h", "elote_pct50_fixconv_geo_3360h.xlsx"),
    "covered_100": ("elote_pct100_fixconv_geo_3360h", "elote_pct100_fixconv_geo_3360h.xlsx"),
}
YEARS = (2027, 2030, 2035, 2040)


def family(tech):
    tech = re.sub(r"_dc$", "", re.sub(r"^server_", "", tech)).lower()
    if "transmission" in tech or "distribution" in tech:
        return None
    if tech.startswith(("battery", "batteries", "hydroelectric_pumped")):
        return "battery"
    if "geothermal" in tech:
        return "clean"
    if "nuclear" in tech:
        return "clean"
    if "hydro" in tech:
        return "clean"
    if tech.startswith(("utilitypv", "solar")) or "wind" in tech:
        return "clean"
    if any(x in tech for x in ("coal", "natural_gas", "naturalgas", "ng_", "biomass", "petroleum_liquids")) or tech.startswith("distributed_generation"):
        return "other"
    return None


def export():
    data = {}
    for scenario, (folder, filename) in RUNS.items():
        book = TEMOA / "output_files" / folder / filename
        if not book.exists():
            raise FileNotFoundError(book)
        capacity = pd.read_excel(book, sheet_name="Capacity_electricity")
        emissions = pd.read_excel(book, sheet_name="Emissions")
        transmission = pd.read_excel(book, sheet_name="Activity_transmission")
        capacity["family"] = capacity.Technology.map(family)
        capacity = capacity.dropna(subset=["family"])
        emissions = emissions[emissions["Emission Commodity"] == "CO2"]
        transmission = transmission[transmission.Technology == "transmission"].copy()
        edges = transmission.Region.str.split("-", n=1, expand=True)
        transmission["source"] = edges[0]
        transmission["destination"] = edges[1]
        regions = sorted(set(capacity.Region) | set(emissions.Region))
        for year in YEARS:
            caps = capacity.groupby(["Region", "family"])[year].sum()
            co2 = emissions.groupby("Region")[year].sum()
            outgoing = transmission.groupby("source")[year].sum()
            incoming = transmission.groupby("destination")[year].sum()
            for region in regions:
                value = lambda kind: float(caps.get((region, kind), 0)) / 1000
                clean = value("clean")
                battery = value("battery")
                other = value("other")
                data[scenario, year, region] = [
                    round(clean + battery + other, 5),
                    round(clean, 5),
                    round(battery, 5),
                    round((float(outgoing.get(region, 0)) - float(incoming.get(region, 0))) / 1e6, 5),
                    round(float(co2.get(region, 0)) / 1e6, 5),
                ]
    out = SITE / "data" / "elote-regions.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "year", "region", "capacity_gw", "clean_gw", "battery_gw", "net_exports_twh", "co2_mt"])
        for (scenario, year, region), values in sorted(data.items()):
            writer.writerow([scenario, year, region, *values])
    print(f"Wrote {len(data)} rows to {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    export()
