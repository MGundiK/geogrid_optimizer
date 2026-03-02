#!/usr/bin/env python3
"""
Detailed results viewer for optimization output.

Provides:
- Deduplication of Pareto front
- Detailed configuration export
- Comparison tables
- Filtering by criteria
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import GridDesign, DirectionConfig, get_material_db
from optimizer import NSGA2Optimizer, DesignBounds, Constraints


def design_signature(design: GridDesign) -> str:
    """Create a unique signature for a design to detect duplicates."""
    return (
        f"{design.warp.material_code}|"
        f"{design.warp.tex}|{design.warp.strands_per_rib}|{design.warp.density_per_10cm:.2f}|"
        f"{design.weft.tex}|{design.weft.strands_per_rib}|{design.weft.density_per_10cm:.2f}|"
        f"{design.weave_code}|{design.impreg_code}"
    )


def deduplicate_pareto_front(pareto_front):
    """Remove duplicate solutions from Pareto front."""
    seen = set()
    unique = []
    for ind in pareto_front:
        sig = design_signature(ind.design)
        if sig not in seen:
            seen.add(sig)
            unique.append(ind)
    return unique


def print_detailed_solution(design: GridDesign, index: int):
    """Print detailed breakdown of a single solution."""
    print(f"\n{'='*70}")
    print(f"SOLUTION {index} - DETAILED BREAKDOWN")
    print(f"{'='*70}")
    
    mat_db = get_material_db()
    warp_mat = mat_db.get(design.warp.material_code)
    weft_mat = mat_db.get(design.weft.material_code)
    
    print(f"\n--- MATERIAL & CONSTRUCTION ---")
    print(f"  Warp Material:      {warp_mat.name if warp_mat else design.warp.material_code}")
    print(f"  Weft Material:      {weft_mat.name if weft_mat else design.weft.material_code}")
    print(f"  Weave Type:         {design.weave.name} ({design.weave_code})")
    print(f"  Impregnation:       {design.impregnation.name}")
    
    print(f"\n--- WARP DIRECTION ---")
    print(f"  Tex per strand:     {design.warp.tex} g/1000m")
    print(f"  Strands per rib:    {design.warp.strands_per_rib}")
    print(f"  Total tex per rib:  {design.warp.total_tex_per_rib} g/1000m")
    print(f"  Density:            {design.warp.density_per_10cm} ribs/10cm")
    print(f"  Threads per meter:  {design.warp.threads_per_meter}")
    print(f"  Rib spacing:        {design.rib_spacing_mm('warp'):.2f} mm")
    
    print(f"\n--- WEFT DIRECTION ---")
    print(f"  Tex per strand:     {design.weft.tex} g/1000m")
    print(f"  Strands per rib:    {design.weft.strands_per_rib}")
    print(f"  Total tex per rib:  {design.weft.total_tex_per_rib} g/1000m")
    print(f"  Density:            {design.weft.density_per_10cm} ribs/10cm")
    print(f"  Threads per meter:  {design.weft.threads_per_meter}")
    print(f"  Rib spacing:        {design.rib_spacing_mm('weft'):.2f} mm")
    
    print(f"\n--- CALCULATED PROPERTIES ---")
    print(f"  {'Property':<30} {'Warp':<15} {'Weft':<15}")
    print(f"  {'-'*60}")
    print(f"  {'Cross-section (mm²/m)':<30} {design.cross_section_per_meter_mm2('warp'):<15.2f} {design.cross_section_per_meter_mm2('weft'):<15.2f}")
    print(f"  {'Cross-section per rib (mm²)':<30} {design.cross_section_per_rib_mm2('warp'):<15.4f} {design.cross_section_per_rib_mm2('weft'):<15.4f}")
    print(f"  {'Breaking force (kN/m)':<30} {design.breaking_force_kN_m('warp'):<15.2f} {design.breaking_force_kN_m('weft'):<15.2f}")
    print(f"  {'Breaking force (N/5cm)':<30} {design.breaking_force_N_5cm('warp'):<15.1f} {design.breaking_force_N_5cm('weft'):<15.1f}")
    print(f"  {'Tensile stress (MPa)':<30} {design.tensile_stress_mpa('warp'):<15.1f} {design.tensile_stress_mpa('weft'):<15.1f}")
    print(f"  {'Clear aperture (mm)':<30} {design.clear_aperture_mm('warp'):<15.2f} {design.clear_aperture_mm('weft'):<15.2f}")
    
    print(f"\n--- WEIGHT BREAKDOWN ---")
    print(f"  Warp material usage:    {design._direction_usage_g_m2('warp'):.2f} g/m²")
    print(f"  Weft material usage:    {design._direction_usage_g_m2('weft'):.2f} g/m²")
    print(f"  Raw weight (total):     {design.raw_weight_g_m2():.2f} g/m²")
    print(f"  Impregnation added:     {design.impregnation_weight_g_m2():.2f} g/m²")
    print(f"  Final weight:           {design.impregnated_weight_g_m2():.2f} g/m²")
    
    print(f"\n--- EFFICIENCY FACTORS APPLIED ---")
    print(f"  Weave η (warp):         {design.weave.eta_warp}")
    print(f"  Weave η (weft):         {design.weave.eta_weft}")
    print(f"  Impreg η (warp):        {design.impregnation.total_strength_coefficient('warp'):.3f}")
    print(f"  Impreg η (weft):        {design.impregnation.total_strength_coefficient('weft'):.3f}")


def compare_solutions_table(solutions, max_show=20):
    """Print a comparison table of multiple solutions."""
    print(f"\n{'='*120}")
    print("SOLUTION COMPARISON TABLE")
    print(f"{'='*120}")
    
    header = (
        f"{'#':<3} {'Material':<12} {'Weave':<6} {'Tex(W)':<8} {'Tex(F)':<8} "
        f"{'Str(W)':<6} {'Str(F)':<6} {'Den(W)':<8} {'Den(F)':<8} "
        f"{'Force(W)':<10} {'Force(F)':<10} {'Weight':<8} {'Aper(W)':<8}"
    )
    print(header)
    print("-" * 120)
    
    for i, ind in enumerate(solutions[:max_show], 1):
        d = ind.design
        row = (
            f"{i:<3} {d.warp.material_code:<12} {d.weave_code:<6} "
            f"{d.warp.tex:<8.0f} {d.weft.tex:<8.0f} "
            f"{d.warp.strands_per_rib:<6} {d.weft.strands_per_rib:<6} "
            f"{d.warp.density_per_10cm:<8.2f} {d.weft.density_per_10cm:<8.2f} "
            f"{d.breaking_force_kN_m('warp'):<10.1f} {d.breaking_force_kN_m('weft'):<10.1f} "
            f"{d.impregnated_weight_g_m2():<8.1f} {d.clear_aperture_mm('warp'):<8.1f}"
        )
        print(row)
    
    if len(solutions) > max_show:
        print(f"\n... and {len(solutions) - max_show} more solutions")


def run_optimization_with_details(
    min_strength=50,
    max_weight=400,
    materials=None,
    show_top=10,
    show_detailed=3
):
    """Run optimization and show detailed results."""
    
    bounds = DesignBounds(
        materials=materials or ['AR_glass', 'carbon', 'basalt'],
        weaves=['LE', 'DLE', 'PLE'],
        impregnations=['SBR_latex', 'epoxy'],
        tex_values=[320, 640, 800, 1200, 1600, 2400, 3200],
        strands_min=1,
        strands_max=6,
        density_min=2,
        density_max=20,
        allow_asymmetric=True
    )
    
    constraints = Constraints(
        min_breaking_force_warp=min_strength,
        min_breaking_force_weft=min_strength,
        max_weight=max_weight
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['weight', 'neg_strength_min'],
        population_size=100,
        max_generations=100,
        seed=42
    )
    
    print("Running optimization...")
    pareto_front = optimizer.run(verbose=True)
    
    # Deduplicate
    unique_solutions = deduplicate_pareto_front(pareto_front)
    print(f"\nAfter deduplication: {len(unique_solutions)} unique solutions "
          f"(removed {len(pareto_front) - len(unique_solutions)} duplicates)")
    
    # Sort by weight
    unique_solutions.sort(key=lambda x: x.design.impregnated_weight_g_m2())
    
    # Show comparison table
    compare_solutions_table(unique_solutions, max_show=show_top)
    
    # Show detailed view of top solutions
    print(f"\n\nDETAILED VIEW OF TOP {show_detailed} SOLUTIONS:")
    for i, ind in enumerate(unique_solutions[:show_detailed], 1):
        print_detailed_solution(ind.design, i)
    
    return unique_solutions


def filter_solutions(solutions, **criteria):
    """
    Filter solutions by criteria.
    
    Example:
        filter_solutions(solutions, 
            material='AR_glass',
            min_aperture=20,
            max_weight=300)
    """
    filtered = []
    
    for ind in solutions:
        d = ind.design
        match = True
        
        if 'material' in criteria:
            if d.warp.material_code != criteria['material']:
                match = False
        
        if 'weave' in criteria:
            if d.weave_code != criteria['weave']:
                match = False
        
        if 'min_aperture' in criteria:
            min_ap = min(d.clear_aperture_mm('warp'), d.clear_aperture_mm('weft'))
            if min_ap < criteria['min_aperture']:
                match = False
        
        if 'max_weight' in criteria:
            if d.impregnated_weight_g_m2() > criteria['max_weight']:
                match = False
        
        if 'min_strength' in criteria:
            min_str = min(d.breaking_force_kN_m('warp'), d.breaking_force_kN_m('weft'))
            if min_str < criteria['min_strength']:
                match = False
        
        if match:
            filtered.append(ind)
    
    return filtered


if __name__ == '__main__':
    print("=" * 70)
    print("GEOGRID OPTIMIZER - DETAILED RESULTS VIEWER")
    print("=" * 70)
    
    # Run optimization
    solutions = run_optimization_with_details(
        min_strength=50,
        max_weight=400,
        show_top=15,
        show_detailed=3
    )
    
    # Example: Filter for AR-glass only
    print("\n\n" + "=" * 70)
    print("FILTERED: AR-Glass solutions only")
    print("=" * 70)
    ar_glass_solutions = filter_solutions(solutions, material='AR_glass')
    if ar_glass_solutions:
        compare_solutions_table(ar_glass_solutions, max_show=10)
    else:
        print("No AR-glass solutions found meeting constraints.")
    
    # Example: Filter for large aperture
    print("\n\n" + "=" * 70)
    print("FILTERED: Solutions with aperture ≥ 25mm")
    print("=" * 70)
    large_aperture = filter_solutions(solutions, min_aperture=25)
    if large_aperture:
        compare_solutions_table(large_aperture, max_show=10)
    else:
        print("No solutions with aperture ≥ 25mm found.")
