#!/usr/bin/env python3
"""
Multi-seed optimizer runner.

Runs the optimizer multiple times with different seeds and combines
deduplicated results into a single output file.

Usage:
    python run_multi_seed.py --seeds 42,123,456,789,1000 \
        --min-strength 80 --max-strength 100 \
        --min-weight 420 --max-weight 450 \
        --mesh-size 30 --mesh-tolerance 3 \
        --output combined_results
"""

import sys
import json
import argparse
from pathlib import Path

# Handle imports
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

from models import GridDesign, DirectionConfig, get_material_db
from optimizer.nsga2 import NSGA2Optimizer, DesignBounds, Constraints


# Material properties for filtering and display
MATERIAL_PROPERTIES = {
    'AR_glass': {'e_modulus_gpa': 72.0, 'tensile_mpa': 1100, 'name': 'AR Glass'},
    'E_glass': {'e_modulus_gpa': 72.4, 'tensile_mpa': 1300, 'name': 'E Glass'},
    'carbon': {'e_modulus_gpa': 230.0, 'tensile_mpa': 1700, 'name': 'Carbon'},
    'basalt': {'e_modulus_gpa': 89.0, 'tensile_mpa': 1100, 'name': 'Basalt'},
}


def design_signature(design):
    """Create unique signature for deduplication."""
    return (
        design.warp.material_code,
        round(design.warp.tex, 0),
        design.warp.strands_per_rib,
        round(design.warp.density_per_10cm, 1),
        design.warp.secondary_tex,
        design.warp.secondary_strands,
        round(design.weft.tex, 0),
        design.weft.strands_per_rib,
        round(design.weft.density_per_10cm, 1),
        design.weft.secondary_tex,
        design.weft.secondary_strands,
        design.impreg_code
    )


def run_single_seed(args, seed):
    """Run optimizer with a single seed and return results."""
    
    # Filter materials
    if args.materials:
        materials = args.materials.split(',')
    else:
        materials = list(MATERIAL_PROPERTIES.keys())
        if args.min_e_modulus:
            materials = [m for m in materials 
                        if MATERIAL_PROPERTIES[m]['e_modulus_gpa'] >= args.min_e_modulus]
        if args.min_tensile_mpa:
            materials = [m for m in materials 
                        if MATERIAL_PROPERTIES[m]['tensile_mpa'] >= args.min_tensile_mpa]
    
    if not materials:
        return []
    
    # Parse tex values
    if args.tex_values:
        tex_values = [float(t.strip()) for t in args.tex_values.split(',')]
    else:
        tex_values = [320, 640, 1200, 2400, 4800]
    
    # Parse dual-tex pairs
    dual_tex_pairs = None
    if args.dual_tex_pairs:
        dual_tex_pairs = []
        for pair_str in args.dual_tex_pairs.split(','):
            parts = pair_str.strip().split('+')
            if len(parts) == 2:
                dual_tex_pairs.append((float(parts[0]), float(parts[1])))
    
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
        allow_dual_tex=args.allow_dual_tex or (dual_tex_pairs is not None),
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
    
    # Objectives
    objectives = [obj.strip() for obj in args.objectives.split(',')]
    
    # Run optimizer
    optimizer = NSGA2Optimizer(
        bounds=bounds,
        constraints=constraints,
        objectives=objectives,
        population_size=args.population,
        max_generations=args.generations,
        seed=seed
    )
    
    pareto_front = optimizer.run(verbose=False)
    
    # Return only feasible solutions (constraint_violation == 0)
    feasible = [ind for ind in pareto_front if ind.constraint_violation == 0]
    return feasible


def main():
    parser = argparse.ArgumentParser(
        description='Run optimizer with multiple seeds and combine results',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Seeds
    parser.add_argument('--seeds', default='42,123,456,789,1000',
                       help='Comma-separated seeds (default: 42,123,456,789,1000)')
    
    # Constraints
    parser.add_argument('--min-strength', type=float, default=None)
    parser.add_argument('--max-strength', type=float, default=None)
    parser.add_argument('--min-weight', type=float, default=None)
    parser.add_argument('--max-weight', type=float, default=None)
    parser.add_argument('--min-aperture', type=float, default=None)
    parser.add_argument('--max-aperture', type=float, default=None)
    parser.add_argument('--mesh-size', type=float, default=None)
    parser.add_argument('--mesh-tolerance', type=float, default=5.0)
    
    # Material filters
    parser.add_argument('--min-e-modulus', type=float, default=None)
    parser.add_argument('--min-tensile-mpa', type=float, default=None)
    parser.add_argument('--materials', default=None)
    
    # Design bounds
    parser.add_argument('--weaves', default=None)
    parser.add_argument('--tex-min', type=float, default=400)
    parser.add_argument('--tex-max', type=float, default=5000)
    parser.add_argument('--tex-values', default=None)
    parser.add_argument('--strands-min', type=int, default=1)
    parser.add_argument('--strands-max', type=int, default=6)
    parser.add_argument('--density-min', type=float, default=1.5)
    parser.add_argument('--density-max', type=float, default=20)
    parser.add_argument('--allow-asymmetric', action='store_true')
    parser.add_argument('--allow-dual-tex', action='store_true')
    parser.add_argument('--dual-tex-pairs', default=None)
    parser.add_argument('--dual-tex-prob', type=float, default=0.3)
    
    # Optimizer settings
    parser.add_argument('--objectives', default='weight,neg_strength_min')
    parser.add_argument('--population', type=int, default=100)
    parser.add_argument('--generations', type=int, default=200)
    
    # Output
    parser.add_argument('--output', '-o', default='combined_results')
    parser.add_argument('--output-format', choices=['json', 'csv', 'both'], default='both')
    parser.add_argument('--max-display', type=int, default=20)
    
    args = parser.parse_args()
    
    # Parse seeds
    seeds = [int(s.strip()) for s in args.seeds.split(',')]
    
    print("=" * 70)
    print("MULTI-SEED OPTIMIZATION")
    print("=" * 70)
    print(f"Running with {len(seeds)} seeds: {seeds}")
    print()
    
    # Collect all results
    all_solutions = []
    seen_signatures = set()
    
    for i, seed in enumerate(seeds):
        print(f"[{i+1}/{len(seeds)}] Running with seed {seed}...", end=" ", flush=True)
        
        feasible = run_single_seed(args, seed)
        
        # Deduplicate against existing solutions
        new_count = 0
        for ind in feasible:
            sig = design_signature(ind.design)
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                all_solutions.append(ind)
                new_count += 1
        
        print(f"Found {len(feasible)} feasible, {new_count} new unique")
    
    print()
    print("=" * 70)
    print(f"COMBINED RESULTS: {len(all_solutions)} unique solutions")
    print("=" * 70)
    
    if not all_solutions:
        print("\nNo feasible solutions found across all seeds!")
        print("Try relaxing constraints or increasing generations.")
        return
    
    # Sort by weight
    all_solutions.sort(key=lambda x: x.design.impregnated_weight_g_m2())
    
    # Parse objectives for output
    objectives = [obj.strip() for obj in args.objectives.split(',')]
    
    # Display results
    for i, ind in enumerate(all_solutions[:args.max_display]):
        design = ind.design
        mat_props = MATERIAL_PROPERTIES.get(design.warp.material_code, {})
        
        print(f"\n--- Solution {i+1} ---")
        print(f"Material: {design.warp.material_code}")
        print(f"  E modulus: {mat_props.get('e_modulus_gpa', '?')} GPa")
        print(f"  Tensile strength: {mat_props.get('tensile_mpa', '?')} MPa")
        print(f"Mesh Size: {design.rib_spacing_mm('warp'):.1f} × {design.rib_spacing_mm('weft'):.1f} mm")
        print(f"Weight: {design.impregnated_weight_g_m2():.1f} g/m²")
        print(f"Breaking Force: {design.breaking_force_kN_m('warp'):.1f} / "
              f"{design.breaking_force_kN_m('weft'):.1f} kN/m (warp/weft)")
        
        # Warp config
        if design.warp.is_dual_tex:
            print(f"Warp: {design.warp.tex_summary()} [DUAL-TEX] @ {design.warp.density_per_10cm}/10cm")
        else:
            print(f"Warp: {design.warp.tex_summary()} @ {design.warp.density_per_10cm}/10cm")
        
        # Weft config
        if design.weft.is_dual_tex:
            print(f"Weft: {design.weft.tex_summary()} [DUAL-TEX] @ {design.weft.density_per_10cm}/10cm")
        else:
            print(f"Weft: {design.weft.tex_summary()} @ {design.weft.density_per_10cm}/10cm")
        
        print(f"Impregnation: {design.impreg_code}")
    
    if len(all_solutions) > args.max_display:
        print(f"\n... and {len(all_solutions) - args.max_display} more solutions")
    
    # Export results
    export_data = []
    for i, ind in enumerate(all_solutions):
        design = ind.design
        mat_props = MATERIAL_PROPERTIES.get(design.warp.material_code, {})
        
        solution = {
            'id': i + 1,
            'material': design.warp.material_code,
            'e_modulus_gpa': mat_props.get('e_modulus_gpa'),
            'tensile_strength_mpa': mat_props.get('tensile_mpa'),
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
            'objectives': {name: round(val, 2) for name, val in zip(objectives, ind.objectives)}
        }
        export_data.append(solution)
    
    base_name = args.output
    
    # Export JSON
    if args.output_format in ['json', 'both']:
        json_file = f"{base_name}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'metadata': {
                    'seeds_used': seeds,
                    'total_unique_solutions': len(all_solutions),
                    'objectives': objectives,
                    'constraints': {
                        'min_strength': args.min_strength,
                        'max_strength': args.max_strength,
                        'min_weight': args.min_weight,
                        'max_weight': args.max_weight,
                        'mesh_size': args.mesh_size,
                        'mesh_tolerance': args.mesh_tolerance,
                    }
                },
                'solutions': export_data
            }, f, indent=2)
        print(f"\nJSON exported to: {json_file}")
    
    # Export CSV
    if args.output_format in ['csv', 'both']:
        import csv
        csv_file = f"{base_name}.csv"
        csv_data = []
        for sol in export_data:
            flat_sol = {k: v for k, v in sol.items() if k != 'objectives'}
            for obj_name, obj_val in sol['objectives'].items():
                flat_sol[f'objective_{obj_name}'] = obj_val
            csv_data.append(flat_sol)
        
        if csv_data:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
            print(f"CSV exported to: {csv_file}")


if __name__ == '__main__':
    main()
