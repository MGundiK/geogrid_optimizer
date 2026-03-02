# Geogrid Optimizer

A Python package for calculating and optimizing geogrid textile reinforcement properties using multi-objective genetic algorithms.

## Features

- **Grid Property Calculations**: Calculate breaking force, weight, aperture, cross-section, and stress for any grid configuration
- **Multi-Objective Optimization**: Find Pareto-optimal designs using NSGA-II algorithm
- **Flexible Configuration**: Support for asymmetric warp/weft designs, multiple materials, weave types, and impregnations
- **Production-Aligned Formulas**: Based on real production calculation sheets from textile manufacturers

## Installation

```bash
# Clone or copy the package
cd geogrid_optimizer

# No external dependencies required for core functionality
# Optional: install matplotlib/pandas for visualization
pip install matplotlib pandas
```

## Quick Start

### 1. Calculate Properties for a Single Grid

```python
from geogrid_optimizer import create_symmetric_grid

# Create a symmetric AR-glass grid
design = create_symmetric_grid(
    material_code='AR_glass',
    tex=640,
    strands=2,
    density_per_10cm=8,  # 8 ribs per 10cm = 12.5mm spacing
    weave_code='LE',
    impreg_code='SBR_latex'
)

print(design.summary())
print(f"Breaking Force: {design.breaking_force_kN_m('warp'):.1f} kN/m")
print(f"Weight: {design.impregnated_weight_g_m2():.1f} g/m²")
```

### 2. Run Multi-Objective Optimization

```python
from geogrid_optimizer import NSGA2Optimizer, DesignBounds, Constraints

# Define search space
bounds = DesignBounds(
    materials=['AR_glass', 'carbon', 'basalt'],
    weaves=['LE', 'DLE', 'PLE'],
    tex_values=[640, 1200, 2400],
    strands_min=1,
    strands_max=4,
    density_min=5,
    density_max=20
)

# Define constraints (what designs must satisfy)
constraints = Constraints(
    min_breaking_force_warp=50,  # At least 50 kN/m
    min_breaking_force_weft=50,
    max_weight=400  # At most 400 g/m²
)

# Run optimization
optimizer = NSGA2Optimizer(
    bounds=bounds,
    constraints=constraints,
    objectives=['weight', 'neg_strength_min'],  # Minimize weight, maximize strength
    population_size=100,
    max_generations=200
)

pareto_front = optimizer.run()

# View results
for solution in pareto_front[:5]:
    d = solution.design
    print(f"Weight={d.impregnated_weight_g_m2():.0f} g/m², "
          f"Force={d.breaking_force_kN_m('warp'):.1f} kN/m")
```

### 3. Command Line Interface

```bash
# Calculate a specific design
python main.py calculate --material AR_glass --tex 640 --strands 2 --density 8

# Run optimization
python main.py optimize --min-strength 50 --max-weight 400 --output results.json

# List available materials and options
python main.py list

# Run example demonstration
python main.py example
```

## Core Concepts

### Materials

Available fiber materials with their properties:

| Code | Name | Density (g/cm³) | Strength (MPa) |
|------|------|-----------------|----------------|
| AR_glass | AR-Glass (Alkali Resistant) | 2.6 | 1700 |
| E_glass | E-Glass | 2.54 | 3450 |
| carbon | Carbon Fiber | 1.75 | 4900 |
| basalt | Basalt Fiber | 2.7 | 3000 |
| PP | Polypropylene | 0.91 | 550 |

### Weave Types

| Code | Name | η_warp | η_weft | Description |
|------|------|--------|--------|-------------|
| LE | Half Leno (Gauze) | 0.95 | 0.92 | Standard geogrid construction |
| DLE | Double Leno | 0.97 | 0.94 | Higher efficiency, better load transfer |
| PLE | Plain + Leno | 0.94 | 0.91 | Hybrid construction |

### Key Formulas

**Cross-section per rib:**
```
A_rib = (tex × strands) / (ρ × 1000)  [mm²]
```

**Material usage:**
```
usage = (threads_per_m × tex) / (0.98 × 1000)  [g/m²]
```

**Breaking force per meter:**
```
F = F_thread × threads_per_m × η_weave × η_impreg / 1000  [kN/m]
```

**Aperture:**
```
clear_aperture = rib_spacing - thread_thickness  [mm]
```

## Configuration Files

The system uses JSON configuration files in the `data/` directory:

- `materials.json`: Material properties and tex-to-breaking-force lookup
- `weave_types.json`: Weave construction types with efficiency factors
- `impregnation.json`: Impregnation types and their strength coefficients
- `thread_thickness.json`: Empirical thread thickness lookup table

### Calibrating the Model

To match your production data, adjust these parameters:

1. **Material strength**: Update `tex_breaking_force` in `materials.json`
2. **Weave efficiency**: Adjust `eta_warp` and `eta_weft` in `weave_types.json`
3. **Impregnation coefficients**: Modify strength coefficients in `impregnation.json`

## Optimization Objectives

Available objectives for multi-objective optimization:

- `weight`: Minimize impregnated weight (g/m²)
- `neg_strength_warp`: Maximize warp breaking force
- `neg_strength_weft`: Maximize weft breaking force
- `neg_strength_min`: Maximize minimum of warp/weft force
- `cost`: Minimize cost (requires cost data in materials)

## API Reference

### GridDesign

Main class for grid calculations.

```python
design = GridDesign(
    warp=DirectionConfig(...),
    weft=DirectionConfig(...),
    weave_code='LE',
    impreg_code='SBR_latex',
    application_ratio_percent=1.2
)

# Properties
design.breaking_force_kN_m('warp')
design.impregnated_weight_g_m2()
design.clear_aperture_mm('warp')
design.cross_section_per_meter_mm2('warp')
design.tensile_stress_mpa('warp')

# Export
design.properties_dict()  # All properties as dict
design.summary()  # Human-readable summary
```

### NSGA2Optimizer

Multi-objective optimizer using NSGA-II algorithm.

```python
optimizer = NSGA2Optimizer(
    bounds=DesignBounds(...),
    constraints=Constraints(...),
    objectives=['weight', 'neg_strength_min'],
    population_size=100,
    max_generations=200,
    seed=42  # For reproducibility
)

results = optimizer.run(verbose=True)
optimizer.export_results('pareto_front.json')
```

## File Structure

```
geogrid_optimizer/
├── __init__.py
├── main.py              # CLI entry point
├── validate.py          # Validation against production data
├── requirements.txt
├── README.md
├── data/
│   ├── materials.json
│   ├── weave_types.json
│   ├── impregnation.json
│   └── thread_thickness.json
├── models/
│   ├── __init__.py
│   ├── material.py
│   ├── weave.py
│   ├── impregnation.py
│   └── grid.py
└── optimizer/
    ├── __init__.py
    └── nsga2.py
```

## Future Extensions

Planned features for future versions:

1. **Visualization**: Pareto frontier plots, design space exploration
2. **Cost Optimization**: Include material costs in optimization
3. **Additional Constraints**: E-modulus, elongation, durability
4. **Export Formats**: Excel, CSV, production specification sheets
5. **GUI**: Web-based interface for interactive design exploration

## License

MIT License

## Contributing

Contributions welcome! Please read the code documentation and follow the existing patterns.
