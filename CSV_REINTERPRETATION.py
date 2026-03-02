# CSV Data Re-interpretation
# Based on user clarification:
# - osnova = warp, potka = weft
# - Single tex value = 1 strand of that tex
# - Multiple tex values (e.g., "4800 tex + 2400 tex") = multiple strands of different tex
# - Notation like "2,625 x (2+1)" means: 2.625 ribs/10cm, with (2+1) = 2 strands of first tex + 1 strand of second tex

"""
ORIGINAL CSV DATA (from transcript):

Row | Product                          | Warp (osnova)      | Weft (potka)           | Weft density        | Weight
----|----------------------------------|--------------------|-----------------------|---------------------|--------
4   | ANTISEISMIC Grid 185             | 1200 tex           | 1200 tex              | 6                   | 185
5   | ANTISEISMIC Grid 280             | 1200 tex           | 2400 tex              | 4                   | 280
6   | ANTISEISMIC Grid 350             | 1200 tex + 640 tex | 2400 tex + 1200 tex   | 3,75 + 3,75         | 350
7   | FLEX GRID ARG-240-5x5            | 640 tex            | 640 tex               | 15                  | 240
8   | FLEX GRID ARG-290-8x8            | 1200 tex           | 1200 tex              | 10                  | 290
9   | ANTISEISMIC Grid 250             | 1200 tex           | 1200 tex              | 3,973 x 2           | 250
10  | ANTISEISMIC Grid 130             | 320 tex            | 640 tex               | 8                   | 130
11  | FLEX GRID ARG-460-AAS3           | 1200 tex           | 2 x 2400 tex          | 3.33                | 460
12  | ANTISEISMIC Grid 320             | 640 tex            | 2400 tex              | 5                   | 320
13  | FLEX GRID ARG-130-AAS2           | 320 tex            | 640 tex               | 8                   | 130
14  | FLEX GRID ARG-330-AAS1           | 1200 tex           | 3 x 2400 tex          | 1.8                 | 330
15  | FLEX GRID ARG-550-AAS3           | 1200 tex           | 2 x 2400 tex          | 4.5                 | 550
16  | ANTISEISMIC Grid 320 (Bordo)     | 640 tex            | 2400 tex              | 5                   | 320
17  | FLEX GRID ARG-300-18x18          | 640 tex            | 2400 tex              | 4.5                 | 305
18  | FLEX GRID ARG-160-40x40          | 320 tex            | 2400 tex              | 2.5                 | 160
19  | FLEX GRID ARG-310-35x35          | 640 tex            | 2 x 2400 tex          | 2.5                 | 310
20  | FLEX GRID ARG-320-8x8-FR         | 1200 tex           | 1200 tex              | 10                  | 320
21  | FLEX GRID ARG-450-12x12-FR       | 2400 tex           | 2400 tex              | 7                   | 450
22  | FLEX GRID ARG-110-14x12          | 320 tex            | 640 tex               | 7                   | 110
23  | GRID Q121-RRE-38                 | 4800 tex + 2400 tex| 4800 tex + 2400 tex   | 2,625 x (2+1)       | 945
24  | ANTISEISMIC Grid 49              | 1200 tex           | 2400 tex              | 2,6 x 2             | 385


NEW INTERPRETATION:
==================

1. ANTISEISMIC Grid 185:
   Warp: 1×1200 tex (single strand)
   Weft: 1×1200 tex (single strand), 6/10cm
   Total tex per rib: warp=1200, weft=1200

2. ANTISEISMIC Grid 280:
   Warp: 1×1200 tex
   Weft: 1×2400 tex, 4/10cm
   Total tex per rib: warp=1200, weft=2400

3. ANTISEISMIC Grid 350 (MIXED):
   Warp: 1×1200 tex + 1×640 tex = 1840 tex total per rib
   Weft: 1×2400 tex + 1×1200 tex = 3600 tex total per rib
   Density: 3.75 + 3.75 = alternating pattern
   This is COMPLEX - alternating different tex in the same direction

4. FLEX GRID ARG-240-5x5:
   Warp: 1×640 tex
   Weft: 1×640 tex, 15/10cm
   Total tex per rib: warp=640, weft=640

5. FLEX GRID ARG-290-8x8:
   Warp: 1×1200 tex
   Weft: 1×1200 tex, 10/10cm
   Total tex per rib: warp=1200, weft=1200

6. ANTISEISMIC Grid 250:
   Warp: 1×1200 tex
   Weft: 1200 tex, "3,973 x 2" = 3.973/10cm × 2 strands per rib
   Total tex per rib: warp=1200, weft=2×1200=2400

7. ANTISEISMIC Grid 130:
   Warp: 1×320 tex
   Weft: 1×640 tex, 8/10cm
   Total tex per rib: warp=320, weft=640

8. FLEX GRID ARG-460-AAS3:
   Warp: 1×1200 tex
   Weft: "2 x 2400 tex" = 2 strands × 2400 tex = 4800 tex total, 3.33/10cm
   Total tex per rib: warp=1200, weft=4800

9. ANTISEISMIC Grid 320:
   Warp: 1×640 tex
   Weft: 1×2400 tex, 5/10cm
   Total tex per rib: warp=640, weft=2400

10. FLEX GRID ARG-330-AAS1:
    Warp: 1×1200 tex
    Weft: "3 x 2400 tex" = 3 strands × 2400 tex = 7200 tex total, 1.8/10cm
    Total tex per rib: warp=1200, weft=7200

11. FLEX GRID ARG-550-AAS3:
    Warp: 1×1200 tex
    Weft: "2 x 2400 tex" = 2×2400 = 4800 tex total, 4.5/10cm
    Total tex per rib: warp=1200, weft=4800

12. FLEX GRID ARG-300-18x18:
    Warp: 1×640 tex
    Weft: 1×2400 tex, 4.5/10cm
    Total tex per rib: warp=640, weft=2400

13. FLEX GRID ARG-160-40x40:
    Warp: 1×320 tex
    Weft: 1×2400 tex, 2.5/10cm
    Total tex per rib: warp=320, weft=2400

14. FLEX GRID ARG-310-35x35:
    Warp: 1×640 tex
    Weft: "2 x 2400 tex" = 2×2400 = 4800 tex total, 2.5/10cm
    Total tex per rib: warp=640, weft=4800

15. FLEX GRID ARG-320-8x8-FR:
    Warp: 1×1200 tex
    Weft: 1×1200 tex, 10/10cm
    Total tex per rib: warp=1200, weft=1200

16. FLEX GRID ARG-450-12x12-FR:
    Warp: 1×2400 tex
    Weft: 1×2400 tex, 7/10cm
    Total tex per rib: warp=2400, weft=2400

17. FLEX GRID ARG-110-14x12:
    Warp: 1×320 tex
    Weft: 1×640 tex, 7/10cm
    Total tex per rib: warp=320, weft=640

18. GRID Q121-RRE-38 (COMPLEX MIXED):
    Warp: "4800 tex + 2400 tex" with "2,625 x (2+1)" 
          = 2.625/10cm, with 2×4800 + 1×2400 = 9600 + 2400 = 12000 tex per rib
    Weft: Same as warp
    Total tex per rib: warp=12000, weft=12000

19. ANTISEISMIC Grid 49:
    Warp: 1×1200 tex
    Weft: 2400 tex, "2,6 x 2" = 2.6/10cm × 2 strands = 2×2400 = 4800 tex per rib
    Total tex per rib: warp=1200, weft=4800

"""

# Summary of key corrections from previous interpretation:
corrections = """
KEY CORRECTIONS:
================

1. Grid 49: 
   - OLD: warp=1200×4 strands, weft=1200×4 strands
   - NEW: warp=1200×1 strand, weft=2400×2 strands (4800 total)
   - The "2,6 x 2" means 2.6/10cm density with 2 strands of 2400 tex

2. Grid 250:
   - OLD: warp=1200×1, weft=1200×2 at 3.973/10cm
   - NEW: Same interpretation, this was correct!

3. ARG-460:
   - OLD: warp=1200×1, weft=2400×2 at 3.33/10cm
   - NEW: Same - "2 x 2400 tex" means 2 strands of 2400 tex

4. ARG-550:
   - OLD: warp=1200×1, weft=2400×2 at 4.5/10cm  
   - NEW: Same interpretation, this was correct!

5. Q121-RRE-38:
   - OLD: Complex mixed with primary/secondary tex
   - NEW: 2×4800 + 1×2400 = 12000 tex total per rib in both directions
   
6. Grid 350 (Mixed):
   - Warp: alternating 1200 and 640 tex strands
   - Weft: alternating 2400 and 1200 tex strands
   - "3,75 + 3,75" means alternating density pattern

CRITICAL INSIGHT:
=================
The CSV shows tex per STRAND, not total per rib.
- "1200 tex" = 1 strand of 1200 tex
- "2 x 2400 tex" = 2 strands of 2400 tex each = 4800 tex total per rib
- "4800 tex + 2400 tex" with "(2+1)" = 2×4800 + 1×2400 = 12000 tex total per rib
"""

print(corrections)
