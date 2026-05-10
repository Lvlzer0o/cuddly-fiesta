"""UI-facing rhythm and display control registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple, Type

from .core import ArrhythmiaPattern
from .rhythms import (
    Asystole,
    AtrialFibrillation,
    AtrialFlutter,
    BundleBranchBlock,
    FirstDegreeAVBlock,
    MultifocalAtrialTachycardia,
    NormalSinusRhythm,
    SupraventricularTachycardia,
    ThirdDegreeAVBlock,
    TorsadesDePointes,
    VentricularFibrillation,
    VentricularTachycardia,
    WolffParkinsonWhite,
)


@dataclass(frozen=True)
class ParameterSpec:
    """Describes one UI-editable parameter."""

    name: str
    label: str
    default: Any
    kind: str = "float"
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    units: str = ""
    options: Tuple[str, ...] = ()


@dataclass(frozen=True)
class RhythmSpec:
    """Describes a rhythm available in the public UI."""

    key: str
    label: str
    rhythm_cls: Type[ArrhythmiaPattern]
    parameters: Tuple[ParameterSpec, ...] = ()
    description: str = ""

    def defaults(self) -> Dict[str, Any]:
        """Return constructor defaults for this rhythm."""
        return {param.name: param.default for param in self.parameters}


HEART_RATE = ParameterSpec(
    "heart_rate_bpm", "Heart rate", 70, "int", 30, 250, 1, "bpm"
)
DURATION = ParameterSpec(
    "duration_sec", "Duration", 10, "float", 1, 30, 1, "s"
)
TARGET_FPS_OPTIONS = ("24", "30", "60", "120")


RHYTHM_REGISTRY: Dict[str, RhythmSpec] = {
    "normal_sinus": RhythmSpec(
        "normal_sinus",
        "Normal Sinus Rhythm",
        NormalSinusRhythm,
        (HEART_RATE, DURATION),
    ),
    "atrial_fibrillation": RhythmSpec(
        "atrial_fibrillation",
        "Atrial Fibrillation",
        AtrialFibrillation,
        (
            ParameterSpec(
                "ventricular_rate_bpm",
                "Ventricular rate",
                110,
                "int",
                60,
                180,
                1,
                "bpm",
            ),
            DURATION,
        ),
    ),
    "atrial_flutter": RhythmSpec(
        "atrial_flutter",
        "Atrial Flutter",
        AtrialFlutter,
        (
            ParameterSpec("atrial_rate_bpm", "Atrial rate", 300, "int", 220, 350, 5, "bpm"),
            ParameterSpec("conduction_ratio", "AV ratio", 2, "int", 2, 4, 1),
            DURATION,
        ),
    ),
    "first_degree_av_block": RhythmSpec(
        "first_degree_av_block",
        "First-Degree AV Block",
        FirstDegreeAVBlock,
        (
            HEART_RATE,
            DURATION,
            ParameterSpec("pr_interval_ms", "PR interval", 240, "int", 200, 360, 10, "ms"),
        ),
    ),
    "third_degree_av_block": RhythmSpec(
        "third_degree_av_block",
        "Third-Degree AV Block",
        ThirdDegreeAVBlock,
        (
            ParameterSpec("atrial_rate_bpm", "Atrial rate", 75, "int", 45, 120, 1, "bpm"),
            ParameterSpec(
                "ventricular_rate_bpm", "Ventricular rate", 40, "int", 25, 70, 1, "bpm"
            ),
            DURATION,
        ),
    ),
    "bundle_branch_block": RhythmSpec(
        "bundle_branch_block",
        "Bundle Branch Block",
        BundleBranchBlock,
        (
            HEART_RATE,
            DURATION,
            ParameterSpec("qrs_duration_ms", "QRS duration", 140, "int", 120, 200, 5, "ms"),
            ParameterSpec(
                "block_type", "Block type", "right", "choice", options=("right", "left")
            ),
        ),
        "RBBB and LBBB profiles expose V1/V6 morphology changes.",
    ),
    "supraventricular_tachycardia": RhythmSpec(
        "supraventricular_tachycardia",
        "Supraventricular Tachycardia",
        SupraventricularTachycardia,
        (
            ParameterSpec("heart_rate_bpm", "Heart rate", 180, "int", 150, 250, 1, "bpm"),
            DURATION,
        ),
    ),
    "multifocal_atrial_tachycardia": RhythmSpec(
        "multifocal_atrial_tachycardia",
        "Multifocal Atrial Tachycardia",
        MultifocalAtrialTachycardia,
        (
            ParameterSpec("heart_rate_bpm", "Heart rate", 120, "int", 101, 180, 1, "bpm"),
            DURATION,
        ),
    ),
    "ventricular_tachycardia": RhythmSpec(
        "ventricular_tachycardia",
        "Ventricular Tachycardia",
        VentricularTachycardia,
        (
            ParameterSpec("heart_rate_bpm", "Heart rate", 180, "int", 120, 240, 1, "bpm"),
            DURATION,
        ),
    ),
    "ventricular_fibrillation": RhythmSpec(
        "ventricular_fibrillation",
        "Ventricular Fibrillation",
        VentricularFibrillation,
        (ParameterSpec("amplitude_mv", "Amplitude", 0.5, "float", 0.1, 1.5, 0.1, "mV"),),
    ),
    "torsades_de_pointes": RhythmSpec(
        "torsades_de_pointes",
        "Torsades de Pointes",
        TorsadesDePointes,
        (
            ParameterSpec(
                "ventricular_rate_bpm", "Ventricular rate", 200, "int", 150, 300, 1, "bpm"
            ),
            ParameterSpec(
                "twist_frequency_hz", "Twist frequency", 0.5, "float", 0.1, 1.5, 0.1, "Hz"
            ),
            DURATION,
        ),
    ),
    "wolff_parkinson_white": RhythmSpec(
        "wolff_parkinson_white",
        "Wolff-Parkinson-White",
        WolffParkinsonWhite,
        (
            HEART_RATE,
            DURATION,
            ParameterSpec("pr_interval_ms", "PR interval", 100, "int", 60, 119, 5, "ms"),
        ),
    ),
    "asystole": RhythmSpec("asystole", "Asystole", Asystole),
}


DISPLAY_CONTROL_SPECS: Tuple[ParameterSpec, ...] = (
    ParameterSpec("view_mode", "View", "single", "choice", options=("single", "12-lead")),
    ParameterSpec("lead_focus", "Lead focus", "II", "choice", options=(
        "I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"
    )),
    ParameterSpec("show_grid", "Grid", True, "bool"),
    ParameterSpec("gain", "Gain", 10, "float", 5, 20, 1, "mm/mV"),
    ParameterSpec("paper_speed", "Paper speed", 25, "float", 12.5, 50, 12.5, "mm/s"),
    ParameterSpec("speed", "Playback speed", 1.0, "float", 0.25, 4.0, 0.25, "x"),
    ParameterSpec("target_fps", "Target FPS", "60", "choice", options=TARGET_FPS_OPTIONS),
    ParameterSpec("export_image", "Export image", "png", "command"),
    ParameterSpec("export_csv", "Export CSV", "csv", "command"),
)


def coerce_parameter_value(param: ParameterSpec, value: Any) -> Any:
    """Convert UI string values into constructor-ready values."""
    if param.kind == "choice":
        if str(value) not in param.options:
            raise ValueError(f"{param.name} must be one of {param.options}")
        return str(value)
    if param.kind == "bool":
        return bool(value)
    if param.kind == "int":
        return int(float(value))
    if param.kind == "float":
        return float(value)
    return value


def create_rhythm(
    key: str, values: Optional[Mapping[str, Any]] = None
) -> ArrhythmiaPattern:
    """Instantiate a rhythm from registry metadata."""
    spec = RHYTHM_REGISTRY[key]
    values = values or {}
    kwargs = {}
    for param in spec.parameters:
        value = values.get(param.name, param.default)
        kwargs[param.name] = coerce_parameter_value(param, value)
    return spec.rhythm_cls(**kwargs)
