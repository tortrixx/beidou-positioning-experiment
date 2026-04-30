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
        self.setWindowTitle("Beidou Positioning Experiment")
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

        browse_obs = QPushButton("Browse...")
        browse_nav = QPushButton("Browse...")
        browse_csv = QPushButton("Browse...")
        browse_obs.clicked.connect(lambda: self._browse(self.obs_edit, "OBS Files (*.o *.obs);;All Files (*)"))
        browse_nav.clicked.connect(lambda: self._browse(self.nav_edit, "NAV Files (*.n *.nav);;All Files (*)"))
        browse_csv.clicked.connect(lambda: self._browse_save(self.csv_edit, "CSV Files (*.csv);;All Files (*)"))

        self.run_btn = QPushButton("Run")
        self.plot_btn = QPushButton("Plot")
        self.replay_btn = QPushButton("Replay")
        self.run_btn.clicked.connect(self._start_run)
        self.plot_btn.clicked.connect(self._plot)
        self.replay_btn.clicked.connect(self._replay)
        self.plot_btn.setEnabled(False)
        self.replay_btn.setEnabled(False)

        form = QFormLayout()
        form.addRow("Obs file", self._row(self.obs_edit, browse_obs))
        form.addRow("Nav file", self._row(self.nav_edit, browse_nav))
        form.addRow("Output CSV", self._row(self.csv_edit, browse_csv))
        form.addRow("Step", self.step_spin)
        form.addRow("Max epochs (0=all)", self.max_epochs_spin)
        form.addRow("Max iterations", self.max_iter_spin)
        form.addRow("Error threshold (m)", self.err_spin)
        form.addRow("Elevation mask (deg)", self.elev_spin)
        form.addRow("GNSS systems", self.systems_edit)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.plot_btn)
        btn_row.addWidget(self.replay_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("Realtime position"))
        self.pos_label = QLabel("Lat: -  Lon: -  H: -")
        self.stat_label = QLabel("Used sats: -  PDOP: -")
        layout.addWidget(self.pos_label)
        layout.addWidget(self.stat_label)
        layout.addWidget(QLabel("Log"))
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
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", pattern)
        if path:
            target.setText(path)

    def _browse_save(self, target: QLineEdit, pattern: str) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save file", target.text(), pattern)
        if path:
            target.setText(path)

    def _append_log(self, text: str) -> None:
        self.log_view.append(text)

    def _start_run(self) -> None:
        self.run_btn.setEnabled(False)
        self.plot_btn.setEnabled(False)
        self._append_log("Running...")

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
        self._append_log(
            f"Solutions: {len(solutions)} | "
            f"Horiz RMS/Mean/Max: {stats['horiz_rms']:.3f}/{stats['horiz_mean']:.3f}/{stats['horiz_max']:.3f} | "
            f"3D RMS/Mean/Max: {stats['3d_rms']:.3f}/{stats['3d_mean']:.3f}/{stats['3d_max']:.3f}"
        )
        self.run_btn.setEnabled(True)
        self.plot_btn.setEnabled(True)
        self.replay_btn.setEnabled(True)
        self.worker = None
        self.thread.quit()

    def _on_failed(self, message: str) -> None:
        self._append_log(f"Error: {message}")
        self.run_btn.setEnabled(True)
        self.plot_btn.setEnabled(False)
        self.replay_btn.setEnabled(False)
        self.worker = None
        self.thread.quit()

    def _on_progress(self, epoch_idx: int, count: int, sol) -> None:
        self.pos_label.setText(
            f"Lat: {sol.position_blh[0]:.6f}  Lon: {sol.position_blh[1]:.6f}  H: {sol.position_blh[2]:.2f}"
        )
        self.stat_label.setText(f"Used sats: {len(sol.used_sats)}  PDOP: {sol.pdop:.3f}")
        if count - self._last_log_count >= 50:
            self._append_log(f"Epoch {epoch_idx} | Solutions {count}")
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
            self._append_log("matplotlib not available; replay disabled")
            return

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
        dialog.setWindowTitle("Trajectory Replay")
        dialog.resize(640, 640)
        layout = QVBoxLayout()

        fig = Figure(figsize=(6, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Longitude (deg)")
        ax.set_ylabel("Latitude (deg)")
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

        line, = ax.plot([], [], linewidth=1.0)
        point, = ax.plot([], [], marker="o", markersize=4)
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
                line.set_data(lon[: idx + 1], lat[: idx + 1])
                point.set_data([lon[idx]], [lat[idx]])
                canvas.draw_idle()
                self._replay_index += 1
            except Exception as exc:
                self._append_log(f"Replay error: {exc}")
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
