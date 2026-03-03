"""
Core grid model implementing the physics calculations for geogrid properties.

This module contains the main GridDesign class that calculates:
- Breaking force (kN/m)
- Areal weight (g/m²)
- Aperture size (mm)
- Cross-sectional area (mm²/m)
- Mechanical stress (MPa)
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any
import math
import json
from pathlib import Path

from .material import Material, get_material_db
from .weave import WeaveType, BindingThread, get_weave_db
from .impregnation import ImpregnationType, ImpregnationParameters, get_impregnation_db


@dataclass
class DirectionConfig:
    """
    Configuration for one direction (warp or weft) of the grid.
    
    Supports both single-tex and dual-tex constructions:
    
    Single-tex example (ARG-460):
        tex=1200, strands_per_rib=4
        → 1200 tex × 4 strands = 4800 total tex/rib
    
    Dual-tex example (Grid 350 warp):
        tex=1200, strands_per_rib=2, secondary_tex=640, secondary_strands=2
        → (1200×2) + (640×2) = 3680 total tex/rib
        Factory notation: "3.75×2×2 with osnova 1 (640 tex) + osnova 2 (1200 tex)"
    """
    
    material_code: str
    tex: float                    # Primary tex per strand (g/1000m)
    strands_per_rib: int          # Number of primary strands per rib
    density_per_10cm: float       # Number of ribs per 10cm
    
    # Dual-tex support: secondary tex (for mixed constructions)
    secondary_tex: Optional[float] = None
    secondary_strands: int = 0
    
    @property
    def is_dual_tex(self) -> bool:
        """Check if this is a dual-tex construction."""
        return self.secondary_tex is not None and self.secondary_strands > 0
    
    @property
    def total_tex_per_rib(self) -> float:
        """Total tex per rib (sum of all strands)."""
        total = self.tex * self.strands_per_rib
        if self.is_dual_tex:
            total += self.secondary_tex * self.secondary_strands
        return total
    
    @property
    def total_strands_per_rib(self) -> int:
        """Total number of strands per rib."""
        total = self.strands_per_rib
        if self.is_dual_tex:
            total += self.secondary_strands
        return total
    
    @property
    def threads_per_meter(self) -> float:
        """Total number of threads per meter."""
        return self.density_per_10cm * 10
    
    @property
    def rib_spacing_mm(self) -> float:
        """Center-to-center spacing between ribs (mm)."""
        if self.density_per_10cm <= 0:
            return 0
        return 100.0 / self.density_per_10cm
    
    def weight_per_m2_g(self) -> float:
        """
        Calculate raw fiber weight per m² for this direction.
        
        Formula: (tex × strands × threads_per_m) / 1000
        """
        total_tex = self.total_tex_per_rib
        threads_per_m = self.threads_per_meter
        return (total_tex * threads_per_m) / 1000
    
    def tex_summary(self) -> str:
        """Get human-readable tex configuration string."""
        if self.is_dual_tex:
            return f"{self.tex:.0f}×{self.strands_per_rib} + {self.secondary_tex:.0f}×{self.secondary_strands}"
        else:
            return f"{self.tex:.0f}×{self.strands_per_rib}"
    
    def factory_notation(self) -> str:
        """
        Get factory-style notation.
        
        Format: density × pairs × threads_per_pair / 10cm
        Example: "3.75×2×2" means 3.75 ribs/10cm, 2 pairs, 2 threads per pair
        """
        if self.is_dual_tex:
            # For dual-tex, show both components
            pairs = self.strands_per_rib  # Assuming strands = pairs for dual-tex
            return f"{self.density_per_10cm}×{pairs}×2 (dual: {self.tex:.0f}+{self.secondary_tex:.0f} tex)"
        else:
            # Single tex - simplified notation
            return f"{self.density_per_10cm}×{self.strands_per_rib}"


@dataclass
class GridDesign:
    """
    Complete geogrid design specification.
    
    This class calculates all grid properties from the design parameters.
    """
    
    # Direction configurations
    warp: DirectionConfig
    weft: DirectionConfig
    
    # Construction parameters
    weave_code: str
    impreg_code: str
    application_ratio_percent: float = 1.2
    
    # Optional binding thread
    binding_thread: Optional[BindingThread] = None
    
    # Cached databases (will be loaded on first access)
    _material_db: Any = field(default=None, repr=False)
    _weave_db: Any = field(default=None, repr=False)
    _impreg_db: Any = field(default=None, repr=False)
    
    def __post_init__(self):
        """Initialize database references."""
        if self._material_db is None:
            self._material_db = get_material_db()
        if self._weave_db is None:
            self._weave_db = get_weave_db()
        if self._impreg_db is None:
            self._impreg_db = get_impregnation_db()
    
    # =========================================================================
    # Material/Weave/Impreg accessors
    # =========================================================================
    
    @property
    def warp_material(self) -> Material:
        return self._material_db[self.warp.material_code]
    
    @property
    def weft_material(self) -> Material:
        return self._material_db[self.weft.material_code]
    
    @property
    def weave(self) -> WeaveType:
        return self._weave_db[self.weave_code]
    
    @property
    def impregnation(self) -> ImpregnationType:
        return self._impreg_db[self.impreg_code]
    
    # =========================================================================
    # Cross-sectional area calculations
    # =========================================================================
    
    def cross_section_per_rib_mm2(self, direction: str) -> float:
        """
        Calculate cross-sectional area of a single rib.
        
        Formula: A = (tex × strands) / (ρ × 1000)
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Cross-sectional area in mm²
        """
        config = self.warp if direction == 'warp' else self.weft
        material = self.warp_material if direction == 'warp' else self.weft_material
        
        total_tex = config.total_tex_per_rib
        return total_tex / (material.density_g_cm3 * 1000)
    
    def cross_section_per_meter_mm2(self, direction: str) -> float:
        """
        Calculate cross-sectional area per meter width.
        
        Formula: A_grid = A_rib × ribs_per_meter
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Cross-sectional area in mm²/m
        """
        config = self.warp if direction == 'warp' else self.weft
        material = self.warp_material if direction == 'warp' else self.weft_material
        
        # Total tex per meter = tex × strands × threads_per_m
        total_tex_per_m = config.total_tex_per_rib * config.threads_per_meter
        return total_tex_per_m / (material.density_g_cm3 * 1000)
    
    # Alias for compatibility
    def fiber_cross_section_mm2_per_m(self, direction: str) -> float:
        """Alias for cross_section_per_meter_mm2."""
        return self.cross_section_per_meter_mm2(direction)
    
    # =========================================================================
    # Weight calculations
    # =========================================================================
    
    def _direction_usage_g_m2(self, direction: str) -> float:
        """
        Calculate material usage for one direction (raw, before impregnation).
        
        Formula: usage = (threads_per_m × tex_total) / (weaving_coeff × 1000)
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Material usage in g/m²
        """
        config = self.warp if direction == 'warp' else self.weft
        
        # Get weaving coefficient
        weaving_coeff = 0.98  # Default from production data
        
        total_tex = config.total_tex_per_rib
        threads_per_m = config.threads_per_meter
        
        return (threads_per_m * total_tex) / (weaving_coeff * 1000)
    
    def raw_weight_g_m2(self) -> float:
        """
        Calculate raw fabric weight before impregnation.
        
        Returns:
            Weight in g/m²
        """
        warp_usage = self._direction_usage_g_m2('warp')
        weft_usage = self._direction_usage_g_m2('weft')
        
        # Add binding thread if present
        binding_weight = 0.0
        if self.binding_thread is not None:
            binding_weight = self.binding_thread.typical_weight_g_m2
        elif self.weave.binding_thread_required:
            # Use default binding thread weight
            binding_weight = 3.5  # g/m²
        
        return warp_usage + weft_usage + binding_weight
    
    def impregnated_weight_g_m2(self) -> float:
        """
        Calculate final fabric weight after impregnation.
        
        Returns:
            Weight in g/m²
        """
        raw_weight = self.raw_weight_g_m2()
        
        # Weight ratio based on application ratio
        # Empirical: ~20× multiplier from % to ratio increment
        weight_ratio = 1.0 + (self.application_ratio_percent / 100) * 20
        
        return raw_weight * weight_ratio
    
    def impregnation_weight_g_m2(self) -> float:
        """Weight added by impregnation (g/m²)."""
        return self.impregnated_weight_g_m2() - self.raw_weight_g_m2()
    
    # =========================================================================
    # Breaking force calculations
    # =========================================================================
    
    def breaking_force_per_thread_N(self, direction: str) -> float:
        """
        Calculate breaking force per thread/rib (raw, before impregnation).
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Breaking force in Newtons
        """
        config = self.warp if direction == 'warp' else self.weft
        material = self.warp_material if direction == 'warp' else self.weft_material
        
        # Get base breaking force for primary tex
        base_force = material.get_breaking_force(config.tex)
        total_force = base_force * config.strands_per_rib
        
        # Add secondary strands if present
        if config.secondary_tex and config.secondary_strands > 0:
            secondary_force = material.get_breaking_force(config.secondary_tex)
            total_force += secondary_force * config.secondary_strands
        
        # Apply weave efficiency
        eta = self.weave.get_efficiency(direction)
        
        return total_force * eta
    
    def breaking_force_per_thread_impreg_N(self, direction: str) -> float:
        """
        Calculate breaking force per thread after impregnation.
        
        Impregnation enhances the breaking force.
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Breaking force in Newtons
        """
        raw_force = self.breaking_force_per_thread_N(direction)
        impreg_coeff = self.impregnation.total_strength_coefficient(direction)
        
        return raw_force * impreg_coeff
    
    def breaking_force_kN_m(self, direction: str) -> float:
        """
        Calculate breaking force per meter width.
        
        This is the main strength specification (e.g., 50 kN/m).
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Breaking force in kN/m
        """
        config = self.warp if direction == 'warp' else self.weft
        
        force_per_thread = self.breaking_force_per_thread_impreg_N(direction)
        threads_per_m = config.threads_per_meter
        
        return (force_per_thread * threads_per_m) / 1000
    
    def breaking_force_N_5cm(self, direction: str) -> float:
        """
        Calculate breaking force per 5cm width.
        
        Common testing specification.
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Breaking force in N/5cm
        """
        kn_per_m = self.breaking_force_kN_m(direction)
        return kn_per_m * 1000 / 20  # Convert to N/5cm
    
    # =========================================================================
    # Mechanical stress calculations
    # =========================================================================
    
    def tensile_stress_mpa(self, direction: str) -> float:
        """
        Calculate tensile stress (mechanical stress).
        
        Formula: σ = F / A
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Stress in MPa (N/mm²)
        """
        force_kn_m = self.breaking_force_kN_m(direction)
        area_mm2_m = self.cross_section_per_meter_mm2(direction)
        
        if area_mm2_m <= 0:
            return 0
        
        # kN/m to N/m, then divide by mm²/m
        return (force_kn_m * 1000) / area_mm2_m
    
    # =========================================================================
    # Aperture calculations
    # =========================================================================
    
    def _estimate_thread_thickness_mm(self, direction: str) -> float:
        """
        Estimate thread thickness for aperture calculation.
        
        This is a simplified estimate; real values should come from lookup table.
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Estimated thickness in mm
        """
        config = self.warp if direction == 'warp' else self.weft
        material = self.warp_material if direction == 'warp' else self.weft_material
        
        total_tex = config.total_tex_per_rib
        
        # Empirical formula based on production data
        # thickness ≈ a × tex^b
        if direction == 'warp':
            a, b = 0.015, 0.55
        else:
            a, b = 0.025, 0.52
        
        return a * (total_tex ** b)
    
    def rib_spacing_mm(self, direction: str) -> float:
        """
        Get center-to-center rib spacing.
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Spacing in mm
        """
        config = self.warp if direction == 'warp' else self.weft
        return config.rib_spacing_mm
    
    def clear_aperture_mm(self, direction: str) -> float:
        """
        Calculate clear aperture (open space between ribs).
        
        Formula: aperture = rib_spacing - thread_thickness
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Clear aperture in mm
        """
        spacing = self.rib_spacing_mm(direction)
        thickness = self._estimate_thread_thickness_mm(direction)
        
        return max(0, spacing - thickness)
    
    def aperture_size(self) -> Tuple[float, float]:
        """
        Get aperture dimensions (warp × weft).
        
        Returns:
            Tuple of (warp_aperture_mm, weft_aperture_mm)
        """
        return (
            self.clear_aperture_mm('warp'),
            self.clear_aperture_mm('weft')
        )
    
    # =========================================================================
    # Summary methods
    # =========================================================================
    
    def properties_dict(self) -> Dict[str, Any]:
        """
        Get all calculated properties as a dictionary.
        
        Returns:
            Dictionary with all grid properties
        """
        return {
            'weight': {
                'raw_g_m2': round(self.raw_weight_g_m2(), 2),
                'impregnated_g_m2': round(self.impregnated_weight_g_m2(), 2),
                'impregnation_g_m2': round(self.impregnation_weight_g_m2(), 2)
            },
            'breaking_force': {
                'warp_kN_m': round(self.breaking_force_kN_m('warp'), 2),
                'weft_kN_m': round(self.breaking_force_kN_m('weft'), 2),
                'warp_N_5cm': round(self.breaking_force_N_5cm('warp'), 1),
                'weft_N_5cm': round(self.breaking_force_N_5cm('weft'), 1)
            },
            'cross_section': {
                'warp_mm2_m': round(self.cross_section_per_meter_mm2('warp'), 2),
                'weft_mm2_m': round(self.cross_section_per_meter_mm2('weft'), 2),
                'warp_mm2_rib': round(self.cross_section_per_rib_mm2('warp'), 4),
                'weft_mm2_rib': round(self.cross_section_per_rib_mm2('weft'), 4)
            },
            'stress': {
                'warp_mpa': round(self.tensile_stress_mpa('warp'), 1),
                'weft_mpa': round(self.tensile_stress_mpa('weft'), 1)
            },
            'aperture': {
                'warp_spacing_mm': round(self.rib_spacing_mm('warp'), 2),
                'weft_spacing_mm': round(self.rib_spacing_mm('weft'), 2),
                'warp_clear_mm': round(self.clear_aperture_mm('warp'), 2),
                'weft_clear_mm': round(self.clear_aperture_mm('weft'), 2)
            },
            'configuration': {
                'warp_material': self.warp.material_code,
                'weft_material': self.weft.material_code,
                'warp_tex': self.warp.tex,
                'weft_tex': self.weft.tex,
                'warp_strands': self.warp.strands_per_rib,
                'weft_strands': self.weft.strands_per_rib,
                'warp_density_10cm': self.warp.density_per_10cm,
                'weft_density_10cm': self.weft.density_per_10cm,
                'weave': self.weave_code,
                'impregnation': self.impreg_code
            }
        }
    
    def summary(self) -> str:
        """
        Get a human-readable summary of the grid design.
        
        Returns:
            Formatted string with key properties
        """
        props = self.properties_dict()
        
        lines = [
            "=" * 60,
            "GEOGRID DESIGN SUMMARY",
            "=" * 60,
            "",
            "CONFIGURATION:",
            f"  Materials: {self.warp.material_code} (warp) / {self.weft.material_code} (weft)",
            f"  Tex: {self.warp.total_tex_per_rib} (warp) / {self.weft.total_tex_per_rib} (weft)",
            f"  Strands/rib: {self.warp.strands_per_rib} (warp) / {self.weft.strands_per_rib} (weft)",
            f"  Density: {self.warp.density_per_10cm}/10cm (warp) / {self.weft.density_per_10cm}/10cm (weft)",
            f"  Weave: {self.weave.name} ({self.weave_code})",
            f"  Impregnation: {self.impregnation.name}",
            "",
            "BREAKING FORCE:",
            f"  Warp: {props['breaking_force']['warp_kN_m']:.2f} kN/m",
            f"  Weft: {props['breaking_force']['weft_kN_m']:.2f} kN/m",
            "",
            "WEIGHT:",
            f"  Raw: {props['weight']['raw_g_m2']:.1f} g/m²",
            f"  Impregnated: {props['weight']['impregnated_g_m2']:.1f} g/m²",
            "",
            "APERTURE:",
            f"  Spacing: {props['aperture']['warp_spacing_mm']:.1f} × {props['aperture']['weft_spacing_mm']:.1f} mm",
            f"  Clear: {props['aperture']['warp_clear_mm']:.1f} × {props['aperture']['weft_clear_mm']:.1f} mm",
            "",
            "CROSS-SECTION:",
            f"  Warp: {props['cross_section']['warp_mm2_m']:.2f} mm²/m",
            f"  Weft: {props['cross_section']['weft_mm2_m']:.2f} mm²/m",
            "",
            "=" * 60
        ]
        
        return "\n".join(lines)


def create_symmetric_grid(
    material_code: str,
    tex: float,
    strands: int,
    density_per_10cm: float,
    weave_code: str = "LE",
    impreg_code: str = "SBR_latex",
    application_ratio: float = 1.2
) -> GridDesign:
    """
    Convenience function to create a symmetric (square) grid.
    
    Args:
        material_code: Material code (e.g., 'AR_glass')
        tex: Tex value for each strand
        strands: Number of strands per rib
        density_per_10cm: Rib density per 10cm
        weave_code: Weave type code
        impreg_code: Impregnation type code
        application_ratio: Impregnation application ratio (%)
        
    Returns:
        Configured GridDesign object
    """
    config = DirectionConfig(
        material_code=material_code,
        tex=tex,
        strands_per_rib=strands,
        density_per_10cm=density_per_10cm
    )
    
    return GridDesign(
        warp=config,
        weft=DirectionConfig(
            material_code=config.material_code,
            tex=config.tex,
            strands_per_rib=config.strands_per_rib,
            density_per_10cm=config.density_per_10cm
        ),
        weave_code=weave_code,
        impreg_code=impreg_code,
        application_ratio_percent=application_ratio
    )
