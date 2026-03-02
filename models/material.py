"""
Material definitions and properties for geogrid fibers.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
import json
from pathlib import Path


@dataclass
class Material:
    """Represents a fiber material with its physical properties."""
    
    name: str
    code: str
    density_g_cm3: float
    tensile_strength_mpa: float
    e_modulus_gpa: float
    cost_per_kg: Optional[float] = None
    notes: str = ""
    
    # Breaking force lookup: tex -> N/thread
    tex_breaking_force: Dict[int, float] = field(default_factory=dict)
    
    @property
    def density_kg_m3(self) -> float:
        """Density in SI units (kg/m³)."""
        return self.density_g_cm3 * 1000
    
    def get_breaking_force(self, tex: float) -> float:
        """
        Get breaking force for a single roving at given tex.
        Interpolates if exact tex not in lookup table.
        
        Args:
            tex: Linear density in g/1000m
            
        Returns:
            Breaking force in Newtons per single thread
        """
        if not self.tex_breaking_force:
            # Fallback: estimate from tensile strength and cross-section
            # F = σ * A, where A = tex / (ρ * 1000)
            cross_section_mm2 = tex / (self.density_g_cm3 * 1000)
            return self.tensile_strength_mpa * cross_section_mm2
        
        # Check for exact match
        tex_int = int(tex)
        if tex_int in self.tex_breaking_force:
            return self.tex_breaking_force[tex_int]
        
        # Linear interpolation between known values
        tex_values = sorted(self.tex_breaking_force.keys())
        
        if tex < tex_values[0]:
            # Extrapolate below
            ratio = tex / tex_values[0]
            return self.tex_breaking_force[tex_values[0]] * ratio
        
        if tex > tex_values[-1]:
            # Extrapolate above
            ratio = tex / tex_values[-1]
            return self.tex_breaking_force[tex_values[-1]] * ratio
        
        # Find bracketing values
        for i, t in enumerate(tex_values[:-1]):
            if t <= tex <= tex_values[i + 1]:
                t1, t2 = t, tex_values[i + 1]
                f1, f2 = self.tex_breaking_force[t1], self.tex_breaking_force[t2]
                # Linear interpolation
                return f1 + (f2 - f1) * (tex - t1) / (t2 - t1)
        
        return 0.0
    
    def cross_section_mm2(self, tex: float, strands: int = 1) -> float:
        """
        Calculate cross-sectional area of fiber bundle.
        
        Args:
            tex: Linear density per strand (g/1000m)
            strands: Number of strands in bundle
            
        Returns:
            Cross-sectional area in mm²
        """
        # A = (tex * strands) / (density * 1000)
        return (tex * strands) / (self.density_g_cm3 * 1000)


class MaterialDatabase:
    """Manages the collection of available materials."""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.materials: Dict[str, Material] = {}
        
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "materials.json"
        
        self._load_from_json(data_path)
    
    def _load_from_json(self, path: Path):
        """Load materials from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        materials_data = data.get("materials", {})
        tex_forces = data.get("tex_breaking_force", {})
        
        for code, props in materials_data.items():
            # Get breaking force lookup for this material
            force_lookup = {}
            if code in tex_forces:
                force_lookup = {int(k): float(v) for k, v in tex_forces[code].items()}
            
            material = Material(
                name=props["name"],
                code=code,
                density_g_cm3=props["density_g_cm3"],
                tensile_strength_mpa=props["tensile_strength_mpa"],
                e_modulus_gpa=props["e_modulus_gpa"],
                cost_per_kg=props.get("cost_per_kg"),
                notes=props.get("notes", ""),
                tex_breaking_force=force_lookup
            )
            self.materials[code] = material
    
    def get(self, code: str) -> Optional[Material]:
        """Get material by code."""
        return self.materials.get(code)
    
    def list_materials(self) -> list:
        """Return list of available material codes."""
        return list(self.materials.keys())
    
    def __getitem__(self, code: str) -> Material:
        return self.materials[code]
    
    def __contains__(self, code: str) -> bool:
        return code in self.materials


# Convenience function to get default database
_default_db: Optional[MaterialDatabase] = None

def get_material_db() -> MaterialDatabase:
    """Get the default material database (singleton)."""
    global _default_db
    if _default_db is None:
        _default_db = MaterialDatabase()
    return _default_db
