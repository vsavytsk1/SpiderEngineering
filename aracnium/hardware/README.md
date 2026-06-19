# hardware/

The physical spider, from micro-soldering up.

```
hardware/
├── pcb/        # KiCad project(s) — mainboard: MCU + motor drivers + IMU
├── cad/        # mechanical — the 7-segment legs, the two body discs
├── bom/        # bom.csv = ONE unit's parts. build_fleet.py scales it ×N.
└── assembly/   # build instructions, photos, the order you solder things
```

**Rule:** dimensions come from `spec/aracnium.toml`. The BOM lists parts for a
single unit; quantity-per-fleet is computed, never hand-multiplied.
