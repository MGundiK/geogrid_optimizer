#!/usr/bin/env python3
"""
Comprehensive validation using ACTUAL factory construction data.

This validates the model against products where we know the exact tex × strands configuration.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import GridDesign, DirectionConfig


def load_product_database():
    """Load the product database with actual construction details."""
    db_path = Path(__file__).parent / 'data' / 'products.json'
    with open(db_path) as f:
        return json.load(f)


def validate_product(product_key: str, db: dict) -> dict:
    """Validate a single product against its datasheet values."""
    product = db['products'].get(product_key)
    if not product:
        return None
    
    # Skip products without complete data
    warp = product.get('warp', {})
    weft = product.get('weft', {})
    
    if 'tex' not in warp or 'tex' not in weft:
        return {'product': product_key, 'status': 'incomplete_data'}
    
    # Determine impregnation code
    impreg_map = {
        'epoxy': 'epoxy',
        'styrene_butadiene': 'styrene_butadiene',
    }
    impreg_code = impreg_map.get(product.get('impregnation', 'styrene_butadiene'), 'SBR_latex')
    
    # Build design from actual construction
    try:
        warp_config = DirectionConfig(
            material_code=warp.get('material', 'AR_glass'),
            tex=warp['tex'],
            strands_per_rib=warp.get('strands_per_rib', 1),
            density_per_10cm=warp.get('density_per_10cm', weft.get('density_per_10cm', 5))
        )
        
        weft_config = DirectionConfig(
            material_code=weft.get('material', 'AR_glass'),
            tex=weft['tex'],
            strands_per_rib=weft.get('strands_per_rib', 1),
            density_per_10cm=weft.get('density_per_10cm', 5)
        )
        
        design = GridDesign(
            warp=warp_config,
            weft=weft_config,
            weave_code='DLE',
            impreg_code=impreg_code,
            application_ratio_percent=product.get('impregnation_percent', 20) / 100 + 1.0
        )
    except Exception as e:
        return {'product': product_key, 'status': 'error', 'error': str(e)}
    
    # Compare with datasheet
    ds = product.get('datasheet_values', {})
    results = {
        'product': product_key,
        'name': product.get('full_name', product_key),
        'status': 'validated',
        'comparisons': []
    }
    
    # Weight comparison
    if 'weight_g_m2' in product:
        calc_weight = design.impregnated_weight_g_m2()
        target_weight = product['weight_g_m2']
        error = abs(calc_weight - target_weight) / target_weight * 100
        results['comparisons'].append({
            'parameter': 'weight',
            'unit': 'g/m²',
            'datasheet': target_weight,
            'calculated': round(calc_weight, 1),
            'error_pct': round(error, 1)
        })
    
    # Breaking force comparisons (various formats)
    force_checks = [
        ('breaking_force_warp_kN_m', 'warp', lambda d: d.breaking_force_kN_m('warp')),
        ('breaking_force_weft_kN_m', 'weft', lambda d: d.breaking_force_kN_m('weft')),
        ('breaking_force_warp_N_5cm', 'warp', lambda d: d.breaking_force_N_5cm('warp')),
        ('breaking_force_weft_N_5cm', 'weft', lambda d: d.breaking_force_N_5cm('weft')),
    ]
    
    for ds_key, direction, calc_func in force_checks:
        if ds_key in ds:
            calc_val = calc_func(design)
            target_val = ds[ds_key]
            error = abs(calc_val - target_val) / target_val * 100
            unit = 'kN/m' if 'kN_m' in ds_key else 'N/5cm'
            results['comparisons'].append({
                'parameter': f'breaking_force_{direction}',
                'unit': unit,
                'datasheet': target_val,
                'calculated': round(calc_val, 1),
                'error_pct': round(error, 1)
            })
    
    # Mesh size comparisons
    mesh_checks = [
        ('mesh_size_mm', 'warp', lambda d: d.rib_spacing_mm('warp')),
        ('mesh_size_mm', 'weft', lambda d: d.rib_spacing_mm('weft')),
        ('mesh_size_warp_mm', 'warp', lambda d: d.rib_spacing_mm('warp')),
        ('mesh_size_weft_mm', 'weft', lambda d: d.rib_spacing_mm('weft')),
    ]
    
    for ds_key, direction, calc_func in mesh_checks:
        if ds_key in ds:
            calc_val = calc_func(design)
            target_val = ds[ds_key]
            error = abs(calc_val - target_val) / target_val * 100
            results['comparisons'].append({
                'parameter': f'mesh_size_{direction}',
                'unit': 'mm',
                'datasheet': target_val,
                'calculated': round(calc_val, 1),
                'error_pct': round(error, 1)
            })
            break  # Only add once per direction
    
    # Cross-section comparisons
    cs_checks = [
        ('fiber_cross_section_mm2', 'warp', lambda d: d.cross_section_per_rib_mm2('warp')),
        ('fiber_cross_section_warp_mm2', 'warp', lambda d: d.cross_section_per_rib_mm2('warp')),
        ('fiber_cross_section_weft_mm2', 'weft', lambda d: d.cross_section_per_rib_mm2('weft')),
        ('cross_section_per_m_mm2', 'warp', lambda d: d.cross_section_per_meter_mm2('warp')),
        ('cross_section_per_m_warp_mm2', 'warp', lambda d: d.cross_section_per_meter_mm2('warp')),
        ('cross_section_per_m_weft_mm2', 'weft', lambda d: d.cross_section_per_meter_mm2('weft')),
    ]
    
    for ds_key, direction, calc_func in cs_checks:
        if ds_key in ds:
            calc_val = calc_func(design)
            target_val = ds[ds_key]
            error = abs(calc_val - target_val) / target_val * 100
            results['comparisons'].append({
                'parameter': f'{ds_key}',
                'unit': 'mm²' if 'per_m' not in ds_key else 'mm²/m',
                'datasheet': target_val,
                'calculated': round(calc_val, 3),
                'error_pct': round(error, 1)
            })
    
    return results


def print_validation_results(results: dict):
    """Pretty print validation results."""
    print(f"\n{'='*70}")
    print(f"VALIDATION: {results.get('name', results['product'])}")
    print(f"{'='*70}")
    
    if results['status'] != 'validated':
        print(f"  Status: {results['status']}")
        if 'error' in results:
            print(f"  Error: {results['error']}")
        return
    
    comparisons = results.get('comparisons', [])
    if not comparisons:
        print("  No datasheet values to compare")
        return
    
    print(f"\n{'Parameter':<30} {'Unit':<10} {'Datasheet':<12} {'Calc':<12} {'Error':<10}")
    print("-" * 70)
    
    for comp in comparisons:
        status = "✓" if comp['error_pct'] < 15 else "⚠" if comp['error_pct'] < 25 else "✗"
        print(f"{comp['parameter']:<30} {comp['unit']:<10} {comp['datasheet']:<12} "
              f"{comp['calculated']:<12} {comp['error_pct']:>5.1f}% {status}")


def run_all_validations():
    """Run validation for all products in database."""
    db = load_product_database()
    
    print("=" * 70)
    print("COMPREHENSIVE VALIDATION WITH ACTUAL CONSTRUCTION DATA")
    print("=" * 70)
    
    all_results = []
    
    # Validate each product
    for product_key in db['products']:
        results = validate_product(product_key, db)
        if results:
            all_results.append(results)
            print_validation_results(results)
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    total_comparisons = 0
    good_count = 0
    warning_count = 0
    error_count = 0
    
    for results in all_results:
        for comp in results.get('comparisons', []):
            total_comparisons += 1
            if comp['error_pct'] < 15:
                good_count += 1
            elif comp['error_pct'] < 25:
                warning_count += 1
            else:
                error_count += 1
    
    print(f"\nTotal comparisons: {total_comparisons}")
    print(f"  ✓ Good (<15% error): {good_count} ({good_count/total_comparisons*100:.0f}%)")
    print(f"  ⚠ Warning (15-25%):  {warning_count} ({warning_count/total_comparisons*100:.0f}%)")
    print(f"  ✗ High (>25%):       {error_count} ({error_count/total_comparisons*100:.0f}%)")
    
    return all_results


if __name__ == '__main__':
    results = run_all_validations()
