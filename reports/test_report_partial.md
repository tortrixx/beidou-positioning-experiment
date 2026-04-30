# Test Report (Partial)

## 1. Test Environment
- OS: macOS local workspace
- Python: 3.9.6 (`.venv/bin/python`)
- Key dependencies: standard library, NumPy-free core solver, optional Matplotlib for plots

## 2. Test Data
- Sample GPS data: `data/sample/bjfs1170.26o`, `data/sample/brdc1170.26n`
- Managed datasets:
  - `data/datasets/bjfs_2026_117_gps`
  - `data/datasets/daej_2026_117_gps`
  - `data/datasets/hksl_2026_117_gps`
  - `data/datasets/twtf_2026_117_mixed`
- Dataset manifest: `data/manifests/datasets.csv`

## 3. Completed Test Cases
| Test case | Command or scope | Result |
| --- | --- | --- |
| Default RINEX inspection | `python scripts/inspect_rinex.py` | Passed; bundled sample data can be opened directly |
| Pipeline parameter validation | `step=0` unit test | Passed; raises clear `ValueError` |
| Plot generation | `plot_error_and_dop`, `plot_trajectory` unit test | Passed; missing plot save is reported correctly |
| Five module facade | `RinexDataModule` through `SoftwareSystemModule` | Passed; single-epoch and continuous GPS workflow runs |
| RINEX 3 BDS navigation parsing | synthetic BDS nav unit test | Passed; `BDSA/BDSB` ionospheric coefficients parsed |
| RINEX 3 mixed observation parsing | TWTF mixed dataset | Passed; BDS and Galileo observations detected |
| Mixed navigation parsing | TWTF BRDM navigation | Passed; GPS and BDS records detected while short SBAS records are skipped |
| Weighted LS + residual diagnostics | sample GPS dataset | Passed; CSV includes `residual_rms_m` and `residual_max_m` |
| BDS-only stability and accuracy | TWTF mixed dataset, `systems=("C",)` | Passed; full-day run remains finite with 3D RMS 7.488 m |
| GPS+BDS joint positioning | TWTF mixed dataset, `systems=("G", "C")` | Passed; per-system clock model gives full-day 3D RMS 6.029 m |

## 4. Verification Commands
```bash
MPLCONFIGDIR=/private/tmp/mplconfig XDG_CACHE_HOME=/private/tmp/xdgcache \
  .venv/bin/python -m unittest tests.test_experiment_modules -v
```
Result: 12 tests passed.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/beidou_pycache \
  .venv/bin/python -m compileall src scripts tests
```
Result: all modules compiled successfully.

```bash
.venv/bin/python scripts/run_continuous.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --systems C --csv results/datasets/twtf_2026_117_bds/results.csv \
  --plot --save-plots results/datasets/twtf_2026_117_bds
```
Result: 2880 BDS-only solutions; horizontal RMS 6.015 m, 3D RMS 7.488 m.

```bash
.venv/bin/python scripts/run_continuous.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --systems G,C --csv results/datasets/twtf_2026_117_gps_bds/results.csv \
  --plot --save-plots results/datasets/twtf_2026_117_gps_bds
```
Result: 2880 GPS+BDS solutions; horizontal RMS 5.347 m, 3D RMS 6.029 m.

## 5. Issues Fixed
- Default sample paths now point to managed sample data under `data/sample/`.
- Continuous pipeline validates `step`, `max_epochs`, and `max_iter`.
- Plotting functions report save failures instead of printing false success.
- RINEX 3 mixed observation and navigation parsing covers BDS records needed by the lab.
- BDS time conversion now uses the correct GPST to BDT direction for BDS satellite propagation.
- BDS-only continuous runs use a BDS-appropriate residual gate and receiver-state sanity checks to prevent divergent heights from overflowing the atmospheric model.
- GPS+BDS joint runs estimate one clock term per GNSS system, preventing BDS observations from being forced into the GPS receiver clock parameter.
- CSV export now creates missing parent directories, so batch result folders can be generated directly.
- Positioning uses elevation-weighted normal equations and exports post-fit residual RMS/max diagnostics for debugging and later model training.
- Error/DOP plots now include visible/used satellite count curves.

## 6. Remaining Risks
- Current validation covers one mixed BDS station/day; more BDS datasets should be added for robustness.
- The solver is weighted by elevation but does not yet use CN0/SNR-based weights.
- Future tests should include GUI screenshots and longer multi-day batch runs.
