import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cuddly_fiesta.ecg_core import ECGCore
from cuddly_fiesta.core import MultiLeadECG
from cuddly_fiesta.rhythms import BundleBranchBlock, NormalSinusRhythm


class TestRhythmRegistry(unittest.TestCase):
    def test_registry_covers_public_ui_rhythms_and_parameters(self):
        from cuddly_fiesta.ui_registry import DISPLAY_CONTROL_SPECS, RHYTHM_REGISTRY

        required = {
            "normal_sinus",
            "atrial_fibrillation",
            "atrial_flutter",
            "first_degree_av_block",
            "third_degree_av_block",
            "bundle_branch_block",
            "supraventricular_tachycardia",
            "multifocal_atrial_tachycardia",
            "ventricular_tachycardia",
            "ventricular_fibrillation",
            "torsades_de_pointes",
            "wolff_parkinson_white",
            "asystole",
        }

        self.assertTrue(required.issubset(RHYTHM_REGISTRY))

        bbb_params = {
            param.name: param
            for param in RHYTHM_REGISTRY["bundle_branch_block"].parameters
        }
        self.assertEqual(bbb_params["block_type"].options, ("right", "left"))
        self.assertEqual(bbb_params["qrs_duration_ms"].default, 140)

        display_controls = {control.name for control in DISPLAY_CONTROL_SPECS}
        self.assertTrue(
            {
                "view_mode",
                "lead_focus",
                "show_grid",
                "gain",
                "paper_speed",
                "speed",
                "export_image",
                "export_csv",
            }.issubset(display_controls)
        )

    def test_registry_instantiates_rhythms_with_supported_parameters(self):
        from cuddly_fiesta.ui_registry import create_rhythm

        rhythm = create_rhythm(
            "bundle_branch_block",
            {
                "heart_rate_bpm": 60,
                "duration_sec": 1,
                "qrs_duration_ms": 150,
                "block_type": "left",
            },
        )

        self.assertIsInstance(rhythm, BundleBranchBlock)
        self.assertEqual(rhythm.block_type, "left")
        self.assertEqual(rhythm.qrs_duration_ms, 150)

    def test_all_registered_rhythms_generate_from_defaults(self):
        from cuddly_fiesta.ui_registry import RHYTHM_REGISTRY, create_rhythm

        for key in RHYTHM_REGISTRY:
            rhythm = create_rhythm(key)
            ecg = ECGCore(duration_sec=1, sampling_rate=1000)
            rhythm.apply_to_ecg(ecg)


class TestUIEntrypoints(unittest.TestCase):
    def test_public_ui_entrypoints_share_one_visualizer(self):
        import cuddly_fiesta
        from cuddly_fiesta.ecg_visualizer import ECGVisualizer, run_visualizer
        from cuddly_fiesta.ecg_visualizer_fixed import (
            ECGVisualizerFixed,
            run_visualizer_fixed,
        )
        from cuddly_fiesta.gui import ekg_ui

        self.assertIs(cuddly_fiesta.ECGVisualizer, ECGVisualizer)
        self.assertIs(ekg_ui.ECGGui, ECGVisualizer)
        self.assertIs(ekg_ui.main, run_visualizer)
        self.assertIs(ECGVisualizerFixed, ECGVisualizer)
        self.assertIs(run_visualizer_fixed, run_visualizer)

    def test_module_gui_command_routes_to_canonical_visualizer(self):
        from cuddly_fiesta.__main__ import _cmd_gui

        with patch("cuddly_fiesta.ecg_visualizer.run_visualizer") as run_visualizer:
            _cmd_gui(None)

        run_visualizer.assert_called_once_with()

    def test_legacy_demo_wrapper_imports_and_routes_to_visualizer(self):
        import run_demo

        with patch("run_demo.run_visualizer") as run_visualizer:
            run_demo.main()

        run_visualizer.assert_called_once_with()

    def test_export_helpers_write_clinical_image_and_csv(self):
        from cuddly_fiesta.ecg_visualizer import export_ecg_csv, export_ecg_image

        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm(heart_rate_bpm=60, duration_sec=1).apply_to_ecg(ecg)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            image_path = tmp_path / "ecg.png"
            csv_path = tmp_path / "ecg.csv"

            export_ecg_image(
                ecg,
                image_path,
                view_mode="12-lead",
                lead_focus="V1",
                show_grid=True,
                gain=10,
                paper_speed=25,
            )
            export_ecg_csv(ecg, csv_path)

            self.assertGreater(image_path.stat().st_size, 0)
            header = csv_path.read_text().splitlines()[0]
            self.assertEqual(header, "time,I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6")


class TestClinicalRendering(unittest.TestCase):
    def test_render_uses_cached_multi_lead_when_supplied(self):
        from cuddly_fiesta.ecg_visualizer import render_ecg_figure

        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm(heart_rate_bpm=60, duration_sec=1).apply_to_ecg(ecg)
        multi = MultiLeadECG.from_ecg(ecg)

        with patch("cuddly_fiesta.ecg_visualizer.MultiLeadECG.from_ecg") as synth:
            figure, _ = render_ecg_figure(ecg, lead_focus="II", multi=multi)

        synth.assert_not_called()
        plt.close(figure)

    def test_render_reuses_single_lead_axes_and_line(self):
        from cuddly_fiesta.ecg_visualizer import render_ecg_figure

        ecg = ECGCore(duration_sec=1, sampling_rate=100)
        ecg.time = np.linspace(0, 1, 100, endpoint=False)
        ecg.voltage = np.sin(ecg.time)
        multi = MultiLeadECG(ecg)
        figure, ax = render_ecg_figure(
            ecg, view_mode="single", lead_focus="II", multi=multi
        )
        line = ax.lines[0]

        with patch.object(figure, "clear", wraps=figure.clear) as clear:
            _, next_ax = render_ecg_figure(
                ecg, view_mode="single", lead_focus="II", figure=figure, multi=multi
            )

        clear.assert_not_called()
        self.assertIs(next_ax, ax)
        self.assertIs(next_ax.lines[0], line)
        plt.close(figure)

    def test_render_uses_dynamic_y_limits_for_high_gain_signals(self):
        from cuddly_fiesta.ecg_visualizer import render_ecg_figure

        ecg = ECGCore(duration_sec=1, sampling_rate=100)
        ecg.time = np.linspace(0, 1, 100, endpoint=False)
        signal = np.linspace(-4.0, 4.0, ecg.time.size)
        ecg.voltage = signal / 1.5
        multi = MultiLeadECG(ecg)

        figure, ax = render_ecg_figure(
            ecg,
            view_mode="single",
            lead_focus="II",
            gain=20,
            multi=multi,
        )

        y_min, y_max = ax.get_ylim()
        plotted = ax.lines[0].get_ydata()
        self.assertLessEqual(y_min, float(np.min(plotted)))
        self.assertGreaterEqual(y_max, float(np.max(plotted)))
        plt.close(figure)

    def test_animation_reuses_existing_single_lead_plot(self):
        from cuddly_fiesta.ecg_visualizer import ECGVisualizer

        class DummyVar:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        class DummyCanvas:
            def __init__(self):
                self.draws = 0

            def draw_idle(self):
                self.draws += 1

        class DummyMaster:
            def __init__(self):
                self.scheduled = []

            def after(self, delay, callback):
                self.scheduled.append((delay, callback))
                return "timer"

        ecg = ECGCore(duration_sec=1, sampling_rate=100)
        ecg.time = np.linspace(0, 1, 100, endpoint=False)
        ecg.voltage = np.sin(ecg.time)
        viz = ECGVisualizer.__new__(ECGVisualizer)
        viz.is_playing = True
        viz.current_ecg = ecg
        viz.current_multi = MultiLeadECG(ecg)
        viz.frame_index = 0
        viz.sampling_rate = 100
        viz.speed_var = DummyVar(1.0)
        viz.lead_focus_var = DummyVar("II")
        viz.show_grid_var = DummyVar(True)
        viz.gain_var = DummyVar(10.0)
        viz.paper_speed_var = DummyVar(25.0)
        viz.figure = plt.Figure()
        viz.figure.add_subplot(111)
        viz.canvas = DummyCanvas()
        viz.master = DummyMaster()
        viz._plot_state = ("single", "II", True, 10.0, 25.0)

        with patch("cuddly_fiesta.ecg_visualizer.render_ecg_figure") as render:
            viz._animate_once()

        render.assert_not_called()
        self.assertEqual(viz.canvas.draws, 1)
        self.assertEqual(len(viz.master.scheduled), 1)
        plt.close(viz.figure)


if __name__ == "__main__":
    unittest.main()
