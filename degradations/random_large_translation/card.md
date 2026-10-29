---
name: random_large_translation
kind: degradation
---

## Definition

The field is rolled by a random offset drawn independently for each spatial direction,
uniformly from the middle half of the domain:

$$
n_i \sim \mathcal{U}\{N/4,\; 3N/4\}, \qquad g(x) = f(x - n) \tag{1}
$$

The offsets are drawn from a generator seeded by the run seed together with the variant
label, the frame index and the field name, so a given draw is reproducible and independent
of the order in which anything is evaluated.

Restricting the offset to the middle half keeps every draw far from alignment: a small
offset would leave the field partly correlated with its reference, and an offset near the
full domain would wrap back to near-alignment.

This operator is declared ``ordinal=False``, meaning its levels carry no order from mild
to severe. Its levels are independent random draws rather than increasing strengths, so it
is excluded from every rank correlation.

### Boundary handling

On a periodic axis, wrap, exactly as for the whole-cell translation: the operation is a
bijection on the grid and no value is created or destroyed. On an axis with walls the
harness rolls the mirror-extended field and crops it back, so the result is a window onto a
mirrored copy, and values are created and destroyed.

## Intuition

This one is not imitating a model failure. It is a probe that answers a question the
other degradations cannot: what number does a metric give for a field that is the right
kind of field in the wrong place? That is the double penalty this suite exists to measure,
taken to its limit.

Using a large translation rather than, say, noise or a distant frame is deliberate. On a
periodic domain the result has *exactly* the reference's distribution of values, its
variance, its spectrum and its texture -- it is the same flow, simply not lined up. A
metric that scores it well is telling you it cannot see position at all. Its damage is read
on the suite's damage scale, where zero is the reference and one is the field's own mean
(`mean_field`).

On the four-by-four test field, one draw gives

```
before                 after (one draw)
0 0 0 0                0 0 1 1
0 1 1 0                0 0 1 1
0 1 1 0                0 0 0 0
0 0 0 0                0 0 0 0
```

The feature is intact, the same size and the same brightness, and it is somewhere else.
The multiset of values is identical to the original's, so the mean, the variance and the
histogram all match exactly.

What this degradation leaves untouched is every statistic that does not depend on
position. That is the whole design.

## Severity scale

There is no severity here. The configured numbers 0 through 5 are draw indices, and
the configuration entry named ``uncorrelated`` runs six of them.

Six draws rather than one because a single random offset is a single sample: on a flow
with any large-scale structure, one particular offset can happen to land in partial
alignment and give an anomalously low value. The analysis reports the median over every
draw of every frame.

Because the levels are not ordered, this degradation is excluded from rank correlation and
from monotonicity checks.

## Limitations

**The moved copy is not an unrelated field.** A translation by d multiplies the mode at
wavenumber k by the phase k·d. A field whose energy sits in a few large-scale modes does not
average that phase away, so the copy stays partly correlated, or anti-correlated, with the
reference. Measured on `kinet_re5e4`, the median `energy_changed` of these rows -- the mean
squared difference over the reference variance, which is 2 for an unrelated field of the same
variance -- is 1.64 on density, 3.05 on velocity and 2.25 on vorticity, and density's six
draws differ by a median factor of 3.2 within a frame. This is why it is no longer the damage
anchor (`judgements/001`).

**On a domain with walls it is a mirrored window.** On `sod_shock_tube` the harness rolls the
mirror-extended tube and crops it, which flips the step: the copy is anti-correlated with the
reference (median correlation about −0.8) and its `energy_changed` is 3.46 on density.

**A distant frame is not a substitute.** The flow decays, so a frame far along the trajectory
has about 0.70 of the reference's variance and a different flatness, making it a different
field rather than the same field moved.

## What the degradation looks like

### The picture

<!-- GENERATED exemplars: written by `python -m fmeval.cards exemplars random_large_translation`, do not edit -->

![random_large_translation: the same snapshot, undegraded and then degraded](_generated/exemplars.png)

**random_large_translation** on vorticity, frame 5000 of `kinet_re5e4`. Three independent draws beside the original, because there is no weak-to-strong ordering to show. The pdf row is the point: every draw has exactly the reference's distribution of values, which is what makes it a fair anchor rather than merely a bad field.

3 independent random draws, seeded from the run seed so that every draw reproduces exactly.

<!-- END GENERATED exemplars -->

There is no weak-to-strong progression to look for. Compare the three draws against
one another instead: they should look equally unrelated to the original and equally like
plausible fields in their own right.

The pdf row is the one that carries the argument. All four panels -- original and three
draws -- should show the same distribution of values, because a translation on a periodic
domain cannot change which values are present.

In the difference row, expect large error everywhere rather than error concentrated at
edges, in contrast with the small-shift panels.

## References

\bibliography
