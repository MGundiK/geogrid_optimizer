#!/usr/bin/env python3
"""
Analysis of CSV interpretation vs Datasheet validation

Key insight: The CSV column "Broj niti potke na 10 cm" is for WEFT only!
The warp construction is NOT fully specified in the CSV.
"""

# The CSV column headers are:
# - Šifra artikla (Product code)
# - Naziv artikla (Product name)  
# - Trenutno/osnova (Current/warp) - just tex
# - Trenutno/potka (Current/weft) - just tex
# - Broj niti potke na 10 cm (Number of WEFT threads per 10 cm) - weft density and strands
# - Težina artikla (Product weight)
# - *SC (some coefficient)

# CRITICAL INSIGHT:
# The density/strands notation (like "2,6 x 2" or "3.33") appears in the WEFT column only!
# We DON'T have warp density or warp strands from CSV directly.

# For products where we need warp construction, we must:
# 1. Back-calculate from datasheet cross-section values, OR
# 2. Assume warp = weft (symmetric), OR  
# 3. Get additional data from manufacturer

print("=" * 70)
print("CSV INTERPRETATION ANALYSIS")
print("=" * 70)

products = [
    {
        "name": "Grid 49",
        "csv_warp": "1200 tex",
        "csv_weft": "2400 tex",
        "csv_weft_density": "2,6 x 2",
        "datasheet_warp_cs_per_m": 49.11,  # mm²/m
        "datasheet_weft_cs_per_m": 48.0,   # mm²/m
        "datasheet_cs_per_rib": 1.85,      # mm²
    },
    {
        "name": "Grid 250",
        "csv_warp": "1200 tex",
        "csv_weft": "1200 tex", 
        "csv_weft_density": "3,973 x 2",
        "datasheet_weight": 250,
    },
    {
        "name": "ARG-460",
        "csv_warp": "1200 tex",
        "csv_weft": "2 x 2400 tex",
        "csv_weft_density": "3.33",
        "datasheet_warp_force": 100,  # kN/m
        "datasheet_weft_force": 100,
    },
]

print("\nPROBLEM: The CSV only gives WEFT density/strands notation, not WARP!")
print()

# Back-calculate Grid 49 warp construction
print("GRID 49 WARP BACK-CALCULATION:")
print("-" * 50)

# From datasheet
warp_cs_per_m = 49.11  # mm²/m
weft_cs_per_m = 48.0   # mm²/m
cs_per_rib = 1.85      # mm² (this is per rib)

# Calculate ribs per meter from cross-section
warp_ribs_per_m = warp_cs_per_m / cs_per_rib
weft_ribs_per_m = weft_cs_per_m / cs_per_rib

print(f"Datasheet warp cross-section: {warp_cs_per_m} mm²/m")
print(f"Datasheet cross-section per rib: {cs_per_rib} mm²")
print(f"→ Calculated warp ribs/m: {warp_ribs_per_m:.1f} = {warp_ribs_per_m/10:.2f}/10cm")
print(f"→ Calculated weft ribs/m: {weft_ribs_per_m:.1f} = {weft_ribs_per_m/10:.2f}/10cm")

# Now back-calculate strands from cross-section
# For 1200 tex AR-glass (ρ=2.6): cross-section = tex × strands / (ρ × 1000)
# 1.85 = 1200 × strands / 2600
# strands = 1.85 × 2600 / 1200 = 4.0
tex_warp = 1200
rho = 2.6
strands_warp = cs_per_rib * rho * 1000 / tex_warp
print(f"\nBack-calculate warp strands:")
print(f"  cs_per_rib = tex × strands / (ρ × 1000)")
print(f"  {cs_per_rib} = {tex_warp} × strands / {rho * 1000}")
print(f"  strands = {strands_warp:.1f}")

# For weft: 2400 tex × 2 strands = 4800 tex total
tex_weft = 2400
strands_weft = 2  # From CSV notation "2,6 x 2"
total_tex_weft = tex_weft * strands_weft
cs_weft_calc = total_tex_weft / (rho * 1000)
print(f"\nWeft (from CSV '2,6 x 2'):")
print(f"  2400 tex × 2 strands = 4800 tex total")
print(f"  Cross-section/rib = {cs_weft_calc:.3f} mm²")

print("\n" + "=" * 70)
print("CORRECTED GRID 49 CONSTRUCTION:")
print("=" * 70)
print(f"""
WARP (back-calculated from datasheet):
  - tex: 1200
  - strands_per_rib: 4  ← NOT shown in CSV!
  - total_tex_per_rib: 4800
  - density: 2.66/10cm (from 49.11 / 1.85 = 26.6/m)

WEFT (from CSV "2,6 x 2"):
  - tex: 2400  
  - strands_per_rib: 2
  - total_tex_per_rib: 4800
  - density: 2.6/10cm

This matches the datasheet values!
""")

print("=" * 70)
print("KEY FINDING:")
print("=" * 70)
print("""
The CSV notation rules are:

1. Warp column (osnova): Shows ONLY the base tex value
   - "1200 tex" = single strand tex is 1200, but strands NOT specified
   
2. Weft column (potka): Shows tex with optional multiplier
   - "2400 tex" = single strand of 2400 tex
   - "2 x 2400 tex" = 2 strands of 2400 tex
   - "4800 tex + 2400 tex" = mixed tex construction

3. Weft density column (Broj niti potke na 10 cm):
   - "6" = 6 ribs per 10cm, 1 strand each
   - "2,6 x 2" = 2.6 ribs per 10cm, 2 strands each
   - "2,625 x (2+1)" = 2.625/10cm, 2 strands of first tex + 1 of second

4. Warp density: NOT in CSV! Must be:
   - Assumed same as weft (if symmetric), OR
   - Back-calculated from datasheet cross-section
   
5. Warp strands: NOT in CSV! Must be:
   - Assumed same as weft (if symmetric), OR
   - Back-calculated from datasheet
""")

print("\n" + "=" * 70)
print("PRODUCTS NEEDING WARP BACK-CALCULATION:")
print("=" * 70)
print("""
Products where warp ≠ weft (asymmetric) need datasheet back-calculation:
- Grid 49: warp 1200 tex, weft 2400 tex → warp strands = 4
- Grid 280: warp 1200 tex, weft 2400 tex → need datasheet
- Grid 320: warp 640 tex, weft 2400 tex → need datasheet
- ARG-300: warp 640 tex, weft 2400 tex → need datasheet
- ARG-460: warp 1200 tex, weft 2×2400 tex → need datasheet
- ARG-550: warp 1200 tex, weft 2×2400 tex → need datasheet

Products that are likely symmetric (can assume warp = weft):
- Grid 185: 1200/1200 tex
- ARG-240: 640/640 tex
- ARG-290: 1200/1200 tex
- ARG-320-FR: 1200/1200 tex
- ARG-450-FR: 2400/2400 tex
""")
