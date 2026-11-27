---
name: scale_dilatational
kind: degradation
---

## Definition

On a periodic domain every velocity splits uniquely into its spatial mean, a solenoidal part
$\mathbf{u}_s$ (divergence-free, carrying all the vorticity) and a dilatational part
$\mathbf{u}_d$ (curl-free, carrying all the divergence) [@bhatia2013]. Each Fourier mode's
dilatational part is its projection onto its wavevector $\mathbf{k}$:

$$
\hat{\mathbf{u}}_d(\mathbf{k}) = \frac{\mathbf{k}\,\bigl(\mathbf{k}\cdot\hat{\mathbf{u}}(\mathbf{k})\bigr)}{|\mathbf{k}|^2},
\quad \mathbf{k} \ne 0, \qquad \hat{\mathbf{u}}_d(0) = 0, \tag{1}
$$

with $\mathbf{k}$ the physical wavevector of the grid's spacing. The operator returns

$$
\mathbf{u}' = \mathbf{u} + \delta\,\mathbf{u}_d, \qquad
\delta = -s \ \text{(default)}, \quad \delta = +s \ \text{(option amplify)}, \tag{2}
$$

for the severity $s$, so the dilatational part is multiplied by $\lambda = 1 + \delta$ and the
solenoidal part and the mean are unchanged. It acts on velocity only; every other field,
vorticity included, is passed through unchanged, which is exact because Equation (1) has no
curl. The two parts are orthogonal mode by mode, so the kinetic energy becomes
$E_s + \lambda^2 E_d$ and the mean squared error against the original, averaged over the
components, is $\delta^2 E_d$, with $E = \tfrac12\langle|\mathbf{u}|^2\rangle$
(`dataset_specs/10_acoustic_and_helmholtz_fields.md`, Sect. 3.6; asserted through the
pipeline in `tests/test_analytic_datasets.py`). The projection is
`fmeval.derived.helmholtz_split`.

### Boundary handling

The projection is a discrete Fourier transform, so it wraps on a periodic axis. On a
non-periodic axis the driver first extends the field by that axis's rule and crops the result,
as for every operator, so the split is that of the extended periodic field, not a Helmholtz
decomposition with wall conditions.

## Intuition

This stands in for a surrogate that has learnt the vortices but not the sound: the
compressive motions of a flow, acoustic waves and the expansion and compression around a
vortex at finite Mach number, come out too weak (damped, smoothed away) or too strong, while
every vortex is in the right place with the right strength. A metric built on the vorticity
cannot see this failure at all, and that blindness is what the degradation tests.

On a nearly incompressible flow a picture of the velocity barely changes, because there is
almost nothing compressive to remove. On a flow with a strong compressive part the change is
plain: removing it all leaves only the swirling motion.

A four by four velocity, a vortex array plus a compressive pattern of half its size, with all
of the compressive part removed (severity 1), produced by running the operator:

```
x-velocity before        x-velocity after
 0.25 -0.25 -0.25  0.25   0.5 -0.5 -0.5  0.5
 0.25 -0.25 -0.25  0.25   0.5 -0.5 -0.5  0.5
-0.25  0.25  0.25 -0.25  -0.5  0.5  0.5 -0.5
-0.25  0.25  0.25 -0.25  -0.5  0.5  0.5 -0.5

y-velocity before        y-velocity after
-0.75 -0.75  0.75  0.75  -0.5 -0.5  0.5  0.5
 0.75  0.75 -0.75 -0.75   0.5  0.5 -0.5 -0.5
 0.75  0.75 -0.75 -0.75   0.5  0.5 -0.5 -0.5
-0.75 -0.75  0.75  0.75  -0.5 -0.5  0.5  0.5
```

What is left is the vortex array alone. The curl of the velocity is the same before and
after, plus or minus 1 in every cell, and the kinetic energy falls from 0.3125 to 0.25, the
vortex's share.

What this degradation leaves untouched is the vorticity, the spatial mean of the velocity,
and every field other than velocity.

## Severity scale

The severity is the fraction of the dilatational part removed, or with the option `amplify`
added: dimensionless and absolute, the same on every field, and never calibrated against a
spectrum. Zero returns the input unchanged; 1 removes the part entirely, or doubles it with
`amplify`. A severity above 1 is refused when attenuating, because it would reverse the
part's sign rather than remove more of it. The two directions are separate ladder entries,
`scale_dilatational_down` and `scale_dilatational_up` in `configs/degradation/default.yaml`,
each at 0.25, 0.5, 0.75 and 1, because a signed severity would be sorted with the mildest
case in the middle of one axis. Both are disabled by default: the operator only means
something on a dataset with a compressive part (Limitations).

## Limitations

The damage is the dilatational part's own size, so it depends entirely on the dataset. On an
incompressible field, such as the default `taylor_green_2d`, `random_field` or
`advecting_blobs`, whose velocities are solenoidal by construction, the part is round-off and
every level is flagged as doing nothing. On `kinet_re5e4` it holds 1e-6 to 1e-5 of the
velocity's fluctuation energy (measured in `dataset_specs/10_acoustic_and_helmholtz_fields.md`,
Sect. 1), so even removing all of it changes the velocity by a few thousandths of its RMS. The
reference it is meant for is `taylor_green_2d` with an acoustic part, where the fraction is set
in closed form.

Only the velocity changes. In a compressible flow the dilatational velocity and the density
or pressure perturbation travel together as sound [@chukovasznay1958], so the damaged
velocity no longer matches the unchanged density and pressure; a metric on those fields reads
no change. That makes it a clean blind-axis test, and a less faithful imitation of a model
whose sound is wrong in every field.

## What the degradation looks like

### The picture

<!-- GENERATED exemplars: written by `python -m fmeval.cards exemplars scale_dilatational`, do not edit -->

Not generated yet. Run `python -m fmeval.cards exemplars scale_dilatational`.

<!-- END GENERATED exemplars -->

The panel, once drawn, is from the canonical frame of `kinet_re5e4`, whose velocity is almost
incompressible, so the field row will look unchanged at every strength. Look at the
difference row: it is the dilatational part itself, scaled by the strength, and shows where
the flow compresses and expands.

## References

\bibliography
