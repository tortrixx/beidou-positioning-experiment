from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import os
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class ExperimentModuleTests(unittest.TestCase):
    def test_rinex3_spaced_satellite_ids_are_normalized(self) -> None:
        from rinex_obs import parse_rinex_obs

        content = "\n".join(
            [
                "     3.03           OBSERVATION DATA    M: Mixed            RINEX VERSION / TYPE",
                f"{'G    1 C1C':<60}SYS / # / OBS TYPES",
                f"{'C    1 C2I':<60}SYS / # / OBS TYPES",
                f"{'  2021     5    17     2    33   13.0000000     GPS':<60}TIME OF FIRST OBS",
                "                                                            END OF HEADER",
                "> 2021  5 17  2 33 13.0000000  0  2",
                "G 1  21642195.014",
                "C 3  36582024.261",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            obs_path = Path(tmp) / "spaced_ids.obs"
            obs_path.write_text(content, encoding="utf-8")
            header, epochs = parse_rinex_obs(obs_path)

        self.assertEqual(header.time_first_obs.year, 2021)
        self.assertIn("G01", epochs[0].sat_obs)
        self.assertIn("C03", epochs[0].sat_obs)
        self.assertNotIn("G 1", epochs[0].sat_obs)
        self.assertNotIn("C 3", epochs[0].sat_obs)

    def test_rinex_obs_parser_reads_gzip_and_rejects_hatanaka(self) -> None:
        from rinex_obs import parse_rinex_obs

        content = "\n".join(
            [
                "     3.03           OBSERVATION DATA    M: Mixed            RINEX VERSION / TYPE",
                f"{'G    1 C1C':<60}SYS / # / OBS TYPES",
                f"{'  2021     5    17     2    33   13.0000000     GPS':<60}TIME OF FIRST OBS",
                "                                                            END OF HEADER",
                "> 2021  5 17  2 33 13.0000000  0  1",
                "G 1  21642195.014",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            obs_gz = tmp_path / "sample.obs.gz"
            with gzip.open(obs_gz, "wt", encoding="utf-8") as f:
                f.write(content)

            header, epochs = parse_rinex_obs(obs_gz)
            self.assertEqual(header.version, 3.03)
            self.assertEqual(len(epochs), 1)

            crx_gz = tmp_path / "sample.crx.gz"
            with gzip.open(crx_gz, "wt", encoding="utf-8") as f:
                f.write(content)
            with self.assertRaisesRegex(ValueError, "Hatanaka"):
                parse_rinex_obs(crx_gz)

    def test_rinex3_short_observation_line_does_not_consume_next_epoch(self) -> None:
        from rinex_obs import parse_rinex_obs

        content = "\n".join(
            [
                "     3.03           OBSERVATION DATA    M: Mixed            RINEX VERSION / TYPE",
                f"{'G   15 C1C C2W C2X C5X L1C L2W L2X L5X S1C S2W S2X S5X':<60}SYS / # / OBS TYPES",
                f"{'      C6X L6X S6X':<60}SYS / # / OBS TYPES",
                f"{'  2026     4    27     0     0    0.0000000     GPS':<60}TIME OF FIRST OBS",
                "                                                            END OF HEADER",
                "> 2026 04 27 00 00 00.0000000  0  1",
                "G01" + "".join(f"{21642195.014 + idx:14.3f}  " for idx in range(14)),
                "> 2026 04 27 00 00 30.0000000  0  1",
                "G01" + "".join(f"{21642196.014 + idx:14.3f}  " for idx in range(14)),
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            obs_path = Path(tmp) / "short.obs"
            obs_path.write_text(content, encoding="utf-8")
            _, epochs = parse_rinex_obs(obs_path)

        self.assertEqual(len(epochs), 2)
        self.assertEqual(epochs[0].sat_obs["G01"]["C1C"], 21642195.014)

    def test_rinex_nav_parser_reads_gzip(self) -> None:
        from rinex_nav import parse_rinex_nav

        content = "\n".join(
            [
                "     3.04           N: GNSS NAV DATA    M: MIXED            RINEX VERSION / TYPE",
                "GPSA  1.0D-08 2.0D-08 3.0D-08 4.0D-08                  IONOSPHERIC CORR",
                "                                                            END OF HEADER",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            nav_gz = Path(tmp) / "nav.rnx.gz"
            with gzip.open(nav_gz, "wt", encoding="utf-8") as f:
                f.write(content)
            header, records = parse_rinex_nav(nav_gz)

        self.assertEqual(header.ion_alpha, (1e-8, 2e-8, 3e-8, 4e-8))
        self.assertEqual(records, [])

    def test_redundancy_runner_classifies_ok_warning_and_expected_error(self) -> None:
        from redundancy import RedundancyCase, run_redundancy_cases

        with tempfile.TemporaryDirectory() as tmp:
            crx_gz = Path(tmp) / "sample.crx.gz"
            with gzip.open(crx_gz, "wt", encoding="utf-8") as f:
                f.write("placeholder")
            rows = run_redundancy_cases(
                [
                    RedundancyCase(
                        name="sample_ok",
                        obs_path=ROOT / "data" / "sample" / "bjfs1170.26o",
                        nav_path=ROOT / "data" / "sample" / "brdc1170.26n",
                        systems=("G",),
                        max_epochs=1,
                        min_solutions=1,
                    ),
                    RedundancyCase(
                        name="sample_no_selected_system",
                        obs_path=ROOT / "data" / "sample" / "bjfs1170.26o",
                        nav_path=ROOT / "data" / "sample" / "brdc1170.26n",
                        systems=("C",),
                        max_epochs=1,
                        min_solutions=1,
                    ),
                    RedundancyCase(
                        name="hatanka_expected",
                        obs_path=crx_gz,
                        nav_path=ROOT / "data" / "sample" / "brdc1170.26n",
                        systems=("G",),
                        max_epochs=1,
                        expect_error="Hatanaka",
                    ),
                ]
            )

        by_name = {row["name"]: row for row in rows}
        self.assertEqual(by_name["sample_ok"]["status"], "ok")
        self.assertEqual(by_name["sample_no_selected_system"]["status"], "warning")
        self.assertEqual(by_name["hatanka_expected"]["status"], "expected_error")

    def test_plotting_keeps_error_lines_and_trajectory_scatter(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from plotting import plot_error_and_dop, plot_trajectory

        original_show = plt.show
        plt.show = lambda: None
        try:
            self.assertTrue(plot_error_and_dop([0, 1], [1.0, 2.0], [2.0, 3.0], [1.5, 1.6], sat_counts=[8, 9]))
            error_fig = plt.gcf()
            self.assertEqual(sum(len(ax.collections) for ax in error_fig.axes), 0)
            self.assertGreaterEqual(sum(len(ax.lines) for ax in error_fig.axes), 4)
            plt.close(error_fig)

            self.assertTrue(plot_trajectory([39.0, 39.1], [116.0, 116.1]))
            traj_fig = plt.gcf()
            self.assertGreater(sum(len(ax.collections) for ax in traj_fig.axes), 0)
            self.assertEqual(sum(len(ax.lines) for ax in traj_fig.axes), 0)
            plt.close(traj_fig)
        finally:
            plt.show = original_show

    def test_pipeline_returns_empty_result_when_no_selected_system_can_solve(self) -> None:
        from pipeline import run_continuous_pipeline

        obs_header, solutions, errors, stats = run_continuous_pipeline(
            str(ROOT / "data" / "sample" / "bjfs1170.26o"),
            str(ROOT / "data" / "sample" / "brdc1170.26n"),
            systems=("C",),
            max_epochs=3,
        )

        self.assertEqual(obs_header.marker_name, "BJFS")
        self.assertEqual(solutions, [])
        self.assertEqual(errors, [])
        self.assertEqual(stats["solution_epochs"], 0)
        self.assertGreater(stats["skipped_epochs"], 0)

    def test_continuous_cli_with_plot_handles_no_solutions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = os.environ.copy()
            env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")
            env["XDG_CACHE_HOME"] = str(tmp_path / "xdgcache")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_continuous.py",
                    "--obs",
                    "data/sample/bjfs1170.26o",
                    "--nav",
                    "data/sample/brdc1170.26n",
                    "--systems",
                    "C",
                    "--max-epochs",
                    "1",
                    "--csv",
                    str(tmp_path / "empty.csv"),
                    "--plot",
                    "--save-plots",
                    str(tmp_path / "plots"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("有效解数量：0", result.stdout)
        self.assertIn("没有有效定位解", result.stdout)

    def test_plot_results_cli_handles_empty_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "empty.csv"
            csv_path.write_text("time,lat,lon,pdop,used_sats,horiz,three_d\n", encoding="utf-8")
            env = os.environ.copy()
            env["MPLCONFIGDIR"] = str(tmp_path / "mplconfig")
            env["XDG_CACHE_HOME"] = str(tmp_path / "xdgcache")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/plot_results.py",
                    "--csv",
                    str(csv_path),
                    "--save-dir",
                    str(tmp_path / "plots"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CSV 中没有结果行", result.stdout)

    def test_inspect_cli_reports_hatanaka_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            crx_gz = Path(tmp) / "sample.crx.gz"
            with gzip.open(crx_gz, "wt", encoding="utf-8") as f:
                f.write("placeholder")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/inspect_rinex.py",
                    "--obs",
                    str(crx_gz),
                    "--nav",
                    "data/sample/brdc1170.26n",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Hatanaka", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_spp_cli_reports_invalid_input_without_traceback(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_spp.py",
                "--obs",
                "missing.obs",
                "--nav",
                "data/sample/brdc1170.26n",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("错误：", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_continuous_cli_reports_invalid_input_without_traceback(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_continuous.py",
                "--obs",
                "missing.obs",
                "--nav",
                "data/sample/brdc1170.26n",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("错误：", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_urban_nav_inventory_detects_bds_observation_files(self) -> None:
        from data_inventory import summarize_dataset_directory

        urban_root = ROOT / "1_UrbanNav-HK-Medium-Urban-1"
        if not urban_root.exists():
            self.skipTest("UrbanNav dataset is not present")

        summary = summarize_dataset_directory(urban_root)
        gc = next(row for row in summary["observations"] if row["receiver"] == "ublox.m8t.GC")

        self.assertEqual(summary["dataset_id"], "urban_nav_hk_medium_urban_1")
        self.assertIn("C", gc["systems"])
        self.assertIn("G", gc["systems"])
        self.assertGreater(gc["epochs"], 0)
        self.assertGreater(gc["bds_epochs"], 0)
        self.assertFalse(summary["has_navigation"])

    def test_inventory_supports_managed_dataset_layout(self) -> None:
        from data_inventory import summarize_dataset_directory

        content = "\n".join(
            [
                "     3.03           OBSERVATION DATA    M: Mixed            RINEX VERSION / TYPE",
                f"{'C    1 C2I':<60}SYS / # / OBS TYPES",
                f"{'  2021     5    17     2    33   13.0000000     GPS':<60}TIME OF FIRST OBS",
                "                                                            END OF HEADER",
                "> 2021  5 17  2 33 13.0000000  0  1",
                "C 3  36582024.261",
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "urban_nav_hk_medium_urban_1"
            rinex_dir = root / "rinex"
            nmea_dir = root / "nmea"
            rinex_dir.mkdir(parents=True)
            nmea_dir.mkdir(parents=True)
            (rinex_dir / "toy.receiver.obs").write_text(content, encoding="utf-8")
            (rinex_dir / "BRDM00DLR_S_20211370000_01D_MN.rnx").write_text("", encoding="utf-8")
            (nmea_dir / "toy.receiver.nmea").write_text("$GNGGA\n", encoding="utf-8")

            summary = summarize_dataset_directory(root)

        self.assertTrue(summary["has_navigation"])
        self.assertEqual(summary["observations"][0]["receiver"], "toy.receiver")
        self.assertTrue(summary["observations"][0]["has_nmea"])

    def test_default_inspection_command_uses_bundled_data(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/inspect_rinex.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("观测文件版本：", result.stdout)
        self.assertIn("导航记录数：", result.stdout)

    def test_continuous_pipeline_rejects_zero_step(self) -> None:
        from pipeline import run_continuous_pipeline

        with self.assertRaisesRegex(ValueError, "step"):
            run_continuous_pipeline(
                str(ROOT / "data" / "sample" / "bjfs1170.26o"),
                str(ROOT / "data" / "sample" / "brdc1170.26n"),
                step=0,
                max_epochs=1,
            )

    def test_plotting_reports_saved_files(self) -> None:
        from plotting import plot_error_and_dop, plot_trajectory

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            error_path = tmp_path / "error_dop.png"
            traj_path = tmp_path / "trajectory.png"

            error_saved = plot_error_and_dop(
                [0, 1],
                [1.0, 2.0],
                [2.0, 3.0],
                [1.5, 1.6],
                str(error_path),
                sat_counts=[8, 9],
            )
            traj_saved = plot_trajectory([39.0, 39.1], [116.0, 116.1], str(traj_path))

            self.assertTrue(error_saved)
            self.assertTrue(error_path.exists())
            self.assertTrue(traj_saved)
            self.assertTrue(traj_path.exists())

    def test_solution_csv_includes_residual_diagnostics(self) -> None:
        from experiment_modules import SoftwareSystemModule

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "diagnostics" / "results.csv"
            result = SoftwareSystemModule().run(
                ROOT / "data" / "sample" / "bjfs1170.26o",
                ROOT / "data" / "sample" / "brdc1170.26n",
                max_epochs=2,
                output_csv=csv_path,
            )

            self.assertEqual(len(result.solutions), 2)
            self.assertIsNotNone(result.solutions[0].residual_rms_m)
            self.assertIsNotNone(result.solutions[0].residual_max_m)
            header = csv_path.read_text(encoding="utf-8").splitlines()[0]
            self.assertIn("residual_rms_m", header)
            self.assertIn("residual_max_m", header)

    def test_five_experiment_modules_run_single_epoch(self) -> None:
        from experiment_modules import (
            ContinuousAnalysisModule,
            RinexDataModule,
            SatelliteCorrectionModule,
            SinglePointPositioningModule,
            SoftwareSystemModule,
        )

        data_module = RinexDataModule()
        dataset = data_module.load(ROOT / "data" / "sample" / "bjfs1170.26o", ROOT / "data" / "sample" / "brdc1170.26n")
        self.assertEqual(dataset.obs_header.marker_name, "BJFS")
        self.assertGreater(len(dataset.epochs), 0)

        sat_module = SatelliteCorrectionModule(dataset.nav_header, dataset.nav_records)
        self.assertGreater(len(sat_module.visible_measurements(dataset.epochs[0], dataset.obs_header.approx_position_xyz)), 0)

        spp_module = SinglePointPositioningModule(dataset.nav_header, dataset.nav_records)
        solution = spp_module.solve_epoch(dataset.epochs[0], dataset.obs_header.approx_position_xyz)
        self.assertGreaterEqual(len(solution.used_sats), 4)

        analysis_module = ContinuousAnalysisModule()
        errors, stats = analysis_module.evaluate([solution], dataset.obs_header.approx_position_xyz)
        self.assertEqual(len(errors), 1)
        self.assertIn("horiz_rms", stats)

        system = SoftwareSystemModule()
        run = system.run(ROOT / "data" / "sample" / "bjfs1170.26o", ROOT / "data" / "sample" / "brdc1170.26n", max_epochs=2)
        self.assertEqual(len(run.solutions), 2)
        self.assertIn("3d_rms", run.stats)

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "nested" / "results.csv"
            system.run(
                ROOT / "data" / "sample" / "bjfs1170.26o",
                ROOT / "data" / "sample" / "brdc1170.26n",
                max_epochs=1,
                output_csv=csv_path,
            )
            self.assertTrue(csv_path.exists())

    def test_rinex3_bds_navigation_header_and_record_parse(self) -> None:
        from rinex_nav import parse_rinex_nav

        def nav_line(prefix: str, values: list[float]) -> str:
            return prefix + "".join(f"{value:19.12E}".replace("E", "D") for value in values)

        content = "\n".join(
            [
                "     3.04           N: GNSS NAV DATA    M: MIXED            RINEX VERSION / TYPE",
                "BDSA  1.0D-08 2.0D-08 3.0D-08 4.0D-08                  IONOSPHERIC CORR",
                "BDSB  1.0D+05 2.0D+05 3.0D+05 4.0D+05                  IONOSPHERIC CORR",
                "                                                            END OF HEADER",
                nav_line("C01 2026 04 27 00 00 00", [1e-4, 2e-12, 0.0]),
                nav_line("    ", [1.0, 2.0, 3.0e-9, 0.1]),
                nav_line("    ", [1.0e-6, 0.01, 2.0e-6, 5153.7955]),
                nav_line("    ", [345600.0, 1.0e-7, 0.2, 2.0e-7]),
                nav_line("    ", [0.9, 100.0, 0.3, -8.0e-9]),
                nav_line("    ", [1.0e-10, 0.0, 2420.0, 0.0]),
                nav_line("    ", [2.0, 0.0, -1.0e-8, 0.0]),
                nav_line("    ", [100.0, 0.0, 0.0, 0.0]),
                "",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            nav_path = Path(tmp) / "bds_nav.rnx"
            nav_path.write_text(content, encoding="utf-8")
            header, records = parse_rinex_nav(nav_path)

        self.assertEqual(header.ion_corr["BDSA"], (1e-8, 2e-8, 3e-8, 4e-8))
        self.assertEqual(header.ion_corr["BDSB"], (1e5, 2e5, 3e5, 4e5))
        self.assertEqual(records[0].prn, "C01")
        self.assertEqual(records[0].epoch.year, 2026)
        self.assertAlmostEqual(records[0].sqrt_a, 5153.7955)

    def test_bds_ionosphere_coefficients_are_selected(self) -> None:
        from models import NavHeader
        from positioning import _ionosphere_coefficients

        header = NavHeader(
            ion_alpha=(1.0, 2.0, 3.0, 4.0),
            ion_beta=(5.0, 6.0, 7.0, 8.0),
            leap_seconds=None,
            ion_corr={
                "BDSA": (9.0, 10.0, 11.0, 12.0),
                "BDSB": (13.0, 14.0, 15.0, 16.0),
            },
        )

        self.assertEqual(_ionosphere_coefficients(header, "G"), ((1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0)))
        self.assertEqual(_ionosphere_coefficients(header, "C"), ((9.0, 10.0, 11.0, 12.0), (13.0, 14.0, 15.0, 16.0)))

    def test_bds_geo_prns_are_identified(self) -> None:
        from satellite import _is_bds_geo

        self.assertTrue(_is_bds_geo("C01"))
        self.assertTrue(_is_bds_geo("C05"))
        self.assertFalse(_is_bds_geo("C06"))
        self.assertFalse(_is_bds_geo("G01"))

    def test_downloaded_rinex3_mixed_observation_parses(self) -> None:
        from rinex_obs import parse_rinex_obs

        obs_path = ROOT / "data" / "datasets" / "twtf_2026_117_mixed" / "rinex" / "TWTF00TWN_R_20261170000_01D_30S_MO.rnx"
        if not obs_path.exists():
            self.skipTest("Downloaded TWTF mixed RINEX3 dataset is not present")

        header, epochs = parse_rinex_obs(obs_path)

        self.assertEqual(header.version, 3.04)
        self.assertEqual(header.marker_name, "TWTF")
        self.assertGreater(len(epochs), 0)
        self.assertIn("C01", epochs[0].sat_obs)
        self.assertIn("E02", epochs[0].sat_obs)

    def test_downloaded_mixed_navigation_skips_short_sbas_records(self) -> None:
        from rinex_nav import parse_rinex_nav

        nav_path = ROOT / "data" / "datasets" / "twtf_2026_117_mixed" / "rinex" / "BRDM00DLR_S_20261170000_01D_MN.rnx"
        if not nav_path.exists():
            self.skipTest("Downloaded BRDM mixed RINEX3 navigation dataset is not present")

        header, records = parse_rinex_nav(nav_path)

        self.assertIn("BDSA", header.ion_corr)
        self.assertTrue(any(record.prn.startswith("G") for record in records))
        self.assertTrue(any(record.prn.startswith("C") for record in records))

    def test_bds_only_continuous_run_remains_finite(self) -> None:
        from experiment_modules import SoftwareSystemModule

        obs_path = ROOT / "data" / "datasets" / "twtf_2026_117_mixed" / "rinex" / "TWTF00TWN_R_20261170000_01D_30S_MO.rnx"
        nav_path = ROOT / "data" / "datasets" / "twtf_2026_117_mixed" / "rinex" / "BRDM00DLR_S_20261170000_01D_MN.rnx"
        if not obs_path.exists() or not nav_path.exists():
            self.skipTest("Downloaded TWTF mixed RINEX3 dataset is not present")

        result = SoftwareSystemModule().run(obs_path, nav_path, systems=("C",), max_epochs=3)

        self.assertGreater(len(result.solutions), 0)
        for solution in result.solutions:
            self.assertTrue(all(abs(value) < 1.0e8 for value in solution.position_ecef))
            self.assertLess(abs(solution.position_blh[2]), 5.0e4)
        self.assertLess(result.stats["3d_rms"], 20.0)

    def test_gps_bds_joint_run_models_inter_system_bias(self) -> None:
        from experiment_modules import SoftwareSystemModule

        obs_path = ROOT / "data" / "datasets" / "twtf_2026_117_mixed" / "rinex" / "TWTF00TWN_R_20261170000_01D_30S_MO.rnx"
        nav_path = ROOT / "data" / "datasets" / "twtf_2026_117_mixed" / "rinex" / "BRDM00DLR_S_20261170000_01D_MN.rnx"
        if not obs_path.exists() or not nav_path.exists():
            self.skipTest("Downloaded TWTF mixed RINEX3 dataset is not present")

        result = SoftwareSystemModule().run(obs_path, nav_path, systems=("G", "C"), max_epochs=120)

        self.assertEqual(len(result.solutions), 120)
        self.assertLess(result.stats["3d_rms"], 100.0)

    def test_batch_summary_reads_result_csv(self) -> None:
        from batch import summarize_result_csv

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "results.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "time,used_sats,pdop,gdop,residual_rms_m,residual_max_m,horiz,three_d",
                        "2026-01-01T00:00:00,8,2.0,3.0,0.5,1.0,3.0,4.0",
                        "2026-01-01T00:00:30,10,4.0,5.0,0.7,1.5,5.0,6.0",
                    ]
                ),
                encoding="utf-8",
            )

            summary = summarize_result_csv("toy", "G", csv_path)

        self.assertEqual(summary["dataset"], "toy")
        self.assertEqual(summary["system"], "G")
        self.assertEqual(summary["epochs"], 2)
        self.assertAlmostEqual(summary["horiz_rms"], (17.0) ** 0.5)
        self.assertAlmostEqual(summary["3d_mean"], 5.0)
        self.assertAlmostEqual(summary["used_sats_mean"], 9.0)

    def test_linear_error_compensation_improves_synthetic_holdout(self) -> None:
        from ml_compensation import evaluate_compensation, split_train_test, train_linear_model

        rows = []
        for idx in range(40):
            pdop = 1.0 + idx * 0.1
            rows.append(
                {
                    "dataset": "synthetic",
                    "used_sats": "8",
                    "pdop": str(pdop),
                    "gdop": str(pdop + 0.5),
                    "residual_rms_m": "0.2",
                    "residual_max_m": "0.4",
                    "clock_bias_m": "0.0",
                    "h": "100.0",
                    "east": str(2.0 * pdop + 1.0),
                    "north": str(-pdop),
                    "up": str(0.5 * pdop),
                }
            )

        train_rows, test_rows = split_train_test(rows, train_ratio=0.7)
        model = train_linear_model(train_rows)
        metrics = evaluate_compensation(model, test_rows)

        self.assertLess(metrics["compensated_3d_rms"], metrics["original_3d_rms"])
        self.assertLess(metrics["compensated_horiz_rms"], metrics["original_horiz_rms"])


if __name__ == "__main__":
    unittest.main()
