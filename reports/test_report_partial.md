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
| BDS-only stability | TWTF mixed dataset, `systems=("C",)`, first 3 valid epochs | Passed; no overflow and finite receiver states |

## 4. Verification Commands
```bash
MPLCONFIGDIR=/private/tmp/mplconfig XDG_CACHE_HOME=/private/tmp/xdgcache \
  .venv/bin/python -m unittest tests.test_experiment_modules -v
```
Result: 10 tests passed.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/beidou_pycache \
  .venv/bin/python -m compileall src scripts tests
```
Result: all modules compiled successfully.

```bash
.venv/bin/python scripts/run_continuous.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --systems C --max-epochs 3 --csv /private/tmp/twtf_bds_check.csv
```
Result: 3 BDS-only solutions; horizontal RMS 2809.343 m, 3D RMS 3554.110 m.

## 5. Issues Fixed
- Default sample paths now point to managed sample data under `data/sample/`.
- Continuous pipeline validates `step`, `max_epochs`, and `max_iter`.
- Plotting functions report save failures instead of printing false success.
- RINEX 3 mixed observation and navigation parsing covers BDS records needed by the lab.
- BDS-only continuous runs now use a BDS-appropriate residual gate and receiver-state sanity checks to prevent divergent heights from overflowing the atmospheric model.

## 6. Remaining Risks
- BDS-only precision is not yet acceptable for the final experiment target; the current result mainly proves parser/model integration and runtime stability.
- GPS+BDS joint positioning still needs inter-system clock/bias modeling.
- The solver is unweighted; low-elevation and noisy satellites can still dominate residuals.
