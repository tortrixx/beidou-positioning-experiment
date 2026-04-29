# Project Continuation Plan

This plan is for continuing the Beidou positioning experiment project after the current implementation. It records what is done, what is missing, and the next steps to complete the experiment requirements.

## Current Status (Done)
- Core SPP pipeline implemented: RINEX parsing -> satellite position/clock -> SPP least squares -> continuous positioning -> analysis -> CSV/plots.
- GUI implemented with data import, parameter settings, realtime position display, plotting, and trajectory replay.
- Single dataset tested (bjfs1170.26o / brdc1170.26n), results saved in results.csv.
- README and partial experiment report drafted.

## Known Limitations
- Only one dataset tested; experiment requires multiple datasets and a test report.
- BDS datasets are not currently available; multi-GNSS verification is pending.
- Reports are not fully filled (design report, full experiment report, test report).

## Plan (Detailed Steps)

### Step 1: Collect Additional Datasets
1) Acquire at least 2 additional RINEX obs/nav pairs.
2) Prefer different dates or stations.
3) Put files into project root or data/ directory.
4) Record dataset metadata (date, station, duration).

### Step 2: Batch Processing + Results
1) Run continuous solver for each dataset:
   - python3 scripts/run_continuous.py --obs <obs> --nav <nav> --csv <out.csv>
2) Generate plots for each dataset:
   - python3 scripts/plot_results.py --csv <out.csv> --save-dir <dir>
3) Record key metrics: solutions count, RMS/mean/max (horizontal + 3D), PDOP range.
4) Save outputs under data/<dataset_name>/ or results/ directories.

### Step 3: Write Test Report
1) Fill reports/test_report_template.md using real outputs.
2) Add the following sections per dataset:
   - Environment (OS, Python, dependencies)
   - Dataset description
   - Metrics table
   - Plots (error/DOP + trajectory)
3) Note issues and fixes (if any).

### Step 4: Complete Design Report
1) Fill reports/design_report_template.md:
   - Architecture diagram (data flow)
   - Module responsibilities
   - Data structures (ObsHeader, NavRecord, PositionSolution)
2) Add diagrams or flowcharts if needed.

### Step 5: Complete Experiment Report
1) Expand reports/experiment_report_partial.md to full.
2) Add:
   - Detailed module algorithms and key formulas
   - Error sources and analysis
   - Screenshots of GUI and plots
   - Discussion of limitations and improvements

### Optional Step 6: BDS/Multi-GNSS Verification
1) Acquire RINEX 3 BDS data (obs + nav).
2) Run with --systems G,C and compare results.
3) Document differences and any fixes needed.

## Files to Update
- README.md (finalize if needed)
- reports/design_report_template.md (fill)
- reports/experiment_report_partial.md (expand)
- reports/test_report_template.md (fill)

## Suggested Output Structure
- data/<dataset_name>/
  - obs/nav
  - outputs (csv, plots)
- reports/
  - final_design_report.md
  - final_experiment_report.md
  - final_test_report.md
