"""
Impregnation (apretura) types and their effects on grid properties.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
import json
from pathlib import Path


@dataclass
class ImpregnationComponent:
    """A component in an impregnation mixture."""
    name: str
    percentage: float


@dataclass
class ImpregnationType:
    """Represents an impregnation/coating type."""
    
    name: str
    code: str
    components: List[ImpregnationComponent] = field(default_factory=list)
    
    # Strength coefficients due to impregnation type
    strength_coeff_type_warp: float = 1.0
    strength_coeff_type_weft: float = 1.0
    
    # Strength coefficients due to application method
    strength_coeff_application_warp: float = 1.0
    strength_coeff_application_weft: float = 1.0
    
    notes: str = ""
    
    def total_strength_coefficient(self, direction: str) -> float:
        """
        Get total strength coefficient for a direction.
        
        The impregnation enhances breaking force by this factor.
        
        Args:
            direction: 'warp' or 'weft'
            
        Returns:
            Total strength multiplier (typically > 1.0)
        """
        if direction.lower() == 'warp':
            return self.strength_coeff_type_warp * self.strength_coeff_application_warp
        elif direction.lower() == 'weft':
            return self.strength_coeff_type_weft * self.strength_coeff_application_weft
        else:
            raise ValueError(f"Unknown direction: {direction}")
    
    def get_coefficients(self) -> Tuple[float, float]:
        """Return (warp_coeff, weft_coeff) tuple."""
        return (
            self.total_strength_coefficient('warp'),
            self.total_strength_coefficient('weft')
        )


@dataclass
class ImpregnationParameters:
    """Parameters controlling impregnation application."""
    
    impreg_type: ImpregnationType
    application_ratio_percent: float  # nanos apreture, typically 1.0-1.5%
    
    # Weaving coefficient (material loss during weaving), ~0.98
    weaving_coefficient: float = 0.98
    
    # Loss coefficient during application, ~2.1
    application_loss_coefficient: float = 2.1
    
    def weight_ratio(self, base_weight_g_m2: float) -> float:
        """
        Calculate the weight ratio (omjer apreture).
        
        This is an approximation - actual ratio depends on fabric structure.
        
        Args:
            base_weight_g_m2: Raw fabric weight before impregnation
            
        Returns:
            Ratio of impregnated weight to raw weight
        """
        # Empirical relationship based on application ratio
        # Higher application ratio -> higher weight ratio
        # Typical: 1.2% application -> ~1.20-1.25 weight ratio
        return 1.0 + (self.application_ratio_percent / 100) * 20  # Rough approximation
    
    def impregnation_weight(self, base_weight_g_m2: float) -> float:
        """
        Calculate weight added by impregnation (g/m²).
        
        Args:
            base_weight_g_m2: Raw fabric weight
            
        Returns:
            Weight of impregnation material that stays on fabric
        """
        ratio = self.weight_ratio(base_weight_g_m2)
        return base_weight_g_m2 * (ratio - 1)
    
    def impregnation_usage(self, base_weight_g_m2: float) -> float:
        """
        Calculate total impregnation material usage (including losses).
        
        Args:
            base_weight_g_m2: Raw fabric weight
            
        Returns:
            Total impregnation material consumed (g/m²)
        """
        weight_on_fabric = self.impregnation_weight(base_weight_g_m2)
        return weight_on_fabric * self.application_loss_coefficient


class ImpregnationDatabase:
    """Manages available impregnation types."""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.impreg_types: Dict[str, ImpregnationType] = {}
        self.weaving_coefficient: float = 0.98
        self.application_loss_coefficient: float = 2.1
        self.typical_application_ratios: Dict[str, float] = {}
        
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "impregnation.json"
        
        self._load_from_json(data_path)
    
    def _load_from_json(self, path: Path):
        """Load impregnation data from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        impreg_data = data.get("impregnation_types", {})
        
        for code, props in impreg_data.items():
            components = [
                ImpregnationComponent(c["name"], c["percentage"])
                for c in props.get("components", [])
            ]
            
            coeff_type = props.get("strength_coefficient_type", {})
            coeff_app = props.get("strength_coefficient_application", {})
            
            impreg = ImpregnationType(
                name=props["name"],
                code=code,
                components=components,
                strength_coeff_type_warp=coeff_type.get("warp", 1.0),
                strength_coeff_type_weft=coeff_type.get("weft", 1.0),
                strength_coeff_application_warp=coeff_app.get("warp", 1.0),
                strength_coeff_application_weft=coeff_app.get("weft", 1.0),
                notes=props.get("notes", "")
            )
            self.impreg_types[code] = impreg
        
        # Load application parameters
        app_params = data.get("application_parameters", {})
        self.typical_application_ratios = app_params.get(
            "typical_application_ratio_percent", {}
        )
        
        weave_coeff = data.get("weaving_coefficient", {})
        self.weaving_coefficient = weave_coeff.get("value", 0.98)
    
    def get(self, code: str) -> Optional[ImpregnationType]:
        """Get impregnation type by code."""
        return self.impreg_types.get(code)
    
    def list_types(self) -> list:
        """Return list of available impregnation codes."""
        return list(self.impreg_types.keys())
    
    def create_parameters(
        self,
        impreg_code: str,
        application_ratio_percent: float = 1.2
    ) -> ImpregnationParameters:
        """
        Create impregnation parameters with given settings.
        
        Args:
            impreg_code: Impregnation type code
            application_ratio_percent: Application ratio (nanos apreture)
            
        Returns:
            Configured ImpregnationParameters object
        """
        impreg_type = self.get(impreg_code)
        if impreg_type is None:
            raise ValueError(f"Unknown impregnation type: {impreg_code}")
        
        return ImpregnationParameters(
            impreg_type=impreg_type,
            application_ratio_percent=application_ratio_percent,
            weaving_coefficient=self.weaving_coefficient,
            application_loss_coefficient=self.application_loss_coefficient
        )
    
    def __getitem__(self, code: str) -> ImpregnationType:
        return self.impreg_types[code]
    
    def __contains__(self, code: str) -> bool:
        return code in self.impreg_types


# Convenience function
_default_db: Optional[ImpregnationDatabase] = None

def get_impregnation_db() -> ImpregnationDatabase:
    """Get the default impregnation database (singleton)."""
    global _default_db
    if _default_db is None:
        _default_db = ImpregnationDatabase()
    return _default_db
