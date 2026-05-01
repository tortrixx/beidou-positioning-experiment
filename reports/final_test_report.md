# 北斗定位解算软件测试报告

## 1. 测试环境

- 操作系统：macOS 本地开发环境
- Python：3.9.6
- 运行环境：项目 `.venv`
- 主要依赖：PyQt5、matplotlib
- 核心算法：手写实现，未调用第三方定位库

## 2. 测试数据

| 数据集 | 类型 | 观测文件 | 导航文件 | 用途 |
| --- | --- | --- | --- | --- |
| BJFS 2026-117 | GPS RINEX 2.11 | `data/sample/bjfs1170.26o` | `data/sample/brdc1170.26n` | 默认样例与 GPS 基准测试 |
| DAEJ 2026-117 | GPS RINEX 2.11 | `data/datasets/daej_2026_117_gps/rinex/daej1170.26o` | `data/datasets/daej_2026_117_gps/rinex/brdc1170.26n` | 多站点 GPS 测试 |
| HKSL 2026-117 | GPS RINEX 2.11 | `data/datasets/hksl_2026_117_gps/rinex/hksl1170.26o` | `data/datasets/hksl_2026_117_gps/rinex/brdc1170.26n` | 多站点 GPS 测试 |
| TWTF 2026-117 | RINEX 3 Mixed | `data/datasets/twtf_2026_117_mixed/rinex/TWTF00TWN_R_20261170000_01D_30S_MO.rnx` | `data/datasets/twtf_2026_117_mixed/rinex/BRDM00DLR_S_20261170000_01D_MN.rnx` | RINEX 3、BDS、GPS+BDS 测试 |

## 3. 功能测试结果

| 测试项 | 结果 | 说明 |
| --- | --- | --- |
| 默认 RINEX 检查命令 | 通过 | `python scripts/inspect_rinex.py` 可直接读取样例数据 |
| 单历元 SPP | 通过 | 可输出 ECEF、BLH、钟差、使用卫星数、PDOP/GDOP |
| 连续定位 | 通过 | 逐历元输出 CSV 与统计指标 |
| 参数校验 | 通过 | `step=0` 会抛出清晰错误，避免除零 |
| 绘图保存 | 通过 | Matplotlib 可用时保存误差/DOP/卫星数曲线与轨迹图 |
| RINEX 3 混合观测解析 | 通过 | 识别 GPS、BDS、Galileo 等卫星观测 |
| BDS 电离层参数解析 | 通过 | 解析 `BDSA/BDSB` 并用于 Klobuchar 改正 |
| BDS-only 解算 | 通过 | TWTF 全日 2880 历元稳定输出 |
| GPS+BDS 联合解算 | 通过 | 每系统钟差模型稳定输出 |
| GUI 主界面 | 通过 | 支持数据导入、参数设置、实时显示、绘图和回放 |

## 4. 定位精度测试

| 数据集 | 系统 | 解算历元 | 水平 RMS/均值/最大值 (m) | 三维 RMS/均值/最大值 (m) | 平均卫星数 | PDOP 均值 |
| --- | --- | ---: | --- | --- | ---: | ---: |
| BJFS | GPS | 2880 | 1.658 / 1.378 / 4.758 | 4.253 / 3.517 / 10.121 | 8.57 | 3.596 |
| DAEJ | GPS | 2880 | 1.948 / 1.491 / 7.122 | 3.904 / 3.280 / 9.308 | 8.36 | 3.670 |
| HKSL | GPS | 2880 | 3.895 / 3.362 / 7.864 | 5.265 / 4.685 / 13.005 | 8.94 | 3.684 |
| TWTF | GPS | 2880 | 5.779 / 4.434 / 12.705 | 6.598 / 5.531 / 14.513 | 8.88 | 3.701 |
| TWTF | BDS | 2880 | 6.015 / 4.072 / 53.206 | 7.488 / 6.055 / 59.987 | 7.48 | 5.936 |
| TWTF | GPS+BDS | 2880 | 5.347 / 3.979 / 11.681 | 6.029 / 5.175 / 12.411 | 16.36 | 2.815 |

## 5. 图表结果

UrbanNav BDS 误差、PDOP 与卫星数曲线：

![UrbanNav BDS error dop](latex/figures/urban_nav_bds_final/error_dop.png)

UrbanNav BDS 轨迹散点图：

![UrbanNav BDS trajectory](latex/figures/urban_nav_bds_final/trajectory.png)

TWTF BDS-only 误差、PDOP 与卫星数曲线：

![TWTF BDS error dop](latex/figures/twtf_bds_final/error_dop.png)

TWTF GPS+BDS 误差、PDOP 与卫星数曲线：

![TWTF GPS BDS error dop](latex/figures/twtf_gps_bds_final/error_dop.png)

GUI 主界面截图：

![GUI](latex/figures/gui_main_window.png)

## 6. 问题与修复记录

| 问题 | 修复 |
| --- | --- |
| 默认数据路径不一致导致脚本开箱失败 | 默认路径统一到 `data/sample/` |
| `step=0` 导致除零 | 在 pipeline 入口校验 `step >= 1` |
| Matplotlib 缺失时仍提示保存成功 | 绘图函数返回保存状态，脚本检查后再输出成功 |
| RINEX 3 BDS 电离层参数未解析 | 增加 `IONOSPHERIC CORR` 解析和 BDSA/BDSB 选择 |
| BDS 时间转换方向错误 | 修正 GPST 到 BDT 的转换方向 |
| GPS+BDS 共用一个接收机钟差导致混合解偏差 | 扩展状态向量，为每个系统估计独立钟差 |
| 新结果目录不存在时 CSV 写入失败 | `write_csv()` 自动创建父目录 |
| 缺少解算残差诊断 | `PositionSolution` 与 CSV 增加残差 RMS/Max |

## 7. 自动化验证

执行命令：

```bash
MPLCONFIGDIR=/private/tmp/mplconfig XDG_CACHE_HOME=/private/tmp/xdgcache \
  .venv/bin/python -m unittest tests.test_experiment_modules -v
```

当前单元测试覆盖 RINEX 解析、参数校验、绘图保存、五模块封装、BDS 解析、BDS-only 解算、GPS+BDS 联合解算、CSV 残差诊断等。

## 8. 测试结论

测试结果表明：软件可完成实验要求的五个基础模块，在 GPS、BDS、GPS+BDS 数据上均能稳定运行并输出米级定位结果。BDS-only 的最大误差明显高于 GPS+BDS，主要与 BDS 单系统可用卫星数量、几何构型和个别历元 PDOP 较大有关。GPS+BDS 联合后平均卫星数提升至 16.36，PDOP 均值降低至 2.815，整体精度优于单 BDS。
