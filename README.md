My personal website, inspired by my classmates at CMU and other far more experienced programmers. Now somewhat decorated and reshuffled by myself and some LLMs.

## Data center scenarios dashboard

The static dashboard is at `elote.html` (published URL: `https://davidlikeslearning.github.io/elote.html`). It reads `data/elote-regions.csv` and `data/elote-regions.geojson`; it does not run Temoa in the browser. The CSV has four scenarios (no servers, unregulated servers, 50% New-Build 3P coverage, 100% New-Build 3P coverage), four model years, and 26 model regions.

To refresh the CSV from the adjacent `Hubs/temoa` repository, use its Python environment with pandas and openpyxl:

```sh
/path/to/Hubs/temoa/temoa_env/bin/python tools/export_elote_dashboard.py /path/to/Hubs/temoa
```

The exporter reads the four corresponding Temoa `.xlsx` outputs. Installed capacity is grouped using the same technology-family rules as the Temoa figure scripts. Clean capacity includes solar, wind, hydro, geothermal, and nuclear; battery power capacity is separate. Net exports are outgoing minus incoming public transmission activity, in TWh/yr. CO₂ is the sum of the `Emissions` sheet's CO₂ rows, in Mt/yr. The map geometry is copied from Temoa's `external/mip_26zone/conus_26z_latlon_simple.geojson`.
