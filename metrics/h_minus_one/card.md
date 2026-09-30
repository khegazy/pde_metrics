---
name: h_minus_one
kind: metric
---

## Definition

Write the error field as $d = f - g$ on a periodic box of $N = \prod_j N_j$ cells with
spacing $h_j$ and side lengths $L_j = N_j h_j$. Its discrete Fourier coefficients, indexed
by the integer mode vector $\mathbf{m}$, are taken with the $1/N$ normalisation

$$
\hat{d}_{\mathbf{m}} = \frac{1}{N} \sum_{\mathbf{n}} d_{\mathbf{n}} \,
\exp\left( -2\pi i \sum_j \frac{m_j n_j}{N_j} \right) \tag{1}
$$

so that Parseval reads $\sum_{\mathbf{m}} |\hat{d}_{\mathbf{m}}|^2 = \langle d^2 \rangle$,
the mean square over cells. The physical wavevector of mode $\mathbf{m}$ is

$$
k_j(\mathbf{m}) = \frac{2\pi m_j}{L_j},
\qquad
|\mathbf{k}| = \Bigl( \sum_j k_j^2 \Bigr)^{1/2} \tag{2}
$$

and the metric is the homogeneous Sobolev seminorm of order $-1$, pooled over the $C$
channels:

$$
\mathrm{H}^{-1}(f, g) = \left(
\frac{1}{C} \sum_{c=1}^{C} \sum_{\mathbf{m} \neq 0}
\frac{\bigl| \hat{d}^{(c)}_{\mathbf{m}} \bigr|^2}{|\mathbf{k}(\mathbf{m})|^2}
\right)^{1/2} \tag{3}
$$

Two things about Equation (3) are choices rather than consequences. The $1/C$ and the
mean-square normalisation inherited from Equation (1) are picked so that replacing the
exponent $-1$ by $0$ returns exactly [rmse](../../metrics/rmse/card.md) — the two numbers are then on
one scale and their ratio is the factor this metric applies and a pointwise norm does not.
And the mode $\mathbf{m} = \mathbf{0}$ is omitted because $|\mathbf{k}|^{-2}$ is undefined
there. That omission is what makes this a *homogeneous* seminorm, and it has a consequence
large enough to belong in the definition: the sum is blind to the mean of $d$, so two
fields differing by a constant are at distance zero.

Equivalently, and this is what the implementation computes, let $w = (-\Delta)^{-1/2} d$ be
the field whose Fourier coefficients are $\hat{d}_{\mathbf{m}} / |\mathbf{k}(\mathbf{m})|$
with the zero mode set to zero. Then

$$
\mathrm{H}^{-1}(f, g) = \left(
\frac{1}{C} \Bigl\langle \sum_{c=1}^{C} \bigl( w^{(c)} \bigr)^2 \Bigr\rangle
\right)^{1/2} \tag{4}
$$

where $\langle \cdot \rangle$ averages over cells. Equations (3) and (4) agree by Parseval.
Equation (4) is the reason this norm has a per-cell map at all: the quantity inside the
average is a density over the domain even though the transform that produced it is not
local.

The reason to want a negative-order norm here is its relation to optimal transport.
Theorem 1 of [@peyre2018] bounds the quadratic Wasserstein distance between measures
$\mu, \nu$ by

$$
W_2(\mu, \nu) \;\le\; 2 \, \| \mu - \nu \|_{\dot{H}^{-1}(\mu)} \tag{5}
$$

and its Equation (5) gives the infinitesimal statement $W_2(\mu, \mu + d\mu) = \| d\mu
\|_{\dot{H}^{-1}(\mu)} + o(d\mu)$ that Equation (5) here integrates. Note the weight: the
norms in that paper are taken against $\mu$, while Equation (3) is the unweighted
$\dot{H}^{-1}(dx)$ that a single FFT gives. The two are related through upper and lower
bounds on the density, and the relation degrades as the lower bound approaches zero. The
equation and theorem numbers above are those of the preprint, arXiv:1104.4631v2; the
publisher's page could not be read, so the published version's numbering is not confirmed
here.

The wavevectors of Equation (2) come from the same
$k_j = 2\pi \, \mathrm{fftfreq}(N_j, h_j)$ convention the repository already uses for its
spectral derivatives [@pope2000]. This is deliberately not the integer-cycle magnitude in
`fmeval/wavenumbers.py`, which exists so that filter cutoffs and the energy calibration
agree about which side of a shell a mode falls on; that quantity is a mode index and this
one carries units of inverse length.

### Boundary handling

Periodic on every axis, inherited from the discrete Fourier transform in Equation (1). The
spacing used in Equation (2) is read from the analysis grid rather than assumed, because
the norm carries a length: on a grid coarsened by a factor, using the native spacing would
scale the result by exactly that factor. On a domain that is not periodic the transform
would wrap the field onto itself and the resulting number would be meaningless rather than
merely approximate.

## Performance

<!-- GENERATED performance: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| test family | field | degradations | rank correlation | weakest gap between neighbouring strengths | first strength detected |
|---|---|---|---|---|---|
| Displacement | density | 2 | 1 to 1 | 0.959 | level 4 |
| Displacement | velocity | 2 | 1 to 1 | 0.93 | level 5 |
| Displacement | vorticity | 2 | 1 to 1 | 0.984 | level 4 |
| Resolution loss | density | 2 | 1 to 1 | 0.864 | level — |
| Resolution loss | velocity | 2 | 1 to 1 | 1 | level — |
| Resolution loss | vorticity | 2 | 1 to 1 | 0.931 | level — |
| Smoothing | density | 3 | 1 to 1 | 0.963 | level 3 |
| Smoothing | velocity | 3 | 1 to 1 | 0.992 | level 4 |
| Smoothing | vorticity | 3 | 1 to 1 | 0.844 | level — |
| Spectral filtering | density | 4 | 1 to 1 | 0.546 | level 1 |
| Spectral filtering | velocity | 4 | 1 to 1 | 0.809 | level 1 |
| Spectral filtering | vorticity | 4 | 1 to 1 | 0.529 | level 1 |
| Noise | density | 1 | 1 to 1 | 1 | level — |
| Noise | velocity | 1 | 1 to 1 | 1 | level — |
| Noise | vorticity | 1 | 1 to 1 | 1 | level — |
| trap test: fake prediction, right spectrum | density | 1 | — | — | damage 1.21 |
| trap test: fake prediction, right spectrum | velocity | 1 | — | — | damage 0.793 |
| trap test: fake prediction, right spectrum | vorticity | 1 | — | — | damage 0.818 |

One row per family of degradation and physical field. **Rank correlation** asks whether the metric put the strengths of one degradation in the right order: it is the Spearman correlation between the metric and the applied strength, computed inside a single frame, and the column gives the range over the degradations in that family. A value of 1 means every strength was ordered correctly in every frame. **Weakest gap between neighbouring strengths** asks whether the metric can tell one strength from the next: it is the smallest Mann-Whitney overlap between any two neighbouring strengths, where 1 means the two never overlap and 0.5 means the metric cannot separate them at all. **First strength detected** is the mildest strength at which the metric has moved a tenth of the way from the undegraded reference toward a field with no relation to the truth; a dash means the metric never reached that tenth. **Damage** is that same 0-to-1 scale read as a number: 0 is the undegraded reference and 1 is an unrelated field.

This table reports what was measured and grades none of the measurements. What the numbers mean for this metric is written in the subsections below, beside the test that produced each number.

**Profile.**

| field | selectivity | charges most for | charges least for | response provably below 0.05 at 90% on | elasticity to a sub-pixel shift, against severity (distance) | compute cost (x cheapest in this run) |
|---|---|---|---|---|---|---|
| density | 0.379 | `translate_subpixel` | `additive_noise` | `additive_noise` `coarsen` `coarsen_bandlimited` | 1 | 30.7 |
| velocity | 0.382 | `translate_subpixel` | `additive_noise` | `additive_noise` `coarsen` `coarsen_bandlimited` `median_blur` `translate_subpixel` | 1 | 52.4 |
| vorticity | 0.418 | `median_blur` | `additive_noise` | `additive_noise` `box_blur` | 0.999 | 30.1 |

One row per physical field. **Selectivity** is how concentrated the metric's response is on a few degradations, measured per unit of field change: 0 means it charges every degradation the same, as mean squared error does by construction, and values toward 1 that one degradation carries most of it. **Charges most and least for** name the two ends of that profile. **Response provably below** lists degradations on which the upper confidence bound of the largest damage lies below the margin -- an equivalence test, so an entry says the response is provably small, not merely not significant; a dash means no degradation met the bound. **Elasticity** is the slope of log damage against log shift over the smallest shifts: 1 means damage grows in proportion to the shift, 2 with its square. **Compute cost** is wall-clock per evaluation over the cheapest metric and field in the same run.

<!-- END GENERATED performance -->

## Intuition

This metric measures how wrong a prediction is, but it charges different prices for
different kinds of wrongness: an error spread over a large region costs a lot, and an error
of the same size broken into fine-grained wiggles costs little. That makes it reveal a
different failure than a cell-by-cell norm does. A cell-by-cell norm is at its harshest
exactly where sharp features are slightly misplaced, because it compares each cell against
the cell at the same index and a shifted edge disagrees with itself twice over. This metric
softens that, so a prediction whose structures are right but sit a little off their true
positions is penalised roughly in proportion to how far they moved rather than to how sharp
they are.

The mechanism is a change of weights in frequency. Any field can be written as a sum of
waves of different wavelengths. This metric takes the difference between the two fields,
decomposes it into those waves, and divides each one's amplitude by its frequency before
measuring the total size. Long waves are left almost intact; short waves are suppressed in
proportion to how short they are. Since a small displacement of a sharp feature produces an
error made mostly of short waves, dividing by frequency is precisely what stops that error
from dominating. There is a second reason to want this particular weighting rather than any
other gentle one: for fields that are well spread out, it is provably close to the cost of
physically transporting one field onto the other, which is the quantity the displacement
problem really calls for and which is far more expensive to compute directly.

A worked example, four cells by four cells. The reference is flat at zero. The prediction
is a single wave running along the vertical axis and constant along the horizontal one,
with one full period across the box:

```
reference        candidate        h_minus_one    rmse
0 0 0 0           1  1  1  1
0 0 0 0           0  0  0  0         0.4502      0.7071
0 0 0 0          -1 -1 -1 -1
0 0 0 0           0  0  0  0
```

Now squeeze the same wave to half the wavelength, so it alternates every cell instead of
every two. The prediction is wrong by more in the cell-by-cell sense, and yet this metric
returns a smaller number:

```
reference        candidate        h_minus_one    rmse
0 0 0 0           1  1  1  1
0 0 0 0          -1 -1 -1 -1        0.3183      1.0000
0 0 0 0           1  1  1  1
0 0 0 0          -1 -1 -1 -1
```

Measured per unit of cell-by-cell error, the second case scores exactly half the first,
because its wave has exactly twice the frequency. That ratio is the whole behaviour of the
metric in one number.

What it ignores: the average level of the error. If a prediction is uniformly too high
everywhere by any amount, that offset lives entirely in the one component this metric
discards, and it scores zero for it.

## Reading the output

Zero and unbounded above, in the field's units multiplied by a length, so a value has no
meaning until the units and the domain size are known. Lower is better, and identical
fields score zero — but so do fields differing by a constant, so zero means
indistinguishable to this metric rather than identical.

What counts as a good value depends on the field and on the domain, which is why the
evaluation reports it against measured anchors rather than absolutely. The comparison that
carries meaning is between two predictions of the *same* reference field on the *same*
analysis grid: there the ratio of their values is the ratio of their transport-like error.
Comparing across fields is invalid without normalising, because density and vorticity here
differ by four orders of magnitude in fluctuation size. Comparing across analysis-grid
resolutions is also invalid: the sum in Equation (3) runs to the grid's Nyquist mode, so a
finer grid admits modes a coarser one does not have, and the change in value mixes the
metric's response with the change in how many modes exist. The one comparison that is
always safe is against [rmse](../../metrics/rmse/card.md) on the same pair of fields, because
Equation (3) is normalised to make that ratio the metric's own weighting factor.

## Limitations

The blind spot is exact and easy to hit. A prediction offset by a constant — a mass or
energy bias uniform over the domain — is at distance zero from the reference no matter how
large the offset is. A model that has drifted in its mean while keeping its structure
perfect will look flawless here and badly wrong under any pointwise norm. This is not a
degenerate corner: a uniform bias is a common failure of a learned surrogate, and it is why
this metric must be read beside a pointwise control rather than instead of one.

The transport reading, which is the reason to prefer this over an arbitrary smooth norm,
carries a condition that this project's own data can violate. The equivalence between the
norm and the Wasserstein distance is controlled by upper and lower bounds on the density,
and it degrades as the lower bound approaches zero. A field with near-vacuum regions — a
strong rarefaction, or any quantity that is genuinely zero over part of the domain — sits
where the constants blow up, and the number remains a perfectly well-defined norm while the
sentence "this approximates the transport cost" stops being true. Nothing in the output
signals the transition.

Finally, it is a weak norm by construction, and weakness cuts both ways. Fine-scale error
is suppressed in proportion to its wavenumber, so a prediction that has destroyed the
smallest scales entirely while keeping the large ones will be scored gently. Read together
with a metric that resolves scales, not alone.

## Results

<!-- GENERATED run: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

Measured on `kinet_re5e4`, frames 2000 to 10000 (161 frames of developed flow), on the 256 analysis grid, seed 20260807, at commit `ce78cb2d30d8` (working tree dirty). Run `comparison_1790639359`.

Every number in this section comes from that one run. Regenerate with `python -m fmeval.cards evidence <name> --results results/comparison_1790639359`.

<!-- END GENERATED run -->

### Smoothing

[gaussian_blur](../../degradations/gaussian_blur/card.md) ·
[box_blur](../../degradations/box_blur/card.md)

<!-- GENERATED results_smoothing: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `box_blur` | density | 4 | 1 | 1 | 0.963 |
| `box_blur` | velocity | 4 | 1 | 1 | 1 |
| `box_blur` | vorticity | 4 | 1 | 1 | 0.844 |
| `gaussian_blur` | density | 4 | 1 | 1 | 0.974 |
| `gaussian_blur` | velocity | 4 | 1 | 1 | 1 |
| `gaussian_blur` | vorticity | 4 | 1 | 1 | 1 |
| `median_blur` | density | 3 | 1 | 1 | 0.971 |
| `median_blur` | velocity | 3 | 1 | 1 | 0.992 |
| `median_blur` | vorticity | 3 | 1 | 1 | 0.93 |

<!-- END GENERATED results_smoothing -->

Every smoothing axis is ordered correctly in every frame, on all three fields. The
separability column is where the three kernels differ: the metric never confuses two
neighbouring Gaussian-blur strengths on velocity or vorticity, and its weakest separation
anywhere in this family is on `box_blur` applied to vorticity. Blur is the degradation this
metric is least gentle on, which follows from what it does — smoothing removes small-scale
content outright rather than moving it, and dividing by the wavenumber does not excuse an
error that is simply missing.

### Spectral filtering

[lowpass_ideal](../../degradations/lowpass_ideal/card.md) ·
[highpass_ideal](../../degradations/highpass_ideal/card.md)

<!-- GENERATED results_spectral: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `highpass_butterworth` | density | 4 | 1 | 1 | 0.575 |
| `highpass_butterworth` | velocity | 3 | 1 | 1 | 0.809 |
| `highpass_butterworth` | vorticity | 4 | 1 | 1 | 0.545 |
| `highpass_ideal` | density | 3 | 1 | 1 | 0.546 |
| `highpass_ideal` | velocity | 2 | 1 | 1 | 0.814 |
| `highpass_ideal` | vorticity | 4 | 1 | 1 | 0.529 |
| `lowpass_butterworth` | density | 4 | 1 | 1 | 0.848 |
| `lowpass_butterworth` | velocity | 3 | 1 | 1 | 1 |
| `lowpass_butterworth` | vorticity | 4 | 1 | 1 | 0.982 |
| `lowpass_ideal` | density | 3 | 1 | 1 | 0.968 |
| `lowpass_ideal` | velocity | 2 | 1 | 1 | 1 |
| `lowpass_ideal` | vorticity | 4 | 1 | 1 | 0.994 |

<!-- END GENERATED results_spectral -->

The ordering is perfect on all four filters, but the separability is the weakest recorded
anywhere for this metric, and it splits cleanly by which side of the spectrum the filter
cuts. The two low-pass filters separate their neighbouring strengths well. The two high-pass
filters do not: on density and vorticity their weakest gaps sit close to the 0.5 floor at
which two strengths are indistinguishable.

That is mostly a fact about the axis rather than about the metric, and `AGENTS.md` records
it independently: on this data the high-pass axis is squeezed between a cutoff that does
nothing and one that destroys almost everything, so the intermediate strengths are close
together for any metric. There is a second contribution that is specific to this metric,
though, and it works in the same direction: a high-pass filter removes the low modes, which
are exactly the ones this metric weights most heavily, so the damage saturates as soon as
the cutoff clears the first few shells.

### Displacement

[translate_x](../../degradations/translate/card.md) ·
[translate_subpixel](../../degradations/translate_subpixel/card.md)

<!-- GENERATED results_geometric: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `translate_subpixel` | density | 6 | 1 | 1 | 0.961 |
| `translate_subpixel` | velocity | 6 | 1 | 1 | 0.934 |
| `translate_subpixel` | vorticity | 6 | 1 | 1 | 0.984 |
| `translate_x` | density | 5 | 1 | 1 | 0.959 |
| `translate_x` | velocity | 5 | 1 | 1 | 0.93 |
| `translate_x` | vorticity | 5 | 1 | 1 | 0.984 |

<!-- END GENERATED results_geometric -->

Both displacement axes are ordered perfectly on all three fields, with high separability
throughout — the strongest showing of any family here apart from coarsening and noise.

The measurement that matters for this metric is not in the table above, because the table
reports ordering rather than magnitude, and what distinguishes a displacement-tolerant
metric is how *little* it charges rather than whether it ranks. Read against the pointwise
metrics on the same run, the tolerance is real but strongly field-dependent: it is large on
vorticity and almost absent on density and velocity. The mechanism is visible in the
calibration this run recorded — vorticity varies on a scale several times shorter than the
other two fields, so the error a small shift produces sits at high wavenumber where dividing
by the wavenumber bites, while on the smooth fields the same shift produces error at low
wavenumber where it does not. The numbers behind that statement are in the generated table
under *Damage beside the other metrics* below.

### Resolution loss

[coarsen](../../degradations/coarsen/card.md) ·
[coarsen_bandlimited](../../degradations/coarsen_bandlimited/card.md)

<!-- GENERATED results_resolution: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `coarsen` | density | 4 | 1 | 1 | 1 |
| `coarsen` | velocity | 4 | 1 | 1 | 1 |
| `coarsen` | vorticity | 4 | 1 | 1 | 1 |
| `coarsen_bandlimited` | density | 4 | 1 | 1 | 0.864 |
| `coarsen_bandlimited` | velocity | 4 | 1 | 1 | 1 |
| `coarsen_bandlimited` | vorticity | 4 | 1 | 1 | 0.931 |

<!-- END GENERATED results_resolution -->

Ordered perfectly on all three fields under both coarsenings, with a rank correlation of 1 in
every frame. Under `coarsen` there is no overlap at all between neighbouring strengths; under
`coarsen_bandlimited` the weakest separation is 0.864, on density. The two operators differ
less here than under the pointwise metrics: at a factor of 16, `coarsen` costs 0.042, 0.012 and
0.051 of the unrelated-field value on density, velocity and vorticity, and the band-limited
version 0.008, 0.003 and 0.040. That is consistent with Equation (3): the staircase's extra
error sits at its block edges, at high wavenumber, which is exactly what dividing by the
wavenumber discounts.

### Noise

[additive_noise](../../degradations/additive_noise/card.md)

<!-- GENERATED results_stochastic: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| degradation | field | strengths | rank correlation | fraction of frames in the right order | weakest gap between neighbouring strengths |
|---|---|---|---|---|---|
| `additive_noise` | density | 4 | 1 | 1 | 1 |
| `additive_noise` | velocity | 4 | 1 | 1 | 1 |
| `additive_noise` | vorticity | 4 | 1 | 1 | 1 |

<!-- END GENERATED results_stochastic -->

Ordered perfectly with no overlap between neighbouring strengths on any field. Additive
noise is broadband, so it puts energy into every mode including the low ones this metric
weights most, and the response is correspondingly clean. This is worth stating explicitly
because it rules out a reading the displacement results might otherwise invite: a metric
that divides by the wavenumber is not thereby insensitive to small-scale corruption in
general — it is insensitive to small-scale error that arises from *moving* structure that is
otherwise correct.

### Trap tests

[gaussian_impostor](../../degradations/gaussian_impostor/card.md) ·
[uncorrelated](../../degradations/random_large_translation/card.md)

<!-- GENERATED results_canaries: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| field | damage assigned to the fake prediction | closest real degradation | value on an unrelated field |
|---|---|---|---|
| density | 1.21 | `lowpass_ideal=1.4029` | 0.19 |
| velocity | 0.793 | `highpass_ideal=4.02293` | 2.71 |
| vorticity | 0.818 | `highpass_ideal=41.6842` | 0.0982 |

The fake prediction here has exactly the reference field's amplitude spectrum and completely scrambled structure. Damage of 1 is what a field with no relation to the truth scores, so the damage column says how close to useless this metric considers that fake prediction: a low number means the metric was fooled. The third column translates the same number into an ordinary degradation whose damage the fake prediction matches, which is easier to picture.

<!-- END GENERATED results_canaries -->

This metric is not fooled by the impostor on any field. On density it scores the fake
prediction as *worse* than an unrelated field, which is possible because the damage scale is
anchored at the unrelated field rather than bounded by it.

That is the expected outcome rather than a success to claim credit for, and `AGENTS.md`
states the general form of it: the Gaussian impostor is built to have the reference's
amplitude spectrum and scrambled phase, so it catches metrics that are functions of the
amplitude spectrum alone. This metric is a norm of the pointwise difference, reweighted in
wavenumber but still phase-sensitive, so scrambling phase is close to the most damaging
thing that can be done to it. No conclusion about this metric's structural fidelity should
be drawn from the trap test passing.

### Compared with the other metrics

<!-- GENERATED results_summary: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

| compared with | rank correlation over every degradation |
|---|---|
| `nrmse` | 0.946 |
| `rmse` | 0.937 |
| `mse` | 0.937 |
| `mae` | 0.913 |
| `h1_seminorm` | 0.515 |
| `spectrum_l2` | 0.147 |
| `increment_w1` | -0.0552 |
| `increment_flatness` | -0.0907 |
| `enstrophy` | -0.183 |
| `palinstrophy` | -0.222 |
| `kinetic_energy` | -0.292 |

Computed on the median value at each combination of degradation and strength, over every degradation and physical field in the run, with the undegraded reference excluded. Two metrics correlating near 1 put the degradations in the same order, but the two may still weight those degradations very differently. A correlation near 1 therefore means the two metrics are redundant for ranking models, not that the two are interchangeable as training losses.

<!-- END GENERATED results_summary -->

The rank correlation is 1 on every one of the 36 ordered axes in this run (12 degradations on
each of three fields; the two trap tests have no ordering) — every degradation,
every field, every frame. As a ranker of damage this metric has no failure in the recorded
evidence.

It correlates 0.91 to 0.95 with the four pointwise baselines across the whole ladder. That is
high, and it is the number most likely to be misread. A correlation in that range means the
two order the degradations almost identically and are therefore close to redundant for model
selection; it says nothing about whether they agree on magnitude, and on the displacement
axes they do not. `AGENTS.md` records the same trap in its sharpest form for MAE against MSE,
which correlate at 0.995 and differ by 55x in displacement damage. The case for adding this
metric to a panel rests on the magnitudes, not on these correlations, and anyone reading the
correlations alone would conclude the opposite.

### Damage beside the other metrics

<!-- GENERATED results_damage_by_level: written by `python -m fmeval.cards evidence h_minus_one --results results/comparison_1790639359`, do not edit -->

**Displacement, density, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `h_minus_one` | 0.00312 | 0.00624 | 0.0125 | 0.0249 | 0.0499 | 0.0996 |
| `mae` | 0.00328 | 0.00655 | 0.0131 | 0.0262 | 0.0521 | 0.103 |
| `mse` | 1.49e-05 | 5.97e-05 | 0.000238 | 0.000952 | 0.00379 | 0.015 |
| `rmse` | 0.00386 | 0.00772 | 0.0154 | 0.0309 | 0.0616 | 0.123 |
| `nrmse` | 0.00362 | 0.00723 | 0.0145 | 0.0289 | 0.0576 | 0.115 |

**Displacement, density, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h_minus_one` | 0.0249 | 0.0499 | 0.0996 | 0.198 | 0.391 |
| `mae` | 0.0262 | 0.0521 | 0.103 | 0.205 | 0.401 |
| `mse` | 0.000952 | 0.00379 | 0.015 | 0.0584 | 0.211 |
| `rmse` | 0.0309 | 0.0616 | 0.123 | 0.242 | 0.46 |
| `nrmse` | 0.0289 | 0.0576 | 0.115 | 0.226 | 0.43 |

**Displacement, velocity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `h_minus_one` | 0.00134 | 0.00267 | 0.00535 | 0.0107 | 0.0214 | 0.0428 |
| `mae` | 0.00163 | 0.00325 | 0.0065 | 0.013 | 0.0257 | 0.05 |
| `mse` | 4.76e-06 | 1.91e-05 | 7.61e-05 | 0.000303 | 0.00118 | 0.00445 |
| `rmse` | 0.00218 | 0.00437 | 0.00873 | 0.0174 | 0.0344 | 0.0667 |
| `nrmse` | 0.00219 | 0.00437 | 0.00873 | 0.0174 | 0.0343 | 0.0667 |

**Displacement, velocity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h_minus_one` | 0.0107 | 0.0214 | 0.0428 | 0.0853 | 0.169 |
| `mae` | 0.013 | 0.0257 | 0.05 | 0.0951 | 0.18 |
| `mse` | 0.000303 | 0.00118 | 0.00445 | 0.016 | 0.0541 |
| `rmse` | 0.0174 | 0.0344 | 0.0667 | 0.127 | 0.233 |
| `nrmse` | 0.0174 | 0.0343 | 0.0667 | 0.127 | 0.232 |

**Displacement, vorticity, `translate_subpixel`** (strength: distance).

| metric | 0.125 | 0.25 | 0.5 | 1 | 2 | 4 |
|---|---|---|---|---|---|---|
| `h_minus_one` | 0.00217 | 0.00434 | 0.00868 | 0.0173 | 0.0342 | 0.0664 |
| `mae` | 0.0225 | 0.045 | 0.0892 | 0.172 | 0.306 | 0.453 |
| `mse` | 0.000476 | 0.0019 | 0.00747 | 0.028 | 0.0889 | 0.187 |
| `rmse` | 0.0218 | 0.0436 | 0.0865 | 0.167 | 0.298 | 0.432 |
| `nrmse` | 0.0219 | 0.0437 | 0.0868 | 0.169 | 0.304 | 0.447 |

**Displacement, vorticity, `translate_x`** (strength: distance).

| metric | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| `h_minus_one` | 0.0173 | 0.0342 | 0.0664 | 0.126 | 0.231 |
| `mae` | 0.172 | 0.306 | 0.453 | 0.581 | 0.69 |
| `mse` | 0.028 | 0.0889 | 0.187 | 0.288 | 0.468 |
| `rmse` | 0.167 | 0.298 | 0.432 | 0.537 | 0.684 |
| `nrmse` | 0.169 | 0.304 | 0.447 | 0.555 | 0.702 |

Median damage over frames at every strength, this metric in the first row and the pointwise controls beneath it, all on the same 0-to-1 scale where 0 is the undegraded reference and 1 an unrelated field; a dash means no damage scale on that field. The rank correlations under *Compared with the other metrics* say whether two metrics put the strengths in the same order; this table says how much each one charges for the same strength, which decides whether two metrics are interchangeable as training losses.

<!-- END GENERATED results_damage_by_level -->

## References

\bibliography
