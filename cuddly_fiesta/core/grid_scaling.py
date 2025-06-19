"""ECG grid scaling and validation constants.

This module provides constants and utilities for maintaining proper ECG grid scaling
and validation of timing and voltage values against standard ECG paper specifications.
"""

# Standard ECG parameters (in mm)
PAPER_SPEED_MM_PER_SEC = 25.0  # Standard paper speed (25 mm/s)
VOLTAGE_SCALE_MM_PER_MV = 10.0  # Standard calibration (10 mm/mV)

# Derived grid dimensions
SMALL_SQUARE_MM = 1.0  # 1mm per small square
LARGE_SQUARE_MM = 5.0  # 5mm per large square (5 small squares)

# Time calculations (seconds)
SMALL_SQUARE_TIME_SEC = SMALL_SQUARE_MM / PAPER_SPEED_MM_PER_SEC  # 0.04s
LARGE_SQUARE_TIME_SEC = LARGE_SQUARE_MM / PAPER_SPEED_MM_PER_SEC  # 0.20s

# Voltage calculations (mV)
SMALL_SQUARE_VOLTAGE_MV = SMALL_SQUARE_MM / VOLTAGE_SCALE_MM_PER_MV  # 0.1 mV
LARGE_SQUARE_VOLTAGE_MV = LARGE_SQUARE_MM / VOLTAGE_SCALE_MM_PER_MV  # 0.5 mV


class GridScaling:
    """Immutable grid scaling constants and validation utilities.
    
    This class provides methods to validate that ECG timing and voltage values
    align with standard ECG grid specifications. All values are treated as 
    immutable to ensure consistent grid scaling throughout the application.
    """

    # Standard ECG parameters
    PAPER_SPEED_MM_PER_SEC = PAPER_SPEED_MM_PER_SEC
    VOLTAGE_SCALE_MM_PER_MV = VOLTAGE_SCALE_MM_PER_MV

    # Grid dimensions - IMMUTABLE
    SMALL_SQUARE_TIME_SEC = SMALL_SQUARE_TIME_SEC
    SMALL_SQUARE_VOLTAGE_MV = SMALL_SQUARE_VOLTAGE_MV
    LARGE_SQUARE_TIME_SEC = LARGE_SQUARE_TIME_SEC
    LARGE_SQUARE_VOLTAGE_MV = LARGE_SQUARE_VOLTAGE_MV

    @classmethod
    def validate_timing(cls, duration_ms: float) -> bool:
        """Validate that a duration aligns with grid timing.
        
        Args:
            duration_ms: Duration in milliseconds to validate
            
        Returns:
            True if duration is a multiple of the small grid square,
            False otherwise.
        """
        ratio = duration_ms / (cls.SMALL_SQUARE_TIME_SEC * 1000.0)
        return abs(ratio - round(ratio)) < 1e-6

    @classmethod
    def validate_voltage(cls, voltage_mv: float) -> bool:
        """Validate that a voltage aligns with grid scaling.
        
        Args:
            voltage_mv: Voltage in millivolts to validate
            
        Returns:
            True if voltage is a multiple of the small grid square,
            False otherwise.
        """
        # Check if voltage is multiple of small square
        remainder = voltage_mv % cls.SMALL_SQUARE_VOLTAGE_MV
        return abs(remainder) < 1e-10  # Account for floating point precision

    @classmethod
    def snap_to_grid_time(cls, time_sec: float) -> float:
        """Snap a time value to the nearest grid line.
        
        Args:
            time_sec: Time in seconds to snap to grid
            
        Returns:
            Time value snapped to the nearest small grid line
        """
        grid_units = round(time_sec / cls.SMALL_SQUARE_TIME_SEC)
        return grid_units * cls.SMALL_SQUARE_TIME_SEC

    @classmethod
    def snap_to_grid_voltage(cls, voltage_mv: float) -> float:
        """Snap a voltage value to the nearest grid line.
        
        Args:
            voltage_mv: Voltage in millivolts to snap to grid
            
        Returns:
            Voltage value snapped to the nearest small grid line
        """
        grid_units = round(voltage_mv / cls.SMALL_SQUARE_VOLTAGE_MV)
        return grid_units * cls.SMALL_SQUARE_VOLTAGE_MV
