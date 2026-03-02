#!/usr/bin/env python3
"""
Validation script to compare calculated values against production data.

This script recreates the AR-240-5x5 grid from the production sheets
and compares calculated values against the known production values.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import GridDesign, DirectionConfig, get_material_db


def validate_ar_240_5x5():
    """
    Validate against AR-240-5x5 production data.
    
    From the production sheet (razrada_artikla images):
    - Material: AR-glass (Cem-Fil 5325 640)
    - Warp: tex=640, 1 strand, density=16/10cm (160 threads/m)
    - Weft: tex=640, 1 strand, density=15/10cm (150 threads/m)
    - Binding thread: PES 22 tex
    - Impregnation: SBR-latex, application ratio 1.2%
    
    Expected values:
    - Raw weight: ~201.99 g/m²
    - Impregnated weight: ~242.39 g/m²
    - Breaking force: ~50 kN/m (warp), ~53 kN/m (weft)
    - Cross-section: 39.38 mm²/m (warp), 36.92 mm²/m (weft)
    """
    print("=" * 70)
    print("VALIDATION: AR-240-5x5 Grid")
    print("=" * 70)
    
    # Create the grid design matching production specs
    warp_config = DirectionConfig(
        material_code='AR_glass',
        tex=640,
        strands_per_rib=1,
        density_per_10cm=16  # 160 threads/m
    )
    
    weft_config = DirectionConfig(
        material_code='AR_glass',
        tex=640,
        strands_per_rib=1,
        density_per_10cm=15  # 150 threads/m
    )
    
    design = GridDesign(
        warp=warp_config,
        weft=weft_config,
        weave_code='LE2',  # With binding thread
        impreg_code='SBR_latex',
        application_ratio_percent=1.2
    )
    
    # Production values (from the sheets)
    production = {
        'raw_weight': 201.99,
        'impreg_weight': 242.39,
        'warp_usage': 102.40,
        'weft_usage': 96.00,
        'binding_weight': 3.59,
        'breaking_force_warp': 49.56,
        'breaking_force_weft': 52.80,
        'cross_section_warp': 39.38,
        'cross_section_weft': 36.92,
        'thread_cross_section': 0.246,
        'aperture_spacing_warp': 6.250,
        'aperture_spacing_weft': 6.667,
    }
    
    # Calculate values
    calculated = {
        'raw_weight': design.raw_weight_g_m2(),
        'impreg_weight': design.impregnated_weight_g_m2(),
        'warp_usage': design._direction_usage_g_m2('warp'),
        'weft_usage': design._direction_usage_g_m2('weft'),
        'breaking_force_warp': design.breaking_force_kN_m('warp'),
        'breaking_force_weft': design.breaking_force_kN_m('weft'),
        'cross_section_warp': design.cross_section_per_meter_mm2('warp'),
        'cross_section_weft': design.cross_section_per_meter_mm2('weft'),
        'thread_cross_section': design.cross_section_per_rib_mm2('warp'),
        'aperture_spacing_warp': design.rib_spacing_mm('warp'),
        'aperture_spacing_weft': design.rib_spacing_mm('weft'),
    }
    
    # Compare
    print(f"\n{'Parameter':<25} {'Production':<15} {'Calculated':<15} {'Diff %':<10}")
    print("-" * 70)
    
    for key in production:
        prod_val = production[key]
        calc_val = calculated.get(key, 'N/A')
        
        if isinstance(calc_val, (int, float)) and prod_val != 0:
            diff_pct = abs(calc_val - prod_val) / prod_val * 100
            status = "✓" if diff_pct < 10 else "⚠" if diff_pct < 20 else "✗"
            print(f"{key:<25} {prod_val:<15.2f} {calc_val:<15.2f} {diff_pct:<8.1f}% {status}")
        else:
            print(f"{key:<25} {prod_val:<15} {calc_val:<15}")
    
    print()
    print("Notes:")
    print("- Raw weight difference may be due to binding thread calculation")
    print("- Breaking force depends on impregnation coefficient calibration")
    print("- Cross-section calculations should be exact (same formula)")
    print()
    
    return design


def validate_ar_460_25x25():
    """
    Validate against AR-460-25x25 production data.
    
    From the production sheet:
    - Material: AR-glass
    - Warp: tex=1200+640 (2 strands each), density=3.33/10cm, 4 threads/pair
    - Weft: tex=2400, density=3.33/10cm, 2 threads/pair
    - Impregnation: SBR-latex, application ratio 1.4%
    
    Expected values:
    - Raw weight: ~326.20 g/m²
    - Impregnated weight: ~456.69 g/m²
    - Breaking force: ~63.44 kN/m (warp), ~67.13 kN/m (weft)
    """
    print("=" * 70)
    print("VALIDATION: AR-460-25x25 Grid")
    print("=" * 70)
    
    # This is a more complex construction with mixed tex
    # Warp has 1200 tex (2 strands) + 640 tex (2 strands) = 4 total
    warp_config = DirectionConfig(
        material_code='AR_glass',
        tex=1200,
        strands_per_rib=2,
        density_per_10cm=3.33,
        secondary_tex=640,
        secondary_strands=2
    )
    
    # Weft has 2400 tex, 2 strands per pair
    weft_config = DirectionConfig(
        material_code='AR_glass',
        tex=2400,
        strands_per_rib=2,
        density_per_10cm=3.33
    )
    
    design = GridDesign(
        warp=warp_config,
        weft=weft_config,
        weave_code='LE',  # No binding thread mentioned
        impreg_code='SBR_latex',
        application_ratio_percent=1.4
    )
    
    production = {
        'raw_weight': 326.20,
        'impreg_weight': 456.69,
        'breaking_force_warp': 63.44,
        'breaking_force_weft': 67.13,
        'cross_section_warp': 61.48,
        'cross_section_weft': 61.48,
        'aperture_spacing_warp': 30.03,
        'aperture_spacing_weft': 30.03,
    }
    
    calculated = {
        'raw_weight': design.raw_weight_g_m2(),
        'impreg_weight': design.impregnated_weight_g_m2(),
        'breaking_force_warp': design.breaking_force_kN_m('warp'),
        'breaking_force_weft': design.breaking_force_kN_m('weft'),
        'cross_section_warp': design.cross_section_per_meter_mm2('warp'),
        'cross_section_weft': design.cross_section_per_meter_mm2('weft'),
        'aperture_spacing_warp': design.rib_spacing_mm('warp'),
        'aperture_spacing_weft': design.rib_spacing_mm('weft'),
    }
    
    print(f"\n{'Parameter':<25} {'Production':<15} {'Calculated':<15} {'Diff %':<10}")
    print("-" * 70)
    
    for key in production:
        prod_val = production[key]
        calc_val = calculated.get(key, 'N/A')
        
        if isinstance(calc_val, (int, float)) and prod_val != 0:
            diff_pct = abs(calc_val - prod_val) / prod_val * 100
            status = "✓" if diff_pct < 10 else "⚠" if diff_pct < 20 else "✗"
            print(f"{key:<25} {prod_val:<15.2f} {calc_val:<15.2f} {diff_pct:<8.1f}% {status}")
        else:
            print(f"{key:<25} {prod_val:<15} {calc_val:<15}")
    
    print()
    
    return design


if __name__ == '__main__':
    design1 = validate_ar_240_5x5()
    print()
    design2 = validate_ar_460_25x25()
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print("""
Key observations:
1. Cross-section calculations match well (same formula)
2. Weight calculations may differ due to:
   - Weaving coefficient variations
   - Binding thread weight estimation
   - Impregnation weight ratio formula
3. Breaking force differences depend on:
   - Efficiency factors (η_warp, η_weft)
   - Impregnation strength coefficients
   - Base breaking force values

The model can be calibrated by adjusting:
- Material tex_breaking_force values in materials.json
- Weave efficiency factors in weave_types.json
- Impregnation coefficients in impregnation.json
""")
