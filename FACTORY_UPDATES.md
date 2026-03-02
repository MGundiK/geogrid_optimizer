# Factory Feedback Updates - March 2026

## Summary of Changes

Based on factory feedback document (Feb 2026), the following updates were made to the geogrid optimizer model.

---

## 1. Density Notation Clarified

### Warp (Osnova): `A × B × C / 10cm`
- A = ribs per 10cm (broj snopova)
- B = pairs per rib (broj parova u snopu)
- C = threads per pair (broj niti u paru)
- **strands_per_rib = B × C**
- **threads_per_m = A × B × C × 10**

### Weft (Potka): `A × B / 10cm`
- A = ribs per 10cm
- B = strands per rib
- **NO gore/dolje concept for weft**
- **threads_per_m = A × B × 10**

---

## 2. Factory-Confirmed Constructions

| Product | Tex × Strands | Factory Notation | Threads/m |
|---------|---------------|------------------|-----------|
| Grid 320 | 640 × 4 | 5×2×2 | 200 |
| Grid 130 | 320 × 2 | 8×1×2 | 160 |
| ARG-300 | 640 × 1 | 10×1×1 | 100 |
| ARG-330 | 1200 × 6 | 1.8×3×2 | 108 |
| ARG-550 | 1200 × 4 | 4.5×2×2 | 180 |
| ARG-160 | 320 × 6 | 2.5×3×2 | 150 |
| ARG-310 | 640 × 6 | 2.5×3×2 | 150 |
| ARG-110 | 320 × 2 | 7×1×2 | 140 |

**Note:** Some of our estimates were corrected:
- ARG-160: We estimated 8 strands → Factory confirms 6 (3×2)
- ARG-310: We estimated 8 strands → Factory confirms 6 (3×2)
- ARG-300: We estimated 4 strands → Factory confirms 1 (1×1)

---

## 3. Grid 350 Complex Construction

Factory confirmed the alternating tex structure:

**Warp:**
- Osnova 1 (640 tex): 3.75 × 2 × 1 = 75 niti/m
- Osnova 2 (1200 tex): 3.75 × 2 × 1 = 75 niti/m
- Combined: 150 threads/m

**Weft:**
- Potka 1 (1200 tex): 3.75 × 1 = 37.5 niti/m
- Potka 2 (2400 tex): 3.75 × 1 = 37.5 niti/m
- Combined: 75 threads/m

---

## 4. Breaking Force Warning

**Factory explicitly stated:**
> "Prekidne sile općenito bih za sada ostavio po strani jer mislim da kod njih imamo najmanje čistu situaciju... Ja sam se svojedobno jako namučio da nađem kvalitetnu formulu za izračun, ali mi ona u praksi nikada nije dobro funkcionirala pa smo je i prestali koristiti."

**Translation:** Even the factory doesn't have a reliable breaking force formula. Focus on weight and cross-section first.

---

## 5. Factory Formula Structure

### Breaking Force (from razrada artikla):
```
F_per_rib = breaking_force_declared × strands × impreg_coeff
F_per_m = F_per_rib × density × 10 / 1000
```

**Key difference:** Factory does NOT use weave efficiency (η) - only impreg coefficient.

### Impregnation Coefficient:
```
UKUPNO = tip_apreture × nanos_apreture × brzina_mjerenja (optional)
```

Example (AR-460):
- tip_apreture: 1.05
- nanos_apreture: 1.05 (warp), 1.25 (weft)
- UKUPNO: 1.103 (warp), 1.313 (weft)

### Weight Formula:
```
weight_impreg = weight_raw × nanos_apreture_ratio
```
Where nanos_apreture_ratio is typically 1.4, 1.5, etc.

---

## 6. Practical Limits (Factory Confirmed)

| Parameter | Min | Max | Notes |
|-----------|-----|-----|-------|
| Strands/rib (warp) | 1 | 6 | Can be higher theoretically |
| Strands/rib (weft) | 1 | 3 | Can be higher theoretically |
| Grid density | 0.7 | 24 | ribs/10cm |
| Fabric density | 15 | 160 | threads/10cm |

---

## 7. Available Tex Values (Factory Provided)

| Material | Standard Tex Values |
|----------|---------------------|
| AR Glass (Roving) | 320, 640, 1200, 2400, 4800 |
| E/ECR Glass (Roving) | 68, 136, 200, 300, 410, 480, 600, 900, 1200, 1800, 2400, 4800, 9600 |
| Glass Thread (Konac) | 34, 68, 110, 136, 204, 272, 408, 544 |
| Basalt | 300, 600, 1200, 2000, 2200, 2400, 4800 |
| Carbon | 67, 200, 400, 800, 1600, 3200, 3360 |

---

## 8. Validation Results After Updates

| Category | Count | Percentage |
|----------|-------|------------|
| Good (<15% error) | 36 | 71% |
| Warning (15-25%) | 7 | 14% |
| High (>25%) | 8 | 16% |

### Products Needing Attention:
- **ARG-240**: 141% weight error - needs factory verification of density
- **ARG-330**: 33.7% weight error - may have incorrect construction
- **Breaking forces**: Several products have high errors - as factory noted, these formulas are unreliable

---

## 9. Next Steps

1. **Get factory calculation sheets** (razrada artikla) for products with high errors
2. **Verify ARG-240 construction** - the 141% weight error suggests incorrect input data
3. **Consider restructuring model** to remove weave efficiency and use factory formula directly
4. **Focus on weight/cross-section accuracy** before attempting breaking force improvements

---

## Files Updated

1. `data/products.json` - Updated with factory-confirmed constructions
2. `data/materials.json` - Added available tex values and declared breaking forces
3. `data/impregnation.json` - Added factory formula structure documentation
