# firmware/

What runs on the microcontroller inside each real spider.

**Rule:** firmware reads geometry, gait, and limits from `spec/aracnium.toml`
(generate a header/constants file from it at build time) — it never hard-codes
leg lengths or servo counts. That's how one firmware image serves every unit
(PX4 does the same: one flight stack, many airframe configs).

The version of record is the **git tag**, not a string in the source (also the
PX4 convention). Tag releases like `mk1-0.1.0`.

Suggested starting layout (add when you start coding):
```
firmware/
├── src/            # gait controller, IK, servo driver, comms
├── include/        # generated-from-spec constants land here
└── README.md
```
