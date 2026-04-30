# 附加题：基于线性回归的定位误差预测与补偿报告

## 1. 任务目标

附加题要求结合 AI 技术，使用实验中生成的连续定位结果构建误差预测模型，并将预测误差用于定位结果补偿。本项目选择线性回归模型，原因是：

- 模型结构简单，便于解释；
- 不需要额外安装复杂机器学习库；
- 与当前 CSV 特征结构匹配，适合先验证误差补偿流程；
- 可作为后续随机森林等非线性模型的基准。

## 2. 数据准备

本次使用 6 组连续定位结果，共 17280 条样本：

| 数据集 | 系统 | 样本数 |
| --- | --- | ---: |
| BJFS | GPS | 2880 |
| DAEJ | GPS | 2880 |
| HKSL | GPS | 2880 |
| TWTF | GPS | 2880 |
| TWTF | BDS | 2880 |
| TWTF | GPS+BDS | 2880 |

数据来源为各数据集的 `results.csv`。汇总文件保存为：

```text
results/summary.csv
```

训练脚本按 70% / 30% 划分训练集和测试集：

- 训练集：12096 条；
- 测试集：5184 条。

## 3. 特征与标签设计

### 3.1 输入特征

模型输入特征来自定位解算结果：

| 特征 | 含义 |
| --- | --- |
| `used_sats` | 当前历元使用卫星数 |
| `pdop` | 位置精度因子 |
| `gdop` | 几何精度因子 |
| `residual_rms_m` | 后验残差 RMS |
| `residual_max_m` | 后验最大残差 |
| `clock_bias_m` | 接收机钟差估计 |
| `h` | 解算高程 |

这些特征与定位误差存在物理联系。例如，卫星几何构型会影响 DOP，残差反映观测噪声和模型误差，高程和钟差可间接反映解算状态。

### 3.2 预测标签

模型分别预测 ENU 三个方向的定位误差：

```text
east, north, up
```

补偿时，将模型预测的误差从原始解算误差中扣除：

```text
comp_error = original_error - predicted_error
```

再计算补偿后的水平误差和三维误差。

## 4. 模型实现

实现文件：

```text
src/ml_compensation.py
scripts/train_error_model.py
```

模型采用标准化特征后的岭回归形式：

```text
y = beta0 + beta1*x1 + beta2*x2 + ... + betaN*xN
```

其中 `east`、`north`、`up` 三个方向分别训练一组回归系数。法方程为：

```text
(X^T X + lambda I) beta = X^T y
```

线性方程求解仍使用项目内手写高斯消元，未调用第三方机器学习库。

## 5. 运行方法

先确保各数据集已生成 `results.csv`，然后运行：

```bash
python3 scripts/run_batch.py --output results/summary.csv
python3 scripts/train_error_model.py --output-dir results/ml_compensation
```

输出文件：

| 文件 | 说明 |
| --- | --- |
| `results/ml_compensation/linear_model.json` | 训练得到的模型参数 |
| `results/ml_compensation/metrics.csv` | 训练集/测试集补偿前后指标 |
| `results/ml_compensation/test_predictions.csv` | 测试集逐样本预测与补偿结果 |
| `results/ml_compensation/compensation_comparison.png` | 补偿前后 RMS 对比图 |

## 6. 实验结果

| 数据划分 | 原始水平 RMS (m) | 补偿后水平 RMS (m) | 原始 3D RMS (m) | 补偿后 3D RMS (m) | 3D 改善率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 训练集 | 4.472 | 2.613 | 5.736 | 3.416 | 40.44% |
| 测试集 | 4.464 | 2.585 | 5.716 | 3.373 | 40.99% |

补偿前后 RMS 对比图：

![误差补偿对比](../results/ml_compensation/compensation_comparison.png)

## 7. 效果分析

测试集三维 RMS 从 5.716 m 降至 3.373 m，改善率约 40.99%。水平 RMS 从 4.464 m 降至 2.585 m，改善率约 42.08%。这说明 DOP、卫星数、残差和高程等特征确实能够刻画一部分系统性误差。

线性模型的优点是稳定、可解释、训练速度快，不需要大量依赖。它的不足是只能表达线性关系，无法充分建模多路径、遮挡、卫星高度角非线性影响和不同站点环境差异。

## 8. 集成方式

当前附加题以脚本方式集成进原有软件流程：

```text
连续定位 results.csv -> 特征提取 -> 线性模型预测 east/north/up 误差 -> 输出补偿后误差指标
```

模型参数保存为 JSON，后续可以在 GUI 或连续定位 pipeline 中加载该模型，对实时定位结果进行误差预测与补偿。

## 9. 改进方向

后续可继续优化：

1. 加入 CN0/SNR、平均高度角、最大残差卫星等更丰富特征；
2. 使用随机森林或梯度提升树捕捉非线性关系；
3. 按站点、系统类型分别训练模型；
4. 使用跨站点留一验证，避免模型只学习站点固定偏差；
5. 将模型加载集成到 GUI，实时显示补偿前后定位结果。

## 10. 结论

本附加题完成了从数据准备、特征提取、模型训练、误差补偿到效果验证的完整流程。线性回归模型在测试集上显著降低了定位误差，证明 AI 技术可以作为传统 GNSS 单点定位算法的后处理增强手段。
