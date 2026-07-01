# Good For One Free Shot Coins

Thirty-millimeter basswood coins with five lines of vector-engraved text:

```text
GOOD FOR
ONE FREE
SHOT
ANYWHERE
ANY TIME
```

Build the current artifact set:

```bash
python3 scripts/laser_build.py --design shot_coins
```

The 300 x 300 mm stock exceeds the Falcon A1 Pro's provisional 268 mm short-axis work area. The build therefore constrains geometry to the 300 x 268 mm usable intersection. With 2 mm edge margins and 1 mm coin spacing, the deterministic hex layout contains 81 coins.

The included 3 mm basswood recipes are unverified manufacturer seed values. Run calibration coupons before fabrication.

The design uses the dependency-free native vector backend. OpenSCAD is not required for this design.

Revision `rev_0003` replaces the original fragmented pixel-run lettering with upright continuous-line vector glyphs. The complete text block is scaled against the circular boundary, and generation fails if any engraving endpoint crosses the configured 1 mm inset.

Revision `rev_0004` is the default normal-font trial. OpenSCAD shapes the pinned Liberation Sans Bold font, and the pipeline converts its filled contours into 0.18 mm horizontal engraving hatches before applying the same containment checks.

The hatch spacing and engraving recipe are calibration-only.

Revision `rev_0005` is the current default. It uses pinned Liberation Sans Regular to improve visual character separation while retaining the font's default spacing. The Bold revision remains reproducible at `rev_0004`.
