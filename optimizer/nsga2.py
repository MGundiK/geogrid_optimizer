"""
NSGA-II Multi-Objective Genetic Algorithm for geogrid optimization.

This module implements the Non-dominated Sorting Genetic Algorithm II (NSGA-II)
for finding Pareto-optimal geogrid designs.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Dict, Any
from copy import deepcopy
import json
import sys
from pathlib import Path

# Handle imports for both package and standalone usage
try:
    from ..models import (
        GridDesign, 
        DirectionConfig,
        get_material_db,
        get_weave_db,
        get_impregnation_db
    )
except ImportError:
    from models import (
        GridDesign, 
        DirectionConfig,
        get_material_db,
        get_weave_db,
        get_impregnation_db
    )


@dataclass
class DesignBounds:
    """Bounds for design variables in the optimization."""
    
    # Material options (discrete)
    materials: List[str] = field(default_factory=lambda: ['AR_glass', 'carbon', 'basalt'])
    
    # Weave options (discrete)
    weaves: List[str] = field(default_factory=lambda: ['LE', 'DLE', 'PLE'])
    
    # Impregnation options (discrete)
    impregnations: List[str] = field(default_factory=lambda: ['SBR_latex', 'epoxy'])
    
    # Tex bounds (continuous, will be discretized to available values)
    tex_min: float = 400
    tex_max: float = 3000
    tex_values: List[float] = field(default_factory=lambda: [320, 640, 800, 1200, 1600, 2400, 3200])
    
    # Strands per rib (integer)
    strands_min: int = 1
    strands_max: int = 10
    
    # Density per 10cm (continuous)
    density_min: float = 2.0
    density_max: float = 20.0
    
    # Application ratio (continuous)
    application_ratio_min: float = 1.0
    application_ratio_max: float = 1.5
    
    # Allow asymmetric designs (different warp/weft)?
    allow_asymmetric: bool = True
    
    # Allow dual-tex constructions (two tex values in same direction)?
    # Example: Grid 350 has warp with 1200 tex + 640 tex combined
    allow_dual_tex: bool = False
    
    # Dual-tex probability (when enabled, chance of creating dual-tex design)
    dual_tex_probability: float = 0.3


@dataclass
class Constraints:
    """Constraints that feasible solutions must satisfy."""
    
    # Breaking force constraints (kN/m)
    min_breaking_force_warp: Optional[float] = None
    min_breaking_force_weft: Optional[float] = None
    max_breaking_force_warp: Optional[float] = None
    max_breaking_force_weft: Optional[float] = None
    
    # Weight constraints (g/m²)
    max_weight: Optional[float] = None
    min_weight: Optional[float] = None
    
    # Aperture constraints (mm)
    min_aperture_warp: Optional[float] = None
    min_aperture_weft: Optional[float] = None
    max_aperture_warp: Optional[float] = None
    max_aperture_weft: Optional[float] = None
    
    # Cost constraints (EUR/m²)
    max_cost: Optional[float] = None
    
    # Tex constraints (per rib)
    max_tex_per_rib: Optional[float] = None
    min_tex_per_rib: Optional[float] = None
    
    # Cross-section constraints (mm²/m)
    min_cross_section: Optional[float] = None
    max_cross_section: Optional[float] = None
    
    # Mesh size constraints (mm)
    target_mesh_size: Optional[float] = None
    mesh_size_tolerance: float = 2.0  # mm tolerance
    
    def is_feasible(self, design: GridDesign) -> Tuple[bool, List[str]]:
        """
        Check if a design satisfies all constraints.
        
        Args:
            design: Grid design to check
            
        Returns:
            Tuple of (is_feasible, list_of_violations)
        """
        violations = []
        
        # Breaking force checks
        bf_warp = design.breaking_force_kN_m('warp')
        bf_weft = design.breaking_force_kN_m('weft')
        
        if self.min_breaking_force_warp and bf_warp < self.min_breaking_force_warp:
            violations.append(f"Warp force {bf_warp:.1f} < min {self.min_breaking_force_warp}")
        if self.min_breaking_force_weft and bf_weft < self.min_breaking_force_weft:
            violations.append(f"Weft force {bf_weft:.1f} < min {self.min_breaking_force_weft}")
        if self.max_breaking_force_warp and bf_warp > self.max_breaking_force_warp:
            violations.append(f"Warp force {bf_warp:.1f} > max {self.max_breaking_force_warp}")
        if self.max_breaking_force_weft and bf_weft > self.max_breaking_force_weft:
            violations.append(f"Weft force {bf_weft:.1f} > max {self.max_breaking_force_weft}")
        
        # Weight checks
        weight = design.impregnated_weight_g_m2()
        if self.max_weight and weight > self.max_weight:
            violations.append(f"Weight {weight:.1f} > max {self.max_weight}")
        if self.min_weight and weight < self.min_weight:
            violations.append(f"Weight {weight:.1f} < min {self.min_weight}")
        
        # Aperture checks
        ap_warp = design.clear_aperture_mm('warp')
        ap_weft = design.clear_aperture_mm('weft')
        
        if self.min_aperture_warp and ap_warp < self.min_aperture_warp:
            violations.append(f"Warp aperture {ap_warp:.1f} < min {self.min_aperture_warp}")
        if self.min_aperture_weft and ap_weft < self.min_aperture_weft:
            violations.append(f"Weft aperture {ap_weft:.1f} < min {self.min_aperture_weft}")
        if self.max_aperture_warp and ap_warp > self.max_aperture_warp:
            violations.append(f"Warp aperture {ap_warp:.1f} > max {self.max_aperture_warp}")
        if self.max_aperture_weft and ap_weft > self.max_aperture_weft:
            violations.append(f"Weft aperture {ap_weft:.1f} > max {self.max_aperture_weft}")
        
        # Tex checks
        tex_warp = design.warp.total_tex_per_rib
        tex_weft = design.weft.total_tex_per_rib
        if self.max_tex_per_rib:
            if tex_warp > self.max_tex_per_rib:
                violations.append(f"Warp tex {tex_warp:.0f} > max {self.max_tex_per_rib}")
            if tex_weft > self.max_tex_per_rib:
                violations.append(f"Weft tex {tex_weft:.0f} > max {self.max_tex_per_rib}")
        if self.min_tex_per_rib:
            if tex_warp < self.min_tex_per_rib:
                violations.append(f"Warp tex {tex_warp:.0f} < min {self.min_tex_per_rib}")
            if tex_weft < self.min_tex_per_rib:
                violations.append(f"Weft tex {tex_weft:.0f} < min {self.min_tex_per_rib}")
        
        # Cross-section checks
        cs_warp = design.fiber_cross_section_mm2_per_m('warp')
        cs_weft = design.fiber_cross_section_mm2_per_m('weft')
        min_cs = min(cs_warp, cs_weft)
        max_cs = max(cs_warp, cs_weft)
        
        if self.min_cross_section and min_cs < self.min_cross_section:
            violations.append(f"Cross-section {min_cs:.1f} < min {self.min_cross_section}")
        if self.max_cross_section and max_cs > self.max_cross_section:
            violations.append(f"Cross-section {max_cs:.1f} > max {self.max_cross_section}")
        
        # Mesh size check
        if self.target_mesh_size:
            mesh_warp = design.clear_aperture_mm('warp')
            mesh_weft = design.clear_aperture_mm('weft')
            if abs(mesh_warp - self.target_mesh_size) > self.mesh_size_tolerance:
                violations.append(f"Mesh warp {mesh_warp:.1f} != target {self.target_mesh_size}±{self.mesh_size_tolerance}")
            if abs(mesh_weft - self.target_mesh_size) > self.mesh_size_tolerance:
                violations.append(f"Mesh weft {mesh_weft:.1f} != target {self.target_mesh_size}±{self.mesh_size_tolerance}")
        
        return len(violations) == 0, violations
    
    def constraint_violation(self, design: GridDesign) -> float:
        """
        Calculate total constraint violation (for penalty-based handling).
        
        Args:
            design: Grid design to check
            
        Returns:
            Sum of squared constraint violations (0 if feasible)
        """
        violation = 0.0
        
        bf_warp = design.breaking_force_kN_m('warp')
        bf_weft = design.breaking_force_kN_m('weft')
        weight = design.impregnated_weight_g_m2()
        ap_warp = design.clear_aperture_mm('warp')
        ap_weft = design.clear_aperture_mm('weft')
        
        if self.min_breaking_force_warp and bf_warp < self.min_breaking_force_warp:
            violation += (self.min_breaking_force_warp - bf_warp) ** 2
        if self.min_breaking_force_weft and bf_weft < self.min_breaking_force_weft:
            violation += (self.min_breaking_force_weft - bf_weft) ** 2
        if self.max_weight and weight > self.max_weight:
            violation += ((weight - self.max_weight) / 100) ** 2
        if self.min_aperture_warp and ap_warp < self.min_aperture_warp:
            violation += (self.min_aperture_warp - ap_warp) ** 2
        if self.min_aperture_weft and ap_weft < self.min_aperture_weft:
            violation += (self.min_aperture_weft - ap_weft) ** 2
        
        # Tex violations
        if self.max_tex_per_rib:
            tex_warp = design.warp.total_tex_per_rib
            tex_weft = design.weft.total_tex_per_rib
            if tex_warp > self.max_tex_per_rib:
                violation += ((tex_warp - self.max_tex_per_rib) / 1000) ** 2
            if tex_weft > self.max_tex_per_rib:
                violation += ((tex_weft - self.max_tex_per_rib) / 1000) ** 2
        
        # Cross-section violations
        if self.min_cross_section:
            cs_warp = design.fiber_cross_section_mm2_per_m('warp')
            cs_weft = design.fiber_cross_section_mm2_per_m('weft')
            if cs_warp < self.min_cross_section:
                violation += (self.min_cross_section - cs_warp) ** 2
            if cs_weft < self.min_cross_section:
                violation += (self.min_cross_section - cs_weft) ** 2
        
        # Mesh size violations
        if self.target_mesh_size:
            mesh_warp = design.clear_aperture_mm('warp')
            mesh_weft = design.clear_aperture_mm('weft')
            err_warp = abs(mesh_warp - self.target_mesh_size) - self.mesh_size_tolerance
            err_weft = abs(mesh_weft - self.target_mesh_size) - self.mesh_size_tolerance
            if err_warp > 0:
                violation += err_warp ** 2
            if err_weft > 0:
                violation += err_weft ** 2
        
        return violation


@dataclass
class Individual:
    """An individual solution in the population."""
    
    design: GridDesign
    objectives: List[float] = field(default_factory=list)
    constraint_violation: float = 0.0
    rank: int = 0
    crowding_distance: float = 0.0
    
    def dominates(self, other: 'Individual') -> bool:
        """
        Check if this individual dominates another.
        
        Domination: at least as good in all objectives, strictly better in at least one.
        Also considers constraint violation.
        """
        # If one is feasible and other isn't, feasible dominates
        if self.constraint_violation == 0 and other.constraint_violation > 0:
            return True
        if self.constraint_violation > 0 and other.constraint_violation == 0:
            return False
        
        # If both infeasible, lower violation dominates
        if self.constraint_violation > 0 and other.constraint_violation > 0:
            return self.constraint_violation < other.constraint_violation
        
        # Both feasible: use Pareto dominance on objectives
        dominated = False
        strictly_better = False
        
        for s, o in zip(self.objectives, other.objectives):
            if s > o:  # Assuming minimization
                dominated = True
            if s < o:
                strictly_better = True
        
        return strictly_better and not dominated


class NSGA2Optimizer:
    """
    NSGA-II optimizer for multi-objective geogrid design.
    
    Finds Pareto-optimal designs that trade off between objectives
    like weight, cost, and strength (while meeting constraints).
    """
    
    def __init__(
        self,
        bounds: DesignBounds,
        constraints: Constraints,
        objectives: List[str] = None,
        population_size: int = 100,
        max_generations: int = 200,
        crossover_prob: float = 0.9,
        mutation_prob: float = 0.1,
        seed: Optional[int] = None
    ):
        """
        Initialize the optimizer.
        
        Args:
            bounds: Design variable bounds
            constraints: Feasibility constraints
            objectives: List of objectives to minimize. Options:
                - 'weight': Minimize impregnated weight
                - 'neg_strength_warp': Maximize warp breaking force
                - 'neg_strength_weft': Maximize weft breaking force  
                - 'neg_strength_min': Maximize minimum of warp/weft force
                - 'cost': Minimize cost (if cost data available)
            population_size: Number of individuals per generation
            max_generations: Maximum number of generations
            crossover_prob: Probability of crossover
            mutation_prob: Probability of mutation
            seed: Random seed for reproducibility
        """
        self.bounds = bounds
        self.constraints = constraints
        self.objectives = objectives or ['weight', 'neg_strength_min']
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        
        if seed is not None:
            random.seed(seed)
        
        self.population: List[Individual] = []
        self.pareto_front: List[Individual] = []
        self.generation = 0
        self.history: List[Dict] = []
    
    def _random_design(self) -> GridDesign:
        """Generate a random grid design within bounds."""
        material = random.choice(self.bounds.materials)
        weave = random.choice(self.bounds.weaves)
        impreg = random.choice(self.bounds.impregnations)
        
        # Select tex from available values within bounds
        valid_tex = [t for t in self.bounds.tex_values 
                     if self.bounds.tex_min <= t <= self.bounds.tex_max]
        if not valid_tex:
            valid_tex = self.bounds.tex_values
        
        # Generate warp configuration
        tex_warp = random.choice(valid_tex)
        strands_warp = random.randint(self.bounds.strands_min, self.bounds.strands_max)
        density_warp = random.uniform(self.bounds.density_min, self.bounds.density_max)
        
        # Check for dual-tex warp
        secondary_tex_warp = None
        secondary_strands_warp = 0
        if self.bounds.allow_dual_tex and random.random() < self.bounds.dual_tex_probability:
            # Select a different tex value for secondary
            other_tex = [t for t in valid_tex if t != tex_warp]
            if other_tex:
                secondary_tex_warp = random.choice(other_tex)
                secondary_strands_warp = random.randint(1, max(1, strands_warp))
        
        # Generate weft configuration
        if self.bounds.allow_asymmetric:
            tex_weft = random.choice(valid_tex)
            strands_weft = random.randint(self.bounds.strands_min, self.bounds.strands_max)
            density_weft = random.uniform(self.bounds.density_min, self.bounds.density_max)
        else:
            tex_weft = tex_warp
            strands_weft = strands_warp
            density_weft = density_warp
        
        # Check for dual-tex weft
        secondary_tex_weft = None
        secondary_strands_weft = 0
        if self.bounds.allow_dual_tex and random.random() < self.bounds.dual_tex_probability:
            other_tex = [t for t in valid_tex if t != tex_weft]
            if other_tex:
                secondary_tex_weft = random.choice(other_tex)
                secondary_strands_weft = random.randint(1, max(1, strands_weft))
        
        app_ratio = random.uniform(
            self.bounds.application_ratio_min,
            self.bounds.application_ratio_max
        )
        
        warp_config = DirectionConfig(
            material_code=material,
            tex=tex_warp,
            strands_per_rib=strands_warp,
            density_per_10cm=round(density_warp, 2),
            secondary_tex=secondary_tex_warp,
            secondary_strands=secondary_strands_warp
        )
        
        weft_config = DirectionConfig(
            material_code=material,  # Same material for now
            tex=tex_weft,
            strands_per_rib=strands_weft,
            density_per_10cm=round(density_weft, 2),
            secondary_tex=secondary_tex_weft,
            secondary_strands=secondary_strands_weft
        )
        
        return GridDesign(
            warp=warp_config,
            weft=weft_config,
            weave_code=weave,
            impreg_code=impreg,
            application_ratio_percent=round(app_ratio, 2)
        )
    
    def _load_cost_data(self) -> dict:
        """Load cost data from JSON file."""
        cost_file = Path(__file__).parent.parent / 'data' / 'costs.json'
        if cost_file.exists():
            with open(cost_file) as f:
                return json.load(f)
        return None
    
    def _calculate_cost(self, design: GridDesign) -> float:
        """
        Calculate material cost in EUR/m².
        
        Cost = fiber_cost + impregnation_cost + processing_cost
        """
        cost_data = self._load_cost_data()
        if not cost_data:
            # Fallback: use weight as proxy
            return design.impregnated_weight_g_m2() / 100
        
        # Fiber cost
        fiber_costs = cost_data.get('fiber_cost_eur_per_kg', {})
        impreg_costs = cost_data.get('impregnation_cost_eur_per_kg', {})
        proc_costs = cost_data.get('processing_cost_eur_per_m2', {})
        
        # Calculate fiber weight and cost for warp and weft
        fiber_weight_warp = design.warp.weight_per_m2_g() / 1000  # kg/m²
        fiber_weight_weft = design.weft.weight_per_m2_g() / 1000
        
        fiber_price_warp = fiber_costs.get(design.warp.material_code, 2.0)
        fiber_price_weft = fiber_costs.get(design.weft.material_code, 2.0)
        
        fiber_cost = fiber_weight_warp * fiber_price_warp + fiber_weight_weft * fiber_price_weft
        
        # Impregnation cost
        raw_weight = design.raw_weight_g_m2()
        impreg_weight = design.impregnated_weight_g_m2() - raw_weight
        impreg_price = impreg_costs.get(design.impreg_code, 2.0)
        impreg_cost = (impreg_weight / 1000) * impreg_price
        
        # Processing cost
        base_proc = proc_costs.get('base', 0.5)
        weave_mult = proc_costs.get('weaving_multiplier', {}).get(design.weave_code, 1.0)
        proc_cost = base_proc * weave_mult
        
        return fiber_cost + impreg_cost + proc_cost
    
    def _evaluate_objectives(self, design: GridDesign) -> List[float]:
        """
        Calculate objective values for a design (all to be minimized).
        
        Available objectives:
        - 'weight': Minimize weight (g/m²)
        - 'cost': Minimize cost (EUR/m²)
        - 'neg_strength_warp': Maximize warp breaking force
        - 'neg_strength_weft': Maximize weft breaking force
        - 'neg_strength_min': Maximize minimum of warp/weft
        - 'neg_strength_avg': Maximize average of warp/weft
        - 'neg_aperture': Maximize mesh opening (minimize density)
        - 'neg_strength_to_weight': Maximize strength/weight ratio
        - 'neg_strength_to_cost': Maximize strength/cost ratio
        - 'total_tex': Minimize total tex usage per rib
        - 'cross_section': Minimize fiber cross-section
        """
        values = []
        
        for obj in self.objectives:
            if obj == 'weight':
                values.append(design.impregnated_weight_g_m2())
            
            elif obj == 'cost':
                values.append(self._calculate_cost(design))
            
            elif obj == 'neg_strength_warp':
                values.append(-design.breaking_force_kN_m('warp'))
            
            elif obj == 'neg_strength_weft':
                values.append(-design.breaking_force_kN_m('weft'))
            
            elif obj == 'neg_strength_min':
                min_strength = min(
                    design.breaking_force_kN_m('warp'),
                    design.breaking_force_kN_m('weft')
                )
                values.append(-min_strength)
            
            elif obj == 'neg_strength_avg':
                avg_strength = (
                    design.breaking_force_kN_m('warp') + 
                    design.breaking_force_kN_m('weft')
                ) / 2
                values.append(-avg_strength)
            
            elif obj == 'neg_aperture':
                # Maximize minimum aperture
                min_aperture = min(
                    design.clear_aperture_mm('warp'),
                    design.clear_aperture_mm('weft')
                )
                values.append(-min_aperture)
            
            elif obj == 'neg_strength_to_weight':
                # Maximize strength/weight ratio (kN/m per g/m²)
                min_strength = min(
                    design.breaking_force_kN_m('warp'),
                    design.breaking_force_kN_m('weft')
                )
                weight = design.impregnated_weight_g_m2()
                ratio = min_strength / weight if weight > 0 else 0
                values.append(-ratio)
            
            elif obj == 'neg_strength_to_cost':
                # Maximize strength/cost ratio (kN/m per EUR/m²)
                min_strength = min(
                    design.breaking_force_kN_m('warp'),
                    design.breaking_force_kN_m('weft')
                )
                cost = self._calculate_cost(design)
                ratio = min_strength / cost if cost > 0 else 0
                values.append(-ratio)
            
            elif obj == 'total_tex':
                # Minimize total tex per rib (warp + weft)
                total_tex = design.warp.total_tex_per_rib + design.weft.total_tex_per_rib
                values.append(total_tex)
            
            elif obj == 'cross_section':
                # Minimize total fiber cross-section per meter
                cs_warp = design.fiber_cross_section_mm2_per_m('warp')
                cs_weft = design.fiber_cross_section_mm2_per_m('weft')
                values.append(cs_warp + cs_weft)
            
            else:
                raise ValueError(f"Unknown objective: {obj}")
        
        return values
    
    def _evaluate_individual(self, design: GridDesign) -> Individual:
        """Create and evaluate an individual from a design."""
        ind = Individual(design=design)
        ind.objectives = self._evaluate_objectives(design)
        ind.constraint_violation = self.constraints.constraint_violation(design)
        return ind
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform crossover between two parents."""
        if random.random() > self.crossover_prob:
            return deepcopy(parent1), deepcopy(parent2)
        
        # Create children by swapping attributes
        d1, d2 = parent1.design, parent2.design
        
        # Randomly swap components
        new_warp1 = deepcopy(d1.warp) if random.random() < 0.5 else deepcopy(d2.warp)
        new_weft1 = deepcopy(d1.weft) if random.random() < 0.5 else deepcopy(d2.weft)
        new_weave1 = d1.weave_code if random.random() < 0.5 else d2.weave_code
        new_impreg1 = d1.impreg_code if random.random() < 0.5 else d2.impreg_code
        new_ratio1 = d1.application_ratio_percent if random.random() < 0.5 else d2.application_ratio_percent
        
        new_warp2 = deepcopy(d2.warp) if random.random() < 0.5 else deepcopy(d1.warp)
        new_weft2 = deepcopy(d2.weft) if random.random() < 0.5 else deepcopy(d1.weft)
        new_weave2 = d2.weave_code if random.random() < 0.5 else d1.weave_code
        new_impreg2 = d2.impreg_code if random.random() < 0.5 else d1.impreg_code
        new_ratio2 = d2.application_ratio_percent if random.random() < 0.5 else d1.application_ratio_percent
        
        child1 = GridDesign(
            warp=new_warp1, weft=new_weft1,
            weave_code=new_weave1, impreg_code=new_impreg1,
            application_ratio_percent=new_ratio1
        )
        child2 = GridDesign(
            warp=new_warp2, weft=new_weft2,
            weave_code=new_weave2, impreg_code=new_impreg2,
            application_ratio_percent=new_ratio2
        )
        
        return self._evaluate_individual(child1), self._evaluate_individual(child2)
    
    def _mutate(self, individual: Individual) -> Individual:
        """Apply mutation to an individual."""
        if random.random() > self.mutation_prob:
            return individual
        
        design = deepcopy(individual.design)
        
        # Build mutation options
        mutation_options = [
            'tex_warp', 'tex_weft', 'strands_warp', 'strands_weft',
            'density_warp', 'density_weft', 'weave', 'impreg', 'ratio'
        ]
        
        # Add dual-tex mutation options if enabled
        if self.bounds.allow_dual_tex:
            mutation_options.extend([
                'secondary_tex_warp', 'secondary_tex_weft',
                'secondary_strands_warp', 'secondary_strands_weft',
                'toggle_dual_tex_warp', 'toggle_dual_tex_weft'
            ])
        
        mutation_type = random.choice(mutation_options)
        
        valid_tex = [t for t in self.bounds.tex_values 
                     if self.bounds.tex_min <= t <= self.bounds.tex_max]
        
        if mutation_type == 'tex_warp' and valid_tex:
            design.warp.tex = random.choice(valid_tex)
        elif mutation_type == 'tex_weft' and valid_tex:
            design.weft.tex = random.choice(valid_tex)
        elif mutation_type == 'strands_warp':
            design.warp.strands_per_rib = random.randint(
                self.bounds.strands_min, self.bounds.strands_max
            )
        elif mutation_type == 'strands_weft':
            design.weft.strands_per_rib = random.randint(
                self.bounds.strands_min, self.bounds.strands_max
            )
        elif mutation_type == 'density_warp':
            design.warp.density_per_10cm = round(random.uniform(
                self.bounds.density_min, self.bounds.density_max
            ), 2)
        elif mutation_type == 'density_weft':
            design.weft.density_per_10cm = round(random.uniform(
                self.bounds.density_min, self.bounds.density_max
            ), 2)
        elif mutation_type == 'weave':
            design.weave_code = random.choice(self.bounds.weaves)
        elif mutation_type == 'impreg':
            design.impreg_code = random.choice(self.bounds.impregnations)
        elif mutation_type == 'ratio':
            design.application_ratio_percent = round(random.uniform(
                self.bounds.application_ratio_min,
                self.bounds.application_ratio_max
            ), 2)
        # Dual-tex mutations
        elif mutation_type == 'secondary_tex_warp' and valid_tex:
            if design.warp.is_dual_tex:
                other_tex = [t for t in valid_tex if t != design.warp.tex]
                if other_tex:
                    design.warp.secondary_tex = random.choice(other_tex)
        elif mutation_type == 'secondary_tex_weft' and valid_tex:
            if design.weft.is_dual_tex:
                other_tex = [t for t in valid_tex if t != design.weft.tex]
                if other_tex:
                    design.weft.secondary_tex = random.choice(other_tex)
        elif mutation_type == 'secondary_strands_warp':
            if design.warp.is_dual_tex:
                design.warp.secondary_strands = random.randint(1, max(1, design.warp.strands_per_rib))
        elif mutation_type == 'secondary_strands_weft':
            if design.weft.is_dual_tex:
                design.weft.secondary_strands = random.randint(1, max(1, design.weft.strands_per_rib))
        elif mutation_type == 'toggle_dual_tex_warp':
            if design.warp.is_dual_tex:
                # Disable dual-tex
                design.warp.secondary_tex = None
                design.warp.secondary_strands = 0
            else:
                # Enable dual-tex
                other_tex = [t for t in valid_tex if t != design.warp.tex]
                if other_tex:
                    design.warp.secondary_tex = random.choice(other_tex)
                    design.warp.secondary_strands = random.randint(1, max(1, design.warp.strands_per_rib))
        elif mutation_type == 'toggle_dual_tex_weft':
            if design.weft.is_dual_tex:
                # Disable dual-tex
                design.weft.secondary_tex = None
                design.weft.secondary_strands = 0
            else:
                # Enable dual-tex
                other_tex = [t for t in valid_tex if t != design.weft.tex]
                if other_tex:
                    design.weft.secondary_tex = random.choice(other_tex)
                    design.weft.secondary_strands = random.randint(1, max(1, design.weft.strands_per_rib))
        
        return self._evaluate_individual(design)
    
    def _fast_non_dominated_sort(self, population: List[Individual]) -> List[List[Individual]]:
        """Perform fast non-dominated sorting."""
        fronts: List[List[Individual]] = [[]]
        
        S = {id(p): [] for p in population}  # Dominated solutions
        n = {id(p): 0 for p in population}   # Domination count
        
        for p in population:
            for q in population:
                if p is q:
                    continue
                if p.dominates(q):
                    S[id(p)].append(q)
                elif q.dominates(p):
                    n[id(p)] += 1
            
            if n[id(p)] == 0:
                p.rank = 0
                fronts[0].append(p)
        
        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in S[id(p)]:
                    n[id(q)] -= 1
                    if n[id(q)] == 0:
                        q.rank = i + 1
                        next_front.append(q)
            i += 1
            fronts.append(next_front)
        
        return fronts[:-1]  # Remove empty last front
    
    def _calculate_crowding_distance(self, front: List[Individual]):
        """Calculate crowding distance for individuals in a front."""
        n = len(front)
        if n <= 2:
            for ind in front:
                ind.crowding_distance = float('inf')
            return
        
        for ind in front:
            ind.crowding_distance = 0
        
        num_objectives = len(front[0].objectives)
        
        for m in range(num_objectives):
            # Sort by objective m
            front.sort(key=lambda x: x.objectives[m])
            
            # Boundary points get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate range
            obj_range = front[-1].objectives[m] - front[0].objectives[m]
            if obj_range == 0:
                continue
            
            # Calculate distances for interior points
            for i in range(1, n - 1):
                front[i].crowding_distance += (
                    front[i + 1].objectives[m] - front[i - 1].objectives[m]
                ) / obj_range
    
    def _tournament_selection(self, population: List[Individual]) -> Individual:
        """Select individual using binary tournament."""
        a, b = random.sample(population, 2)
        
        # Prefer lower rank
        if a.rank < b.rank:
            return a
        if b.rank < a.rank:
            return b
        
        # Same rank: prefer higher crowding distance
        if a.crowding_distance > b.crowding_distance:
            return a
        return b
    
    def initialize_population(self):
        """Initialize random population."""
        self.population = []
        for _ in range(self.population_size):
            design = self._random_design()
            ind = self._evaluate_individual(design)
            self.population.append(ind)
        
        self.generation = 0
    
    def evolve_generation(self):
        """Perform one generation of evolution."""
        # Create offspring
        offspring = []
        while len(offspring) < self.population_size:
            parent1 = self._tournament_selection(self.population)
            parent2 = self._tournament_selection(self.population)
            
            child1, child2 = self._crossover(parent1, parent2)
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            
            offspring.extend([child1, child2])
        
        # Combine parents and offspring
        combined = self.population + offspring[:self.population_size]
        
        # Non-dominated sort
        fronts = self._fast_non_dominated_sort(combined)
        
        # Select next generation
        new_population = []
        front_idx = 0
        
        while len(new_population) + len(fronts[front_idx]) <= self.population_size:
            self._calculate_crowding_distance(fronts[front_idx])
            new_population.extend(fronts[front_idx])
            front_idx += 1
            if front_idx >= len(fronts):
                break
        
        # Fill remaining with best from next front
        if len(new_population) < self.population_size and front_idx < len(fronts):
            self._calculate_crowding_distance(fronts[front_idx])
            fronts[front_idx].sort(key=lambda x: x.crowding_distance, reverse=True)
            remaining = self.population_size - len(new_population)
            new_population.extend(fronts[front_idx][:remaining])
        
        self.population = new_population
        self.generation += 1
        
        # Update Pareto front
        self.pareto_front = [ind for ind in self.population if ind.rank == 0]
        
        # Record history
        feasible = [ind for ind in self.pareto_front if ind.constraint_violation == 0]
        self.history.append({
            'generation': self.generation,
            'pareto_size': len(self.pareto_front),
            'feasible_count': len(feasible),
            'best_objectives': self.pareto_front[0].objectives if self.pareto_front else None
        })
    
    def run(self, verbose: bool = True) -> List[Individual]:
        """
        Run the optimization.
        
        Args:
            verbose: Print progress
            
        Returns:
            Pareto-optimal solutions
        """
        self.initialize_population()
        
        if verbose:
            print(f"Starting NSGA-II optimization")
            print(f"  Population size: {self.population_size}")
            print(f"  Max generations: {self.max_generations}")
            print(f"  Objectives: {self.objectives}")
            print()
        
        for gen in range(self.max_generations):
            self.evolve_generation()
            
            if verbose and (gen + 1) % 20 == 0:
                feasible = len([p for p in self.pareto_front if p.constraint_violation == 0])
                print(f"  Generation {gen + 1}: Pareto front size = {len(self.pareto_front)}, "
                      f"feasible = {feasible}")
        
        # Final sort and filter
        self.pareto_front = [ind for ind in self.population if ind.rank == 0]
        feasible_front = [ind for ind in self.pareto_front if ind.constraint_violation == 0]
        
        if verbose:
            print()
            print(f"Optimization complete!")
            print(f"  Final Pareto front: {len(self.pareto_front)} solutions")
            print(f"  Feasible solutions: {len(feasible_front)}")
        
        return feasible_front if feasible_front else self.pareto_front
    
    def get_pareto_front_data(self) -> List[Dict[str, Any]]:
        """
        Get Pareto front as list of dictionaries for export.
        
        Returns:
            List of solution dictionaries with properties and objectives
        """
        results = []
        
        for ind in self.pareto_front:
            props = ind.design.properties_dict()
            result = {
                'objectives': {
                    name: val for name, val in zip(self.objectives, ind.objectives)
                },
                'constraint_violation': ind.constraint_violation,
                'feasible': ind.constraint_violation == 0,
                **props
            }
            results.append(result)
        
        return results
    
    def export_results(self, filepath: str):
        """Export Pareto front to JSON file."""
        results = self.get_pareto_front_data()
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
