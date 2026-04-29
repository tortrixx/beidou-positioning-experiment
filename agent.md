# 项目续作计划

本计划用于在当前实现基础上继续完成北斗定位实验项目，记录已完成内容、缺口与后续步骤。

## 当前状态（已完成）
- SPP 主流程完成：RINEX 解析 -> 卫星位置/钟差 -> 最小二乘解算 -> 连续定位 -> 分析 -> CSV/绘图。
- GUI 完成：数据导入、参数设置、实时位置显示、绘图与轨迹回放。
- 已测试单组数据（bjfs1170.26o / brdc1170.26n），结果保存至 results.csv。
- README 与部分实验报告已起草。

## 已知限制
- 仅测试一组数据；实验要求多组数据与测试报告。
- 暂无 BDS 数据，尚未完成多系统验证。
- 报告未完整填写（设计报告、实验报告、测试报告）。

## 计划（详细步骤）

### 步骤 1：收集额外数据集
1) 获取至少 2 组 RINEX 观测/导航数据。
2) 优先选择不同日期或不同站点。
3) 放入项目根目录或 data/ 目录。
4) 记录数据集元信息（日期、站点、时长）。

### 步骤 2：批量解算与结果整理
1) 对每组数据运行连续解算：
   - python3 scripts/run_continuous.py --obs <obs> --nav <nav> --csv <out.csv>
2) 生成图表：
   - python3 scripts/plot_results.py --csv <out.csv> --save-dir <dir>
3) 记录关键指标：解算历元数、RMS/均值/最大值（水平+三维）、PDOP 范围。
4) 输出保存到 data/<dataset_name>/ 或 results/。

### 步骤 3：编写测试报告
1) 根据真实输出填写 reports/test_report_template.md。
2) 每组数据至少包含：
   - 环境（OS、Python、依赖）
   - 数据集描述
   - 指标表格
   - 图表（误差/DOP、轨迹）
3) 记录问题与修复过程（如有）。

### 步骤 4：完成设计报告
1) 填写 reports/design_report_template.md：
   - 架构图与数据流
   - 模块职责
   - 数据结构（ObsHeader、NavRecord、PositionSolution）
2) 需要时补充流程图。

### 步骤 5：完成实验报告
1) 将 reports/experiment_report_partial.md 扩展为完整版。
2) 补充：
   - 关键算法与公式说明
   - 误差来源与分析
   - GUI 与图表截图
   - 改进思路

### 可选步骤 6：BDS/多系统验证
1) 获取 RINEX 3 的 BDS 观测/导航数据。
2) 用 --systems G,C 运行并对比结果。
3) 记录差异与修复。

## 待更新文件
- README.md（如需完善）
- reports/design_report_template.md（填写）
- reports/experiment_report_partial.md（扩展）
- reports/test_report_template.md（填写）

## 输出建议结构
- data/<dataset_name>/
  - obs/nav
  - outputs（csv、plots）
- reports/
  - final_design_report.md
  - final_experiment_report.md
  - final_test_report.md
