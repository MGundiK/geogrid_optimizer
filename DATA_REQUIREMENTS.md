# Geogrid Optimizer - Data Requirements Summary

## Current Model Status

**Validation Accuracy: 84%** (48/57 comparisons within 15% error)

The model now correctly interprets CSV construction data and uses back-calculated warp values where datasheet cross-section information is available.

---

## Understanding the CSV Format

### Column Definitions
| Column | Croatian | English | Contains |
|--------|----------|---------|----------|
| Šifra artikla | - | Product code | Internal reference |
| Naziv artikla | - | Product name | Full product name |
| osnova | warp | Warp | **Tex value only** (no strands!) |
| potka | weft | Weft | Tex value, optionally with "N x" prefix |
| Broj niti potke na 10 cm | - | Weft threads/10cm | Density, optionally with "x N" for strands |
| Težina artikla | - | Product weight | g/m² |

### Notation Rules
| CSV Notation | Meaning |
|--------------|---------|
| `1200 tex` | 1 strand of 1200 tex |
| `2 x 2400 tex` | 2 strands of 2400 tex each |
| `4800 tex + 2400 tex` | Mixed: different tex strands |
| `6` (density) | 6 ribs/10cm, 1 strand each |
| `2,6 x 2` (density) | 2.6 ribs/10cm, 2 strands each |
| `2,625 x (2+1)` (density) | 2.625/10cm, 2+1 mixed strands |

### Critical Limitation
**The CSV only provides WEFT construction details!**  
Warp strands and density must be obtained separately or back-calculated from datasheet cross-section values.

---

## Data Needed for Remaining Products

### Priority 1: Products with >25% Error (Need Warp Construction)

#### ANTISEISMIC Grid 350
- **Current issue**: 26% weight error
- **CSV shows**: `osnova: 1200 tex + 640 tex`, `potka: 2400 tex + 1200 tex`, density `3,75 + 3,75`
- **Needed**: 
  - How many strands of 1200 tex in warp?
  - How many strands of 640 tex in warp?
  - Are they alternating or bundled together?
  - What is the warp density?

#### FLEX GRID ARG-460-AAS3 (Weft Force)
- **Current issue**: 30% weft breaking force error
- **CSV shows**: `potka: 2 x 2400 tex` at 3.33/10cm
- **Questions**:
  - Is the impregnation efficiency different for this product?
  - Is the actual weft construction different?

#### FLEX GRID ARG-550-AAS3 (Warp Force)
- **Current issue**: 29% warp breaking force error
- **Currently estimated**: 4 strands of 1200 tex
- **Needed**:
  - Actual warp strands per rib
  - Warp density if different from weft (4.5/10cm)

---

### Priority 2: Products with 15-25% Warning

| Product | Parameter | Error | What's Needed |
|---------|-----------|-------|---------------|
| Grid 49 | Weft force | 22% | Verify weft construction or impreg efficiency |
| Grid 49 | Weight | 17% | May need impreg% verification |
| ARG-300 | Weft force | 24% | Verify weft strands (currently 1) |
| Q121-RRE | Weight | 15% | Complex construction verification |
| Briksy | Forces | 22% | Verify SBR latex efficiency |

---

### Priority 3: Products with Estimated Warp (No Datasheet Cross-Section)

These products have warp construction **estimated** based on matching weft total tex. Actual data would improve accuracy:

| Product | Estimated Warp | Verification Needed |
|---------|----------------|---------------------|
| Grid 320 | 640 tex × 4 strands | Actual strands |
| Grid 130 | 320 tex × 2 strands | Actual strands |
| ARG-300 | 640 tex × 4 strands | Actual strands |
| ARG-330 | 1200 tex × 6 strands | Actual strands |
| ARG-550 | 1200 tex × 4 strands | Actual strands |
| ARG-160 | 320 tex × 8 strands | Actual strands |
| ARG-310 | 640 tex × 8 strands | Actual strands |
| ARG-110 | 320 tex × 2 strands | Actual strands |

---

## Ideal Data Format

For each product, the most useful data would be:

```
Product: [Name]
Warp:
  - tex: [value]
  - strands per rib: [value]
  - ribs per 10cm: [value]
Weft:
  - tex: [value]  
  - strands per rib: [value]
  - ribs per 10cm: [value]
Impregnation:
  - type: [epoxy/SBR/styrene-butadiene]
  - percentage: [%]
```

Or, if available, the **production calculation sheet** (razrada artikla) like the AR-460-25x25 example would be ideal as it contains all construction parameters.

---

## Products with Complete Data (No Action Needed)

These products are validating well with current data:

| Product | Weight Error | Force Error | Status |
|---------|--------------|-------------|--------|
| Grid 185 | 2% | - | ✓ Complete |
| Grid 250 | 4% | - | ✓ Complete |
| Grid 280 | 13% | - | ✓ Complete |
| Grid 130 | 1% | - | ✓ Complete |
| ARG-240-5x5 | 0.4% | 6-10% | ✓ Complete |
| ARG-290-8x8 | 4% | 10% | ✓ Complete |
| ARG-330-50x50 | 1% | - | ✓ Complete |
| ARG-160-40x40 | 3% | - | ✓ Complete |
| ARG-310-35x35 | 1% | - | ✓ Complete |
| ARG-320-FR | 5% | - | ✓ Complete |
| ARG-450-FR | 6% | - | ✓ Complete |
| ARG-110 | 2% | - | ✓ Complete |

---

## Summary

| Category | Count | Action |
|----------|-------|--------|
| Complete (good accuracy) | 12 products | None needed |
| Need warp data | 8 products | Request from factory |
| Complex/alternating | 2 products | Need detailed breakdown |
| Need verification | 5 parameters | Confirm impreg% or construction |

**Total products in database: 22**  
**Fully validated: 12 (55%)**  
**Need additional data: 10 (45%)**
