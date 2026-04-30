# 北斗定位解算实验

本项目基于 RINEX 观测与导航数据实现 GNSS 单点定位（SPP）全流程软件。当前已验证 GPS RINEX 2.11、RINEX 3 混合数据、BDS 单系统与 GPS+BDS 联合解算。代码采用模块化设计，包含解析、卫星位置/钟差、SPP 解算、连续定位、误差分析、可视化以及 PyQt GUI。

## 功能特性
- RINEX 2.11 与 RINEX 3 混合观测/导航解析
- 卫星位置与钟差修正
- 对流层（Saastamoinen）与 GPS/BDS Klobuchar 电离层改正
- GPS、BDS 与 GPS+BDS 联合迭代最小二乘 SPP
- 高度角加权最小二乘、残差门限剔除与残差诊断
- 连续定位与 RMS/均值/最大误差统计
- CSV 导出与绘图（误差/DOP、轨迹）
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
- Plot：显示误差/DOP 与轨迹图
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
  experiment_modules.py
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

## 实验模块封装
`src/experiment_modules.py` 将底层算法按实验要求封装为 5 个高层模块：
- 模块1 `RinexDataModule`：RINEX 观测/导航解析、文件校验、基础观测预处理。
- 模块2 `SatelliteCorrectionModule`：广播星历卫星位置、钟差、地球自转、对流层和电离层改正。
- 模块3 `SinglePointPositioningModule`：可见卫星筛选、迭代最小二乘定位、PDOP/GDOP 输出。
- 模块4 `ContinuousAnalysisModule`：连续定位误差统计、CSV 导出、误差/DOP 与轨迹图生成。
- 模块5 `SoftwareSystemModule`：整合“数据输入 -> 预处理 -> 解算 -> 分析 -> 输出”的完整自动化流程。

## 说明与限制
- 当前已完成 GPS、BDS 与 GPS+BDS 联合解算验证。TWTF 混合数据全日 BDS-only 3D RMS 为 7.488 m，GPS+BDS 3D RMS 为 6.029 m。
- 附加题已实现线性回归误差补偿。当前测试集 3D RMS 从 5.716 m 降至 3.373 m。
- 后续可继续加入 CN0/SNR 权重、更多站点/多日数据和随机森林等非线性模型。
