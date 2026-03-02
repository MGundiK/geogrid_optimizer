#!/usr/bin/env python3
"""
Product Optimization for Customer Requirements

Based on requirements table:
- Product A: ARG-460-AAS3 style (30x30mm, 420-450g/m², 80-100 kN/m)
- Product B: ARG-310-AAS3 style (45-50mm, same construction, 50-60 kN/m)
- Product C: q111 style (30x30mm, ~650g/m², 130-140 kN/m)

All products require:
- E modulus: >38 GPa preferred, >23 GPa acceptable
- Tensile strength: >600 MPa preferred, >240 MPa acceptable
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Fix imports - add parent directory to path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

from models import GridDesign, DirectionConfig
from models.material import get_material_db


@dataclass
class ProductRequirements:
    """Requirements for a product variant."""
    name: str
    mesh_size_mm: Tuple[float, float]  # (min, max) or (target-tolerance, target+tolerance)
    weight_g_m2: Tuple[float, float]   # (min, max)
    breaking_force_kN_m: Tuple[float, float]  # (min, max)
    e_modulus_gpa_min: float = 23.0    # Minimum acceptable
    e_modulus_gpa_preferred: float = 38.0  # Preferred
    tensile_strength_mpa_min: float = 240.0
    tensile_strength_mpa_preferred: float = 600.0


@dataclass
class DesignCandidate:
    """A candidate design with its parameters."""
    material: str
    warp_tex: int
    warp_strands: int
    warp_density: float
    weft_tex: int
    weft_strands: int
    weft_density: float
    impregnation: str
    impreg_percent: int
    
    # Calculated properties (filled after evaluation)
    mesh_size_warp: float = 0.0
    mesh_size_weft: float = 0.0
    weight: float = 0.0
    breaking_force_warp: float = 0.0
    breaking_force_weft: float = 0.0
    cross_section_warp: float = 0.0
    cross_section_weft: float = 0.0
    
    def to_grid_design(self) -> GridDesign:
        """Convert to GridDesign object."""
        warp_config = DirectionConfig(
            material_code=self.material,
            tex=self.warp_tex,
            strands_per_rib=self.warp_strands,
            density_per_10cm=self.warp_density
        )
        weft_config = DirectionConfig(
            material_code=self.material,
            tex=self.weft_tex,
            strands_per_rib=self.weft_strands,
            density_per_10cm=self.weft_density
        )
        
        # Convert impreg_percent to application_ratio
        app_ratio = self.impreg_percent / 100 + 1.0
        
        return GridDesign(
            warp=warp_config,
            weft=weft_config,
            weave_code='DLE',
            impreg_code=self.impregnation,
            application_ratio_percent=app_ratio
        )


def evaluate_candidate(candidate: DesignCandidate) -> DesignCandidate:
    """Evaluate a candidate design and fill in calculated properties."""
    try:
        design = candidate.to_grid_design()
        
        candidate.mesh_size_warp = design.rib_spacing_mm('warp')
        candidate.mesh_size_weft = design.rib_spacing_mm('weft')
        candidate.weight = design.impregnated_weight_g_m2()
        candidate.breaking_force_warp = design.breaking_force_kN_m('warp')
        candidate.breaking_force_weft = design.breaking_force_kN_m('weft')
        candidate.cross_section_warp = design.cross_section_per_rib_mm2('warp')
        candidate.cross_section_weft = design.cross_section_per_rib_mm2('weft')
        
    except Exception as e:
        print(f"Error evaluating candidate: {e}")
    
    return candidate


def check_requirements(candidate: DesignCandidate, req: ProductRequirements) -> Tuple[bool, List[str]]:
    """Check if candidate meets requirements. Returns (meets_all, list_of_issues)."""
    issues = []
    
    # Check mesh size (use average of warp/weft for symmetric, or min for asymmetric)
    mesh_avg = (candidate.mesh_size_warp + candidate.mesh_size_weft) / 2
    if mesh_avg < req.mesh_size_mm[0]:
        issues.append(f"Mesh too small: {mesh_avg:.1f} < {req.mesh_size_mm[0]}")
    if mesh_avg > req.mesh_size_mm[1]:
        issues.append(f"Mesh too large: {mesh_avg:.1f} > {req.mesh_size_mm[1]}")
    
    # Check weight
    if candidate.weight < req.weight_g_m2[0]:
        issues.append(f"Weight too low: {candidate.weight:.0f} < {req.weight_g_m2[0]}")
    if candidate.weight > req.weight_g_m2[1]:
        issues.append(f"Weight too high: {candidate.weight:.0f} > {req.weight_g_m2[1]}")
    
    # Check breaking force (use minimum of warp/weft)
    min_bf = min(candidate.breaking_force_warp, candidate.breaking_force_weft)
    if min_bf < req.breaking_force_kN_m[0]:
        issues.append(f"Breaking force too low: {min_bf:.1f} < {req.breaking_force_kN_m[0]}")
    if min_bf > req.breaking_force_kN_m[1]:
        issues.append(f"Breaking force too high: {min_bf:.1f} > {req.breaking_force_kN_m[1]}")
    
    return len(issues) == 0, issues


def get_material_modulus(material_code: str) -> float:
    """Get elastic modulus for a material."""
    modulus_map = {
        'AR_glass': 72.0,
        'E_glass': 72.4,
        'E_glass_vetrotex': 72.4,
        'E_glass_valmiera': 72.4,
        'carbon': 230.0,
        'basalt': 89.0,
    }
    return modulus_map.get(material_code, 72.0)


def generate_candidates_for_product_a() -> List[DesignCandidate]:
    """
    Generate candidates for Product A: ARG-460 style
    - Mesh: ~30x30 mm → density ~3.33/10cm
    - Weight: 420-450 g/m²
    - Breaking force: 80-100 kN/m
    """
    candidates = []
    
    # For higher weight, we need either:
    # - Higher density (more ribs)
    # - Higher tex
    # - Higher impregnation
    
    promising_configs = [
        # (warp_tex, warp_strands, weft_tex, weft_strands, density)
        # Original ARG-460 config
        (1200, 4, 2400, 2, 3.33),
        (1200, 4, 2400, 2, 3.5),
        (1200, 4, 2400, 2, 3.7),
        (1200, 4, 2400, 2, 4.0),
        # Higher weft strands for more weight
        (1200, 4, 2400, 3, 3.33),
        (1200, 4, 2400, 3, 3.0),
        # Different warp configs
        (1200, 3, 2400, 2, 3.5),
        (1200, 3, 2400, 2, 4.0),
        (640, 6, 2400, 2, 3.33),
        (640, 6, 2400, 2, 3.5),
        (2400, 2, 2400, 2, 3.33),
        (2400, 2, 2400, 2, 3.5),
        # Higher overall tex
        (1200, 5, 2400, 2, 3.0),
        (1200, 5, 2400, 2, 3.33),
    ]
    
    impreg_options = [
        ('styrene_butadiene', 16),
        ('styrene_butadiene', 18),
        ('styrene_butadiene', 20),
        ('styrene_butadiene', 25),
        ('styrene_butadiene', 30),
        ('styrene_butadiene', 40),
        ('epoxy', 20),
        ('epoxy', 25),
    ]
    
    for warp_tex, warp_strands, weft_tex, weft_strands, density in promising_configs:
        for impreg, impreg_pct in impreg_options:
            candidates.append(DesignCandidate(
                material='AR_glass',
                warp_tex=warp_tex,
                warp_strands=warp_strands,
                warp_density=density,
                weft_tex=weft_tex,
                weft_strands=weft_strands,
                weft_density=density,
                impregnation=impreg,
                impreg_percent=impreg_pct
            ))
    
    return candidates


def generate_candidates_for_product_b() -> List[DesignCandidate]:
    """
    Generate candidates for Product B: ARG-310 style
    - Mesh: ~45-50 mm → density ~2.0-2.2/10cm
    - Weight: similar construction to A but larger mesh
    - Breaking force: 50-60 kN/m
    """
    candidates = []
    
    # For 45-50mm mesh: density = 100/mesh_size
    # 45mm → 2.22/10cm, 50mm → 2.0/10cm
    
    promising_configs = [
        # (warp_tex, warp_strands, weft_tex, weft_strands, density)
        # Lower densities for larger mesh
        (640, 6, 2400, 2, 2.0),
        (640, 6, 2400, 2, 2.1),
        (640, 6, 2400, 2, 2.2),
        (640, 6, 2400, 2, 2.22),
        (640, 5, 2400, 2, 2.0),
        (640, 5, 2400, 2, 2.2),
        (1200, 4, 2400, 2, 2.0),
        (1200, 4, 2400, 2, 2.2),
        (1200, 3, 2400, 2, 2.0),
        (1200, 3, 2400, 2, 2.2),
        # With 3 weft strands for more weight/strength
        (640, 6, 2400, 3, 2.0),
        (640, 6, 2400, 3, 2.2),
        (1200, 4, 2400, 3, 2.0),
        (1200, 3, 2400, 3, 2.0),
        # Symmetric options
        (2400, 2, 2400, 2, 2.0),
        (2400, 2, 2400, 2, 2.2),
        # Lower weft strands, higher warp
        (1200, 4, 2400, 1, 2.0),
        (1200, 4, 2400, 1, 2.2),
        (1200, 5, 2400, 1, 2.0),
        (1200, 5, 2400, 2, 2.0),
    ]
    
    impreg_options = [
        ('styrene_butadiene', 16),
        ('styrene_butadiene', 18),
        ('styrene_butadiene', 20),
        ('styrene_butadiene', 25),
    ]
    
    for warp_tex, warp_strands, weft_tex, weft_strands, density in promising_configs:
        for impreg, impreg_pct in impreg_options:
            candidates.append(DesignCandidate(
                material='AR_glass',
                warp_tex=warp_tex,
                warp_strands=warp_strands,
                warp_density=density,
                weft_tex=weft_tex,
                weft_strands=weft_strands,
                weft_density=density,
                impregnation=impreg,
                impreg_percent=impreg_pct
            ))
    
    return candidates


def generate_candidates_for_product_c() -> List[DesignCandidate]:
    """
    Generate candidates for Product C: q111 style (heavy duty)
    - Mesh: ~30x30 mm → density ~3.33/10cm
    - Weight: ~650 g/m²
    - Breaking force: 130-140 kN/m (high!)
    
    Key insight: Need BOTH warp and weft at 130+ kN/m
    At 3.33/10cm, need ~4000 N per rib
    
    Challenge: 130 kN/m at 650 g/m² is very demanding
    Try lower density (larger mesh) to reduce weight while maintaining force
    """
    candidates = []
    
    # Lower density options: at 3.0/10cm (33mm mesh), 130 kN/m needs ~4333 N/rib
    # At 2.8/10cm (35mm mesh), 130 kN/m needs ~4643 N/rib
    # At 2.5/10cm (40mm mesh), 130 kN/m needs ~5200 N/rib
    
    promising_configs = [
        # (warp_tex, warp_strands, weft_tex, weft_strands, density)
        # Standard 30mm mesh - will be heavy
        (2400, 4, 2400, 4, 3.33),
        (2400, 4, 2400, 4, 3.0),
        
        # Lower density options (larger mesh, lighter weight)
        (2400, 4, 2400, 4, 2.8),
        (2400, 4, 2400, 4, 2.5),
        (2400, 5, 2400, 4, 2.5),
        (2400, 5, 2400, 5, 2.5),
        
        # 4800 tex options (fewer strands needed)
        (4800, 2, 4800, 2, 3.33),
        (4800, 2, 4800, 2, 3.0),
        (4800, 2, 4800, 2, 2.8),
        (4800, 2, 4800, 2, 2.5),
        (4800, 3, 4800, 3, 2.5),
        
        # Mixed configurations
        (2400, 4, 4800, 2, 3.0),
        (2400, 4, 4800, 2, 2.8),
        (4800, 2, 2400, 4, 3.0),
        
        # Higher strands with lower density
        (1200, 6, 2400, 4, 2.8),
        (1200, 6, 2400, 4, 2.5),
        (2400, 3, 2400, 3, 3.5),
        (2400, 3, 2400, 3, 3.0),
        
        # Try asymmetric mesh (different warp/weft density)
        # This could allow lighter construction
    ]
    
    impreg_options = [
        ('styrene_butadiene', 18),
        ('styrene_butadiene', 20),
        ('styrene_butadiene', 25),
        ('epoxy', 20),
        ('epoxy', 25),
    ]
    
    for warp_tex, warp_strands, weft_tex, weft_strands, density in promising_configs:
        for impreg, impreg_pct in impreg_options:
            candidates.append(DesignCandidate(
                material='AR_glass',
                warp_tex=warp_tex,
                warp_strands=warp_strands,
                warp_density=density,
                weft_tex=weft_tex,
                weft_strands=weft_strands,
                weft_density=density,
                impregnation=impreg,
                impreg_percent=impreg_pct
            ))
    
    return candidates


def print_candidate(c: DesignCandidate, req: ProductRequirements):
    """Print candidate details."""
    meets, issues = check_requirements(c, req)
    status = "✓ MEETS REQUIREMENTS" if meets else "✗ ISSUES"
    
    print(f"\n  Material: {c.material}")
    print(f"  Warp: {c.warp_tex} tex × {c.warp_strands} strands @ {c.warp_density}/10cm")
    print(f"  Weft: {c.weft_tex} tex × {c.weft_strands} strands @ {c.weft_density}/10cm")
    print(f"  Impregnation: {c.impregnation} @ {c.impreg_percent}%")
    print(f"  ---")
    print(f"  Mesh size: {c.mesh_size_warp:.1f} × {c.mesh_size_weft:.1f} mm")
    print(f"  Weight: {c.weight:.0f} g/m²")
    print(f"  Breaking force: warp={c.breaking_force_warp:.1f}, weft={c.breaking_force_weft:.1f} kN/m")
    print(f"  Cross-section/rib: warp={c.cross_section_warp:.3f}, weft={c.cross_section_weft:.3f} mm²")
    print(f"  E modulus: {get_material_modulus(c.material)} GPa")
    print(f"  Status: {status}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")


def run_optimization():
    """Run optimization for all three products."""
    
    # Define requirements (with some tolerance given model uncertainty)
    requirements = {
        'A': ProductRequirements(
            name="Product A (ARG-460 style)",
            mesh_size_mm=(27, 33),      # ~30mm ± 10%
            weight_g_m2=(400, 470),     # 420-450 with tolerance
            breaking_force_kN_m=(75, 105),  # 80-100 with tolerance
        ),
        'B': ProductRequirements(
            name="Product B (ARG-310 style)",
            mesh_size_mm=(42, 55),      # 45-50mm with tolerance
            weight_g_m2=(260, 380),     # Wider range for larger mesh
            breaking_force_kN_m=(48, 65),   # 50-60 with tolerance
        ),
        'C': ProductRequirements(
            name="Product C (q111 heavy duty)",
            mesh_size_mm=(27, 42),      # ~30mm but allow larger for weight
            weight_g_m2=(580, 720),     # ~650 with tolerance
            breaking_force_kN_m=(125, 145), # 130-140 with tolerance
        ),
    }
    
    # Generate and evaluate candidates for each product
    product_generators = {
        'A': generate_candidates_for_product_a,
        'B': generate_candidates_for_product_b,
        'C': generate_candidates_for_product_c,
    }
    
    for product_id, req in requirements.items():
        print("\n" + "=" * 70)
        print(f"OPTIMIZING: {req.name}")
        print("=" * 70)
        print(f"\nRequirements:")
        print(f"  Mesh size: {req.mesh_size_mm[0]}-{req.mesh_size_mm[1]} mm")
        print(f"  Weight: {req.weight_g_m2[0]}-{req.weight_g_m2[1]} g/m²")
        print(f"  Breaking force: {req.breaking_force_kN_m[0]}-{req.breaking_force_kN_m[1]} kN/m")
        print(f"  E modulus: >{req.e_modulus_gpa_min} GPa (preferred >{req.e_modulus_gpa_preferred})")
        
        # Generate candidates
        candidates = product_generators[product_id]()
        print(f"\nEvaluating {len(candidates)} candidate designs...")
        
        # Evaluate all candidates
        evaluated = [evaluate_candidate(c) for c in candidates]
        
        # Filter those that meet requirements
        meeting = []
        for c in evaluated:
            meets, _ = check_requirements(c, req)
            if meets:
                meeting.append(c)
        
        print(f"\nFound {len(meeting)} designs meeting all requirements:")
        
        if meeting:
            # Sort by some criteria (e.g., minimize weight within range)
            meeting.sort(key=lambda c: c.weight)
            
            # Show top 3
            for i, c in enumerate(meeting[:3], 1):
                print(f"\n--- Option {i} ---")
                print_candidate(c, req)
        else:
            print("\nNo designs fully meet requirements. Showing closest options:")
            # Sort by number of issues
            evaluated.sort(key=lambda c: len(check_requirements(c, req)[1]))
            for i, c in enumerate(evaluated[:3], 1):
                print(f"\n--- Closest Option {i} ---")
                print_candidate(c, req)


if __name__ == '__main__':
    run_optimization()
