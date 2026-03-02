"""
Weave construction types and their efficiency factors.
"""

from dataclasses import dataclass
from typing import Optional, Dict
import json
from pathlib import Path


@dataclass
class WeaveType:
    """Represents a weaving construction pattern."""
    
    name: str
    code: str
    croatian_name: str
    description: str
    
    # Efficiency factors (0-1) representing strength retention vs ideal
    eta_warp: float
    eta_weft: float
    
    # Weight multiplier for binding threads etc.
    weight_factor: float
    
    # Whether construction requires binding thread
    binding_thread_required: bool
    
    notes: str = ""
    
    def get_efficiency(self, direction: str) -> float:
        """
        Get efficiency factor for a direction.
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Efficiency factor (0-1)
        """
        if direction.lower() == 'warp':
            return self.eta_warp
        elif direction.lower() == 'weft':
            return self.eta_weft
        else:
            raise ValueError(f"Unknown direction: {direction}. Use 'warp' or 'weft'.")


@dataclass
class BindingThread:
    """Configuration for binding thread (provezujuća nit)."""
    
    material: str
    tex: float
    contributes_to_strength: bool = False
    typical_weight_g_m2: float = 3.5


class WeaveTypeDatabase:
    """Manages available weave construction types."""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.weave_types: Dict[str, WeaveType] = {}
        self.binding_thread_defaults: Optional[BindingThread] = None
        
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "weave_types.json"
        
        self._load_from_json(data_path)
    
    def _load_from_json(self, path: Path):
        """Load weave types from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        weave_data = data.get("weave_types", {})
        
        for code, props in weave_data.items():
            weave = WeaveType(
                name=props["name"],
                code=code,
                croatian_name=props.get("croatian_name", ""),
                description=props.get("description", ""),
                eta_warp=props["eta_warp"],
                eta_weft=props["eta_weft"],
                weight_factor=props.get("weight_factor", 1.0),
                binding_thread_required=props.get("binding_thread_required", False),
                notes=props.get("notes", "")
            )
            self.weave_types[code] = weave
        
        # Load binding thread defaults
        bt_data = data.get("binding_thread_defaults", {})
        if bt_data:
            self.binding_thread_defaults = BindingThread(
                material=bt_data.get("material", "PES"),
                tex=bt_data.get("tex", 22),
                contributes_to_strength=bt_data.get("contributes_to_strength", False),
                typical_weight_g_m2=bt_data.get("typical_weight_addition_g_m2", 3.5)
            )
    
    def get(self, code: str) -> Optional[WeaveType]:
        """Get weave type by code."""
        return self.weave_types.get(code)
    
    def list_weaves(self) -> list:
        """Return list of available weave codes."""
        return list(self.weave_types.keys())
    
    def __getitem__(self, code: str) -> WeaveType:
        return self.weave_types[code]
    
    def __contains__(self, code: str) -> bool:
        return code in self.weave_types


# Convenience function to get default database
_default_db: Optional[WeaveTypeDatabase] = None

def get_weave_db() -> WeaveTypeDatabase:
    """Get the default weave type database (singleton)."""
    global _default_db
    if _default_db is None:
        _default_db = WeaveTypeDatabase()
    return _default_db
