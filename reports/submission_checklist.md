# 提交前整理清单

## 1. 推荐提交文件

建议直接提交已生成的压缩包：

```text
dist/beidou_positioning_submission.zip
```

该压缩包由以下命令生成：

```bash
python3 scripts/create_submission_package.py \
  --output dist/beidou_positioning_submission.zip \
  --manifest dist/submission_manifest.txt
```

当前压缩包大小约 17 MB，包含 83 个文件。

## 2. 压缩包包含内容

- 源码：`src/`
- 脚本：`scripts/`
- 自动化测试：`tests/`
- 依赖说明：`requirements.txt`
- 项目说明：`README.md`
- 实验题目文档：`MinerU_markdown_北斗定位解算全流程软件系统开发实验题目_2049408313226227712.md`
- 测试数据：`data/sample/` 和 `data/datasets/*/rinex/`
- 数据说明：`data/README.md`, `data/manifests/datasets.csv`, 各数据集 `metadata.json`
- 结果文件：`results/summary.csv`, `results/datasets/*`, `results/ml_compensation/*`
- 图片：误差/DOP/卫星数曲线、轨迹图、GUI 截图、附加题补偿对比图
- 报告：
  - `reports/requirements_audit.md`
  - `reports/final_design_report.md`
  - `reports/final_experiment_report.md`
  - `reports/final_test_report.md`
  - `reports/final_ai_extension_report.md`

## 3. 不建议提交内容

以下内容不应放入最终提交压缩包：

- `.venv/`：本地虚拟环境，体积大且可通过 `requirements.txt` 重建。
- `.git/`：版本控制内部目录。
- `__pycache__/`：Python 缓存。
- `.DS_Store`：macOS 系统文件。
- `data/datasets/*/raw/*.gz`：原始压缩下载文件，已保留解压后的 RINEX 文件，重复且占空间。
- 临时文件、IDE 缓存、系统缓存。

## 4. 验收时建议展示顺序

1. 打开 `README.md`，说明项目功能与运行方式。
2. 展示 `reports/requirements_audit.md`，说明实验要求逐项完成情况。
3. 展示 `reports/final_design_report.md`，说明软件架构和五模块设计。
4. 运行：

```bash
python3 scripts/inspect_rinex.py
python3 scripts/run_continuous.py --max-epochs 10 --csv /tmp/demo_results.csv
python3 scripts/gui_app.py
```

5. 展示 `reports/final_test_report.md` 中的多数据集结果和图。
6. 如需展示附加题，运行：

```bash
python3 scripts/run_batch.py --output results/summary.csv
python3 scripts/train_error_model.py --output-dir results/ml_compensation
```

并展示 `reports/final_ai_extension_report.md`。

## 5. 最终验证命令

提交前建议运行：

```bash
MPLCONFIGDIR=/private/tmp/mplconfig XDG_CACHE_HOME=/private/tmp/xdgcache \
  .venv/bin/python -m unittest tests.test_experiment_modules -v

PYTHONPYCACHEPREFIX=/private/tmp/beidou_pycache \
  .venv/bin/python -m compileall src scripts tests
```

当前项目最近一次验证结果：15 个单元测试通过，源码编译通过。
