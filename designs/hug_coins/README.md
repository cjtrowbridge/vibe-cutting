# Good For One Free Hug Coins

Thirty-millimeter basswood coins with five lines of vector-engraved text:

```text
GOOD FOR
ONE FREE
HUG
ANYWHERE
ANY TIME
```

Build the current artifact set:

```bash
python3 scripts/laser_build.py --design hug_coins
```

The 300 x 300 mm stock exceeds the Falcon A1 Pro's provisional 268 mm short-axis work area. The build constrains geometry to the 300 x 268 mm usable intersection and fits 81 coins with 2 mm edge margins and 1 mm coin spacing.

The text uses upright continuous-line vector glyphs and a 1 mm engraving inset. Generation fails if any engraving endpoint crosses that inset.

The included 3 mm basswood recipes are unverified manufacturer seed values. Run calibration coupons before fabrication.
