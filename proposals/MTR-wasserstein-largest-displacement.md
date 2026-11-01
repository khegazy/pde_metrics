---
type: MTR
kind: variant of wasserstein
related: ["wasserstein", "max_error"]
seen_in: "agent's own"
doi: "none"
found_by: "wasserstein, 2026-10-31"
---

# MTR: Largest displacement of the optimal transport map

## What it measures

How far the furthest-travelling parcel of mass moves under the quadratic-cost optimal map
between the reference and candidate densities: a worst case where `wasserstein` reports a
root mean square, as `max_error` is to `rmse`.

## Definition

With the periodic potential u that `wasserstein` already solves for (Saumier et al. 2015,
Eq. 4, arXiv numbering), the value is max over cells of |grad u(x)|, in length units. This is
my own construction, not the infinity-Wasserstein distance of Peyre & Cuturi (2019, Eq. 2.19),
whose optimal plan is in general different from the quadratic one. It is the largest
displacement of the W_2-optimal map, so it is at least W_2 and at most the largest distance
on the torus.

## Relation to existing work

No metric in the catalog or the ideas pages reports a displacement magnitude of a transport
map. `wasserstein` reports its mass-weighted root mean square, and its companion map
f |grad u|^2 already holds the information cell by cell.

## How it could be tested

On the kinet ladder, `translate_x` and `translate_subpixel` change it in a controlled way.
On the background-ratio experiment (EXP-wasserstein-background-ratio-sweep), it should approach
the shift s as the background vanishes, since every parcel of an isolated feature then moves by s.

## Why it is helpful

A prediction that places one feature far from where it belongs, and everything else well,
has a small root mean square displacement and a large maximum. It is the transport analogue
of keeping `max_error` beside `rmse`. It costs nothing beyond the solve `wasserstein`
already does.

## References

- Saumier, L.-P., Agueh, M. & Khouider, B. (2015). IMA J. Appl. Math. 80(1), 135-157. doi:10.1093/imamat/hxt032.
- Peyre, G. & Cuturi, M. (2019). Found. Trends Mach. Learn. 11(5-6), 355-607. doi:10.1561/2200000073.
