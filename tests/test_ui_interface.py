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
                "target_fps",
                "export_image",
                "export_csv",
            }.issubset(display_controls)
        )
        controls = {control.name: control for control in DISPLAY_CONTROL_SPECS}
        self.assertEqual(controls["target_fps"].default, "60")
        self.assertEqual(controls["target_fps"].options, ("24", "30", "60", "120"))

    def test_show_grid_coercion_accepts_common_bool_inputs(self):
        from cuddly_fiesta.ui_registry import DISPLAY_CONTROL_SPECS, coerce_parameter_value

        show_grid = next(
            control for control in DISPLAY_CONTROL_SPECS if control.name == "show_grid"
        )
        cases = (
            (True, True),
            (False, False),
            ("true", True),
            ("false", False),
            (" TRUE ", True),
            (" False ", False),
            ("1", True),
            ("0", False),
            (1, True),
            (0, False),
            (1.0, True),
            (0.0, False),
            ("yes", True),
            ("no", False),
        )

        for raw_value, expected in cases:
            with self.subTest(raw_value=raw_value):
                self.assertIs(coerce_parameter_value(show_grid, raw_value), expected)

    def test_show_grid_coercion_rejects_ambiguous_bool_inputs(self):
        from cuddly_fiesta.ui_registry import DISPLAY_CONTROL_SPECS, coerce_parameter_value

        show_grid = next(
            control for control in DISPLAY_CONTROL_SPECS if control.name == "show_grid"
        )

        for raw_value in ("", "maybe", "2", 2, -1, None):
            with self.subTest(raw_value=raw_value):
                with self.assertRaises(ValueError):
                    coerce_parameter_value(show_grid, raw_value)

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
        viz.target_fps_var = DummyVar("60")
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
        self.assertEqual(viz.master.scheduled[0][0], 17)
        plt.close(viz.figure)

    def test_animation_timing_uses_target_fps(self):
        from cuddly_fiesta.ecg_visualizer import ECGVisualizer

        class DummyVar:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        expected = {
            "24": (42, 42),
            "30": (33, 33),
            "60": (17, 17),
            "120": (8, 8),
        }
        for fps, timing in expected.items():
            with self.subTest(fps=fps):
                viz = ECGVisualizer.__new__(ECGVisualizer)
                viz.sampling_rate = 1000
                viz.speed_var = DummyVar(1.0)
                viz.target_fps_var = DummyVar(fps)
                self.assertEqual(viz._animation_timing(), timing)

        viz = ECGVisualizer.__new__(ECGVisualizer)
        viz.sampling_rate = 1000
        viz.speed_var = DummyVar(2.0)
        viz.target_fps_var = DummyVar("120")
        self.assertEqual(viz._animation_timing(), (16, 8))

    def test_playback_status_text_reports_visible_runtime_state(self):
        from cuddly_fiesta.ecg_visualizer import ECGVisualizer

        class DummyVar:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        viz = ECGVisualizer.__new__(ECGVisualizer)
        viz.current_rhythm_name = "Normal Sinus Rhythm"
        viz.current_duration_sec = 10.0
        viz.is_playing = False
        viz._plot_state = ("single", "II", True, 10.0, 25.0)
        viz.view_mode_var = DummyVar("12-lead")
        viz.lead_focus_var = DummyVar("II")
        viz.speed_var = DummyVar(1.5)
        viz.target_fps_var = DummyVar("120")

        status = viz._status_text()

        self.assertIn("Normal Sinus Rhythm", status)
        self.assertIn("10s", status)
        self.assertIn("Stopped", status)
        self.assertIn("single", status)
        self.assertNotIn("12-lead", status)
        self.assertIn("Lead II", status)
        self.assertIn("1.5x", status)
        self.assertIn("120 FPS", status)

        viz.speed_var = DummyVar("editing")
        self.assertIn("1x", viz._status_text())

    def test_toggle_play_updates_button_label_and_status(self):
        from cuddly_fiesta.ecg_visualizer import ECGVisualizer

        class DummyVar:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        class DummyMaster:
            def __init__(self):
                self.cancelled = []

            def after_cancel(self, timer):
                self.cancelled.append(timer)

        viz = ECGVisualizer.__new__(ECGVisualizer)
        viz.master = DummyMaster()
        viz.animation_timer = None
        viz.is_playing = False
        viz.play_button_var = DummyVar("Play")
        viz.status_var = DummyVar("")
        viz.current_rhythm_name = "Normal Sinus Rhythm"
        viz.current_duration_sec = 10.0
        viz.view_mode_var = DummyVar("single")
        viz.lead_focus_var = DummyVar("II")
        viz.speed_var = DummyVar(1.0)
        viz.target_fps_var = DummyVar("60")

        with patch.object(viz, "_animate_once") as animate_once:
            viz.toggle_play()

        animate_once.assert_called_once_with()
        self.assertTrue(viz.is_playing)
        self.assertEqual(viz.play_button_var.get(), "Pause")
        self.assertIn("Playing", viz.status_var.get())

        viz.animation_timer = "timer"
        viz.toggle_play()

        self.assertFalse(viz.is_playing)
        self.assertIsNone(viz.animation_timer)
        self.assertEqual(viz.play_button_var.get(), "Play")
        self.assertEqual(viz.master.cancelled, ["timer"])
        self.assertIn("Stopped", viz.status_var.get())


if __name__ == "__main__":
    unittest.main()
