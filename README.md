# ECG Generator - Modular Architecture

## 🏗️ Design Principles

### **NEVER BREAK GRID SCALING**
- All waveforms must map to clinical grid units at every step
- Standard ECG parameters: 25 mm/sec, 10 mm/mV
- Built-in validation ensures grid compliance
- Automatic snapping to grid units when needed

### **MODULAR & SWAPPABLE**
- Waveform segments are plug-and-play modules
- Arrhythmia patterns can be swapped without recoding
- Grid/baseline logic is reusable foundation
- Easy to add new arrhythmias

## 📁 File Structure

```
.
├── ecg_baseline.py              # Original baseline with clinical markers
├── ecg_core.py                  # Core architecture with immutable grid
├── waveform_segments.py         # Example P-wave & QRS modules
├── requirements.txt             # Dependencies
└── docs/                        # Generated plots (not tracked)
    ├── ecg_baseline_demo.png
    ├── ecg_modular_architecture.png
    └── modular_segments_demo.png
```

### Generating Plots Locally

First, ensure you have installed the necessary dependencies:

```bash
pip install -r requirements.txt

```bash
python ecg_baseline.py          # creates docs/ecg_baseline_demo.png
python waveform_segments.py     # creates docs/modular_segments_demo.png
python p_wave_generator.py      # creates docs/p_wave_clinical_demo.png and p_wave_isolation_test.png
python verify_improvements.py   # creates docs/calibration_verification.png and docs/clinical_markers_verification.png
python test_p_wave_fixes.py     # creates docs/p_wave_physiological_verification.png
```

## 🧩 Architecture Components

### 1. **GridScaling Class** (Immutable)
```python
# NEVER modify these values
PAPER_SPEED_MM_PER_SEC = 25      # 25 mm/sec
VOLTAGE_SCALE_MM_PER_MV = 10     # 10 mm/mV
SMALL_SQUARE_TIME_SEC = 0.04     # 1mm = 0.04 sec
SMALL_SQUARE_VOLTAGE_MV = 0.1    # 1mm = 0.1 mV
```

**Built-in Validation:**
- `validate_timing()` - Ensures durations align with grid
- `validate_amplitude()` - Ensures amplitudes align with grid
- `snap_to_grid_*()` - Auto-corrects to nearest grid unit

### 2. **ECGCore Class** (Foundation)
```python
ecg = ECGCore(duration_sec=10, sampling_rate=1000)
ecg.add_waveform_segment(p_wave, start_time_sec=0.5)
ecg.validate_grid_integrity()  # Always check!
```

**Key Features:**
- Immutable baseline with clinical accuracy
- Segment addition with grid validation
- Inherited grid plotting from ECGBaseline
- Tracking of all added segments

### 3. **WaveformSegment Class** (Abstract Base)
```python
class PWave(WaveformSegment):
    def __init__(self, amplitude_mv=0.15, duration_ms=100):
        # Clinical validation built-in
        super().__init__(duration_ms, amplitude_mv)
    
    def generate(self, sampling_rate):
        # Generate waveform respecting grid scaling
        return time, voltage
```

**Clinical Validation:**
- Duration must be in clinical range
- Amplitude must be reasonable
- Grid alignment automatically enforced

### 4. **ArrhythmiaPattern Class** (Swappable)
```python
class NormalSinusRhythm(ArrhythmiaPattern):
    def define_pattern(self):
        # Define segment timing and relationships
        return pattern_list
    
    def apply_to_ecg(self, ecg_core):
        # Apply pattern to ECG while preserving grid
```

**Pattern Swapping:**
- Same core modules, different arrangements
- Easy to create new arrhythmias
- Grid scaling always preserved

## 🔧 Usage Examples

### Basic ECG with Manual Segments
```python
from ecg_core import ECGCore
from waveform_segments import PWave, QRSComplex

# Create ECG foundation
ecg = ECGCore(duration_sec=5, sampling_rate=1000)

# Add segments manually
p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
qrs = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)

ecg.add_waveform_segment(p_wave, start_time_sec=0.5)
ecg.add_waveform_segment(qrs, start_time_sec=0.8)

# Always validate!
ecg.validate_grid_integrity()

# Plot with grid
fig, ax = ecg.plot_with_grid()
```

### Arrhythmia Pattern Application
```python
from waveform_segments import NormalSinusRhythm

# Create pattern
nsr = NormalSinusRhythm(heart_rate_bpm=75)

# Apply to ECG (automatic grid compliance)
nsr.apply_to_ecg(ecg)

# Grid scaling preserved automatically
ecg.validate_grid_integrity()
```

### Creating New Arrhythmia Modules
```python
class AtrialFibrillation(ArrhythmiaPattern):
    def define_pattern(self):
        # Define irregular P-waves, normal QRS
        pattern = []
        # ... implement AF pattern
        return pattern

# Swap patterns easily
af_pattern = AtrialFibrillation()
af_pattern.apply_to_ecg(ecg)  # Same grid, different arrhythmia
```

## ⚠️ Critical Rules

### **NEVER:**
- Modify `GridScaling` constants
- Skip `validate_grid_integrity()` 
- Create segments without clinical validation
- Break the modular pattern

### **ALWAYS:**
- Use `ECGCore` as foundation
- Inherit from `WaveformSegment` for new segments
- Inherit from `ArrhythmiaPattern` for new patterns
- Validate grid compliance after changes
- Respect clinical parameter ranges

## 🎯 Benefits Achieved

✅ **Grid Scaling Integrity**: Never broken, automatically enforced  
✅ **Clinical Accuracy**: Built-in parameter validation  
✅ **Modularity**: Segments and patterns are plug-and-play  
✅ **Swappable Arrhythmias**: Easy to add new patterns  
✅ **Maintainable Code**: Clear separation of concerns  
✅ **Validation**: Built-in checks at every step  

## 📈 Next Steps

Ready to implement:
1. **T-wave module** with asymmetric morphology
2. **U-wave module** (optional)
3. **Complex arrhythmias**: 
   - Atrial fibrillation
   - Ventricular tachycardia  
   - Heart blocks
   - Premature beats
4. **Advanced features**:
   - Rate variability
   - Axis deviation
   - Multi-lead support

## 🔍 Validation Output Example
```
🔍 Validating Grid Integrity...
✅ Segment PWave: Duration 80.0ms
✅ Segment QRSComplex: Duration 80.0ms  
✅ Grid scaling validation complete. Total segments: 2
```

The architecture ensures clinical accuracy while maintaining code modularity for easy arrhythmia development.
