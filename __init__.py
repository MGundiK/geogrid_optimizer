"""
Geogrid Optimizer

A Python package for calculating and optimizing geogrid textile properties.

This package provides tools for:
- Calculating physical properties of geogrid reinforcement textiles
- Finding optimal designs using multi-objective genetic algorithms (NSGA-II)
- Exploring trade-offs between weight, strength, aperture, and cost

Main classes:
- GridDesign: Core model for grid property calculations
- NSGA2Optimizer: Multi-objective optimizer for finding Pareto-optimal designs
- MaterialDatabase: Database of fiber materials
- WeaveTypeDatabase: Database of weave construction types
- ImpregnationDatabase: Database of impregnation/coating types

Example usage:
    from geogrid_optimizer import create_symmetric_grid, NSGA2Optimizer
    
    # Calculate properties for a specific design
    design = create_symmetric_grid(
        material_code='AR_glass',
        tex=640,
        strands=2,
        density_per_10cm=8
    )
    print(design.summary())
    
    # Run optimization
    optimizer = NSGA2Optimizer(...)
    results = optimizer.run()
"""

__version__ = '0.1.0'
__author__ = 'Claude'

from .models import (
    GridDesign,
    DirectionConfig,
    create_symmetric_grid,
    Material,
    MaterialDatabase,
    get_material_db,
    WeaveType,
    WeaveTypeDatabase,
    get_weave_db,
    ImpregnationType,
    ImpregnationDatabase,
    get_impregnation_db
)

from .optimizer import (
    NSGA2Optimizer,
    DesignBounds,
    Constraints,
    Individual
)

__all__ = [
    # Grid models
    'GridDesign',
    'DirectionConfig',
    'create_symmetric_grid',
    
    # Materials
    'Material',
    'MaterialDatabase',
    'get_material_db',
    
    # Weaves
    'WeaveType',
    'WeaveTypeDatabase',
    'get_weave_db',
    
    # Impregnation
    'ImpregnationType',
    'ImpregnationDatabase',
    'get_impregnation_db',
    
    # Optimizer
    'NSGA2Optimizer',
    'DesignBounds',
    'Constraints',
    'Individual'
]
