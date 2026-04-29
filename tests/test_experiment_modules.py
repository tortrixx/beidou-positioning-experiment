from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class ExperimentModuleTests(unittest.TestCase):
    def test_default_inspection_command_uses_bundled_data(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/inspect_rinex.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OBS version:", result.stdout)
        self.assertIn("NAV records:", result.stdout)

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

            error_saved = plot_error_and_dop([0, 1], [1.0, 2.0], [2.0, 3.0], [1.5, 1.6], str(error_path))
            traj_saved = plot_trajectory([39.0, 39.1], [116.0, 116.1], str(traj_path))

            self.assertTrue(error_saved)
            self.assertTrue(error_path.exists())
            self.assertTrue(traj_saved)
            self.assertTrue(traj_path.exists())

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


if __name__ == "__main__":
    unittest.main()
