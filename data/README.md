# Data Directory

This directory separates the default sample, managed experiment datasets, and machine-readable manifests.

## Layout

```text
data/
  sample/                # Default CLI/GUI sample files
  datasets/              # One directory per downloaded dataset
  manifests/             # CSV indexes used for batch tests and reports
```

Each directory under `data/datasets/` uses the same structure:

```text
<dataset_id>/
  raw/                   # Original downloaded archives
  rinex/                 # Decompressed files used by scripts
  metadata.json          # Dataset description and processing status
```

## Dataset Inventory

The main index is:

`data/manifests/datasets.csv`

| Dataset | Format | Systems | Status |
| --- | --- | --- | --- |
| `bjfs_2026_117_gps` | RINEX 2.11 | GPS | Full GPS run OK |
| `daej_2026_117_gps` | RINEX 2.11 | GPS | Full GPS run OK |
| `hksl_2026_117_gps` | RINEX 2.11 | GPS | Full GPS run OK |
| `twtf_2026_117_mixed` | RINEX 3.04 | GPS/BDS/Galileo/GLONASS/QZSS/SBAS | Mixed parse OK; GPS-only run OK; BDS-only pending |

## Result Outputs

Generated CSV and plots are stored under:

`results/datasets/`

| Dataset output | Horizontal RMS / Mean / Max (m) | 3D RMS / Mean / Max (m) |
| --- | --- | --- |
| `results/datasets/bjfs_2026_117_gps` | `1.964 / 1.594 / 5.892` | `4.314 / 3.585 / 10.009` |
| `results/datasets/daej_2026_117_gps` | `2.586 / 1.853 / 12.215` | `4.220 / 3.488 / 14.292` |
| `results/datasets/hksl_2026_117_gps` | `4.005 / 3.448 / 9.780` | `6.048 / 5.276 / 15.305` |
| `results/datasets/twtf_2026_117_gps_from_mixed` | `6.254 / 4.920 / 14.966` | `7.722 / 6.468 / 20.000` |

## Example Commands

```bash
.venv/bin/python scripts/run_continuous.py \
  --obs data/datasets/daej_2026_117_gps/rinex/daej1170.26o \
  --nav data/datasets/daej_2026_117_gps/rinex/brdc1170.26n \
  --csv results/datasets/daej_2026_117_gps/results.csv \
  --plot \
  --save-plots results/datasets/daej_2026_117_gps
```

```bash
.venv/bin/python scripts/run_continuous.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --systems G \
  --csv results/datasets/twtf_2026_117_gps_from_mixed/results.csv
```
