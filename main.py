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
    
    # Material properties database
    MATERIAL_PROPERTIES = {
        'AR_glass': {'e_modulus_gpa': 72.0, 'tensile_mpa': 1100, 'name': 'AR Glass'},
        'E_glass': {'e_modulus_gpa': 72.4, 'tensile_mpa': 1300, 'name': 'E Glass'},
        'carbon': {'e_modulus_gpa': 230.0, 'tensile_mpa': 1700, 'name': 'Carbon'},
        'basalt': {'e_modulus_gpa': 89.0, 'tensile_mpa': 1100, 'name': 'Basalt'},
    }
    
    # Filter materials by E modulus and tensile strength requirements
    if args.materials:
        materials = args.materials.split(',')
    else:
        materials = list(MATERIAL_PROPERTIES.keys())
        
        # Apply E modulus filter
        if args.min_e_modulus:
            materials = [m for m in materials 
                        if MATERIAL_PROPERTIES[m]['e_modulus_gpa'] >= args.min_e_modulus]
        
        # Apply tensile strength filter
        if args.min_tensile_mpa:
            materials = [m for m in materials 
                        if MATERIAL_PROPERTIES[m]['tensile_mpa'] >= args.min_tensile_mpa]
    
    if not materials:
        print("ERROR: No materials meet the E modulus/tensile strength requirements!")
        print("\nAvailable materials:")
        for code, props in MATERIAL_PROPERTIES.items():
            print(f"  {code}: E={props['e_modulus_gpa']} GPa, σ={props['tensile_mpa']} MPa")
        return
    
    # Show selected materials
    print("=" * 70)
    print("MATERIAL SELECTION")
    print("=" * 70)
    if args.min_e_modulus or args.min_tensile_mpa:
        print(f"Requirements: E ≥ {args.min_e_modulus or 'any'} GPa, σ ≥ {args.min_tensile_mpa or 'any'} MPa")
    print(f"Selected materials: {', '.join(materials)}")
    for m in materials:
        props = MATERIAL_PROPERTIES.get(m, {})
        print(f"  {m}: E={props.get('e_modulus_gpa', '?')} GPa, σ={props.get('tensile_mpa', '?')} MPa")
    print()
    
    # Parse tex values if provided
    if args.tex_values:
        tex_values = [float(t.strip()) for t in args.tex_values.split(',')]
    else:
        tex_values = [320, 640, 1200, 2400, 4800]  # AR glass standard values
    
    # Parse dual-tex pairs if provided (format: "1200+640,2400+1200")
    dual_tex_pairs = None
    if args.dual_tex_pairs:
        args.allow_dual_tex = True  # Implies dual-tex is allowed
        dual_tex_pairs = []
        for pair_str in args.dual_tex_pairs.split(','):
            parts = pair_str.strip().split('+')
            if len(parts) == 2:
                dual_tex_pairs.append((float(parts[0]), float(parts[1])))
        print("=" * 70)
        print("DUAL-TEX CONFIGURATION")
        print("=" * 70)
        print(f"Specified dual-tex pairs:")
        for p, s in dual_tex_pairs:
            print(f"  {p:.0f} tex + {s:.0f} tex")
        print()
    
    # Set up bounds
    bounds = DesignBounds(
        materials=materials,
        weaves=args.weaves.split(',') if args.weaves else ['DLE'],
        impregnations=['styrene_butadiene', 'epoxy'],
        tex_min=args.tex_min,
        tex_max=args.tex_max,
        tex_values=tex_values,
        strands_min=args.strands_min,
        strands_max=args.strands_max,
        density_min=args.density_min,
        density_max=args.density_max,
        allow_asymmetric=args.allow_asymmetric,
        allow_dual_tex=args.allow_dual_tex,
        dual_tex_probability=args.dual_tex_prob,
        dual_tex_pairs=dual_tex_pairs
    )
    
    # Set up constraints
    constraints = Constraints(
        min_breaking_force_warp=args.min_strength,
        min_breaking_force_weft=args.min_strength,
        max_breaking_force_warp=args.max_strength,
        max_breaking_force_weft=args.max_strength,
        max_weight=args.max_weight,
        min_weight=args.min_weight,
        min_aperture_warp=args.min_aperture,
        min_aperture_weft=args.min_aperture,
        max_aperture_warp=args.max_aperture,
        max_aperture_weft=args.max_aperture,
        target_mesh_size=args.mesh_size,
        mesh_size_tolerance=args.mesh_tolerance
    )
    
    # Show constraint summary
    print("=" * 70)
    print("CONSTRAINTS & REQUIREMENTS")
    print("=" * 70)
    
    # Material property requirements
    if args.min_e_modulus or args.min_tensile_mpa:
        print("Material requirements:")
        if args.min_e_modulus:
            print(f"  E modulus ≥ {args.min_e_modulus} GPa ✓ (all selected materials meet this)")
        if args.min_tensile_mpa:
            print(f"  Tensile strength ≥ {args.min_tensile_mpa} MPa ✓ (all selected materials meet this)")
    
    # Design constraints
    print("Design constraints:")
    if args.min_strength or args.max_strength:
        print(f"  Breaking force (kN/m): {args.min_strength or 'any'} - {args.max_strength or 'any'}")
    if args.min_weight or args.max_weight:
        print(f"  Weight (g/m²): {args.min_weight or 'any'} - {args.max_weight or 'any'}")
    if args.mesh_size:
        print(f"  Mesh size: {args.mesh_size} ± {args.mesh_tolerance} mm")
    
    # Construction options
    print("Construction options:")
    print(f"  Asymmetric warp/weft: {'enabled' if args.allow_asymmetric else 'disabled'}")
    if args.allow_dual_tex:
        if dual_tex_pairs:
            print(f"  Dual-tex: enabled with specific pairs")
        else:
            print(f"  Dual-tex: enabled (random, probability: {args.dual_tex_prob})")
    else:
        print(f"  Dual-tex: disabled")
    print()
    
    # Set up objectives from CLI
    objectives = [obj.strip() for obj in args.objectives.split(',')]
    
    # Show objectives
    print("=" * 70)
    print("OPTIMIZATION OBJECTIVES")
    print("=" * 70)
    objective_descriptions = {
        'weight': 'Minimize weight (g/m²)',
        'cost': 'Minimize cost (EUR/m²)',
        'neg_strength_min': 'Maximize minimum strength (kN/m)',
        'neg_strength_warp': 'Maximize warp strength (kN/m)',
        'neg_strength_weft': 'Maximize weft strength (kN/m)',
        'neg_strength_avg': 'Maximize average strength (kN/m)',
        'neg_aperture': 'Maximize mesh opening (mm)',
        'neg_strength_to_weight': 'Maximize strength/weight ratio',
        'total_tex': 'Minimize total tex per rib',
        'cross_section': 'Minimize fiber cross-section'
    }
    for obj in objectives:
        desc = objective_descriptions.get(obj, f'Unknown: {obj}')
        print(f"  • {desc}")
    print()
    
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
    
    if not pareto_front:
        print("\nNo feasible solutions found!")
        print("Try relaxing constraints or expanding search bounds.")
        return
    
    # Deduplicate solutions based on key parameters
    def design_signature(ind):
        d = ind.design
        return (
            d.warp.material_code,
            round(d.warp.tex, 0),
            d.warp.strands_per_rib,
            round(d.warp.density_per_10cm, 1),
            d.warp.secondary_tex,
            d.warp.secondary_strands,
            round(d.weft.tex, 0),
            d.weft.strands_per_rib,
            round(d.weft.density_per_10cm, 1),
            d.weft.secondary_tex,
            d.weft.secondary_strands,
            d.impreg_code
        )
    
    seen_signatures = set()
    unique_solutions = []
    for ind in pareto_front:
        sig = design_signature(ind)
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            unique_solutions.append(ind)
    
    # Sort by first objective (weight)
    unique_solutions.sort(key=lambda x: x.objectives[0])
    
    print(f"\nTotal solutions: {len(pareto_front)}")
    print(f"Unique solutions (after deduplication): {len(unique_solutions)}")
    
    for i, ind in enumerate(unique_solutions[:args.max_display]):
        design = ind.design
        mesh_warp = design.rib_spacing_mm('warp')
        mesh_weft = design.rib_spacing_mm('weft')
        mat_props = MATERIAL_PROPERTIES.get(design.warp.material_code, {})
        
        # Check if material requirements are met
        e_mod = mat_props.get('e_modulus_gpa', 0)
        tensile = mat_props.get('tensile_mpa', 0)
        e_ok = "✓" if (not args.min_e_modulus or e_mod >= args.min_e_modulus) else "✗"
        t_ok = "✓" if (not args.min_tensile_mpa or tensile >= args.min_tensile_mpa) else "✗"
        
        print(f"\n--- Solution {i+1} ---")
        print(f"Material: {design.warp.material_code}")
        print(f"  E modulus: {e_mod} GPa {e_ok}")
        print(f"  Tensile strength: {tensile} MPa {t_ok}")
        print(f"Mesh Size: {mesh_warp:.1f} × {mesh_weft:.1f} mm")
        print(f"Weight: {design.impregnated_weight_g_m2():.1f} g/m²")
        print(f"Breaking Force (mesh tensile): {design.breaking_force_kN_m('warp'):.1f} / "
              f"{design.breaking_force_kN_m('weft'):.1f} kN/m (warp/weft)")
        print(f"Cross-section/rib: {design.cross_section_per_rib_mm2('warp'):.3f} / "
              f"{design.cross_section_per_rib_mm2('weft'):.3f} mm²")
        
        # Show warp configuration (with dual-tex support)
        warp_tex_str = design.warp.tex_summary()
        if design.warp.is_dual_tex:
            print(f"Warp: {warp_tex_str} [DUAL-TEX] @ {design.warp.density_per_10cm}/10cm "
                  f"(total: {design.warp.total_tex_per_rib:.0f} tex)")
        else:
            print(f"Warp: {warp_tex_str} @ {design.warp.density_per_10cm}/10cm")
        
        # Show weft configuration (with dual-tex support)
        weft_tex_str = design.weft.tex_summary()
        if design.weft.is_dual_tex:
            print(f"Weft: {weft_tex_str} [DUAL-TEX] @ {design.weft.density_per_10cm}/10cm "
                  f"(total: {design.weft.total_tex_per_rib:.0f} tex)")
        else:
            print(f"Weft: {weft_tex_str} @ {design.weft.density_per_10cm}/10cm")
        
        print(f"Impregnation: {design.impreg_code}")
    
    if len(unique_solutions) > args.max_display:
        print(f"\n... and {len(unique_solutions) - args.max_display} more unique solutions")
    
    # Export if requested
    if args.output:
        import csv
        
        # Build export data from deduplicated solutions
        export_data = []
        for i, ind in enumerate(unique_solutions):
            design = ind.design
            mat_props = MATERIAL_PROPERTIES.get(design.warp.material_code, {})
            
            solution = {
                'id': i + 1,
                'material': design.warp.material_code,
                'e_modulus_gpa': mat_props.get('e_modulus_gpa', None),
                'tensile_strength_mpa': mat_props.get('tensile_mpa', None),
                'mesh_warp_mm': round(design.rib_spacing_mm('warp'), 1),
                'mesh_weft_mm': round(design.rib_spacing_mm('weft'), 1),
                'weight_g_m2': round(design.impregnated_weight_g_m2(), 1),
                'breaking_force_warp_kn_m': round(design.breaking_force_kN_m('warp'), 1),
                'breaking_force_weft_kn_m': round(design.breaking_force_kN_m('weft'), 1),
                'cross_section_warp_mm2': round(design.cross_section_per_rib_mm2('warp'), 3),
                'cross_section_weft_mm2': round(design.cross_section_per_rib_mm2('weft'), 3),
                'warp_tex': design.warp.tex,
                'warp_strands': design.warp.strands_per_rib,
                'warp_secondary_tex': design.warp.secondary_tex,
                'warp_secondary_strands': design.warp.secondary_strands,
                'warp_total_tex': design.warp.total_tex_per_rib,
                'warp_density_per_10cm': design.warp.density_per_10cm,
                'warp_is_dual_tex': design.warp.is_dual_tex,
                'weft_tex': design.weft.tex,
                'weft_strands': design.weft.strands_per_rib,
                'weft_secondary_tex': design.weft.secondary_tex,
                'weft_secondary_strands': design.weft.secondary_strands,
                'weft_total_tex': design.weft.total_tex_per_rib,
                'weft_density_per_10cm': design.weft.density_per_10cm,
                'weft_is_dual_tex': design.weft.is_dual_tex,
                'impregnation': design.impreg_code,
                'weave': design.weave_code,
                # Objectives
                'objectives': {name: round(val, 2) for name, val in zip(objectives, ind.objectives)}
            }
            export_data.append(solution)
        
        # Determine base filename
        base_name = args.output.rsplit('.', 1)[0] if '.' in args.output else args.output
        
        # Export JSON
        if args.output_format in ['json', 'both']:
            json_file = f"{base_name}.json"
            with open(json_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'total_solutions': len(pareto_front),
                        'unique_solutions': len(unique_solutions),
                        'objectives': objectives,
                        'constraints': {
                            'min_strength': args.min_strength,
                            'max_strength': args.max_strength,
                            'min_weight': args.min_weight,
                            'max_weight': args.max_weight,
                            'mesh_size': args.mesh_size,
                            'mesh_tolerance': args.mesh_tolerance,
                            'min_e_modulus': args.min_e_modulus,
                            'min_tensile_mpa': args.min_tensile_mpa
                        }
                    },
                    'solutions': export_data
                }, f, indent=2)
            print(f"\nJSON exported to: {json_file}")
        
        # Export CSV
        if args.output_format in ['csv', 'both']:
            csv_file = f"{base_name}.csv"
            # Flatten for CSV (remove nested objectives dict)
            csv_data = []
            for sol in export_data:
                flat_sol = {k: v for k, v in sol.items() if k != 'objectives'}
                # Add objectives as separate columns
                for obj_name, obj_val in sol['objectives'].items():
                    flat_sol[f'objective_{obj_name}'] = obj_val
                csv_data.append(flat_sol)
            
            if csv_data:
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
                print(f"CSV exported to: {csv_file}")


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
                           help='Minimum breaking force kN/m (mesh tensile strength)')
    opt_parser.add_argument('--max-strength', type=float, default=None,
                           help='Maximum breaking force kN/m')
    opt_parser.add_argument('--max-weight', type=float, default=None,
                           help='Maximum weight g/m²')
    opt_parser.add_argument('--min-weight', type=float, default=None,
                           help='Minimum weight g/m²')
    opt_parser.add_argument('--min-aperture', type=float, default=None,
                           help='Minimum clear aperture mm')
    opt_parser.add_argument('--max-aperture', type=float, default=None,
                           help='Maximum clear aperture mm')
    opt_parser.add_argument('--mesh-size', type=float, default=None,
                           help='Target mesh size mm (uses ±tolerance)')
    opt_parser.add_argument('--mesh-tolerance', type=float, default=5.0,
                           help='Mesh size tolerance mm (default: 5)')
    opt_parser.add_argument('--min-e-modulus', type=float, default=None,
                           help='Minimum E modulus GPa (filters materials)')
    opt_parser.add_argument('--min-tensile-mpa', type=float, default=None,
                           help='Minimum material tensile strength MPa')
    opt_parser.add_argument('--materials', default=None,
                           help='Comma-separated material codes (overrides E/tensile filters)')
    opt_parser.add_argument('--weaves', default=None,
                           help='Comma-separated weave codes')
    opt_parser.add_argument('--tex-min', type=float, default=400,
                           help='Minimum tex (default: 400)')
    opt_parser.add_argument('--tex-max', type=float, default=5000,
                           help='Maximum tex (default: 5000)')
    opt_parser.add_argument('--tex-values', default=None,
                           help='Specific tex values to use, comma-separated (e.g., "320,640,1200,2400")')
    opt_parser.add_argument('--dual-tex-pairs', default=None,
                           help='Specific dual-tex pairs to explore, format: "primary+secondary,..." '
                                '(e.g., "1200+640,2400+1200"). Implies --allow-dual-tex')
    opt_parser.add_argument('--strands-min', type=int, default=1,
                           help='Minimum strands (default: 1)')
    opt_parser.add_argument('--strands-max', type=int, default=6,
                           help='Maximum strands (default: 6)')
    opt_parser.add_argument('--density-min', type=float, default=1.5,
                           help='Minimum density/10cm (default: 1.5)')
    opt_parser.add_argument('--density-max', type=float, default=20,
                           help='Maximum density/10cm (default: 20)')
    opt_parser.add_argument('--allow-asymmetric', action='store_true',
                           help='Allow asymmetric warp/weft designs')
    opt_parser.add_argument('--allow-dual-tex', action='store_true',
                           help='Allow dual-tex constructions (two tex values in same direction, like Grid 350)')
    opt_parser.add_argument('--dual-tex-prob', type=float, default=0.3,
                           help='Probability of dual-tex when enabled (default: 0.3)')
    opt_parser.add_argument('--objectives', default='weight,neg_strength_min',
                           help='Comma-separated objectives to optimize. Options: '
                                'weight, cost, neg_strength_min, neg_strength_warp, neg_strength_weft, '
                                'neg_strength_avg, neg_aperture, neg_strength_to_weight, total_tex, '
                                'cross_section (default: weight,neg_strength_min)')
    opt_parser.add_argument('--population', type=int, default=100,
                           help='Population size (default: 100)')
    opt_parser.add_argument('--generations', type=int, default=200,
                           help='Max generations (default: 200)')
    opt_parser.add_argument('--seed', type=int, default=None,
                           help='Random seed for reproducibility')
    opt_parser.add_argument('--output', '-o', default=None,
                           help='Output file for results (.json or .csv)')
    opt_parser.add_argument('--output-format', choices=['json', 'csv', 'both'], default='json',
                           help='Output format: json, csv, or both (default: json)')
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
