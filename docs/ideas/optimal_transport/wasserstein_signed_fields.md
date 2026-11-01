# Wasserstein distance for velocity and vorticity

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

The quadratic Wasserstein distance between density fields is built as
[wasserstein](../../metrics/wasserstein.md); what remains is velocity and vorticity, which
take both signs.

## What it is

Instead of asking how different two fields are at each point, the Wasserstein distance asks
for the cheapest way to move mass from one field's profile onto the other's. A pure
translation of a shock by a distance $s$ then costs an amount that grows with $s$, rather
than saturating the way the $L^2$ norm does.

## Precedent

Seismic full-waveform inversion suffers the same pathology, known there as *cycle skipping*:
the $L^2$ misfit between a predicted and an observed waveform behaves badly when the
predicted arrival is shifted in time. Engquist and Froese proposed the Wasserstein metric as
the remedy. They observe that seismic signals are conventionally compared either by
travel-time difference or by $L^2$ difference, and that the Wasserstein metric "exhibits
properties from both of the traditional measures" (Engquist and Froese 2014).

The convexity property is the one this project needs. In the review literature, the $W_2$
misfit "precisely captures the data shift $s$ as the misfit is $s^2$ independent of the
profile of the signal" (Engquist and Yang 2022). That is a clean statement that $W_2$
measures *position* error while remaining blind to *profile shape*.

Converting a pressure or velocity field into a probability distribution requires the field to
be nonnegative with a fixed total mass. This is a known, named problem. Yang, Engquist, Sun
and Froese give explicit attention to "the difficulty of transforming seismic signals into
nonnegative density functions" (Yang et al. 2016). Métivier and colleagues state the
obstruction plainly: "the main difficulty for the application of optimal transport to
seismic data is related to their non positivity: the optimal transport theory is developed
for the comparison of positive quantities" (Métivier et al. 2018, EAGE). The standard fixes
are collected under [transport between signed fields](signed_field_transport.md), and which
one to use is open (issue 066, waiting on issue 047).

## Pitfalls

- On a normalised field, $W_2$ is sensitive only to where mass sits. It therefore accepts a
  field with the wrong amplitude in the right position, and must be paired with a metric that
  is sensitive to amplitude.
- In two and three dimensions, reading the distance as a "horizontal shift" is less clean
  than it is in one dimension.
- The $s^2$ growth with a shift holds for a signal on an empty background. Adding a constant
  to make a signed field positive puts it on a background, and the misfit is then no longer
  convex in shifts (Yang et al. 2018, section "Data normalization"). The density build shows
  a related effect in size: density is already a fluctuation on a large mean, and moving it by
  many cells costs a small fraction of a cell. Its card has the measurements.

## Rationale

*The team's judgement.* High priority: the structural analogy with cycle skipping is exact,
the seismic community has a decade of experience with how the method fails, and the metric
directly targets the shock-position error that $L^2$ cannot see.

## Keywords

quadratic Wasserstein misfit, cycle skipping, optimal transport waveform inversion,
Monge–Ampère, displacement convexity, $W_2$ convexity with respect to translation.

## References

- Engquist, B. & Froese, B. D. (2014). Application of the Wasserstein metric to seismic
  signals. *Communications in Mathematical Sciences* 12(5), 979–988.
  <https://doi.org/10.4310/CMS.2014.v12.n5.a7>
- Engquist, B. & Yang, Y. (2022). Optimal transport based seismic inversion: Beyond cycle
  skipping. *Communications on Pure and Applied Mathematics* 75(10), 2201–2244.
  <https://doi.org/10.1002/cpa.21990>
- Métivier, L., Allain, A., Brossier, R., Mérigot, Q., Oudet, E. & Virieux, J. (2018). A
  graph-space optimal transport approach for full waveform inversion. *80th EAGE Conference
  and Exhibition*, 1–5. <https://doi.org/10.3997/2214-4609.201801031>
- Yang, Y., Engquist, B., Sun, J. & Hamfeldt, B. F. (2018). Application of optimal transport
  and the quadratic Wasserstein metric to full-waveform inversion. *Geophysics* 83(1),
  R43–R62. <https://doi.org/10.1190/geo2016-0663.1> (preprint
  <https://arxiv.org/abs/1612.05075>, 2016, listing the fourth author as Froese)
