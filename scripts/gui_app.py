from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from experiment_modules import SoftwareSystemModule
from plotting import plot_error_and_dop, plot_trajectory


def _configure_chinese_font() -> None:
    try:
        import matplotlib
        import matplotlib.font_manager as fm
    except ImportError:
        return

    candidates = [
        "Arial Unicode MS",
        "PingFang SC",
        "Heiti SC",
        "Heiti TC",
        "Songti SC",
        "Noto Sans CJK SC",
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Zen Hei",
    ]
    installed = {font.name for font in fm.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            matplotlib.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            matplotlib.rcParams["axes.unicode_minus"] = False
            return


class Worker(QObject):
    finished = pyqtSignal(object, object, object, object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, int, object)

    def __init__(
        self,
        obs_path: str,
        nav_path: str,
        step: int,
        max_epochs: int,
        max_iter: int,
        err_thresh: float,
        elev_mask: float,
        systems: Iterable[str],
        csv_path: str,
    ) -> None:
        super().__init__()
        self.obs_path = obs_path
        self.nav_path = nav_path
        self.step = step
        self.max_epochs = max_epochs
        self.max_iter = max_iter
        self.err_thresh = err_thresh
        self.elev_mask = elev_mask
        self.systems = tuple(systems)
        self.csv_path = csv_path

    def run(self) -> None:
        try:
            def _progress(epoch_idx: int, count: int, sol) -> None:
                self.progress.emit(epoch_idx, count, sol)

            result = SoftwareSystemModule().run(
                self.obs_path,
                self.nav_path,
                step=self.step,
                max_epochs=self.max_epochs,
                max_iter=self.max_iter,
                error_thresh_m=self.err_thresh,
                elev_mask_deg=self.elev_mask,
                systems=self.systems,
                output_csv=self.csv_path,
                progress=_progress,
            )
            self.finished.emit(result.obs_header, result.solutions, result.errors, result.stats)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("北斗定位解算实验系统")
        self.resize(640, 520)

        self.obs_edit = QLineEdit("data/sample/bjfs1170.26o")
        self.nav_edit = QLineEdit("data/sample/brdc1170.26n")
        self.csv_edit = QLineEdit("results.csv")

        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 1000)
        self.step_spin.setValue(1)

        self.max_epochs_spin = QSpinBox()
        self.max_epochs_spin.setRange(0, 100000)
        self.max_epochs_spin.setValue(0)

        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 50)
        self.max_iter_spin.setValue(8)

        self.err_spin = QDoubleSpinBox()
        self.err_spin.setRange(0.001, 100.0)
        self.err_spin.setDecimals(3)
        self.err_spin.setSingleStep(0.01)
        self.err_spin.setValue(0.01)

        self.elev_spin = QDoubleSpinBox()
        self.elev_spin.setRange(0.0, 30.0)
        self.elev_spin.setSingleStep(1.0)
        self.elev_spin.setValue(10.0)

        self.systems_edit = QLineEdit("G")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        browse_obs = QPushButton("浏览...")
        browse_nav = QPushButton("浏览...")
        browse_csv = QPushButton("浏览...")
        browse_obs.clicked.connect(lambda: self._browse(self.obs_edit, "观测文件 (*.o *.obs *.rnx *.gz);;所有文件 (*)"))
        browse_nav.clicked.connect(lambda: self._browse(self.nav_edit, "导航文件 (*.n *.nav *.rnx *.gz);;所有文件 (*)"))
        browse_csv.clicked.connect(lambda: self._browse_save(self.csv_edit, "CSV 文件 (*.csv);;所有文件 (*)"))

        self.run_btn = QPushButton("开始解算")
        self.plot_btn = QPushButton("绘制图像")
        self.replay_btn = QPushButton("轨迹回放")
        self.run_btn.clicked.connect(self._start_run)
        self.plot_btn.clicked.connect(self._plot)
        self.replay_btn.clicked.connect(self._replay)
        self.plot_btn.setEnabled(False)
        self.replay_btn.setEnabled(False)

        form = QFormLayout()
        form.addRow("观测文件", self._row(self.obs_edit, browse_obs))
        form.addRow("导航文件", self._row(self.nav_edit, browse_nav))
        form.addRow("输出 CSV", self._row(self.csv_edit, browse_csv))
        form.addRow("处理步长", self.step_spin)
        form.addRow("最大历元数（0=全部）", self.max_epochs_spin)
        form.addRow("最大迭代次数", self.max_iter_spin)
        form.addRow("误差阈值 (m)", self.err_spin)
        form.addRow("高度角截止角 (deg)", self.elev_spin)
        form.addRow("GNSS 系统", self.systems_edit)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.plot_btn)
        btn_row.addWidget(self.replay_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("实时定位结果"))
        self.pos_label = QLabel("纬度：-  经度：-  高程：-")
        self.stat_label = QLabel("参与解算卫星数：-  PDOP：-")
        layout.addWidget(self.pos_label)
        layout.addWidget(self.stat_label)
        layout.addWidget(QLabel("运行日志"))
        layout.addWidget(self.log_view)
        self.setLayout(layout)

        self._solutions = []
        self._errors = []
        self._last_log_count = 0
        self.worker = None
        self._anim = None
        self._replay_dialog = None
        self._replay_timer = None
        self._replay_index = 0

    def _row(self, edit: QLineEdit, button: QPushButton) -> QWidget:
        box = QHBoxLayout()
        box.addWidget(edit)
        box.addWidget(button)
        wrapper = QWidget()
        wrapper.setLayout(box)
        return wrapper

    def _browse(self, target: QLineEdit, pattern: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", pattern)
        if path:
            target.setText(path)

    def _browse_save(self, target: QLineEdit, pattern: str) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", target.text(), pattern)
        if path:
            target.setText(path)

    def _append_log(self, text: str) -> None:
        self.log_view.append(text)

    def _start_run(self) -> None:
        self.run_btn.setEnabled(False)
        self.plot_btn.setEnabled(False)
        self.replay_btn.setEnabled(False)
        self._last_log_count = 0
        self._append_log("正在解算...")

        systems = [s.strip() for s in self.systems_edit.text().split(",") if s.strip()]

        self.worker = Worker(
            self.obs_edit.text(),
            self.nav_edit.text(),
            self.step_spin.value(),
            self.max_epochs_spin.value(),
            self.max_iter_spin.value(),
            self.err_spin.value(),
            self.elev_spin.value(),
            systems,
            self.csv_edit.text(),
        )
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_finished(self, obs_header, solutions, errors, stats) -> None:
        self._solutions = solutions
        self._errors = errors
        if not solutions:
            skip_reasons = stats.get("skip_reasons", {})
            reason_text = "; ".join(f"{reason}: {count}" for reason, count in skip_reasons.items())
            self._append_log(
                "没有有效定位解。"
                f"处理历元数：{stats.get('processed_epochs', 0)}，"
                f"跳过历元数：{stats.get('skipped_epochs', 0)}"
            )
            if reason_text:
                self._append_log(f"跳过原因：{reason_text}")
            self.run_btn.setEnabled(True)
            self.plot_btn.setEnabled(False)
            self.replay_btn.setEnabled(False)
            self.worker = None
            self.thread.quit()
            return
        self._append_log(
            f"有效解数量：{len(solutions)} | "
            f"水平误差 RMS/均值/最大值：{stats['horiz_rms']:.3f}/{stats['horiz_mean']:.3f}/{stats['horiz_max']:.3f} | "
            f"三维误差 RMS/均值/最大值：{stats['3d_rms']:.3f}/{stats['3d_mean']:.3f}/{stats['3d_max']:.3f}"
        )
        self.run_btn.setEnabled(True)
        self.plot_btn.setEnabled(True)
        self.replay_btn.setEnabled(True)
        self.worker = None
        self.thread.quit()

    def _on_failed(self, message: str) -> None:
        self._append_log(f"错误：{message}")
        self.run_btn.setEnabled(True)
        self.plot_btn.setEnabled(False)
        self.replay_btn.setEnabled(False)
        self.worker = None
        self.thread.quit()

    def _on_progress(self, epoch_idx: int, count: int, sol) -> None:
        self.pos_label.setText(
            f"纬度：{sol.position_blh[0]:.6f}  经度：{sol.position_blh[1]:.6f}  高程：{sol.position_blh[2]:.2f}"
        )
        self.stat_label.setText(f"参与解算卫星数：{len(sol.used_sats)}  PDOP：{sol.pdop:.3f}")
        if count - self._last_log_count >= 50:
            self._append_log(f"历元 {epoch_idx} | 有效解 {count}")
            self._last_log_count = count

    def _plot(self) -> None:
        if not self._solutions:
            return
        times = list(range(len(self._solutions)))
        horiz = [err["horiz"] for err in self._errors]
        three_d = [err["three_d"] for err in self._errors]
        pdop = [sol.pdop for sol in self._solutions]
        sat_counts = [len(sol.used_sats) for sol in self._solutions]
        lat = [sol.position_blh[0] for sol in self._solutions]
        lon = [sol.position_blh[1] for sol in self._solutions]
        plot_error_and_dop(times, horiz, three_d, pdop, sat_counts=sat_counts)
        plot_trajectory(lat, lon)

    def _replay(self) -> None:
        if not self._solutions:
            return
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
        except ImportError:
            self._append_log("未安装 matplotlib，无法进行轨迹回放")
            return
        _configure_chinese_font()

        lat = [sol.position_blh[0] for sol in self._solutions]
        lon = [sol.position_blh[1] for sol in self._solutions]
        if not lat or not lon:
            return

        if self._replay_dialog is not None:
            self._replay_dialog.close()
            self._replay_dialog = None
        if self._replay_timer is not None:
            self._replay_timer.stop()
            self._replay_timer = None

        dialog = QDialog(self)
        dialog.setWindowTitle("轨迹回放")
        dialog.resize(640, 640)
        layout = QVBoxLayout()

        fig = Figure(figsize=(6, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_xlabel("经度 (deg)")
        ax.set_ylabel("纬度 (deg)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_aspect("equal", adjustable="box")

        min_lon = min(lon)
        max_lon = max(lon)
        min_lat = min(lat)
        max_lat = max(lat)
        if min_lon == max_lon:
            min_lon -= 1e-5
            max_lon += 1e-5
        if min_lat == max_lat:
            min_lat -= 1e-5
            max_lat += 1e-5
        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)

        history = ax.scatter([], [], s=10, alpha=0.45)
        point = ax.scatter([], [], s=28)
        canvas.draw()

        self._replay_index = 0
        self._replay_timer = QTimer(dialog)
        self._replay_timer.setInterval(100)

        def advance() -> None:
            try:
                if self._replay_index >= len(lat):
                    self._replay_timer.stop()
                    return
                idx = self._replay_index
                history.set_offsets(list(zip(lon[: idx + 1], lat[: idx + 1])))
                point.set_offsets([(lon[idx], lat[idx])])
                canvas.draw_idle()
                self._replay_index += 1
            except Exception as exc:
                self._append_log(f"轨迹回放错误：{exc}")
                self._replay_timer.stop()

        self._replay_timer.timeout.connect(advance)
        self._replay_timer.start()
        layout.addWidget(canvas)
        dialog.setLayout(layout)
        dialog.show()
        dialog.finished.connect(self._stop_replay_timer)

        self._replay_dialog = dialog

    def _stop_replay_timer(self) -> None:
        if self._replay_timer is not None:
            self._replay_timer.stop()
            self._replay_timer = None


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
