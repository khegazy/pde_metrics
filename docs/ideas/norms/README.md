# Norms and function-space metrics

A norm measures the size of the difference between two fields with a single number. Norms of
positive Sobolev order, such as $H^1$, add the size of the gradient to that number, and they
fail at discontinuities: a field with a jump is not an element of $H^1$ at all, so at a shock
the gradient term measures the grid resolution rather than the physics. Norms of negative
order go the other way. They are weaker than $L^2$, they stay finite for rough and
discontinuous fields, and they are quantitatively close to the Wasserstein transport
distance. The organising principle for this theme, and for much of the rest of the plan, is
to split a field into a smooth part and a sharp remainder and to compare each part with a
metric suited to it.

Built already, and so not listed here: the $H^1$ seminorm
([h1_seminorm](../../metrics/h1_seminorm.md)) and the homogeneous $\dot H^{-1}$ norm
([h_minus_one](../../metrics/h_minus_one.md)).

## Ideas in this theme

- [Negative Sobolev norms of general order](negative_sobolev_hs.md): norms of any negative
  order, and dual norms, which stay finite at discontinuities and approximate a transport
  distance.
- [Splitting a field into smooth and sharp parts](mollification_split.md): smooth the field,
  keep the remainder as its sharp part, and compare the two parts with different metrics.
- [Maximum pointwise error](maximum_error.md): the largest error in any single cell, reported
  only as a worst-case stability diagnostic beside the averaged pointwise norms.
