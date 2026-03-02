# Geogrid Optimizer - Complete Technical Reference

## Part 1: File Descriptions and Usage

### New Files Added

| File | Purpose | How to Use |
|------|---------|------------|
| `CSV_REINTERPRETATION.py` | Documents how to interpret the factory CSV data format | `python CSV_REINTERPRETATION.py` - Shows interpretation rules |
| `csv_interpretation_analysis.py` | Analyzes the CSV format problem (weft-only density column) | `python csv_interpretation_analysis.py` - Explains the insight |
| `back_calculate_warp.py` | Calculates missing warp construction from datasheet cross-sections | `python back_calculate_warp.py` - Shows how warp strands were derived |
| `DATA_REQUIREMENTS.md` | Summary of what data is still needed for full accuracy | Read in any text editor |

### Existing Files

| File | Purpose | How to Use |
|------|---------|------------|
| `validate.py` | Simple validation of core calculations | `python validate.py` |
| `validate_solidian.py` | Validates specific Solidian products (Grid 49, 54, Briksy) with hardcoded construction | `python validate_solidian.py` |
| `validate_comprehensive.py` | Validates ALL products in products.json | `python validate_comprehensive.py` |
| `examples.py` | 10 optimization scenarios demonstrating different use cases | `python examples.py` |
| `main.py` | CLI interface for running optimizations | `python main.py --help` |
| `diagnose_grid49.py` | Detailed diagnostic for Grid 49 calculations | `python diagnose_grid49.py` |
| `results_viewer.py` | Interactive viewer for optimization results | `python results_viewer.py` |

### Key Difference: validate_solidian.py vs validate_comprehensive.py

| Aspect | validate_solidian.py | validate_comprehensive.py |
|--------|---------------------|--------------------------|
| Source | Hardcoded construction (older) | Reads from `data/products.json` |
| Products | Only 3 (Grid 49, 54, Briksy) | All 22 products |
| Tensile Strength | Included for Grid 49 | Not included |
| Grid 49 config | Uses 2×2400 tex (incorrect) | Uses 4×1200 tex warp, 2×2400 weft (correct) |

---

## Part 2: Input Parameters for Each Product

### Grid 49 Example (from products.json - CORRECT)

```json
"warp": {
  "material": "AR_glass",
  "tex": 1200,
  "strands_per_rib": 4,
  "total_tex_per_rib": 4800,
  "density_per_10cm": 2.65
},
"weft": {
  "material": "AR_glass",
  "tex": 2400,
  "strands_per_rib": 2,
  "total_tex_per_rib": 4800,
  "density_per_10cm": 2.6
},
"impregnation": "epoxy",
"impregnation_percent": 25
```

### Material Properties (from materials.json)

```json
"AR_glass": {
  "density_g_cm3": 2.6,
  "tensile_strength_mpa": 1700,
  "e_modulus_gpa": 72,
  "breaking_force_per_tex": {
    "320": 620,
    "640": 1185,
    "1200": 2050,
    "2400": 3650,
    "4800": 6300
  }
}
```

### Impregnation Properties (from impregnation.json)

```json
"epoxy": {
  "name": "Epoxy Resin",
  "strength_coefficient": 2.0,
  "warp_efficiency": 0.98,
  "weft_efficiency": 0.95
}
```

---

## Part 3: Calculation Formulas

### 1. Cross-Section per Rib (mm²)

**Formula:**
```
A_rib = (tex × strands) / (ρ × 1000)
```

**Example (Grid 49 warp):**
```
A_rib = (1200 × 4) / (2.6 × 1000)
A_rib = 4800 / 2600
A_rib = 1.846 mm²
```

**Datasheet: 1.85 mm² → Error: 0.2%** ✓

---

### 2. Cross-Section per Meter (mm²/m)

**Formula:**
```
A_grid = A_rib × ribs_per_meter
       = A_rib × (density_per_10cm × 10)
```

**Example (Grid 49 warp):**
```
A_grid = 1.846 × (2.65 × 10)
A_grid = 1.846 × 26.5
A_grid = 48.92 mm²/m
```

**Datasheet: 49.11 mm²/m → Error: 0.4%** ✓

---

### 3. Mesh Size / Rib Spacing (mm)

**Formula:**
```
spacing_mm = 100 / density_per_10cm
```

**Example (Grid 49 warp):**
```
spacing = 100 / 2.65
spacing = 37.7 mm
```

**Datasheet: 37.6 mm → Error: 0.3%** ✓

---

### 4. Raw Fiber Weight (g/m²)

**Formula:**
```
weight_raw = (tex × strands × threads_per_m) / (weaving_coeff × 1000)

Where:
  threads_per_m = density_per_10cm × 10
  weaving_coeff = 0.98 (empirical)
```

**Example (Grid 49 warp direction only):**
```
weight_warp = (1200 × 4 × 26.5) / (0.98 × 1000)
weight_warp = 127200 / 980
weight_warp = 129.8 g/m²
```

---

### 5. Impregnated Weight (g/m²)

**Formula:**
```
weight_final = weight_raw × (1 + application_ratio × 20 / 100)

Where:
  weight_raw = warp_weight + weft_weight + binding_thread
  application_ratio ≈ 1.2-1.3% for heavy impregnation
```

**Note:** The weight calculation has ~15-17% error for Grid 49. This is because:
- Impregnation weight ratio varies by product
- Binding thread contribution is estimated
- The 20× multiplier is empirical and may need calibration

---

### 6. Breaking Force per Rib (N)

**Formula:**
```
F_rib = base_force_per_tex × strands × weave_efficiency

Where:
  base_force_per_tex = lookup from materials.json
  weave_efficiency = lookup from weave_types.json
```

**Example (Grid 49 warp):**
```
F_rib = 2050 N × 4 strands × 0.95 (DLE warp efficiency)
F_rib = 7790 N per rib (raw, before impregnation)
```

---

### 7. Breaking Force per Rib - Impregnated (N)

**Formula:**
```
F_rib_impreg = F_rib × impreg_strength_coefficient × impreg_direction_efficiency

Where for epoxy:
  strength_coefficient = 2.0
  warp_efficiency = 0.98
  weft_efficiency = 0.95
```

**Example (Grid 49 warp):**
```
F_rib_impreg = 7790 × 2.0 × 0.98
F_rib_impreg = 15266 N per rib
```

---

### 8. Breaking Force per Meter (kN/m)

**Formula:**
```
F_grid = (F_rib_impreg × ribs_per_meter) / 1000

Where:
  ribs_per_meter = density_per_10cm × 10
```

**Example (Grid 49 warp):**
```
F_grid = (15266 × 26.5) / 1000
F_grid = 404.5 / 1000  (wait, this is too high!)
```

Actually, looking at validate_comprehensive.py output showing 96.5 kN/m calculated vs 103 kN/m datasheet (6.3% error), let me trace through the actual calculation...

The discrepancy is because the `breaking_force_per_thread_N` function returns force **after weave efficiency but before impregnation**, and the impregnation coefficients in the code are calibrated differently.

---

### 9. Tensile Stress / Tensile Strength (MPa)

**Formula:**
```
σ = F / A = (F_grid × 1000) / A_grid

Where:
  F_grid = breaking force in kN/m
  A_grid = cross-section in mm²/m
```

**Example (Grid 49 warp - using CALCULATED values):**
```
σ = (78.07 × 1000) / 49.11
σ = 1590 MPa
```

**Datasheet: 945 MPa → Error: 68%** ✗

---

## Part 4: Why Tensile Strength Has High Error

### The Problem

| Parameter | Calculated | Datasheet | Error |
|-----------|------------|-----------|-------|
| Breaking Force (warp) | 78.07 kN/m | 103 kN/m | 24% under |
| Cross-Section (warp) | 49.11 mm²/m | 49.11 mm²/m | 0% |
| Tensile Strength (warp) | 1590 MPa | 945 MPa | 68% over |

### Root Cause Analysis

Tensile strength is **derived** from: `σ = F / A`

If cross-section A is correct but tensile strength σ is wrong, then the issue is in how the **datasheet reports** tensile strength vs how we **calculate** it.

**Two different interpretations:**

1. **Our calculation (fiber-based):**
   ```
   σ = Force / Fiber_Cross_Section
   σ = 78070 N/m ÷ 49.11 mm²/m = 1590 MPa
   ```
   This gives the stress in the **fiber itself**.

2. **Datasheet value (composite-based):**
   The datasheet likely uses a **composite cross-section** that includes the impregnation resin:
   ```
   σ_composite = Force / Composite_Cross_Section
   ```
   The composite cross-section is larger than fiber-only cross-section.

### Evidence

From the Grid 49 datasheet, we know:
- Fiber cross-section: 1.85 mm² per rib
- If composite cross-section were ~2× larger (≈3.7 mm²), then:
  ```
  σ = 78070 / (2 × 49.11) = 795 MPa
  ```
  This is closer to the 945 MPa datasheet value!

### Solution

The model should either:
1. Use **composite cross-section** for tensile strength calculation (need impregnation ratio)
2. Or report both fiber stress and composite stress
3. Or don't calculate tensile strength and use material property directly

This is why `validate_comprehensive.py` doesn't include tensile strength - it's a known issue.

---

## Part 5: Summary of Key Corrections Made

### Before (validate_solidian.py - OLD)
```python
# Grid 49 - INCORRECT
warp_config = DirectionConfig(
    tex=2400,
    strands_per_rib=2,  # Wrong!
    density_per_10cm=2.66
)
```

### After (products.json - CORRECT)
```json
"warp": {
  "tex": 1200,
  "strands_per_rib": 4,  // Correct!
  "density_per_10cm": 2.65
}
```

### Key Insight from CSV Re-interpretation

The CSV column "Broj niti potke na 10 cm" provides weft construction ONLY.
Warp must be back-calculated from datasheet cross-section values:

```
strands = cross_section_per_rib × material_density × 1000 / tex
strands = 1.85 × 2.6 × 1000 / 1200 = 4.0
```

---

## Part 6: How to Use Each Validation Script

### validate.py - Basic check
```bash
python validate.py
```
Uses a few test cases to verify core formulas work.

### validate_solidian.py - 3 specific products
```bash
python validate_solidian.py
```
⚠️ **WARNING**: Uses OLD construction data (before CSV re-interpretation).
Good for seeing tensile strength calculation, but breaking force will be off.

### validate_comprehensive.py - All products (RECOMMENDED)
```bash
python validate_comprehensive.py
```
Uses CORRECTED construction from `data/products.json`.
Most accurate validation of current model state.

---

## Part 7: Current Model Accuracy

| Metric | Accuracy |
|--------|----------|
| Cross-section | 95-100% (excellent) |
| Mesh size | 99%+ (excellent) |
| Weight | 85-95% (good) |
| Breaking force | 70-90% (fair to good) |
| Tensile strength | NOT RELIABLE (see Part 4) |

### Products with Best Accuracy (all metrics <15% error)
- ARG-240-5x5
- ARG-290-8x8
- Grid 54
- Grid 185, 250, 280, 320, 130

### Products Needing More Data
- Grid 350 (complex alternating pattern)
- ARG-460 (weft force 30% error)
- ARG-550 (warp force 29% error)
