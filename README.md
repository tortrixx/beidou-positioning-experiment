# 北斗定位解算实验

本项目基于 RINEX 观测与导航数据实现 GNSS 单点定位（SPP）全流程软件。当前验证数据为 GPS RINEX 2.11。代码采用模块化设计，包含解析、卫星位置/钟差、SPP 解算、连续定位、误差分析、可视化以及 PyQt GUI。

## 功能特性
- RINEX 2.11 观测与导航解析
- 卫星位置与钟差修正
- 对流层（Saastamoinen）与电离层（Klobuchar）改正
- 迭代最小二乘 SPP
- 连续定位与 RMS/均值/最大误差统计
- CSV 导出与绘图（误差/DOP、轨迹）
- PyQt GUI 实时显示与轨迹回放

## 依赖环境
- Python 3.9+
- PyQt5
- matplotlib

如需安装依赖：
```bash

python3 -m pip install PyQt5 matplotlib
```

## 数据说明
将 RINEX 文件放在项目根目录或在命令行中传入路径：
- 观测文件：`*.o` 或 `*.obs`
- 导航文件：`*.n` 或 `*.nav`

本仓库示例数据：
- `bjfs1170.26o`
- `brdc1170.26n`

## 快速开始（命令行）
```bash
# 激活环境（mac）
source .venv/bin/activate

# 激活环境（Windows）
.venv\Scripts\activate
```

单历元解算：
```bash
python3 scripts/run_spp.py --obs bjfs1170.26o --nav brdc1170.26n --epoch 0
```

连续解算并导出 CSV：
```bash
python3 scripts/run_continuous.py --obs bjfs1170.26o --nav brdc1170.26n
```

从 CSV 生成图表：
```bash
python3 scripts/plot_results.py --csv results.csv --save-dir .
```

查看 RINEX 头部信息：
```bash
python3 scripts/inspect_rinex.py --obs bjfs1170.26o --nav brdc1170.26n
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
- GNSS systems：默认 `G`（GPS）

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

## 说明与限制
- 当前验证仅使用 GPS RINEX 2.11 数据。多系统支持已预留，但 BDS 数据尚未在本仓库验证。
- 完整实验需使用多组数据并记录测试结果。
