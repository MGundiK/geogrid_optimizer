# Geogrid Optimizer Model Documentation

## Overview

The model predicts geogrid properties from **construction parameters**. It can work in two directions:

1. **Forward**: Given construction → Calculate properties (for optimization)
2. **Backward**: Given properties → Estimate construction (for validation/reverse engineering)

---

## Part 1: Model Input Variables (What You Provide)

### Primary Inputs (Required)

| Variable | Symbol | Unit | Description | Example |
|----------|--------|------|-------------|---------|
| **Material code** | - | - | Fiber type identifier | `AR_glass`, `E_glass`, `carbon` |
| **Tex (warp)** | `tex_w` | g/1000m | Linear density of warp fiber | 1200 |
| **Tex (weft)** | `tex_f` | g/1000m | Linear density of weft fiber | 2400 |
| **Strands per rib (warp)** | `n_w` | count | Number of fiber bundles per warp rib | 4 |
| **Strands per rib (weft)** | `n_f` | count | Number of fiber bundles per weft rib | 2 |
| **Density (warp)** | `d_w` | ribs/10cm | Warp ribs per 10 centimeters | 2.65 |
| **Density (weft)** | `d_f` | ribs/10cm | Weft ribs per 10 centimeters | 2.60 |
| **Weave type** | - | - | Weaving pattern | `DLE` (Double Leno) |
| **Impregnation type** | - | - | Coating/binder type | `epoxy`, `styrene_butadiene` |

### Secondary Inputs (Optional, have defaults)

| Variable | Symbol | Unit | Description | Default |
|----------|--------|------|-------------|---------|
| **Impregnation %** | `imp%` | % | Percentage of impregnation by weight | From type |
| **Application ratio** | `app` | ratio | Extra impregnation application factor | 1.0 |

---

## Part 2: Material Database (Calibrated Constants)

These values come from **lab testing** and are stored in `data/materials.json`:

### Breaking Force by Tex (AR-Glass, Owens Corning)

| Tex | Breaking Force (N) | Cross-section (mm²) | N/tex ratio |
|-----|-------------------|---------------------|-------------|
| 320 | 174.3 | 0.123 | 0.54 |
| 640 | 300.5 | 0.246 | 0.47 |
| 1200 | 481.3 | 0.462 | 0.40 |
| 2400 | 775.8 | 0.923 | 0.32 |
| 4800 | 1200.0 | 1.846 | 0.25 |

**Key insight**: N/tex ratio DECREASES with larger bundles (efficiency loss in bigger rovings)

### Material Density

| Material | Density (g/cm³) |
|----------|-----------------|
| AR-Glass | 2.60 |
| E-Glass | 2.54 |
| Carbon | 1.75 |
| Basalt | 2.67 |

---

## Part 3: Efficiency Coefficients (Calibrated from Products)

Stored in `data/impregnation.json` and `data/weave_types.json`:

### Impregnation Efficiency (η_impreg)

| Type | η_warp | η_weft | Notes |
|------|--------|--------|-------|
| **Epoxy (high-perf)** | 1.95 | 2.025 | Best fiber-matrix bonding |
| **Styrene-butadiene** | 1.38 | 1.44 | Standard FLEX GRID |
| **SBR-latex** | 1.21 | 1.32 | Economy option |

### Weave Efficiency (η_weave)

| Weave | η_warp | η_weft | Description |
|-------|--------|--------|-------------|
| **DLE** (Double Leno) | 0.97 | 0.94 | Most common |
| **LE** (Leno) | 0.95 | 0.92 | Standard |
| **PLE** (Plain Leno) | 0.93 | 0.90 | Basic |

---

## Part 4: Calculated Variables (Model Outputs)

### 4.1 Fiber Cross-Section per Rib

**Formula:**
```
A_rib = tex × n / (ρ × 1000)
```

Where:
- `A_rib` = Cross-section per rib (mm²)
- `tex` = Fiber tex value
- `n` = Number of strands per rib
- `ρ` = Material density (g/cm³)

**Example (Grid 49 warp):**
```
A_rib = 1200 × 4 / (2.6 × 1000) = 1.846 mm²
```

---

### 4.2 Cross-Section per Meter

**Formula:**
```
A_m = A_rib × d × 10
```

Where:
- `A_m` = Cross-section per meter width (mm²/m)
- `d` = Density (ribs/10cm)

**Example (Grid 49 warp):**
```
A_m = 1.846 × 2.65 × 10 = 48.92 mm²/m
```

---

### 4.3 Mesh Size (Clear Aperture)

**Formula:**
```
mesh = 1000 / (d × 10) - rib_width
```

Simplified (ignoring rib width):
```
mesh ≈ 100 / d
```

**Example (Grid 49):**
```
mesh = 100 / 2.65 = 37.7 mm
```

---

### 4.4 Breaking Force per Rib

**Formula:**
```
F_rib = F_base × n × η_weave × η_impreg
```

Where:
- `F_rib` = Breaking force per rib (N)
- `F_base` = Base breaking force for the tex value (from material database)
- `n` = Number of strands per rib
- `η_weave` = Weave efficiency coefficient
- `η_impreg` = Impregnation efficiency coefficient

**Example (Grid 49 warp):**
```
F_rib = 481.3 × 4 × 0.97 × 1.95 = 3641 N
```

---

### 4.5 Breaking Force per Meter (kN/m)

**Formula:**
```
F_m = F_rib × d × 10 / 1000
```

**Example (Grid 49 warp):**
```
F_m = 3641 × 2.65 × 10 / 1000 = 96.5 kN/m
```

---

### 4.6 Breaking Force per 5cm (N/5cm)

**Formula:**
```
F_5cm = F_m × 1000 × 0.05 = F_m × 50
```

**Example:**
```
F_5cm = 96.5 × 50 = 4825 N/5cm
```

---

### 4.7 Raw Weight (Fiber Only)

**Formula:**
```
W_raw = (tex_w × n_w × d_w × 10 + tex_f × n_f × d_f × 10) / 1000
```

**Example (Grid 49):**
```
W_warp = 1200 × 4 × 2.65 × 10 / 1000 = 127.2 g/m²
W_weft = 1200 × 4 × 2.60 × 10 / 1000 = 124.8 g/m²
W_raw = 127.2 + 124.8 = 252.0 g/m²
```

---

### 4.8 Impregnated Weight (Final)

**Formula:**
```
W_final = W_raw × weight_ratio
```

Where `weight_ratio` depends on impregnation %:

| Impreg % | Weight Ratio |
|----------|--------------|
| 14% | 1.16 |
| 16% | 1.19 |
| 20% | 1.25 |
| 25% | 1.33 |

**Example (Grid 49, 25% epoxy):**
```
W_final = 252.0 × 1.33 = 335 g/m²
```

---

### 4.9 Tensile Stress (MPa)

**Formula:**
```
σ = F_m × 1000 / A_m
```

**Example (Grid 49 warp):**
```
σ = 96.5 × 1000 / 48.92 = 1973 MPa
```

---

## Part 5: Validation Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TECHNICAL DATASHEET                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Inputs we READ from datasheet:                          │   │
│  │  • Weight (g/m²)                                        │   │
│  │  • Mesh size warp/weft (mm)                             │   │
│  │  • Breaking force warp/weft (kN/m or N/5cm)             │   │
│  │  • Fiber cross-section (mm²) - if available             │   │
│  │  • Impregnation type and %                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CONSTRUCTION DATABASE (products.json)           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Inputs we KNOW from factory/CSV:                        │   │
│  │  • tex_warp, tex_weft                                   │   │
│  │  • strands_per_rib (warp/weft)                          │   │
│  │  • density_per_10cm (warp/weft)                         │   │
│  │  • impregnation_type                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL CALCULATION                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Using formulas from Part 4:                             │   │
│  │  • Calculate cross-section from tex × strands           │   │
│  │  • Calculate breaking force from base × efficiency      │   │
│  │  • Calculate weight from fiber usage + impreg           │   │
│  │  • Calculate mesh size from density                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        COMPARISON                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ For each variable:                                      │   │
│  │                                                         │   │
│  │   Error % = |Calculated - Datasheet| / Datasheet × 100  │   │
│  │                                                         │   │
│  │   ✓ Good:    < 15%                                      │   │
│  │   ⚠ Warning: 15-25%                                     │   │
│  │   ✗ High:    > 25%                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Variable Summary Table

| Variable | Symbol | Calculated From | Used For |
|----------|--------|-----------------|----------|
| **Cross-section/rib** | A_rib | tex, strands, density | Force, stress |
| **Cross-section/m** | A_m | A_rib, density | Force/m, stress |
| **Breaking force/rib** | F_rib | F_base, strands, η | Force/m |
| **Breaking force/m** | F_m | F_rib, density | Specification |
| **Mesh size** | mesh | density | Specification |
| **Raw weight** | W_raw | tex, strands, density | Final weight |
| **Final weight** | W_final | W_raw, impreg% | Specification |
| **Tensile stress** | σ | F_m, A_m | Specification |

---

## Part 7: What Each Validation Script Does

### `validate.py` - Original Production Data
- Tests against your original production calculation sheets
- Uses products like AR-240-5x5, AR-460-25x25

### `validate_solidian.py` - Solidian Datasheets
- Tests against official Solidian technical datasheets
- Uses Grid 49, Grid 54, Briksy

### `validate_comprehensive.py` - Full Product Database
- Tests ALL products in `products.json`
- Uses construction data from factory CSV + datasheets
- Most complete validation

---

## Part 8: Calibration Dependencies

```
                    ┌──────────────────┐
                    │  LAB TEST DATA   │
                    │  (breaking_forces│
                    │   CSV files)     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ materials.json   │
                    │ (tex → force     │
                    │  lookup table)   │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ PRODUCT DATA    │ │ DATASHEET       │ │ impregnation    │
│ (products.json) │ │ VALUES          │ │ .json           │
│                 │ │ (known outputs) │ │ (η coefficients)│
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   VALIDATION     │
                    │   (compare calc  │
                    │    vs datasheet) │
                    └──────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ If error > 15%:  │
                    │ Adjust η or      │
                    │ construction     │
                    └──────────────────┘
```

---

## Quick Reference: Formulas

```python
# Cross-section per rib (mm²)
A_rib = tex * strands / (density_material * 1000)

# Cross-section per meter (mm²/m)
A_m = A_rib * ribs_per_10cm * 10

# Mesh size (mm)
mesh = 100 / ribs_per_10cm

# Breaking force per rib (N)
F_rib = F_base[tex] * strands * η_weave * η_impreg

# Breaking force per meter (kN/m)
F_m = F_rib * ribs_per_10cm * 10 / 1000

# Breaking force per 5cm (N/5cm)
F_5cm = F_m * 50

# Raw weight (g/m²)
W_raw = Σ(tex * strands * ribs_per_10cm * 10) / 1000

# Final weight (g/m²)
W_final = W_raw * (1 + impreg% / 100) * loss_factor
```
