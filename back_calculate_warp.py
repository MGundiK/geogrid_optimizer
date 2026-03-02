#!/usr/bin/env python3
"""
Back-calculate warp construction from datasheet cross-section values.

Formula:
  cross_section_per_rib = tex × strands / (ρ × 1000)
  
Solving for strands:
  strands = cross_section_per_rib × ρ × 1000 / tex

Solving for density:
  density_per_10cm = (cross_section_per_m / cross_section_per_rib) / 10
"""

import json

# Material densities
DENSITIES = {
    'AR_glass': 2.6,
    'E_glass': 2.54,
    'ECR_glass': 2.62,
    'carbon': 1.75,
    'basalt': 2.67
}

def back_calculate_strands(tex, cross_section_per_rib, material='AR_glass'):
    """Back-calculate strands from cross-section per rib."""
    rho = DENSITIES[material]
    strands = cross_section_per_rib * rho * 1000 / tex
    return round(strands)

def back_calculate_density(cross_section_per_m, cross_section_per_rib):
    """Back-calculate density from cross-section values."""
    ribs_per_m = cross_section_per_m / cross_section_per_rib
    return round(ribs_per_m / 10, 2)  # Convert to per 10cm

print("=" * 70)
print("BACK-CALCULATING WARP CONSTRUCTION FROM DATASHEETS")
print("=" * 70)

# Products with datasheet cross-section data
products_to_calculate = [
    {
        "name": "ANTISEISMIC_Grid_49",
        "warp_tex": 1200,
        "weft_tex": 2400,
        "weft_strands": 2,
        "weft_density": 2.6,
        "ds_cs_per_rib": 1.85,
        "ds_cs_per_m_warp": 49.11,
        "ds_cs_per_m_weft": 48.0,
        "ds_force_warp": 103,
        "ds_force_weft": 99,
        "ds_weight": 385,
    },
    {
        "name": "ANTISEISMIC_Grid_54",
        "warp_tex": 2400,  # Assumed same as weft
        "weft_tex": 2400,
        "ds_cs_per_rib": 3.69,
        "ds_cs_per_m": 54.49,
        "ds_force_warp": 100,
        "ds_force_weft": 96,
        "ds_weight": 420,
        "ds_mesh": 67.8,
    },
    {
        "name": "ANTISEISMIC_Grid_280",
        "warp_tex": 1200,
        "weft_tex": 2400,
        "weft_strands": 1,
        "weft_density": 4.0,
        "ds_cs_per_rib": 0.895,
        "ds_cs_per_m": 35.8,
        "ds_mesh": 25,
        "ds_weight": 280,
    },
    {
        "name": "FLEX_GRID_ARG_460_AAS3",
        "warp_tex": 1200,
        "weft_tex": 2400,
        "weft_strands": 2,
        "weft_density": 3.33,
        "ds_cs_per_rib": 1.85,  # From datasheet
        "ds_force_warp": 100,
        "ds_force_weft": 100,
        "ds_weight": 460,
        "ds_mesh": 30,
    },
]

results = {}

for prod in products_to_calculate:
    name = prod["name"]
    print(f"\n{name}:")
    print("-" * 50)
    
    warp_tex = prod["warp_tex"]
    cs_per_rib = prod.get("ds_cs_per_rib")
    
    if cs_per_rib:
        # Back-calculate warp strands
        warp_strands = back_calculate_strands(warp_tex, cs_per_rib)
        print(f"  Warp tex: {warp_tex}")
        print(f"  Cross-section/rib: {cs_per_rib} mm²")
        print(f"  → Back-calculated warp strands: {warp_strands}")
        
        # Back-calculate warp density if we have cross-section per m
        cs_per_m_warp = prod.get("ds_cs_per_m_warp") or prod.get("ds_cs_per_m")
        if cs_per_m_warp:
            warp_density = back_calculate_density(cs_per_m_warp, cs_per_rib)
            print(f"  Cross-section/m (warp): {cs_per_m_warp} mm²/m")
            print(f"  → Back-calculated warp density: {warp_density}/10cm")
        else:
            warp_density = prod.get("weft_density")  # Assume symmetric
            print(f"  → Assumed warp density (same as weft): {warp_density}/10cm")
        
        results[name] = {
            "warp_strands": warp_strands,
            "warp_density": warp_density,
            "warp_total_tex": warp_tex * warp_strands,
        }
        
        # Also show weft for comparison
        weft_tex = prod.get("weft_tex")
        weft_strands = prod.get("weft_strands", 1)
        weft_total = weft_tex * weft_strands if weft_tex else None
        print(f"\n  Weft: {weft_tex} tex × {weft_strands} = {weft_total} total tex")
        print(f"  Warp: {warp_tex} tex × {warp_strands} = {warp_tex * warp_strands} total tex")

print("\n" + "=" * 70)
print("SUMMARY OF CORRECTIONS:")
print("=" * 70)
for name, data in results.items():
    print(f"\n{name}:")
    print(f"  Warp strands: {data['warp_strands']}")
    print(f"  Warp density: {data['warp_density']}/10cm")
    print(f"  Warp total tex: {data['warp_total_tex']}")
