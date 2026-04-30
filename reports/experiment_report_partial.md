# Experiment Report (Partial)

## 1. Experiment Goals
- Implement a full SPP workflow using RINEX observation and navigation data.
- Parse RINEX data, compute satellite positions and clock corrections, solve user position, and analyze accuracy.
- Provide basic visualization and a GUI for interactive use.

## 2. Methods and Steps
1) Parse RINEX observation (`*.o`) and navigation (`*.n`) files.
2) Preprocess observations with elevation mask and basic outlier filtering.
3) Compute satellite ECEF positions and clock corrections from broadcast ephemeris.
4) Apply tropospheric (Saastamoinen) and ionospheric (Klobuchar) corrections.
5) Solve user position using iterative least squares.
6) Perform continuous positioning, compute statistics, and export results.
7) Visualize errors and trajectory; provide GUI for interaction.

## 3. System Overview
Modules:
- Module 1: RINEX data import and preprocessing (`RinexDataModule`)
- Module 2: Satellite position, clock, atmosphere, and ionosphere corrections (`SatelliteCorrectionModule`)
- Module 3: Single point positioning and DOP calculation (`SinglePointPositioningModule`)
- Module 4: Continuous positioning, statistics, CSV, and plots (`ContinuousAnalysisModule`)
- Module 5: Integrated CLI/GUI software workflow (`SoftwareSystemModule`)

Data flow:
Input RINEX -> preprocess -> satellite/clock -> least squares -> analysis -> CSV/plots

## 4. Implementation Highlights
- RINEX 2.11 and RINEX 3 mixed observation/navigation parsing supports observation types and epoch alignment.
- RINEX 3 BDS `IONOSPHERIC CORR` coefficients are parsed and selected for BDS Klobuchar correction.
- Satellite orbit computed in ECEF with Earth rotation correction.
- Clock correction includes broadcast polynomial and relativistic term.
- BDT/GPST conversion is handled explicitly for BDS ephemeris selection and satellite propagation.
- BDS GEO satellites C01-C05 use a dedicated GEO rotation branch.
- Troposphere and ionosphere corrections applied per satellite.
- Iterative least squares supports one receiver clock parameter per GNSS system, so GPS+BDS joint positioning can estimate inter-system clock bias instead of forcing all systems into one clock term.
- Solver controls include convergence threshold, configurable residual gate, elevation weighted least squares, receiver-state sanity checks, residual diagnostics, and PDOP/GDOP metrics.

## 5. Test Results (Current Dataset)
Dataset:
- Observation: `data/sample/bjfs1170.26o`
- Navigation: `data/sample/brdc1170.26n`

Continuous positioning (full dataset):
- Solutions: 2880 epochs
- Horizontal RMS/Mean/Max (m): 1.658 / 1.378 / 4.758
- 3D RMS/Mean/Max (m): 4.253 / 3.517 / 10.121

Plots:
- Error/DOP curve and trajectory can be generated from `results.csv`.

Additional validation datasets:

| Dataset | System | Solutions | Horizontal RMS/Mean/Max (m) | 3D RMS/Mean/Max (m) | Notes |
| --- | --- | ---: | --- | --- | --- |
| `data/datasets/bjfs_2026_117_gps` | GPS | 2880 | 1.658 / 1.378 / 4.758 | 4.253 / 3.517 / 10.121 | Baseline sample and daily GPS validation |
| `data/datasets/daej_2026_117_gps` | GPS | 2880 | 1.948 / 1.491 / 7.122 | 3.904 / 3.280 / 9.308 | Independent station validation |
| `data/datasets/hksl_2026_117_gps` | GPS | 2880 | 3.895 / 3.362 / 7.864 | 5.265 / 4.685 / 13.005 | Independent station validation |
| `data/datasets/twtf_2026_117_mixed` | GPS from mixed RINEX | 2880 | 5.779 / 4.434 / 12.705 | 6.598 / 5.531 / 14.513 | RINEX 3 mixed data parser validation |
| `data/datasets/twtf_2026_117_mixed` | BDS only | 2880 | 6.015 / 4.072 / 53.206 | 7.488 / 6.055 / 59.987 | Full-day BDS verification |
| `data/datasets/twtf_2026_117_mixed` | GPS+BDS | 2880 | 5.347 / 3.979 / 11.681 | 6.029 / 5.175 / 12.411 | Joint solution with per-system clock parameters |

## 6. Error Analysis (Brief)
- Errors correlate with satellite geometry (DOP) and measurement noise.
- Low elevation satellites increase multipath and residuals; elevation mask mitigates this.

## 7. Limitations and Future Work
- BDS-only and GPS+BDS full-day runs are now meter-level on the TWTF mixed dataset, but more stations/days are still needed before claiming broad generality.
- Multi-GNSS joint positioning currently estimates per-system receiver clock terms; later work can add explicit inter-frequency and receiver hardware bias diagnostics.
- Add richer outlier detection and robustness, such as CN0 weighting and satellite-specific long-term residual diagnostics.
