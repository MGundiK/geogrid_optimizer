#!/usr/bin/env python3
"""
Geogrid Optimizer - Main Entry Point

This module provides CLI interface and example usage for the geogrid
optimization system.

Usage:
    python -m geogrid_optimizer --help
    python -m geogrid_optimizer optimize --strength 50 --max-weight 300
    python -m geogrid_optimizer calculate --material AR_glass --tex 640 --strands 2 --density 8
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, List

# Add parent directory to path for imports when running as script
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

from models import (
    GridDesign,
    DirectionConfig,
    create_symmetric_grid,
    get_material_db,
    get_weave_db,
    get_impregnation_db
)
from optimizer import NSGA2Optimizer, DesignBounds, Constraints


def calculate_single(args):
    """Calculate properties for a single grid configuration."""
    # Create symmetric grid from arguments
    design = create_symmetric_grid(
        material_code=args.material,
        tex=args.tex,
        strands=args.strands,
        density_per_10cm=args.density,
        weave_code=args.weave,
        impreg_code=args.impregnation,
        application_ratio=args.application_ratio
    )
    
    print(design.summary())
    
    if args.json:
        props = design.properties_dict()
        print("\nJSON Output:")
        print(json.dumps(props, indent=2))


def optimize(args):
    """Run multi-objective optimization."""
    # Set up bounds
    bounds = DesignBounds(
        materials=args.materials.split(',') if args.materials else ['AR_glass', 'carbon', 'basalt'],
        weaves=args.weaves.split(',') if args.weaves else ['LE', 'DLE', 'PLE'],
        impregnations=['SBR_latex', 'epoxy'],
        tex_min=args.tex_min,
        tex_max=args.tex_max,
        strands_min=args.strands_min,
        strands_max=args.strands_max,
        density_min=args.density_min,
        density_max=args.density_max,
        allow_asymmetric=args.allow_asymmetric
    )
    
    # Set up constraints
    constraints = Constraints(
        min_breaking_force_warp=args.min_strength,
        min_breaking_force_weft=args.min_strength,
        max_weight=args.max_weight,
        min_aperture_warp=args.min_aperture,
        min_aperture_weft=args.min_aperture
    )
    
    # Set up objectives
    objectives = ['weight', 'neg_strength_min']  # Minimize weight, maximize min strength
    
    # Create and run optimizer
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=objectives,
        population_size=args.population,
        max_generations=args.generations,
        seed=args.seed
    )
    
    pareto_front = optimizer.run(verbose=not args.quiet)
    
    # Display results
    print("\n" + "=" * 70)
    print("PARETO-OPTIMAL SOLUTIONS")
    print("=" * 70)
    
    # Sort by first objective (weight)
    pareto_front.sort(key=lambda x: x.objectives[0])
    
    for i, ind in enumerate(pareto_front[:args.max_display]):
        design = ind.design
        print(f"\n--- Solution {i+1} ---")
        print(f"Weight: {design.impregnated_weight_g_m2():.1f} g/m²")
        print(f"Breaking Force: {design.breaking_force_kN_m('warp'):.1f} / "
              f"{design.breaking_force_kN_m('weft'):.1f} kN/m (warp/weft)")
        print(f"Aperture: {design.clear_aperture_mm('warp'):.1f} × "
              f"{design.clear_aperture_mm('weft'):.1f} mm")
        print(f"Config: {design.warp.material_code}, "
              f"tex={design.warp.total_tex_per_rib:.0f}, "
              f"density={design.warp.density_per_10cm}/10cm, "
              f"weave={design.weave_code}")
    
    if len(pareto_front) > args.max_display:
        print(f"\n... and {len(pareto_front) - args.max_display} more solutions")
    
    # Export if requested
    if args.output:
        optimizer.export_results(args.output)
        print(f"\nResults exported to: {args.output}")


def list_options(args):
    """List available materials, weaves, etc."""
    mat_db = get_material_db()
    weave_db = get_weave_db()
    impreg_db = get_impregnation_db()
    
    print("AVAILABLE MATERIALS:")
    print("-" * 40)
    for code in mat_db.list_materials():
        mat = mat_db[code]
        print(f"  {code:15} - {mat.name}")
        print(f"                    Density: {mat.density_g_cm3} g/cm³, "
              f"Strength: {mat.tensile_strength_mpa} MPa")
    
    print("\nAVAILABLE WEAVE TYPES:")
    print("-" * 40)
    for code in weave_db.list_weaves():
        weave = weave_db[code]
        print(f"  {code:6} - {weave.name}")
        print(f"           η_warp={weave.eta_warp}, η_weft={weave.eta_weft}")
    
    print("\nAVAILABLE IMPREGNATION TYPES:")
    print("-" * 40)
    for code in impreg_db.list_types():
        impreg = impreg_db[code]
        print(f"  {code:15} - {impreg.name}")


def example_usage():
    """Demonstrate example usage of the library."""
    print("=" * 70)
    print("GEOGRID OPTIMIZER - EXAMPLE USAGE")
    print("=" * 70)
    
    # Example 1: Create and analyze a specific grid design
    print("\n1. SINGLE GRID CALCULATION")
    print("-" * 40)
    
    design = create_symmetric_grid(
        material_code='AR_glass',
        tex=640,
        strands=1,
        density_per_10cm=16,  # ~6.25mm spacing
        weave_code='LE',
        impreg_code='SBR_latex',
        application_ratio=1.2
    )
    
    print(design.summary())
    
    # Example 2: Compare different configurations
    print("\n2. CONFIGURATION COMPARISON")
    print("-" * 40)
    
    configs = [
        ('AR_glass', 640, 1, 16),
        ('AR_glass', 640, 2, 8),
        ('AR_glass', 1200, 1, 10),
        ('carbon', 800, 1, 12),
    ]
    
    print(f"{'Material':<12} {'Tex×Str':<10} {'Density':<8} {'Force kN/m':<12} {'Weight g/m²':<12}")
    print("-" * 60)
    
    for mat, tex, strands, density in configs:
        try:
            d = create_symmetric_grid(mat, tex, strands, density)
            force = d.breaking_force_kN_m('warp')
            weight = d.impregnated_weight_g_m2()
            print(f"{mat:<12} {tex}×{strands:<6} {density}/10cm   {force:<12.1f} {weight:<12.1f}")
        except Exception as e:
            print(f"{mat:<12} {tex}×{strands:<6} {density}/10cm   ERROR: {e}")
    
    # Example 3: Quick optimization
    print("\n3. QUICK OPTIMIZATION EXAMPLE")
    print("-" * 40)
    print("Finding designs with ≥50 kN/m strength, minimizing weight...")
    
    bounds = DesignBounds(
        materials=['AR_glass'],
        weaves=['LE', 'DLE'],
        tex_values=[640, 1200, 2400],
        strands_min=1,
        strands_max=4,
        density_min=5,
        density_max=20,
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
        max_generations=50,
        seed=42
    )
    
    results = optimizer.run(verbose=True)
    
    print("\nTop 5 Solutions (by weight):")
    results.sort(key=lambda x: x.design.impregnated_weight_g_m2())
    
    for i, ind in enumerate(results[:5]):
        d = ind.design
        print(f"  {i+1}. Weight={d.impregnated_weight_g_m2():.0f} g/m², "
              f"Force={d.breaking_force_kN_m('warp'):.1f} kN/m, "
              f"tex={d.warp.total_tex_per_rib:.0f}, strands={d.warp.strands_per_rib}, "
              f"density={d.warp.density_per_10cm}/10cm")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Geogrid Design Optimizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate properties for a specific design
  python main.py calculate --material AR_glass --tex 640 --strands 2 --density 8

  # Find optimal designs meeting strength requirements
  python main.py optimize --min-strength 50 --max-weight 400

  # List available materials and options
  python main.py list

  # Run example demonstration
  python main.py example
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Calculate command
    calc_parser = subparsers.add_parser('calculate', help='Calculate grid properties')
    calc_parser.add_argument('--material', '-m', default='AR_glass',
                            help='Material code (default: AR_glass)')
    calc_parser.add_argument('--tex', '-t', type=float, default=640,
                            help='Tex value per strand (default: 640)')
    calc_parser.add_argument('--strands', '-s', type=int, default=1,
                            help='Strands per rib (default: 1)')
    calc_parser.add_argument('--density', '-d', type=float, default=10,
                            help='Rib density per 10cm (default: 10)')
    calc_parser.add_argument('--weave', '-w', default='LE',
                            help='Weave type code (default: LE)')
    calc_parser.add_argument('--impregnation', '-i', default='SBR_latex',
                            help='Impregnation type (default: SBR_latex)')
    calc_parser.add_argument('--application-ratio', '-a', type=float, default=1.2,
                            help='Application ratio %% (default: 1.2)')
    calc_parser.add_argument('--json', '-j', action='store_true',
                            help='Output as JSON')
    
    # Optimize command
    opt_parser = subparsers.add_parser('optimize', help='Run multi-objective optimization')
    opt_parser.add_argument('--min-strength', type=float, default=None,
                           help='Minimum breaking force kN/m')
    opt_parser.add_argument('--max-weight', type=float, default=None,
                           help='Maximum weight g/m²')
    opt_parser.add_argument('--min-aperture', type=float, default=None,
                           help='Minimum clear aperture mm')
    opt_parser.add_argument('--materials', default=None,
                           help='Comma-separated material codes')
    opt_parser.add_argument('--weaves', default=None,
                           help='Comma-separated weave codes')
    opt_parser.add_argument('--tex-min', type=float, default=400,
                           help='Minimum tex (default: 400)')
    opt_parser.add_argument('--tex-max', type=float, default=3000,
                           help='Maximum tex (default: 3000)')
    opt_parser.add_argument('--strands-min', type=int, default=1,
                           help='Minimum strands (default: 1)')
    opt_parser.add_argument('--strands-max', type=int, default=10,
                           help='Maximum strands (default: 10)')
    opt_parser.add_argument('--density-min', type=float, default=2,
                           help='Minimum density/10cm (default: 2)')
    opt_parser.add_argument('--density-max', type=float, default=20,
                           help='Maximum density/10cm (default: 20)')
    opt_parser.add_argument('--allow-asymmetric', action='store_true',
                           help='Allow asymmetric warp/weft designs')
    opt_parser.add_argument('--population', type=int, default=100,
                           help='Population size (default: 100)')
    opt_parser.add_argument('--generations', type=int, default=200,
                           help='Max generations (default: 200)')
    opt_parser.add_argument('--seed', type=int, default=None,
                           help='Random seed for reproducibility')
    opt_parser.add_argument('--output', '-o', default=None,
                           help='Output JSON file for results')
    opt_parser.add_argument('--max-display', type=int, default=10,
                           help='Max solutions to display (default: 10)')
    opt_parser.add_argument('--quiet', '-q', action='store_true',
                           help='Suppress progress output')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available options')
    
    # Example command
    example_parser = subparsers.add_parser('example', help='Run example demonstration')
    
    args = parser.parse_args()
    
    if args.command == 'calculate':
        calculate_single(args)
    elif args.command == 'optimize':
        optimize(args)
    elif args.command == 'list':
        list_options(args)
    elif args.command == 'example':
        example_usage()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
