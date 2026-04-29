# Beidou Positioning Experiment

This project implements a full GNSS single point positioning (SPP) workflow based on RINEX observation/navigation data. The current dataset is a GPS RINEX 2.11 pair. The code is modular and includes parsing, satellite position/clock, SPP solver, continuous processing, analysis, visualization, and a PyQt GUI.

## Features
- RINEX 2.11 observation and navigation parsing
- Satellite position and clock correction
- Troposphere (Saastamoinen) and ionosphere (Klobuchar) corrections
- Iterative least-squares SPP
- Continuous positioning with RMS/mean/max statistics
- CSV export and plotting (error/DOP, trajectory)
- PyQt GUI with realtime updates and trajectory replay

## Requirements
- Python 3.9+
- PyQt5
- matplotlib

If needed, install dependencies:
```
python3 -m pip install PyQt5 matplotlib
```

## Data
Place RINEX files in the project root or provide paths:
- Observation: `*.o` or `*.obs`
- Navigation: `*.n` or `*.nav`

Example files in this repo:
- `bjfs1170.26o`
- `brdc1170.26n`

## Quick Start (CLI)
Single-epoch solve:
```
python3 scripts/run_spp.py --obs bjfs1170.26o --nav brdc1170.26n --epoch 0
```

Continuous solve + CSV:
```
python3 scripts/run_continuous.py --obs bjfs1170.26o --nav brdc1170.26n
```

Generate plots from CSV:
```
python3 scripts/plot_results.py --csv results.csv --save-dir .
```

Inspect RINEX headers:
```
python3 scripts/inspect_rinex.py --obs bjfs1170.26o --nav brdc1170.26n
```

## GUI
Run the GUI:
```
python3 scripts/gui_app.py
```

GUI options:
- Obs/Nav file: select input data
- Output CSV: set output path
- Step / Max epochs: control sampling and runtime
- Max iterations / Error threshold: solver convergence
- Elevation mask: satellite cutoff
- GNSS systems: default `G` for GPS

Buttons:
- Run: start continuous positioning
- Plot: show error/DOP and trajectory
- Replay: trajectory playback

## Output
- `results.csv`: time series of positions, DOP, and errors
- Plot images when using `--save-dir`

## Project Structure
```
src/
  analysis.py
  atmosphere.py
  constants.py
  coords.py
  models.py
  pipeline.py
  plotting.py
  positioning.py
  rinex_nav.py
  rinex_obs.py
  satellite.py
  time_utils.py
scripts/
  gui_app.py
  inspect_rinex.py
  plot_results.py
  run_continuous.py
  run_spp.py
reports/
  design_report_template.md
  experiment_report_template.md
  test_report_template.md
```

## Notes / Limitations
- Current validation uses GPS RINEX 2.11 data. Multi-GNSS support is scaffolded, but BDS data has not been verified in this repo.
- For full experiment requirements, use multiple datasets and record test results.
