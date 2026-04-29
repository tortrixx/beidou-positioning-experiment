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
- BDS GEO satellites C01-C05 use a dedicated GEO rotation branch.
- Troposphere and ionosphere corrections applied per satellite.
- Iterative least squares with convergence threshold, configurable residual gate, receiver-state sanity checks, and PDOP/GDOP metrics.

## 5. Test Results (Current Dataset)
Dataset:
- Observation: `data/sample/bjfs1170.26o`
- Navigation: `data/sample/brdc1170.26n`

Continuous positioning (full dataset):
- Solutions: 2880 epochs
- Horizontal RMS/Mean/Max (m): 1.964 / 1.594 / 5.892
- 3D RMS/Mean/Max (m): 4.314 / 3.585 / 10.009

Plots:
- Error/DOP curve and trajectory can be generated from `results.csv`.

Additional validation datasets:

| Dataset | System | Solutions | Horizontal RMS/Mean/Max (m) | 3D RMS/Mean/Max (m) | Notes |
| --- | --- | ---: | --- | --- | --- |
| `data/datasets/bjfs_2026_117_gps` | GPS | 2880 | 1.964 / 1.594 / 5.892 | 4.314 / 3.585 / 10.009 | Baseline sample and daily GPS validation |
| `data/datasets/daej_2026_117_gps` | GPS | 2880 | 2.586 / 1.853 / 12.215 | 4.220 / 3.488 / 14.292 | Independent station validation |
| `data/datasets/hksl_2026_117_gps` | GPS | 2880 | 4.005 / 3.448 / 9.780 | 6.048 / 5.276 / 15.305 | Independent station validation |
| `data/datasets/twtf_2026_117_mixed` | GPS from mixed RINEX | 2880 | 6.254 / 4.920 / 14.966 | 7.722 / 6.468 / 20.000 | RINEX 3 mixed data parser validation |
| `data/datasets/twtf_2026_117_mixed` | BDS only | 3 | 2809.343 / 2808.914 / 2868.813 | 3554.110 / 3553.547 / 3631.011 | Stability regression test; current BDS-only precision remains limited |

## 6. Error Analysis (Brief)
- Errors correlate with satellite geometry (DOP) and measurement noise.
- Low elevation satellites increase multipath and residuals; elevation mask mitigates this.

## 7. Limitations and Future Work
- BDS-only positioning is now stable on the TWTF RINEX 3 mixed dataset, but the current error is still at kilometer level. It should be treated as a parser/model integration milestone, not as final high-precision BDS performance.
- Multi-GNSS joint positioning still needs inter-system bias modeling before GPS+BDS fusion can be considered complete.
- Add richer outlier detection and robustness, such as elevation/CN0 weighting, robust least squares, and satellite-specific residual diagnostics.
