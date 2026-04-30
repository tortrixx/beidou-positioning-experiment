# 北斗定位解算实验要求逐项对照审查

说明：本审查仅覆盖基础题 60 分部分，不包含附加题机器学习误差预测与补偿。

## 1. 模块完成度总览

| 实验要求 | 对应实现 | 完成情况 | 说明 |
| --- | --- | --- | --- |
| 模块1 RINEX 数据解析 | `src/rinex_obs.py`, `src/rinex_nav.py`, `RinexDataModule` | 已完成 | 支持 RINEX 2.11 GPS 与 RINEX 3 混合 OBS/NAV；观测类型、伪距、SNR、广播星历参数均被解析到数据结构中 |
| 模块1 数据预处理 | `RinexDataModule.valid_observations`, `positioning.single_point_position`, `satellite.select_ephemeris` | 已完成 | 剔除无效伪距、跳过不健康卫星、按高度角筛选、按历元组织多卫星观测 |
| 模块2 卫星位置与钟差 | `src/satellite.py` | 已完成 | 手写广播星历轨道计算、摄动改正、地球自转改正、钟差多项式与相对论改正 |
| 模块2 传播延迟修正 | `src/atmosphere.py`, `src/positioning.py` | 已完成 | Saastamoinen 对流层改正；GPS/BDS Klobuchar 电离层改正；输出修正伪距用于解算 |
| 模块3 SPP 核心算法 | `src/positioning.py`, `SinglePointPositioningModule` | 已完成并增强 | 迭代最小二乘、ECEF/BLH 输出、PDOP/GDOP、GPS+BDS 每系统钟差、高度角加权、残差诊断 |
| 模块4 连续定位与分析 | `src/pipeline.py`, `src/analysis.py`, `ContinuousAnalysisModule` | 已完成 | 逐历元解算，CSV 输出，RMS/均值/最大误差统计 |
| 模块4 结果可视化 | `src/plotting.py`, `scripts/plot_results.py` | 已完成 | 误差曲线、PDOP 曲线、可用卫星数曲线、经纬度轨迹图 |
| 模块5 系统整合 | `src/experiment_modules.py`, `scripts/run_continuous.py`, `scripts/run_spp.py` | 已完成 | 五个高层模块封装；CLI 自动化运行完整流程 |
| 模块5 GUI | `scripts/gui_app.py` | 已完成 | PyQt 支持数据导入、参数设置、实时定位显示、误差曲线查看、轨迹回放 |
| 多组数据测试与报告 | `data/datasets`, `results/datasets`, `reports/final_test_report.md` | 已完成 | BJFS、DAEJ、HKSL、TWTF 多组数据已测试并生成 CSV/图片 |

## 2. 逐项细化审查

### 模块1：RINEX 数据解析

- 解析观测文件与导航文件：已完成。
- 提取卫星编号：`ObsEpoch.sat_obs` 以 `G01`、`C01` 等 PRN 为键保存。
- 提取伪距观测值：`_choose_pseudorange()` 支持 `C1/P1/P2/C1C/C2I/C6I/C7I` 等。
- 提取信噪比：RINEX 观测类型中的 `S1/S2` 等会保留在每颗卫星观测字典中。
- 提取广播星历参数：`NavRecord` 保存 `sqrt_a/e/i0/omega0/omega_dot/af0/af1/af2/tgd` 等参数。
- 数据预处理：无效伪距范围剔除、不健康星历剔除、高度角筛选、同历元多星对齐均已完成。

### 模块2：卫星位置与钟差计算

- ECEF 坐标计算：已完成 GPS/BDS 广播星历位置计算。
- 轨道摄动修正：已使用 `cuc/cus/crc/crs/cic/cis` 改正。
- BDS 支持：BDS GEO C01-C05 使用专门转换；BDS GPST/BDT 转换已修正。
- 钟差修正：包含 `af0 + af1*t + af2*t^2` 与相对论项。
- 传播延迟修正：Saastamoinen 对流层与 GPS/BDS Klobuchar 电离层已接入。

### 模块3：单点定位解算

- 可见卫星筛选：按系统、伪距有效性、高度角、星历健康状态筛选。
- DOP 计算：由法方程协方差矩阵计算 PDOP/GDOP。
- 迭代最小二乘：核心线性方程手写求解，无第三方定位库。
- GPS+BDS 联合：对每个系统设置独立接收机钟差未知数，避免多系统钟差混淆。
- 稳健性增强：残差门限剔除、接收机状态合理性检查、高度角加权最小二乘、残差 RMS/Max 输出。
- BLH 输出：`coords.ecef_to_geodetic()` 完成 ECEF 到经纬高转换。

### 模块4：连续定位与结果分析

- 连续定位：`run_continuous_pipeline()` 逐历元循环，支持 `step` 与 `max_epochs`。
- 时间序列输出：CSV 包含时间、ECEF、BLH、钟差、卫星数、PDOP/GDOP、残差、ENU 误差。
- 精度评估：计算水平与三维 RMS、均值、最大误差。
- 关系分析：报告中统计卫星数、PDOP、残差与误差关系。
- 可视化：保存误差/DOP/卫星数曲线和轨迹图。

### 模块5：软件系统整合与测试

- 模块化架构：`src/experiment_modules.py` 封装 5 个实验模块。
- CLI：`inspect_rinex.py`、`run_spp.py`、`run_continuous.py`、`plot_results.py` 可独立运行。
- GUI：支持文件选择、迭代次数/阈值/高度角/系统参数、实时结果、绘图与回放。
- 多组测试：已完成 GPS、BDS、GPS+BDS 多数据集测试。
- 文档：正式设计报告、实验报告、测试报告已补齐。

## 3. 仍可继续优化但不影响基础题验收的内容

- 使用 CN0/SNR 构建观测权重，而不仅使用高度角权重。
- 统计每颗卫星长期残差，形成自动黑名单或鲁棒估计。
- 扩展更多 BDS 站点和多日数据验证。
- 附加题机器学习误差预测与补偿尚未纳入本轮。
