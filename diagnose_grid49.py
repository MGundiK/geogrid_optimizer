#!/usr/bin/env python3
"""
Diagnostic analysis for solidian ANTISEISMIC Grid 49 calibration.

This script investigates why our model under-predicts breaking force for Grid 49.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import GridDesign, DirectionConfig, get_material_db


def diagnose_grid_49():
    """
    Deep diagnostic of Grid 49 validation gap.
    """
    print("=" * 70)
    print("DIAGNOSTIC: solidian ANTISEISMIC Grid 49")
    print("=" * 70)
    
    # Known values from datasheet
    print("\n1. DATASHEET VALUES:")
    print("-" * 50)
    datasheet = {
        'fiber_material': 'AR-Glass',
        'impregnation': 'Epoxy Resin ≥25%',
        'basis_weight': 385,  # g/m²
        'fiber_cross_section': 1.85,  # mm² per rib
        'cross_section_per_m_warp': 49.11,  # mm²/m
        'cross_section_per_m_weft': 48.00,  # mm²/m
        'mesh_size_warp': 37.6,  # mm
        'mesh_size_weft': 38.4,  # mm
        'breaking_force_warp': 103,  # kN/m average
        'breaking_force_weft': 99,   # kN/m average
        'tensile_strength_warp': 945,  # MPa
        'tensile_strength_weft': 781,  # MPa
    }
    
    for key, val in datasheet.items():
        print(f"  {key}: {val}")
    
    # Reverse-engineer construction
    print("\n2. REVERSE-ENGINEERED CONSTRUCTION:")
    print("-" * 50)
    
    # From fiber cross-section and density
    density = 2.6  # AR-glass g/cm³
    fiber_cs = 1.85  # mm²
    
    # tex = cross_section × density × 1000
    tex_per_rib = fiber_cs * density * 1000
    print(f"  Tex per rib: {tex_per_rib:.0f} g/1000m")
    print(f"  Possible combinations:")
    print(f"    - 2 × 2400 tex = 4800 tex")
    print(f"    - 4 × 1200 tex = 4800 tex")
    print(f"    - 8 × 600 tex  = 4800 tex (unlikely)")
    
    # Ribs per meter from cross-section
    ribs_per_m_warp = datasheet['cross_section_per_m_warp'] / fiber_cs
    ribs_per_m_weft = datasheet['cross_section_per_m_weft'] / fiber_cs
    print(f"\n  Ribs per meter (warp): {ribs_per_m_warp:.2f} = {ribs_per_m_warp/10:.2f} ribs/10cm")
    print(f"  Ribs per meter (weft): {ribs_per_m_weft:.2f} = {ribs_per_m_weft/10:.2f} ribs/10cm")
    
    # Verify mesh size
    spacing_warp = 1000 / ribs_per_m_warp
    spacing_weft = 1000 / ribs_per_m_weft
    print(f"\n  Calculated spacing (warp): {spacing_warp:.1f} mm (datasheet: {datasheet['mesh_size_warp']})")
    print(f"  Calculated spacing (weft): {spacing_weft:.1f} mm (datasheet: {datasheet['mesh_size_weft']})")
    
    # Calculate required breaking force per rib
    print("\n3. BACK-CALCULATE REQUIRED STRAND STRENGTH:")
    print("-" * 50)
    
    force_per_rib_warp = datasheet['breaking_force_warp'] * 1000 / ribs_per_m_warp  # N
    force_per_rib_weft = datasheet['breaking_force_weft'] * 1000 / ribs_per_m_weft  # N
    
    print(f"  Required force per rib (warp): {force_per_rib_warp:.1f} N")
    print(f"  Required force per rib (weft): {force_per_rib_weft:.1f} N")
    
    # What our model gives
    mat_db = get_material_db()
    ar_glass = mat_db['AR_glass']
    
    # Assuming 2×2400 tex per rib
    base_force_2400 = ar_glass.get_breaking_force(2400)
    print(f"\n  Our base force for 2400 tex AR-glass: {base_force_2400:.1f} N")
    print(f"  For 2 strands (raw): {base_force_2400 * 2:.1f} N")
    
    # With current efficiency factors
    eta_weave_warp = 0.97  # DLE
    eta_weave_weft = 0.94
    eta_impreg_warp = 1.95  # Current epoxy coefficient
    eta_impreg_weft = 2.025
    
    model_force_warp = base_force_2400 * 2 * eta_weave_warp * eta_impreg_warp
    model_force_weft = base_force_2400 * 2 * eta_weave_weft * eta_impreg_weft
    
    print(f"\n  Model prediction (warp): {model_force_warp:.1f} N/rib")
    print(f"  Model prediction (weft): {model_force_weft:.1f} N/rib")
    
    # Gap analysis
    print("\n4. GAP ANALYSIS:")
    print("-" * 50)
    
    gap_warp = force_per_rib_warp / model_force_warp
    gap_weft = force_per_rib_weft / model_force_weft
    
    print(f"  Warp: Datasheet/Model = {gap_warp:.3f} ({(gap_warp-1)*100:+.1f}% gap)")
    print(f"  Weft: Datasheet/Model = {gap_weft:.3f} ({(gap_weft-1)*100:+.1f}% gap)")
    
    # What would fix it
    print("\n5. CALIBRATION OPTIONS TO CLOSE THE GAP:")
    print("-" * 50)
    
    print("\n  Option A: Increase epoxy coefficient")
    required_impreg_warp = eta_impreg_warp * gap_warp
    required_impreg_weft = eta_impreg_weft * gap_weft
    print(f"    Current epoxy η (warp): {eta_impreg_warp}")
    print(f"    Required epoxy η (warp): {required_impreg_warp:.2f}")
    print(f"    Current epoxy η (weft): {eta_impreg_weft}")
    print(f"    Required epoxy η (weft): {required_impreg_weft:.2f}")
    
    print("\n  Option B: Increase base breaking force for 2400 tex AR-glass")
    required_base_warp = force_per_rib_warp / (2 * eta_weave_warp * eta_impreg_warp)
    required_base_weft = force_per_rib_weft / (2 * eta_weave_weft * eta_impreg_weft)
    print(f"    Current base force (2400 tex): {base_force_2400:.1f} N")
    print(f"    Required base force (from warp): {required_base_warp:.1f} N")
    print(f"    Required base force (from weft): {required_base_weft:.1f} N")
    
    print("\n  Option C: Use higher strand count (if construction is 4×1200 instead of 2×2400)")
    base_force_1200 = ar_glass.get_breaking_force(1200)
    model_force_4x1200_warp = base_force_1200 * 4 * eta_weave_warp * eta_impreg_warp
    model_force_4x1200_weft = base_force_1200 * 4 * eta_weave_weft * eta_impreg_weft
    print(f"    Base force for 1200 tex: {base_force_1200:.1f} N")
    print(f"    4×1200 prediction (warp): {model_force_4x1200_warp:.1f} N/rib")
    print(f"    4×1200 prediction (weft): {model_force_4x1200_weft:.1f} N/rib")
    print(f"    Gap with 4×1200 (warp): {force_per_rib_warp/model_force_4x1200_warp:.3f}")
    
    print("\n6. ROOT CAUSE ANALYSIS:")
    print("-" * 50)
    print("""
  The gap can be explained by one or more factors:
  
  1. CONSTRUCTION UNCERTAINTY
     - We assumed 2×2400 tex, but it could be 4×1200 tex
     - Different strand configurations have different efficiency
     - Solidian may use a proprietary construction
  
  2. MATERIAL BATCH VARIATION
     - Our calibration data is from Owens Corning AR-glass
     - Solidian may use a different supplier or grade
     - Higher-quality roving could have better base strength
  
  3. IMPREGNATION PROCESS OPTIMIZATION
     - Solidian's epoxy impregnation is highly optimized
     - Different products may have different impregnation quality
     - Grid 49 may have better fiber-matrix bonding than Grid 54
  
  4. TESTING METHODOLOGY DIFFERENCES
     - Lab testing conditions vary (temperature, grip, speed)
     - Solidian tests follow EAD 340392-00-0104 standard
     - Our calibration data may use different protocols
    """)
    
    print("\n7. RECOMMENDATIONS:")
    print("-" * 50)
    print("""
  To improve Grid 49 prediction accuracy:
  
  1. GET CONSTRUCTION DETAILS
     - Ask Solidian for exact tex/strand configuration
     - Verify if it's 2×2400, 4×1200, or something else
  
  2. CREATE PRODUCT-SPECIFIC CALIBRATION
     - Create "solidian_grid_49" as a specific material/impreg combo
     - Back-calculate efficiency from known output
  
  3. TEST THE ACTUAL MATERIAL
     - If you have access to Grid 49 sample, test strand breaking force
     - This gives the actual base strength with their impregnation
  
  4. USE PRODUCT FAMILY FACTORS
     - Solidian ANTISEISMIC line may have a specific calibration factor
     - Apply a "product family multiplier" (~1.3 for Grid 49)
    """)


def create_calibrated_grid_49():
    """
    Create a Grid 49 design with back-calculated efficiency to match datasheet.
    """
    print("\n" + "=" * 70)
    print("CREATING CALIBRATED GRID 49 MODEL")
    print("=" * 70)
    
    # Use 4×1200 tex which may be closer to actual construction
    warp_config = DirectionConfig(
        material_code='AR_glass',
        tex=1200,
        strands_per_rib=4,  # 4×1200 = 4800 tex total
        density_per_10cm=2.66  # ~37.6mm spacing
    )
    
    weft_config = DirectionConfig(
        material_code='AR_glass',
        tex=1200,
        strands_per_rib=4,
        density_per_10cm=2.60  # ~38.5mm spacing
    )
    
    design = GridDesign(
        warp=warp_config,
        weft=weft_config,
        weave_code='DLE',
        impreg_code='epoxy',
        application_ratio_percent=1.3
    )
    
    print(f"\nUsing 4×1200 tex construction:")
    print(f"  Breaking force (warp): {design.breaking_force_kN_m('warp'):.1f} kN/m (target: 103)")
    print(f"  Breaking force (weft): {design.breaking_force_kN_m('weft'):.1f} kN/m (target: 99)")
    print(f"  Weight: {design.impregnated_weight_g_m2():.1f} g/m² (target: 385)")
    
    # The 4×1200 construction is actually closer!
    # This suggests the product may use finer strands


if __name__ == '__main__':
    diagnose_grid_49()
    create_calibrated_grid_49()
