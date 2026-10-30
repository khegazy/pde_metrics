# Why single metrics are not enough

A machine-learning surrogate of a partial differential equation is usually trained and
judged by one number, most often a mean-squared error and sometimes a comparison of energy
spectra. This page explains why one number is not enough: each such number is satisfied by
fields that are physically wrong, and the ways it fails can be derived rather than only
observed. The ideas in this section exist to see what those numbers miss. Where no citation
is given, the reasoning is the synthesis of the field guide described in
[where this came from](README.md#where-this-came-from), not an established consensus.

## Degeneracy: many wrong fields share one score

A metric is *degenerate* when fields that differ in a physically important way receive the
same value. Any single scalar is degenerate in some direction, because it compresses a whole
field into one number. Three degeneracies recur throughout this section.

- **Right spectrum, wrong phases.** The energy spectrum keeps the amplitude of every Fourier
  mode and discards its phase, which is the information that places features in space and
  couples one scale to another. Two fields with identical spectra can look entirely different.
- **Right mean, wrong fluctuations.** A prediction can match the average of a field while its
  fluctuations about that average have the wrong size or the wrong distribution.
- **Low error by blurring.** A prediction that erases the small, low-energy scales of a field
  can achieve a lower mean-squared error than one that reproduces them in slightly the wrong
  place (the derivation is below).

What follows from this is a *panel*: several metrics, each sensitive to a different kind of
error, reported side by side. [Designing an evaluation](evaluation_design.md) describes how
such panels are put together.

## Four mechanisms by which pointwise losses fail

Throughout, $u(\mathbf{x})$ is the reference field, $\hat u(\mathbf{x})$ is the prediction,
$\Omega$ is the spatial domain, and $\lvert\Omega\rvert$ is its volume.

### Energy weighting and spectral bias

On a periodic domain, Parseval's theorem turns the mean-squared error into a sum over
Fourier modes:

$$
\frac{1}{\lvert\Omega\rvert}\int_\Omega \bigl(u(\mathbf{x})-\hat u(\mathbf{x})\bigr)^2\,
d\mathbf{x}
= \sum_{\mathbf{k}} \bigl\lvert \tilde u_{\mathbf{k}} - \tilde{\hat u}_{\mathbf{k}}
\bigr\rvert^2 , \tag{1}
$$

where $\mathbf{k}$ is a wavevector and $\tilde u_{\mathbf{k}}$ is the Fourier coefficient
of $u$ at that wavevector. Each mode contributes its own squared error, and setting a mode
to zero costs exactly that mode's energy, $\lvert \tilde u_{\mathbf{k}} \rvert^2$. A prediction
that sets every mode above some cutoff $k_c$ to zero therefore pays exactly the reference
energy above $k_c$. In an
inertial range, where the energy spectrum falls as $E(k)\propto k^{-5/3}$ (Kolmogorov's
scaling), that energy is $\int_{k_c}^{\infty} E(k)\,dk \propto k_c^{-2/3}$, which is a
small fraction of the total once $k_c$ is well inside the inertial range. The penalty for
erasing the small scales is small, even though those scales carry most of the velocity
gradients: the spectrum of the gradients, $k^2E(k)$, grows with $k$. This is why the built
[enstrophy](../metrics/enstrophy.md), [palinstrophy](../metrics/palinstrophy.md) and
[$H^1$ seminorm](../metrics/h1_seminorm.md) respond to blurring that the
[mean-squared error](../metrics/mse.md) barely registers.

Neural networks compound the effect. Trained by gradient descent, they fit the
low-frequency content of a target before its high-frequency content, a tendency called the
*frequency principle* or *spectral bias* (Xu et al. 2020). The loss and the optimiser
therefore push in the same direction: towards a prediction that is right at large scales and
smooth at small ones.

### Regression to the conditional mean

Let $X$ be the input the model sees and $u$ the target it is asked to predict. Among all
functions $f$ of the input, the expected squared error splits into two parts:

$$
\mathbb{E}\,\lVert f(X) - u\rVert^2
= \mathbb{E}\,\bigl\lVert f(X) - \mathbb{E}[u \mid X]\bigr\rVert^2
+ \mathbb{E}\,\bigl\lVert u - \mathbb{E}[u \mid X]\bigr\rVert^2 . \tag{2}
$$

The cross term vanishes because $u - \mathbb{E}[u\mid X]$ has zero mean given $X$. The
second term does not depend on $f$, so the minimiser is the conditional mean,
$f^\star(X) = \mathbb{E}[u \mid X]$. When the future is uncertain given the input, as it is
for a chaotic or bifurcating flow, the conditional mean is an average over many admissible
futures. An average of shocks at slightly different positions is a smeared ramp, and an
average of turbulent fields with different phases has weaker fluctuations than any one of
them. Minimising the mean-squared error drives a model towards this blurred average, which
is itself not a solution of the equations.

### The predictability horizon

In a chaotic system, two trajectories that start a small distance $\delta_0$ apart separate
on average as

$$
\delta(t) \approx \delta_0\, e^{\lambda_1 t}, \tag{3}
$$

where $\lambda_1$ is the largest Lyapunov exponent and $\tau_\lambda = 1/\lambda_1$ is the
Lyapunov time (Boffetta et al. 2002). Once $\delta(t)$ reaches the size of the attractor,
prediction and reference are effectively independent samples of the same flow. If both have
mean $\mu$ and variance $\sigma^2$ and are uncorrelated, then

$$
\mathbb{E}\bigl[(u-\hat u)^2\bigr] = \mathbb{E}\bigl[(u-\mu)^2\bigr]
+ \mathbb{E}\bigl[(\hat u-\mu)^2\bigr] = 2\sigma^2 , \tag{4}
$$

so the root-mean-squared error saturates at $\sqrt{2}\,\sigma$. Past that point a perfect
surrogate and a poor one with the right variance receive the same pointwise score, and the
score says nothing about either.

Two consequences follow. Rollout horizons are better reported in Lyapunov times, and the
time at which a normalised error first crosses a threshold, the
[valid prediction time](dynamics/valid_prediction_time.md), becomes a metric in its own
right. Reservoir computers have been used for model-free prediction of spatiotemporally
chaotic systems such as the Kuramoto–Sivashinsky equation (Pathak et al. 2018). After the
horizon, the meaningful
comparisons are between long-time statistics: Lyapunov exponents, attractor dimension, and
the [invariant measure](dynamics/invariant_measure.md) through long-time distributions and
spectra (Boffetta et al. 2002). Kochkov et al. (2021) compare energy spectra in exactly
this regime, after every solution has decorrelated from the reference.

### Blindness to structure and phase

Two fields can share all their one-point statistics and their entire power spectrum while
differing in their coherent structures and in how their scales are coupled. The power
spectrum discards every Fourier phase. The coupling of three modes whose wavevectors sum to
zero, a *triad*, is what builds shocks, fronts and vortices, and it is recorded in the
[bispectrum](basis_decompositions/bispectrum.md), in
[phase coherence](basis_decompositions/spectral_coherence.md), in morphology such as the
[Minkowski functionals](topology/minkowski_functionals.md), and in topology such as
[persistence diagrams](topology/persistence_diagrams.md). None of it is visible to the
spectrum.

## A Gaussian field can match any spectrum

A statistically homogeneous Gaussian random field is completely specified by its mean and its
two-point covariance, and the covariance is the Fourier transform of the energy spectrum.
So for any prescribed spectrum there is a Gaussian field that realises it exactly. Such a
field agrees with the turbulent field in autocorrelation and spectrum, yet, as the next
section shows, every odd-order statistic of its increments and derivatives vanishes where the
turbulent field's does not. A matched spectrum, and even a matched one-point distribution,
does not imply a matched flow.

The repository's [gaussian_impostor](../degradations/gaussian_impostor.md) degradation is
a field of this kind. It keeps every Fourier amplitude of the reference and draws the phases
at random, so it shares the reference's spectrum exactly and none of its structure, and it
exists to catch metrics that respond only to the spectrum.

### Every odd statistic vanishes

A zero-mean Gaussian distribution is unchanged by the reflection $u \to -u$, so every odd
moment is zero. Isserlis's theorem, known in physics as Wick's theorem, goes further and
writes every even moment of a jointly Gaussian vector in terms of its covariances
(Isserlis 1918). For a velocity increment $\delta_\ell u = u(\mathbf{x}+\boldsymbol\ell) -
u(\mathbf{x})$ at separation $\ell = \lvert\boldsymbol\ell\rvert$,

$$
\bigl\langle (\delta_\ell u)^{2p+1} \bigr\rangle = 0
\qquad \text{for every integer } p \ge 0, \tag{5}
$$

where $\langle\cdot\rangle$ is an average over the field (Chevillard et al. 2012 use this
property in a turbulence model). Turbulence is not like this, and each of the following
quantities separates the two.

- **The third-order structure function vanishes.** For a Gaussian field
  $S_3(\ell) = \langle (\delta_\ell u_\parallel)^3\rangle = 0$, where $u_\parallel$ is the
  velocity component along $\boldsymbol\ell$. In turbulence the
  [four-fifths law](turbulence_statistics/four_fifths_law.md), an exact result for the
  inertial range, requires $S_3(\ell) = -\tfrac{4}{5}\,\varepsilon\,\ell$, where
  $\varepsilon$ is the mean rate of energy dissipation per unit mass (Frisch 1995, Eq. 6.5).
  No Gaussian field satisfies it.
- **The mean energy flux between scales vanishes.** The flux of energy through wavenumber
  $k$ is a sum over triads of a triple velocity correlation, so it is zero on average for a
  Gaussian field. A Gaussian field with a perfect $k^{-5/3}$ spectrum carries no cascade; the
  [spectral energy flux](turbulence_statistics/spectral_energy_flux.md) sees this
  immediately.
- **The velocity-derivative skewness vanishes.** The skewness
  $\langle(\partial_x u)^3\rangle / \langle(\partial_x u)^2\rangle^{3/2}$ is zero for a
  Gaussian field and in turbulence between about $-0.5$ and $-0.7$, growing slowly in
  magnitude with Reynolds number (Ishihara et al. 2007). See
  [velocity-derivative skewness](turbulence_statistics/derivative_skewness.md).
- **The mean vortex stretching vanishes.** The mean enstrophy production
  $\langle \omega_i S_{ij}\omega_j\rangle$, where $\boldsymbol\omega$ is the vorticity and
  $S_{ij}$ the strain-rate tensor, is a third-order moment of the velocity gradients and is
  zero on average for a Gaussian field. In three-dimensional turbulence it is positive, with
  the dominant contribution to producing large enstrophy coming from the most extensive
  direction of the strain (Buaria et al. 2020). See [vortex stretching](turbulence_statistics/vortex_stretching.md).
- **The bispectrum vanishes.** A Gaussian field has independent, uniformly distributed
  Fourier phases, so every statistic of phase coupling between triads is zero (Burkhart et
  al. 2009). See [bispectrum and bicoherence](basis_decompositions/bispectrum.md).
- **The flatness is 3.** By Isserlis's theorem the fourth moment of a Gaussian variable is
  three times its squared variance, so the flatness of increments and gradients is exactly 3.
  In turbulence the flatness of velocity gradients is well above 3 and grows with Reynolds
  number, the signature of intermittent, heavy-tailed small scales (Sreenivasan & Antonia
  1997). The built [increment_flatness](../metrics/increment_flatness.md) measures this at one
  cell, and [structure functions](turbulence_statistics/structure_functions.md) extend it
  across separations.

### A loss built on amplitudes cannot see these

A spectral loss is a function of Fourier amplitudes only, so it gives no information about
any quantity in the list above. The mean-squared error does depend on phases, but by
Equation (1) a pure phase error $\Delta\theta$ at a wavevector $\mathbf{k}$ costs
$2\lvert\tilde u_{\mathbf{k}}\rvert^2(1-\cos\Delta\theta)$, at most four times that mode's
energy, which is small at the weak small scales. On the field guide's reading (a conjecture,
not a demonstrated result), gradient descent on a loss of this kind can drift towards
quasi-Gaussian, cascade-free, blurred fields while the reported loss keeps falling, because
nothing in the loss distinguishes them from the truth.

Classical turbulence theory met the same problem. The quasi-normal closure assumed that the
fourth-order moments of the velocity take their Gaussian values, in order to close the
equations for the third-order moments. Ogura (1963) found that it produces negative energy
spectra, which no real field can have, and the approximation was replaced by eddy-damped and
realisable closures (Zhou 2021; Eyink & Frisch 2011). Imposing Gaussian statistics, even
only on the fourth moments, damages the physics of the cascade.

## Why a validation loss can fall while rollouts get worse

A surrogate of a time-dependent equation is usually validated *a priori*: it is given the
true state and asked for the next one. It is deployed *a posteriori*: it is given its own
previous output, again and again, in an autoregressive *rollout*. The two settings see
different input distributions. In sequence modelling this mismatch is called *exposure
bias*: training on true prefixes while predicting from the model's own outputs lets errors
compound, and scheduled sampling was introduced to close the gap (Bengio et al. 2015).
Continued training can therefore sharpen one-step accuracy, lowering the validation error,
while the autoregressive map becomes less stable, because the loss never sees the inputs the
model will actually receive.

The neural-PDE literature documents the same mechanism and its remedies.

- PDE-Refiner identifies the neglect of low-amplitude spatial frequencies, typically the high
  wavenumbers, as the main cause of rollout divergence, and reports as its headline result the
  time until the correlation between rollout and reference falls below a threshold such as
  0.8 (Lippe et al. 2023). That quantity is measured on rollouts, not single steps.
- Solver-in-the-loop training places the numerical solver inside the training loop and
  obtains stable rollouts over hundreds of steps where purely one-step training does not
  (Um et al. 2020).
- The pushforward trick trains on the model's own perturbed outputs, directly targeting the
  distribution shift that one-step losses ignore (Brandstetter et al. 2022).
- Unrolling more solver steps during differentiable training improves long-time statistics,
  with a trade-off between accuracy and stability in the length of the unrolled horizon (List
  et al. 2022).
- Benchmarks of autoregressive and diffusion-based turbulence emulators measure temporal
  stability, spectra and distributional fidelity explicitly, rather than one-step error
  (Kohl et al. 2023).

Two mechanisms from above make the drift worse: regression to the conditional mean drains
fluctuation energy step by step, and a spectral loss cannot see the resulting loss of phase
coherence. The [selection of checkpoints by rollout](infrastructure/checkpoint_selection.md)
describes a procedure that uses rollout metrics instead of the one-step validation loss.

The evaluation culture has its own version of this problem. In a survey of articles on
machine learning for fluid-related PDEs, 60 of the 76 articles (79%) that claimed to
outperform a standard numerical method compared against a weak baseline (McGreivy & Hakim
2024). Choosing honest [baseline predictors](infrastructure/baseline_predictors.md) is part of
the same discipline as choosing honest metrics.

## What goes wrong, and which ideas would see it

Each row is a pattern seen in rollouts of learned surrogates. The middle column lists the
ideas and built metrics that respond to it; the last column lists the change to training that
the cited literature uses against it. The table is the field guide's synthesis.

| What is seen in the rollout | Ideas and built metrics that would see it | Training-side remedy |
|---|---|---|
| Small scales collapse, so the field blurs | [Error by wavenumber band](basis_decompositions/spectral_band_error.md); [spectral coherence](basis_decompositions/spectral_coherence.md); built [spectrum_l2](../metrics/spectrum_l2.md) and [h1_seminorm](../metrics/h1_seminorm.md) | Spectral or Sobolev losses; refinement-style objectives (Lippe et al. 2023) |
| Phases decohere while the spectrum stays intact | [Bispectrum and bicoherence](basis_decompositions/bispectrum.md); [spectral energy flux](turbulence_statistics/spectral_energy_flux.md); [spectral coherence](basis_decompositions/spectral_coherence.md) | Unrolled or solver-in-the-loop training (Um et al. 2020; List et al. 2022) |
| The field becomes Gaussian: fluctuations decay and extremes disappear | [Velocity-derivative skewness](turbulence_statistics/derivative_skewness.md); [four-fifths law](turbulence_statistics/four_fifths_law.md); [spectral energy flux](turbulence_statistics/spectral_energy_flux.md) near zero; built [increment_flatness](../metrics/increment_flatness.md) | Distributional or adversarial losses (Gretton et al. 2012; Granero Belinchon & Cabeza Gallucci 2024) |
| Energy or mass drifts over the rollout | [Admissibility checks](physics_invariants/admissibility_checks.md); [weak residual](physics_invariants/weak_residual.md) | Architectures that conserve by construction; projection steps |
| The rollout blows up or produces NaN | [Admissibility checks](physics_invariants/admissibility_checks.md); [valid prediction time](dynamics/valid_prediction_time.md) | Pushforward training; noise injection (Brandstetter et al. 2022) |

## Which ideas need a reference

Some quantities compare the prediction with a reference field; others are computed from the
prediction alone. The distinction matters past the predictability horizon, where a
phase-aligned reference no longer exists, and in deployment, where there may be no reference
at all.

| Family | Reference needed | What to keep in mind |
|---|---|---|
| Pointwise errors: built [rmse](../metrics/rmse.md), [nrmse](../metrics/nrmse.md) and [max_error](../metrics/max_error.md); [valid prediction time](dynamics/valid_prediction_time.md) | Yes, and phase-aligned with the prediction | Carries no information about model quality once the prediction has decorrelated, Equation (4) |
| Spectra and band errors: built [spectrum_l2](../metrics/spectrum_l2.md); [error by wavenumber band](basis_decompositions/spectral_band_error.md) | A reference that declares which scales it resolves | The bands worth comparing are a property of the reference's resolution |
| Admissibility: [admissibility checks](physics_invariants/admissibility_checks.md); [weak residual](physics_invariants/weak_residual.md); [signed entropy production](physics_invariants/entropy_production.md) | No | Computed from the prediction alone; a constant, laminar or over-smoothed field satisfies them |
| Exact laws: [four-fifths law](turbulence_statistics/four_fifths_law.md); [spectral energy flux](turbulence_statistics/spectral_energy_flux.md); log law in [wall-bounded flows](regime_specific/wall_bounded_flows.md) | No | Remain meaningful after decorrelation; they fix an amplitude and a slope that a degenerate field cannot reproduce |
| Distributions: [Wasserstein distance](optimal_transport/wasserstein.md); [energy distance](distributional/energy_distance.md); built [increment_w1](../metrics/increment_w1.md) and [crps](../metrics/crps.md); [energy and variogram scores](distributional/multivariate_proper_scores.md) | A reference distribution, not a matched field | Integral probability metrics stay well behaved when the two distributions do not overlap |
| Structural checks: [Galilean and rotational equivariance](physics_invariants/equivariance_tests.md); realizability in [admissibility checks](physics_invariants/admissibility_checks.md) | No | Test a symmetry or a bound, independently of the size of the pointwise error |

The admissibility and exact-law rows see different failures. A constant, laminar or
over-smoothed prediction satisfies every admissibility condition, but it cannot reproduce the
inertial-range amplitude and slope that an exact law fixes. Before a reference-free quantity
is trusted where no reference exists, its rank correlation with the true error can be checked
on cases where a reference does exist.

## References

- Bengio, S., Vinyals, O., Jaitly, N. & Shazeer, N. (2015). Scheduled sampling for sequence
  prediction with recurrent neural networks. *NeurIPS* 28. <https://arxiv.org/abs/1506.03099>
- Boffetta, G., Cencini, M., Falcioni, M. & Vulpiani, A. (2002). Predictability: a way to
  characterize complexity. *Physics Reports* 356, 367–474.
  <https://doi.org/10.1016/S0370-1573(01)00025-4>
- Brandstetter, J., Worrall, D. & Welling, M. (2022). Message passing neural PDE solvers.
  *ICLR*. <https://arxiv.org/abs/2202.03376>
- Buaria, D., Bodenschatz, E. & Pumir, A. (2020). Vortex stretching and enstrophy production
  in high Reynolds number turbulence. *Physical Review Fluids* 5, 104602.
  <https://arxiv.org/abs/2006.01312>
- Burkhart, B., Falceta-Gonçalves, D., Kowal, G. & Lazarian, A. (2009). Density studies of
  MHD interstellar turbulence: statistical moments, correlations and bispectrum.
  *Astrophysical Journal* 693, 250–266. <https://doi.org/10.1088/0004-637X/693/1/250>
- Chevillard, L., Castaing, B., Arneodo, A., Lévêque, E., Pinton, J.-F. & Roux, S. G. (2012).
  A phenomenological theory of Eulerian and Lagrangian velocity fluctuations in turbulent flows. *Comptes Rendus
  Physique* 13(9–10), 899–928. <https://arxiv.org/abs/1112.1036>
- Eyink, G. L. & Frisch, U. (2011). Robert H. Kraichnan. In *A Voyage Through Turbulence*,
  Cambridge University Press. <https://arxiv.org/abs/1011.2383>
- Frisch, U. (1995). *Turbulence: The Legacy of A. N. Kolmogorov*. Cambridge University
  Press. <https://doi.org/10.1017/CBO9781139170666>
- Granero Belinchon, C. & Cabeza Gallucci, M. (2024). A multiscale and multicriteria
  Generative Adversarial Network to synthesize 1-dimensional turbulent fields. *Machine
  Learning: Science and Technology* 5(2), 025032. <https://doi.org/10.1088/2632-2153/ad43b3>
- Gretton, A. et al. (2012). A kernel two-sample test. *Journal of Machine Learning
  Research* 13, 723–773. <https://jmlr.org/papers/v13/gretton12a.html>
- Ishihara, T., Kaneda, Y., Yokokawa, M., Itakura, K. & Uno, A. (2007). Small-scale
  statistics in high-resolution direct numerical simulation of turbulence: Reynolds number
  dependence of one-point velocity gradient statistics. *Journal of Fluid Mechanics* 592,
  335–366. <https://doi.org/10.1017/S0022112007008531>
- Isserlis, L. (1918). On a formula for the product-moment coefficient of any order of a
  normal frequency distribution in any number of variables. *Biometrika* 12, 134–139.
  <https://doi.org/10.1093/biomet/12.1-2.134>
- Kochkov, D., Smith, J. A., Alieva, A., Wang, Q., Brenner, M. P. & Hoyer, S. (2021).
  Machine learning–accelerated computational fluid dynamics. *PNAS* 118, e2101784118.
  <https://doi.org/10.1073/pnas.2101784118>
- Kohl, G., Chen, L.-W. & Thuerey, N. (2023). Benchmarking autoregressive conditional
  diffusion models for turbulent flow simulation. <https://arxiv.org/abs/2309.01745>
- Lippe, P., Veeling, B. S., Perdikaris, P., Turner, R. E. & Brandstetter, J. (2023).
  PDE-Refiner: Achieving accurate long rollouts with neural PDE solvers. *NeurIPS* 36.
  <https://arxiv.org/abs/2308.05732>
- List, B., Chen, L.-W. & Thuerey, N. (2022). Learned turbulence modelling with
  differentiable fluid solvers: physics-based loss functions and optimisation horizons.
  *Journal of Fluid Mechanics* 949, A25. <https://doi.org/10.1017/jfm.2022.738>
- McGreivy, N. & Hakim, A. (2024). Weak baselines and reporting biases lead to overoptimism
  in machine learning for fluid-related partial differential equations. *Nature Machine
  Intelligence* 6(10), 1256–1269. <https://doi.org/10.1038/s42256-024-00897-5>
- Ogura, Y. (1963). A consequence of the zero-fourth-cumulant approximation in the decay of
  isotropic turbulence. *Journal of Fluid Mechanics* 16, 33–40.
  <https://doi.org/10.1017/s0022112063000562>
- Pathak, J., Hunt, B., Girvan, M., Lu, Z. & Ott, E. (2018). Model-free prediction of large
  spatiotemporally chaotic systems from data: a reservoir computing approach. *Physical
  Review Letters* 120, 024102. <https://doi.org/10.1103/PhysRevLett.120.024102>
- Sreenivasan, K. R. & Antonia, R. A. (1997). The phenomenology of small-scale turbulence.
  *Annual Review of Fluid Mechanics* 29, 435–472.
  <https://doi.org/10.1146/annurev.fluid.29.1.435>
- Um, K., Brand, R., Fei, Y., Holl, P. & Thuerey, N. (2020). Solver-in-the-loop: learning
  from differentiable physics to interact with iterative PDE-solvers. *NeurIPS*.
  <https://arxiv.org/abs/2007.00016>
- Xu, Z.-Q. J., Zhang, Y., Luo, T., Xiao, Y. & Ma, Z. (2020). Frequency principle: Fourier
  analysis sheds light on deep neural networks. *Communications in Computational Physics*
  28, 1746–1767. <https://doi.org/10.4208/cicp.oa-2020-0085>
- Zhou, Y. (2021). Turbulence theories and statistical closure approaches. *Physics
  Reports* 935, 1–117. <https://doi.org/10.1016/j.physrep.2021.07.001>
