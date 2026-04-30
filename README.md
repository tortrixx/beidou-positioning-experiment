# 北斗定位解算实验

本项目基于 RINEX 观测与导航数据实现 GNSS 单点定位（SPP）全流程软件。当前已验证 GPS RINEX 2.11、RINEX 3 混合数据、BDS 单系统与 GPS+BDS 联合解算。代码采用模块化设计，包含解析、卫星位置/钟差、SPP 解算、连续定位、误差分析、可视化以及 PyQt GUI。

## 功能特性
- RINEX 2.11 与 RINEX 3 混合观测/导航解析
- 卫星位置与钟差修正
- 对流层（Saastamoinen）与 GPS/BDS Klobuchar 电离层改正
- GPS、BDS 与 GPS+BDS 联合迭代最小二乘 SPP
- 高度角加权最小二乘、残差门限剔除与残差诊断
- 连续定位与 RMS/均值/最大误差统计
- CSV 导出与散点绘图（误差/DOP、轨迹）
- PyQt GUI 实时显示与轨迹回放

## 依赖环境
- Python 3.9+
- PyQt5
- matplotlib

如需安装依赖：
```bash
python3 -m pip install -r requirements.txt
```

## 数据说明
将 RINEX 文件放在项目根目录或在命令行中传入路径：
- 观测文件：`*.o` 或 `*.obs`
- 导航文件：`*.n` 或 `*.nav`

本仓库示例数据：
- `data/sample/bjfs1170.26o`
- `data/sample/brdc1170.26n`

批量测试数据按站点/日期整理在：
- `data/datasets/bjfs_2026_117_gps`
- `data/datasets/daej_2026_117_gps`
- `data/datasets/hksl_2026_117_gps`
- `data/datasets/twtf_2026_117_mixed`
- `data/datasets/urban_nav_hk_medium_urban_1`
- `data/datasets/redundancy_stress_2026_117`

`urban_nav_hk_medium_urban_1` 是香港城市动态数据，包含多设备 `.obs/.nmea` 文件与下载整理后的 2021-05-17 mixed navigation 星历。它适合展示北斗、多系统解析和复杂数据容错；因接收机处于运动环境，使用 RINEX 头文件近似坐标统计出的误差不能等同于静态测站精度。

`redundancy_stress_2026_117` 是冗余测试数据，包含下载的 `.26o.gz/.26n.gz`、`.rnx.gz` 和 Hatanaka `.crx.gz` 场景，用于模拟验收时遇到不同压缩格式、不同 RINEX 版本和数据过少/无解等情况。

## 快速开始（命令行）
```bash
# 激活环境（mac）
source .venv/bin/activate

# 激活环境（Windows）
.venv\Scripts\activate
```

单历元解算：
```bash
python3 scripts/run_spp.py --obs data/sample/bjfs1170.26o --nav data/sample/brdc1170.26n --epoch 0
```

连续解算并导出 CSV：
```bash
python3 scripts/run_continuous.py --obs data/sample/bjfs1170.26o --nav data/sample/brdc1170.26n
```

BDS 单系统全日解算：
```bash
python3 scripts/run_continuous.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --systems C \
  --csv results/datasets/twtf_2026_117_bds/results.csv \
  --plot --save-plots results/datasets/twtf_2026_117_bds
```

GPS+BDS 联合解算：
```bash
python3 scripts/run_continuous.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --systems G,C \
  --csv results/datasets/twtf_2026_117_gps_bds/results.csv \
  --plot --save-plots results/datasets/twtf_2026_117_gps_bds
```

UrbanNav 城市数据 GPS+BDS 200 历元解算：
```bash
python3 scripts/run_continuous.py \
  --obs data/datasets/urban_nav_hk_medium_urban_1/rinex/UrbanNav-HK-Medium-Urban-1.ublox.m8t.GC.obs \
  --nav data/datasets/urban_nav_hk_medium_urban_1/rinex/BRDM00DLR_S_20211370000_01D_MN.rnx \
  --systems G,C \
  --max-epochs 200 \
  --csv results/datasets/urban_nav_hk_medium_urban_1_gps_bds/results.csv \
  --plot --save-plots results/datasets/urban_nav_hk_medium_urban_1_gps_bds
```

整理并统计 UrbanNav 数据：
```bash
python3 scripts/summarize_urban_nav.py \
  --root data/datasets/urban_nav_hk_medium_urban_1
```

运行冗余/容错测试：
```bash
python3 scripts/run_redundancy_tests.py \
  --max-epochs 20 \
  --output results/redundancy_tests/summary.csv
```

汇总所有已生成结果：
```bash
python3 scripts/run_batch.py --output results/summary.csv
```

附加题：训练线性回归误差补偿模型：
```bash
python3 scripts/train_error_model.py --output-dir results/ml_compensation
```

从 CSV 生成图表：
```bash
python3 scripts/plot_results.py --csv results.csv --save-dir .
```

查看 RINEX 头部信息：
```bash
python3 scripts/inspect_rinex.py --obs data/sample/bjfs1170.26o --nav data/sample/brdc1170.26n
```

## 五个模块单独运行与展示
以下命令用于课堂讲解、验收演示或单模块测试。若已激活虚拟环境，直接使用 `python3`；也可以将 `python3` 替换为 `.venv/bin/python`。

### 模块1：RINEX 数据导入、解析与预处理
GPS 示例数据：
```bash
python3 scripts/inspect_rinex.py \
  --obs data/sample/bjfs1170.26o \
  --nav data/sample/brdc1170.26n
```

RINEX 3 混合系统数据：
```bash
python3 scripts/inspect_rinex.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx
```

该模块主要展示 RINEX 版本、测站名、观测类型、历元数量、首历元卫星列表、导航星历数量和电离层参数。

UrbanNav 北斗/GPS 数据：
```bash
python3 scripts/inspect_rinex.py \
  --obs data/datasets/urban_nav_hk_medium_urban_1/rinex/UrbanNav-HK-Medium-Urban-1.ublox.m8t.GC.obs \
  --nav data/datasets/urban_nav_hk_medium_urban_1/rinex/BRDM00DLR_S_20211370000_01D_MN.rnx
```

### 模块2：卫星位置、钟差与传播延迟改正
模块2 是内部算法模块，可直接调用 `SatelliteCorrectionModule` 打印首历元可见卫星的改正结果：
```bash
python3 -c '
import sys
sys.path.append("src")
from experiment_modules import RinexDataModule, SatelliteCorrectionModule

d = RinexDataModule().load("data/sample/bjfs1170.26o", "data/sample/brdc1170.26n")
m = SatelliteCorrectionModule(d.nav_header, d.nav_records)
rows = m.visible_measurements(d.epochs[0], d.obs_header.approx_position_xyz, systems=("G",))

for r in rows[:8]:
    x, y, z = r.satellite_position_ecef
    print(f"{r.prn} el={r.elevation_deg:.2f} az={r.azimuth_deg:.2f} "
          f"raw={r.pseudorange_m:.3f} corrected={r.corrected_pseudorange_m:.3f} "
          f"clk={r.satellite_clock_s*1e9:.3f}ns trop={r.troposphere_delay_m:.3f} "
          f"iono={r.ionosphere_delay_m:.3f} xyz=({x:.1f},{y:.1f},{z:.1f})")
'
```

该模块主要展示每颗卫星的高度角、方位角、原始伪距、改正后伪距、卫星钟差、对流层改正、电离层改正和卫星 ECEF 坐标。

### 模块3：单历元单点定位解算
GPS 单历元解算：
```bash
python3 scripts/run_spp.py \
  --obs data/sample/bjfs1170.26o \
  --nav data/sample/brdc1170.26n \
  --epoch 0 \
  --systems G
```

BDS 单系统解算：
```bash
python3 scripts/run_spp.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --epoch 0 \
  --systems C
```

GPS+BDS 联合解算：
```bash
python3 scripts/run_spp.py \
  --obs data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx \
  --nav data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx \
  --epoch 0 \
  --systems G,C
```

该模块主要展示 ECEF 坐标、经纬高 BLH、接收机钟差、使用卫星数、PDOP 和 GDOP。

### 模块4：连续定位、误差统计与绘图
连续定位并保存 CSV 与图片：
```bash
python3 scripts/run_continuous.py \
  --obs data/sample/bjfs1170.26o \
  --nav data/sample/brdc1170.26n \
  --systems G \
  --csv results/demo/results.csv \
  --plot \
  --save-plots results/demo
```

只根据已有 CSV 重新生成图表：
```bash
python3 scripts/plot_results.py \
  --csv results/demo/results.csv \
  --save-dir results/demo
```

该模块主要展示连续历元数量、水平误差 RMS/Mean/Max、三维误差 RMS/Mean/Max、误差/DOP/卫星数散点图和轨迹散点图。

### 模块5：完整软件系统整合与 GUI 演示
启动图形界面：
```bash
python3 scripts/gui_app.py
```

GUI 推荐演示参数：
```text
Obs file: data/sample/bjfs1170.26o
Nav file: data/sample/brdc1170.26n
Output CSV: results/gui_demo.csv
Step: 1
Max epochs: 200
Max iterations: 8
Error threshold: 0.01
Elevation mask: 10
GNSS systems: G
```

操作顺序：
```text
Run -> Plot -> Replay
```

该模块主要展示 RINEX 数据导入、解算参数设置、定位结果实时显示、误差曲线查看和定位轨迹回放。

### 批量结果汇总
汇总所有已生成的多站点、多系统结果：
```bash
python3 scripts/run_batch.py --output results/summary.csv
```

输出文件：
```text
results/summary.csv
```

## GUI
启动 GUI：
```bash
python3 scripts/gui_app.py
```

GUI 参数说明：
- Obs/Nav file：选择观测/导航文件
- Output CSV：设置输出路径
- Step / Max epochs：抽样步长与最大历元数
- Max iterations / Error threshold：迭代上限与收敛阈值
- Elevation mask：高度角掩码
- GNSS systems：默认 `G`（GPS），可填 `C`（BDS）或 `G,C`（GPS+BDS）

按钮：
- Run：开始连续定位
- Plot：显示误差/DOP 与轨迹散点图
- Replay：轨迹回放

## 输出结果
- `results.csv`：位置、DOP、误差时间序列
- 使用 `--save-dir` 生成的图像文件

## 项目结构
```
src/
  analysis.py
  atmosphere.py
  constants.py
  coords.py
  data_inventory.py
  experiment_modules.py
  models.py
  pipeline.py
  plotting.py
  positioning.py
  redundancy.py
  rinex_io.py
  rinex_nav.py
  rinex_obs.py
  satellite.py
  time_utils.py
scripts/
  gui_app.py
  inspect_rinex.py
  plot_results.py
  run_batch.py
  run_continuous.py
  run_redundancy_tests.py
  run_spp.py
  summarize_urban_nav.py
  train_error_model.py
reports/
  requirements_audit.md
  final_design_report.md
  final_experiment_report.md
  final_test_report.md
  final_ai_extension_report.md
  project_explanation_guide.md
```

## 实验模块封装
`src/experiment_modules.py` 将底层算法按实验要求封装为 5 个高层模块：
- 模块1 `RinexDataModule`：RINEX 观测/导航解析、文件校验、基础观测预处理。
- 模块2 `SatelliteCorrectionModule`：广播星历卫星位置、钟差、地球自转、对流层和电离层改正。
- 模块3 `SinglePointPositioningModule`：可见卫星筛选、迭代最小二乘定位、PDOP/GDOP 输出。
- 模块4 `ContinuousAnalysisModule`：连续定位误差统计、CSV 导出、误差/DOP 与轨迹散点图生成。
- 模块5 `SoftwareSystemModule`：整合“数据输入 -> 预处理 -> 解算 -> 分析 -> 输出”的完整自动化流程。

## 说明与限制
- 当前已完成 GPS、BDS 与 GPS+BDS 联合解算验证。TWTF 混合数据全日 BDS-only 3D RMS 为 7.488 m，GPS+BDS 3D RMS 为 6.029 m。
- 附加题已实现线性回归误差补偿。当前测试集 3D RMS 从 5.716 m 降至 3.373 m。
- 后续可继续加入 CN0/SNR 权重、更多站点/多日数据和随机森林等非线性模型。
