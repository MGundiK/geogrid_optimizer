#!/usr/bin/env python3
"""
Geogrid Optimizer - Example Scenarios

This script demonstrates different optimization scenarios beyond just
min-strength/max-weight.

Run with: python examples.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import (
    GridDesign,
    DirectionConfig,
    create_symmetric_grid,
    get_material_db
)
from optimizer import NSGA2Optimizer, DesignBounds, Constraints


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_solution(design, idx, show_cost=False):
    """Print a single design solution."""
    print(f"\n  Solution {idx}:")
    print(f"    Material: {design.warp.material_code}")
    print(f"    Tex: {design.warp.tex} × {design.warp.strands_per_rib} strands = {design.warp.total_tex_per_rib:.0f} total")
    print(f"    Density: {design.warp.density_per_10cm}/10cm")
    print(f"    Weave: {design.weave_code}, Impreg: {design.impreg_code}")
    print(f"    ---")
    print(f"    Weight: {design.impregnated_weight_g_m2():.1f} g/m²")
    print(f"    Breaking force: {design.breaking_force_kN_m('warp'):.1f} kN/m")
    print(f"    Mesh size: {design.clear_aperture_mm('warp'):.1f} mm")
    print(f"    Cross-section: {design.fiber_cross_section_mm2_per_m('warp'):.1f} mm²/m")
    if show_cost:
        # Estimate cost
        cost = design.impregnated_weight_g_m2() / 100 * 2.5  # Rough estimate
        print(f"    Est. cost: ~{cost:.2f} EUR/m²")


def example_1_basic():
    """Example 1: Basic strength vs weight trade-off."""
    print_header("EXAMPLE 1: Basic Optimization (Strength vs Weight)")
    print("""
    Goal: Find designs that maximize strength while minimizing weight
    Constraint: Minimum 50 kN/m breaking force
    
    Command equivalent:
    python main.py optimize --min-strength 50
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass'],
        weaves=['LE', 'DLE'],
        impregnations=['SBR_latex', 'epoxy'],
        tex_values=[640, 1200, 2400],
        strands_min=1,
        strands_max=4,
        density_min=3,
        density_max=15,
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=50,
        min_breaking_force_weft=50
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['weight', 'neg_strength_min'],
        population_size=50,
        max_generations=100,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} Pareto-optimal solutions")
    print("\nTop 3 by weight (lightest first):")
    
    results.sort(key=lambda x: x.design.impregnated_weight_g_m2())
    for i, ind in enumerate(results[:3], 1):
        print_solution(ind.design, i)


def example_2_fixed_tex():
    """Example 2: Optimize with fixed tex value."""
    print_header("EXAMPLE 2: Fixed Tex Optimization")
    print("""
    Goal: Given I only have 1200 tex rovings, what's the best design?
    Constraint: Use only 1200 tex
    
    This is useful when you have limited material options.
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass'],
        weaves=['LE', 'DLE'],
        impregnations=['SBR_latex', 'epoxy'],
        tex_values=[1200],  # FIXED to 1200 tex only
        strands_min=1,
        strands_max=6,
        density_min=2,
        density_max=15,
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=60,
        min_breaking_force_weft=60
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['weight', 'neg_strength_min'],
        population_size=50,
        max_generations=100,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} solutions using 1200 tex")
    print("\nTop 3 by weight:")
    
    results.sort(key=lambda x: x.design.impregnated_weight_g_m2())
    for i, ind in enumerate(results[:3], 1):
        print_solution(ind.design, i)


def example_3_fixed_strands():
    """Example 3: Optimize with fixed strands per rib."""
    print_header("EXAMPLE 3: Fixed Strands Optimization")
    print("""
    Goal: My loom can only handle 2 strands per rib. Find optimal tex.
    Constraint: Exactly 2 strands per rib
    
    This simulates equipment limitations.
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass'],
        weaves=['DLE'],
        impregnations=['epoxy'],
        tex_values=[320, 640, 1200, 2400],  # Various tex options
        strands_min=2,
        strands_max=2,  # FIXED to 2 strands
        density_min=3,
        density_max=12,
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=80,
        min_breaking_force_weft=80
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['weight', 'neg_strength_min'],
        population_size=50,
        max_generations=100,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} solutions with 2 strands")
    print("\nTop 3 by strength:")
    
    results.sort(key=lambda x: -x.design.breaking_force_kN_m('warp'))
    for i, ind in enumerate(results[:3], 1):
        d = ind.design
        print(f"\n  Solution {i}:")
        print(f"    Tex: {d.warp.tex} × 2 = {d.warp.total_tex_per_rib:.0f} total")
        print(f"    Density: {d.warp.density_per_10cm}/10cm")
        print(f"    Breaking force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        print(f"    Weight: {d.impregnated_weight_g_m2():.1f} g/m²")


def example_4_target_mesh():
    """Example 4: Optimize with target mesh size."""
    print_header("EXAMPLE 4: Target Mesh Size")
    print("""
    Goal: I need ~25mm mesh for concrete aggregate interlock.
    Constraint: Mesh size must be 25±3mm
    
    Useful for application-specific requirements.
    """)
    
    # 25mm mesh = 100/25 = 4 ribs/10cm = density 4.0
    target_density = 100.0 / 25.0  # 4.0/10cm
    
    bounds = DesignBounds(
        materials=['AR_glass'],
        weaves=['LE', 'DLE'],
        impregnations=['epoxy'],
        tex_values=[1200, 2400],
        strands_min=1,
        strands_max=6,
        density_min=3.5,  # ~28mm mesh
        density_max=4.5,  # ~22mm mesh
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=90,
        min_breaking_force_weft=90,
        target_mesh_size=25,
        mesh_size_tolerance=3
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['weight', 'neg_strength_min'],
        population_size=50,
        max_generations=100,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} solutions with ~25mm mesh")
    print("\nTop 3 by strength:")
    
    results.sort(key=lambda x: -x.design.breaking_force_kN_m('warp'))
    for i, ind in enumerate(results[:3], 1):
        d = ind.design
        print(f"\n  Solution {i}:")
        print(f"    Tex: {d.warp.tex} × {d.warp.strands_per_rib} = {d.warp.total_tex_per_rib:.0f} total")
        print(f"    Density: {d.warp.density_per_10cm}/10cm")
        print(f"    Mesh size: {d.clear_aperture_mm('warp'):.1f} mm ✓")
        print(f"    Breaking force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        print(f"    Weight: {d.impregnated_weight_g_m2():.1f} g/m²")


def example_5_max_cross_section():
    """Example 5: Optimize with target cross-section."""
    print_header("EXAMPLE 5: Target Cross-Section")
    print("""
    Goal: I need ~50 mm²/m fiber cross-section for structural calculation.
    Constraint: Cross-section ≥ 50 mm²/m
    
    Useful when design is driven by Eurocode calculations.
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass', 'carbon'],
        weaves=['DLE'],
        impregnations=['epoxy'],
        tex_values=[640, 1200, 2400],
        strands_min=1,
        strands_max=8,
        density_min=2,
        density_max=10,
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_cross_section=50,  # mm²/m minimum
        max_weight=500
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['weight', 'cross_section'],  # Minimize both
        population_size=50,
        max_generations=100,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} solutions with ≥50 mm²/m cross-section")
    print("\nTop 3 by weight:")
    
    results.sort(key=lambda x: x.design.impregnated_weight_g_m2())
    for i, ind in enumerate(results[:3], 1):
        d = ind.design
        print(f"\n  Solution {i}:")
        print(f"    Material: {d.warp.material_code}")
        print(f"    Tex: {d.warp.tex} × {d.warp.strands_per_rib}")
        print(f"    Density: {d.warp.density_per_10cm}/10cm")
        print(f"    Cross-section: {d.fiber_cross_section_mm2_per_m('warp'):.1f} mm²/m ✓")
        print(f"    Breaking force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        print(f"    Weight: {d.impregnated_weight_g_m2():.1f} g/m²")


def example_6_strength_to_weight():
    """Example 6: Maximize strength-to-weight ratio."""
    print_header("EXAMPLE 6: Best Strength-to-Weight Ratio")
    print("""
    Goal: Find the most efficient design (highest kN/m per g/m²)
    Objective: Maximize strength/weight ratio
    
    Useful for lightweight high-performance applications.
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass', 'carbon', 'basalt'],
        weaves=['LE', 'DLE'],
        impregnations=['SBR_latex', 'epoxy'],
        tex_values=[640, 1200, 2400],
        strands_min=1,
        strands_max=4,
        density_min=2,
        density_max=15,
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=30  # Minimum usable strength
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['neg_strength_to_weight'],  # Single objective: maximize ratio
        population_size=80,
        max_generations=150,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} solutions")
    print("\nTop 5 by strength/weight ratio:")
    
    # Sort by strength/weight ratio
    results.sort(key=lambda x: -x.design.breaking_force_kN_m('warp') / x.design.impregnated_weight_g_m2())
    
    for i, ind in enumerate(results[:5], 1):
        d = ind.design
        ratio = d.breaking_force_kN_m('warp') / d.impregnated_weight_g_m2()
        print(f"\n  Solution {i}:")
        print(f"    Material: {d.warp.material_code}")
        print(f"    Tex: {d.warp.tex} × {d.warp.strands_per_rib}")
        print(f"    Impreg: {d.impreg_code}")
        print(f"    Strength/Weight: {ratio:.4f} kN·m/g")
        print(f"    Breaking force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        print(f"    Weight: {d.impregnated_weight_g_m2():.1f} g/m²")


def example_7_material_comparison():
    """Example 7: Compare materials for same target."""
    print_header("EXAMPLE 7: Material Comparison")
    print("""
    Goal: Compare AR-glass vs Carbon vs Basalt for 80 kN/m target
    
    Shows trade-offs between materials.
    """)
    
    materials = ['AR_glass', 'carbon', 'basalt']
    
    for material in materials:
        print(f"\n--- {material.upper()} ---")
        
        bounds = DesignBounds(
            materials=[material],
            weaves=['DLE'],
            impregnations=['epoxy'],
            tex_values=[640, 1200, 2400],
            strands_min=1,
            strands_max=6,
            density_min=2,
            density_max=12,
            allow_asymmetric=False
        )
        
        constraints = Constraints(
            min_breaking_force_warp=80,
            min_breaking_force_weft=80
        )
        
        optimizer = NSGA2Optimizer(
            bounds=bounds,
            constraints=constraints,
            objectives=['weight'],
            population_size=40,
            max_generations=80,
            seed=42
        )
        
        results = optimizer.run(verbose=False)
        
        if results:
            best = min(results, key=lambda x: x.design.impregnated_weight_g_m2())
            d = best.design
            print(f"  Best: {d.warp.tex}×{d.warp.strands_per_rib} @ {d.warp.density_per_10cm}/10cm")
            print(f"  Weight: {d.impregnated_weight_g_m2():.1f} g/m²")
            print(f"  Force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        else:
            print("  No feasible solution found")


def example_8_cost_optimization():
    """Example 8: Cost-driven optimization."""
    print_header("EXAMPLE 8: Cost vs Performance Trade-off")
    print("""
    Goal: Find cheapest design that meets 60 kN/m
    Objective: Minimize cost (approximated)
    
    Note: Cost data is placeholder - update with real prices!
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass', 'E_glass'],  # Compare expensive vs cheap
        weaves=['LE', 'DLE'],
        impregnations=['SBR_latex', 'epoxy'],  # Cheap vs expensive
        tex_values=[640, 1200, 2400],
        strands_min=1,
        strands_max=5,
        density_min=3,
        density_max=12,
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=60,
        min_breaking_force_weft=60
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['cost', 'neg_strength_min'],  # Minimize cost, maximize strength
        population_size=60,
        max_generations=120,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} Pareto-optimal solutions")
    print("\nTop 3 by estimated cost (cheapest first):")
    
    # Sort by cost
    results.sort(key=lambda x: x.objectives[0])
    for i, ind in enumerate(results[:3], 1):
        d = ind.design
        cost = ind.objectives[0]
        print(f"\n  Solution {i}:")
        print(f"    Material: {d.warp.material_code}")
        print(f"    Impreg: {d.impreg_code}")
        print(f"    Tex: {d.warp.tex} × {d.warp.strands_per_rib}")
        print(f"    Est. Cost: {cost:.2f} EUR/m²")
        print(f"    Breaking force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        print(f"    Weight: {d.impregnated_weight_g_m2():.1f} g/m²")


def example_9_calculate_tex_from_target():
    """Example 9: Back-calculate: what tex do I need?"""
    print_header("EXAMPLE 9: Back-Calculate Tex Requirement")
    print("""
    Goal: I need 100 kN/m with 3 strands/rib at 4/10cm density.
          What tex value should I use?
    
    This is the INVERSE calculation - finding construction from target.
    """)
    
    # Given parameters
    target_force = 100  # kN/m
    strands = 3
    density = 4.0  # /10cm
    material = 'AR_glass'
    
    print(f"\n  Target: {target_force} kN/m")
    print(f"  Fixed: {strands} strands/rib, {density}/10cm density")
    print(f"  Material: {material}")
    
    # Try different tex values
    tex_options = [320, 640, 1200, 2400, 4800]
    
    print(f"\n  Tex scan results:")
    print(f"  {'Tex':<8} {'Force (kN/m)':<15} {'Status'}")
    print(f"  {'-'*40}")
    
    best_tex = None
    best_diff = float('inf')
    
    for tex in tex_options:
        design = create_symmetric_grid(
            material_code=material,
            tex=tex,
            strands=strands,
            density_per_10cm=density,
            impreg_code='epoxy'
        )
        force = design.breaking_force_kN_m('warp')
        diff = abs(force - target_force)
        
        status = "✓ CLOSE" if diff < 10 else ("↑ too high" if force > target_force else "↓ too low")
        print(f"  {tex:<8} {force:<15.1f} {status}")
        
        if diff < best_diff:
            best_diff = diff
            best_tex = tex
    
    print(f"\n  → Best match: {best_tex} tex (error: {best_diff:.1f} kN/m)")
    
    # Show the winning design
    best_design = create_symmetric_grid(
        material_code=material,
        tex=best_tex,
        strands=strands,
        density_per_10cm=density,
        impreg_code='epoxy'
    )
    print(f"\n  Full specification:")
    print(f"    {material}, {best_tex} tex × {strands} strands @ {density}/10cm")
    print(f"    Breaking force: {best_design.breaking_force_kN_m('warp'):.1f} kN/m")
    print(f"    Weight: {best_design.impregnated_weight_g_m2():.1f} g/m²")


def example_10_aperture_optimization():
    """Example 10: Maximize aperture (for concrete penetration)."""
    print_header("EXAMPLE 10: Maximum Aperture Design")
    print("""
    Goal: Largest possible mesh opening while meeting strength
    Constraint: Minimum 40 kN/m, mesh ≥ 20mm
    
    For concrete applications requiring aggregate penetration.
    """)
    
    bounds = DesignBounds(
        materials=['AR_glass'],
        weaves=['LE', 'DLE'],
        impregnations=['epoxy'],
        tex_values=[1200, 2400, 4800],  # Larger tex for fewer ribs
        strands_min=2,
        strands_max=8,
        density_min=2,  # Large mesh
        density_max=5,  # Still reasonable
        allow_asymmetric=False
    )
    
    constraints = Constraints(
        min_breaking_force_warp=40,
        min_breaking_force_weft=40,
        min_aperture_warp=20,
        min_aperture_weft=20
    )
    
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=['neg_aperture', 'weight'],  # Maximize aperture, minimize weight
        population_size=50,
        max_generations=100,
        seed=42
    )
    
    results = optimizer.run(verbose=False)
    
    print(f"\nFound {len(results)} solutions")
    print("\nTop 3 by aperture size:")
    
    results.sort(key=lambda x: -x.design.clear_aperture_mm('warp'))
    for i, ind in enumerate(results[:3], 1):
        d = ind.design
        print(f"\n  Solution {i}:")
        print(f"    Tex: {d.warp.tex} × {d.warp.strands_per_rib}")
        print(f"    Density: {d.warp.density_per_10cm}/10cm")
        print(f"    Aperture: {d.clear_aperture_mm('warp'):.1f} mm ← LARGE")
        print(f"    Breaking force: {d.breaking_force_kN_m('warp'):.1f} kN/m")
        print(f"    Weight: {d.impregnated_weight_g_m2():.1f} g/m²")


def main():
    """Run all examples."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GEOGRID OPTIMIZER - EXAMPLE SCENARIOS                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  This demonstrates various optimization scenarios you can run.                ║
║  Each example shows different ways to use constraints and objectives.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    examples = [
        ("1", "Basic strength vs weight", example_1_basic),
        ("2", "Fixed tex value", example_2_fixed_tex),
        ("3", "Fixed strands per rib", example_3_fixed_strands),
        ("4", "Target mesh size", example_4_target_mesh),
        ("5", "Target cross-section", example_5_max_cross_section),
        ("6", "Best strength/weight ratio", example_6_strength_to_weight),
        ("7", "Material comparison", example_7_material_comparison),
        ("8", "Cost optimization", example_8_cost_optimization),
        ("9", "Back-calculate tex", example_9_calculate_tex_from_target),
        ("10", "Maximum aperture", example_10_aperture_optimization),
    ]
    
    print("Available examples:")
    for num, desc, _ in examples:
        print(f"  {num}: {desc}")
    
    print("\nEnter example number (or 'all' to run all): ", end="")
    
    try:
        choice = input().strip().lower()
    except EOFError:
        choice = 'all'
    
    if choice == 'all':
        for num, desc, func in examples:
            func()
    else:
        for num, desc, func in examples:
            if num == choice:
                func()
                break
        else:
            print(f"Unknown example: {choice}")


if __name__ == '__main__':
    main()
