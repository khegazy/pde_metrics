---
name: spectral_energy_flux
kind: metric
---

## Definition

Let $\mathbf{u}$ be the velocity on a periodic grid of $M$ cells with $D$ spatial axes, one
component per axis, $\hat{\mathbf{u}}(\mathbf{k})$ its discrete Fourier transform, and
$\mathbf{u}^{<K}$ the velocity keeping only the modes with $\mathrm{rint}(|\mathbf{k}|) \le K$,
$|\mathbf{k}|$ in cycles across the domain. The spectral energy flux through $K$ is the rate at
which the advective term removes kinetic energy from those modes [@alexakis2018], Section 2.3,
Equations (16) and (18):

$$
\Pi(K) = \bigl\langle \mathbf{u}^{<K} \cdot (\mathbf{u} \cdot \nabla) \mathbf{u} \bigr\rangle
= \frac{1}{M^2} \sum_{\mathrm{rint}(|\mathbf{k}|) \le K}
\mathrm{Re}\bigl[ \hat{\mathbf{u}}^{*}(\mathbf{k}) \cdot \hat{\mathbf{N}}(\mathbf{k}) \bigr],
\qquad N_i = \sum_j u_j \, \partial_j u_i \tag{1}
$$

where the angle brackets are the domain average and the second form is Parseval's relation for
the unnormalised transform. Positive $\Pi$ is energy leaving the modes inside $K$ for smaller
scales and negative $\Pi$ energy arriving from them; in two dimensions energy moves toward large
scales, so $\Pi < 0$ is the expected sign over the inverse-cascade range ([@alexakis2018],
Equations (21)–(22) and Section 3.2.1, after [@kraichnan1967]). Nothing in this metric depends
on that sign. Equation (1) is the curve, the metric's companion, sampled at the octaves
$K = 1, 2, 4, \dots$ up to half the smallest side of the grid: eight coordinates, 1 to 128, on
a $256^2$ grid. The number registered is

$$
F(\mathbf{u}_{\text{ref}}, \mathbf{u}_{\text{cand}}) =
\frac{\bigl( \sum_K \bigl[ \Pi_{\text{cand}}(K) - \Pi_{\text{ref}}(K) \bigr]^2 \bigr)^{1/2}}
{\bigl( \sum_K \Pi_{\text{ref}}(K)^2 \bigr)^{1/2}} \tag{2}
$$

the L2 distance between the two curves over the octaves, divided by the reference's norm, as
`spectrum_l2` divides for the energy spectrum. No source reduces the flux curve to one number:
the octave sampling and Equation (2) are this repository's conventions, recorded in
`issues/105`. Because $\Pi$ is cumulative, the value at each octave counts every mode inside it,
so the sampling drops no transfer; it weighs each octave of scale once.

Discretisation: the gradients are spectral derivatives on the analysis grid's spacing (the
repository's one gradient operator, also used to recompute vorticity), the product
$\mathbf{N}$ is formed in physical space without dealiasing, and the shells are those of
`spectrum_l2`'s `radial_energy_spectrum`, with each field's spatial mean removed, so the
$\mathbf{k} = 0$ mode carries no transfer. $\Pi(K)$ is the flux through
$|\mathbf{k}| = K + \tfrac12$.

**Compressibility.** Equation (1) is the flux of constant-density flow. In compressible flow the
coarse-grained budget of the large-scale kinetic energy moves energy across scales through
deformation work, which reduces to the incompressible flux when density is uniform, and
baropycnal work, which needs the pressure gradient and the small-scale mass flux; a third term,
pressure dilatation, exchanges kinetic with internal energy ([@aluie2013], Equations (13)–(15)
and Sections 4.1–4.3; [@aluie2011], Equations (3)–(5)). This metric reads the velocity alone
and omits density weighting, baropycnal work and pressure dilatation (`judgements/003`). In
three-dimensional simulations at an rms Mach number of 0.43, pressure dilatation acts mainly at
large scales and the kinetic-energy flux is close to constant beyond a transitional range
[@aluieli2012], Figures 2–3; that evidence is three-dimensional. With a divergent velocity the
flux through a wavenumber beyond every mode is $-\langle (\nabla \cdot \mathbf{u}) |\mathbf{u}|^2
\rangle / 2$ rather than zero.

### Boundary handling

Periodic wrap on every axis: Equation (1) takes Fourier transforms and spectral derivatives. The
metric therefore declares `requires_periodic`, and the harness does not run it on a dataset with
a non-periodic axis.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED performance -->

## Intuition

In a turbulent flow the motion at each size of eddy feeds energy into other sizes. This
metric measures that traffic: for each octave of size, how fast kinetic energy is carried past
it, from larger eddies to smaller ones or the other way, and it reports how far a prediction's
traffic is from the reference's. A prediction can have exactly the right amount of energy at
every size and still carry none of it between sizes, which is what a field with the right
spectrum and randomised structure does; this metric sees that and an energy-spectrum
comparison does not.

The traffic comes from the flow carrying itself along: the velocity times its own rate of
change in space. Multiplying two waves makes waves of their sum and difference sizes, so three
sizes interact at a time, and the net rate at which those interactions move energy out of
everything larger than a given size is the flux through that size. Because it is a product of
three velocities, it depends on how the waves line up, not only on how strong each one is.

A worked example: along a row of eight cells, the reference's velocity is one wave spanning the
whole row plus an equally strong wave of half that length. The two exchange energy, and the
flux through the largest size is -0.196: energy flowing into the long wave from the short one.
A candidate with the short wave at half strength moves energy at half the rate, -0.098, so the
gap is half the reference's flux and the metric returns 0.5.

```
cell                      1      2      3      4      5      6      7      8
reference velocity     0.00   1.71   1.00  -0.29   0.00   0.29  -1.00  -1.71
candidate velocity     0.00   1.21   1.00   0.21   0.00  -0.21  -1.00  -1.21

flux through the largest size:   reference -0.196   candidate -0.098   result 0.5
```

(The velocity points along the row and does not vary across it; the grid is eight cells by
four.)

It ignores where in the domain the energy moves, and the energy itself at each size: a field
can match the flux while getting the spectrum wrong.

## Reading the output

Dimensionless, from 0 upward; lower is better and 0 means the two curves coincide at every
octave. A value of 1 is what a candidate that carries no flux at all scores, so values near 1
mean the prediction's energy transfer is as far from the reference's as no transfer; values
above 1 mean it carries flux of the wrong sign or of larger size. Comparisons are valid between
predictions of the same reference on the same analysis grid. Values on different grids sample
different octaves and are not comparable, and the number is undefined (NaN) for a reference with
no flux, such as a uniform velocity.

The companion is the curve of Equation (1): a `coordinate` column holding the octave wavenumber
in cycles across the domain and a value column holding $\Pi$ there, in velocity cubed per unit
length, stored for the candidate on every result row in `companions.csv`; on the clean level it
is the reference's curve. Read a candidate's curve against the reference's to see at which
octaves the transfer departs and in which direction.

## Limitations

- **A reference whose flux vanishes only to round-off.** A steady flow whose advection is a pure
  gradient, such as the Taylor–Green vortex, has $\Pi = 0$ exactly in theory and about $10^{-19}$
  in floating point. Equation (2) then divides by round-off and returns a huge, meaningless value
  instead of NaN. Only an exactly zero reference curve is caught.
- **Not the compressible flux.** At larger Mach number the velocity-only flux misses baropycnal
  work and the exchange with internal energy, so a prediction with the right total transfer can
  score badly, and the reverse (`judgements/003`).
- **No reference-free reading.** The constancy of the flux across an inertial range, and its sign,
  are three-dimensional, forced-turbulence expectations; on two-dimensional or decaying flow
  neither gives a target, so the metric only compares against a reference.
- **Aliasing.** The product is formed without dealiasing, so on a field with energy at the grid
  scale the highest octaves include aliased transfer, which a coarse or noisy candidate inflates.
- **Few octaves at the largest scales.** The flux through octave 1 depends on the handful of modes
  in the first shell; on fields whose energy sits there, small changes in those modes move the
  number by a large fraction.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md) ·
[median_blur](../../degradations/median_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_smoothing -->

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[lowpass_butterworth](../../degradations/lowpass_butterworth/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md) ·
[highpass_butterworth](../../degradations/highpass_butterworth/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_spectral -->

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_geometric -->

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_resolution -->

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_stochastic -->

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_canaries -->

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_summary -->

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_damage_by_level -->

### The curve behind the number

<!-- GENERATED results_companion: written by `python -m fmeval.cards evidence spectral_energy_flux`, do not edit -->

Not generated yet. Run `python -m fmeval.cards evidence spectral_energy_flux`.

<!-- END GENERATED results_companion -->

## References

\bibliography
