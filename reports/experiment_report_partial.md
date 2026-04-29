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
- RINEX parsing (obs/nav)
- Satellite position and clock correction
- SPP least squares
- Continuous positioning + statistics
- Visualization and GUI

Data flow:
Input RINEX -> preprocess -> satellite/clock -> least squares -> analysis -> CSV/plots

## 4. Implementation Highlights
- RINEX 2.11 parsing supports observation types and epoch alignment.
- Satellite orbit computed in ECEF with Earth rotation correction.
- Clock correction includes broadcast polynomial and relativistic term.
- Troposphere and ionosphere corrections applied per satellite.
- Iterative least squares with convergence threshold and PDOP/GDOP metrics.

## 5. Test Results (Current Dataset)
Dataset:
- Observation: `bjfs1170.26o`
- Navigation: `brdc1170.26n`

Continuous positioning (full dataset):
- Solutions: 2880 epochs
- Horizontal RMS/Mean/Max (m): 1.964 / 1.594 / 5.892
- 3D RMS/Mean/Max (m): 4.314 / 3.585 / 10.009

Plots:
- Error/DOP curve and trajectory can be generated from `results.csv`.

## 6. Error Analysis (Brief)
- Errors correlate with satellite geometry (DOP) and measurement noise.
- Low elevation satellites increase multipath and residuals; elevation mask mitigates this.

## 7. Limitations and Future Work
- Only a single dataset tested so far; more datasets required for full validation.
- Multi-GNSS (BDS) needs additional datasets for verification.
- Add richer outlier detection and robustness (e.g., weighted least squares).
