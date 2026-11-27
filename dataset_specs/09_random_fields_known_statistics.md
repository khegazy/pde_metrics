# Dataset 09: periodic random fields with known statistics

**Catalog clusters:** the reference fields for G2 (tail axes with known answers), G3 (graded
phase randomisation), G5 (anisotropic blur) and G10 (spatially correlated noise), and for the
degradations X1, X2, X4 and X6 that implement them; the stationary null of spec 04, Option A3,
which is specified in full here (BUILD_ORDER step 10). **Metrics served:** `spectrum_l2`,
`increment_w1`, `increment_w1_by_separation`, `increment_flatness`, `energy_distance`,
`tail_index`, `tail_exceedance`, and every pairwise norm on the translation and phase axes.
**Ideas, proposals and issues served:** `proposals/EXP-tail_index-pareto-spike-injection.md`,
`proposals/EXP-energy_distance-tail-only-degradation.md`,
`proposals/MTR-tail_index-moment-estimator.md` (its light-tail check), issues 036 and 037 (an
exact flatness target and an exact independent realisation), 128 (a separation measured in
known correlation lengths), 132 (the spread of the Hill estimate over many realisations), 044
(the reader's seed). **Date:** 2026-11-26. **Author:** research sub-agent, branch
`build_datasets`. Everything marked "my derivation" or "my design" is the author's, not a
source's. Every number marked "measured" was computed on 2026-11-26 with the repository's own
metric and degradation functions on prototype fields (scripts in the session scratchpad,
`spec09/`), not with the reader specified here, which does not exist yet.

## 1. Purpose

The seven spectral, increment and tail metrics can show today only that their numbers move
under damage (`FUTURE_EXPERIMENTS_CATALOG.md`, D4, "Serves"). None of them has been checked
against a value known before the run, because no dataset in the repository has a known
increment law: kinet flows decay, and `tests/analytic_fields.py` holds single features (a bump,
a stripe, a mode) whose increment distributions are degenerate. The catalog's tail and phase
clusters say the same from the degradation side. G2 needs a reference whose tail is known so
that Pareto spikes have the target 1/α; G3 needs a reference on which phase randomisation is an
exact null; G5 needs a reference of known anisotropy; G10 needs a reference whose spectrum adds
to the noise's in closed form.

A periodic random field built from a prescribed spectrum supplies all of these at once. For a
Gaussian field every second-order statistic follows from the spectrum, every increment is
Gaussian with a variance computed exactly on the grid, and so the flatness, the two
distribution distances and the Hill value have closed-form targets. Three non-Gaussian
families built from the same Gaussian draw (a pointwise transform, a multifractal field, and
Gaussian fields damaged by Pareto spikes) keep exact moments while moving the flatness and the
tail. This is a known-statistics check, not turbulence: it has no cascade, no flux and no
coherent structures (spec 04, Sect. 3.3, "Does not give").

## 2. What the dataset must provide

- **Fields:** `density` (a positive scalar), `velocity` (two components, exactly solenoidal,
  built from a stream function), `vorticity` (its closed form, which the harness recomputes and
  must match). No pressure (repository rule, `docs/recipes/add-a-dataset.md`).
- **Grid and boundaries:** 256² by default, to match the analysis grid of every kinet run and
  the `k = ceil(sqrt(n)) = 256` of `tail_index` and `tail_exceedance`; periodic on both axes,
  because five of the seven metrics declare `requires_periodic`. Any grid, square or not, must
  work, since reader tests use 16×8 (`AGENTS.md`, Sect. 5).
- **Frames:** independent draws (the default) or a stationary time series with a known
  correlation time per Fourier mode (spec 04, A3). Several dozen frames, so a per-frame
  Spearman correlation and a frame average both exist. Frames must not be scalar multiples of
  one another (`BUILD_ORDER.md`, "The task").
- **Realisations:** any number, by seed; two seeds give an exact independent realisation.
- **Known in advance, per field, channel and axis:** the expected energy spectrum in the shells
  of `spectrum_l2`; the covariance and the increment variance S₂(ℓ) at every separation ℓ; the
  increment flatness at every separation; for Gaussian increments, the Hill value at every
  order k, the 1-Wasserstein and energy distances against any other Gaussian field, and the
  frequency bias at any threshold; for the time series, the correlation of each mode at every
  lag.

## 3. Option A, the analytic ideal: a reader of periodic random fields

There is no physical system here, only constructions. Each is computed on the fly from a seed,
in the `ClosedFormTrajectory` pattern of `fmeval/data/analytic.py`, and nothing is stored.

### 3.1 The one construction every family shares

Write $M = N_x N_y$ for the number of cells, $\mathbf m$ for an integer wavevector and
$\boldsymbol\kappa_{\mathbf m} = 2\pi(m_x/L_x, m_y/L_y)$ for the physical wavevector, the
convention of `physical_wavenumber_grid` in `fmeval/external/kinet_spectral.py`, which the
harness's spectral vorticity uses. Given a non-negative per-mode variance $v_{\mathbf m}$, even
in $\mathbf m$, and a real white field $w$ of independent unit-variance cells, the field

$$
g = \mathcal F^{-1}\!\Bigl[\sqrt{v_{\mathbf m}/M}\;\mathcal F[w]_{\mathbf m}\Bigr] \tag{1}
$$

is a periodic, stationary random field. When $w$ is Gaussian, $g$ is exactly Gaussian, because
it is a linear map of a Gaussian vector; its Fourier coefficients satisfy
$\mathbb E|\hat g_{\mathbf m}|^2 = v_{\mathbf m}$, and its covariance is the discrete
Wiener–Khinchin sum

$$
C(\mathbf r) = \mathbb E[g(\mathbf x)\,g(\mathbf x+\mathbf r)]
= \frac{1}{M^2}\sum_{\mathbf m} v_{\mathbf m}\, e^{i\boldsymbol\kappa_{\mathbf m}\cdot\mathbf r} \tag{2}
$$

(my derivation: $\mathcal F[w]$ has $\mathbb E|\hat w_{\mathbf m}|^2 = M$). Equation (2) is one
inverse FFT of $v$, so the covariance at every separation is known to round-off, on the grid
itself, with no continuum approximation. Lang and Potthoff (2011, abstract read) use FFTs in
the same way to simulate Gaussian fields on rectangles; on a periodic grid no embedding is
needed. Two rules make the targets exact. (i) $v_{\mathbf m} = 0$ at $\mathbf m = 0$, so the
fluctuation has zero mean and the mean is set separately. (ii) $v_{\mathbf m} = 0$ on the
Nyquist lines $|m_j| = N_j/2$, where a spectral derivative of a real field is not defined;
then the harness's spectral curl reproduces the reader's vorticity to 6e-16 relative error
(measured).

Equation (1) multiplies the white field's **complex Gaussian** coefficients, amplitude and
phase both random. The `gaussian_impostor` operator instead keeps each amplitude and draws only
a phase (`degradations/gaussian_impostor/degradation.py`, line 62), which gives a field that is
Gaussian only asymptotically, so the draw in Eq. (1) is not the impostor's and cannot reuse it.
It does reuse the impostor's lesson: taking the transform of a real field gets every Hermitian
constraint right without special cases.

**Increments.** The increment $\delta_{\ell,j} g = g(\mathbf x + \ell\mathbf e_j) - g(\mathbf x)$
of the metric cards (`metrics/increment_flatness/card.md`, Eq. 1) is a linear functional of
$g$, so for a Gaussian field it is Gaussian with variance

$$
S_2^{(j)}(\ell) = 2\bigl[C(\mathbf 0) - C(\ell\mathbf e_j)\bigr]
= \frac{2}{M^2}\sum_{\mathbf m} v_{\mathbf m}\bigl[1-\cos(\kappa_{\mathbf m,j}\,\ell\,\Delta x_j)\bigr]. \tag{3}
$$

Measured on 20 000 draws at 64², the empirical S₂ at ℓ = 1, 4, 16, 32 cells matched Eq. (3) to
1e-4 relative (0.15323 against 0.15323 at ℓ = 1).

### 3.2 Family G: Gaussian fields with a prescribed spectrum

**Spectra.** The shell spectrum $E(k)$ of `spectrum_l2` (its Eq. 1) is set, and the per-mode
variance follows by spreading each shell over its modes, $v_{\mathbf m} \propto
E(|\mathbf m|)/(2\pi|\mathbf m|)$ (my construction; a shell of radius k holds about 2πk modes).
Three forms, all on a band $k_{\min} \le |\mathbf m| \le k_{\max} < N/2$ in cycles per box:

1. **Power law**, $E(k) \propto k^{-\beta}$, with β = 5/3 and β = 3 the two slopes of forced
   two-dimensional turbulence (Boffetta and Ecke 2012, Eqs. 12–13, as spec 04, Eq. 2 records).
2. **Broken power law**, $E \propto k^{-5/3}$ below a break $k_b$ and
   $E \propto k_b^{-5/3}(k/k_b)^{-3}$ above it, continuous at $k_b$: the two sides of a forcing
   scale, which spec 04, A3 asks for.
3. **Matérn**, with correlation function $\mathcal M_{\nu,\alpha}(r) =
   \frac{2^{1-\nu}}{\Gamma(\nu)}(r/\alpha)^\nu K_\nu(r/\alpha)$ (Porcu et al. 2023, Eq. 9) and,
   in $d$ dimensions, spectral density proportional to $(1+\alpha^2\kappa^2)^{-(\nu+d/2)}$
   (same, Eq. 23); I use $\alpha = \rho/\sqrt{2\nu}$, so ρ is a length in cells. Its shell
   spectrum, $\propto k(1+\alpha^2\kappa^2)^{-(\nu+1)}$ in 2D, is peaked, so this form is also
   the "peaked spectrum" the task asks for. Its integral scale is, by my derivation from the
   standard integral of $x^\nu K_\nu(x)$,
   $$
   L = \int_0^\infty \mathcal M(r)\,dr = \rho\,\frac{\sqrt\pi\,\Gamma(\nu+\tfrac12)}{\sqrt{2\nu}\,\Gamma(\nu)}, \tag{4}
   $$
   which is ρ at ν = 1/2 (the exponential) and $\pi\rho/(2\sqrt2) = 1.111\rho$ at ν = 1.

In every form $v$ is rescaled so that $C(\mathbf 0)$ equals the requested variance exactly.
The continuum laws are a guide, the discrete sums are the targets. For instance, for
$1 < \beta < 3$ the continuum $S_2(r) \propto r^{\beta-1}$ (my derivation: substitute $k = x/r$
in $S_2 = 4\int E(k)[1-J_0(kr)]\,dk$, whose integral converges exactly for $1<\beta<3$), so
$r^{2/3}$ for β = 5/3, while the band edges bend the discrete curve.

**Known exactly, and the metrics' targets.** With $\sigma_j(\ell) = \sqrt{S_2^{(j)}(\ell)}$:

- *Flatness* (`increment_flatness`, its Eq. 2): 3 at every separation, on every channel and
  axis, because every increment is Gaussian. Measured on 20 frames at 256² (β = 5/3):
  2.997 ± 0.017.
- *1-Wasserstein distance* between the increments of two Gaussian fields with increment
  standard deviations $\sigma_1, \sigma_2$ along one pair: on the line $W_1$ is the $L^1$
  distance of the quantile functions (Peyré and Cuturi 2019, Remark 2.30, Eq. 2.36, as
  `metrics/increment_w1/card.md` cites it), and the quantile functions are $\sigma_i\Phi^{-1}$,
  so (my derivation, with $\mathbb E|Z| = \sqrt{2/\pi}$ for a standard normal Z)
  $$
  W_1 = |\sigma_1 - \sigma_2|\,\sqrt{2/\pi}. \tag{5}
  $$
  Measured, a field against an independent one with 1.5 times its amplitude: 0.004389 ± 0.000065
  against 0.004400 from Eq. (5).
- *Energy distance* (`metrics/energy_distance/card.md`, Eq. 2, from Székely and Rizzo 2013,
  Definition 1, Eq. 2.4): with $X - Y \sim \mathcal N(0, \sigma_1^2 + \sigma_2^2)$ and
  $X - X' \sim \mathcal N(0, 2\sigma_1^2)$ (my derivation),
  $$
  D^2 = \sqrt{2/\pi}\,\Bigl[\,2\sqrt{\sigma_1^2+\sigma_2^2} - \sqrt2\,(\sigma_1+\sigma_2)\Bigr]. \tag{6}
  $$
  Measured on the same pair: 0.02476 ± 0.00037 against 0.02482.
- *Frequency bias* (`metrics/tail_exceedance/card.md`, Eq. 4): for two fields with the same
  law the expected bias is $n/(n+1)$ if increments were independent (that card, Eq. 5); measured
  between independent draws, 0.997 ± 0.080. Between Gaussian increment laws of standard
  deviations $\sigma_f$ (reference) and $\sigma_g$, with the threshold $u$ at reference
  exceedance fraction $p = k/n$, $u = \sigma_f\,\Phi^{-1}(1 - p/2)$, the expected bias is
  $\operatorname{erfc}\bigl(u/(\sqrt2\sigma_g)\bigr)/p$ (my derivation).
- *Hill value* (`metrics/tail_index/card.md`, Eq. 2): a Gaussian has extreme-value index 0, but
  at a fixed order the Hill estimate converges to the population value
  $\mathbb E[\ln(X/u_p)\mid X>u_p]$ for $X = |Z|$ and $u_p$ its upper $p$ quantile (my
  statement: Eq. 2 is the empirical version of that functional). It does not depend on the
  spectrum or the variance, because the estimate is scale-free and every increment marginal is
  a scaled normal. By quadrature at n = 65 536: **0.0623, 0.0928 and 0.1790 at k = 16, 256 and
  4096**. Measured with the metric at k = 256 on 20 frames: 0.0928 ± 0.0027 against 0.09279.
  This is the exact target of `tail_index` on every Gaussian frame at 256².
- *Spectrum*: the expected shell spectrum is $\tfrac12\sum_{\text{shell}} v_{\mathbf m}/M^2$.
  Between two independent draws `spectrum_l2` is not zero but sampling noise of size
  $\bigl(2\sum_{\text{shells}}\operatorname{Var}E(k) / \sum_{\text{shells}}\mathbb E[E(k)^2]\bigr)^{1/2}$,
  with $\operatorname{Var}E(k) = \tfrac12\sum_{\text{shell}}(v_{\mathbf m}/M^2)^2$ (my
  derivation: each Hermitian pair is one exponential variable). Measured over 200 pairs at
  β = 5/3: 0.642 with $k_{\min} = 1$ against 0.659 from that ratio, and 0.235 with
  $k_{\min} = 8$ against 0.239. Few modes in the lowest shells make the null floor of
  `spectrum_l2` of order one; a band starting at $k_{\min} \ge 4$ is my recommendation.

**Velocity.** A stream function ψ is drawn by Eq. (1) with
$v^\psi_{\mathbf m} = v^E_{\mathbf m}/|\boldsymbol\kappa_{\mathbf m}|^2$, where $v^E$ is the
per-mode variance for the velocity's shell spectrum; then $u_x = \partial_y\psi$,
$u_y = -\partial_x\psi$ spectrally, and $\omega = \partial_x u_y - \partial_y u_x = -\nabla^2\psi$.
The divergence is zero to round-off (measured 7e-16), and the per-mode variances of the
components, $\kappa_y^2 v^\psi$ and $\kappa_x^2 v^\psi$, give the longitudinal and transverse
S₂ by Eq. (3). On the broken spectrum of Sect. 6 the transverse-to-longitudinal ratio at
ℓ = 1, 2, 4, 8 is 2.85, 2.54, 2.19, 1.85; for a smooth field the 2D incompressibility relation
$S_T = S_L + r\,dS_L/dr$ with $S_L \propto r^2$ gives 3 (my derivation), a consistency check on
the construction. Velocity increments along every pair are Gaussian, so every target above
holds for velocity too.

### 3.3 The stationary time-evolving version (spec 04, A3)

Each Fourier coefficient follows an Ornstein–Uhlenbeck process with correlation time
$\tau_{\mathbf m}$, sampled exactly at the frame spacing Δt by the autoregression

$$
\hat g_{\mathbf m}(t_{n+1}) = a_{\mathbf m}\,\hat g_{\mathbf m}(t_n)
+ \sqrt{1-a_{\mathbf m}^2}\;\sqrt{v_{\mathbf m}/M}\;\hat w^{(n+1)}_{\mathbf m},
\qquad a_{\mathbf m} = e^{-\Delta t/\tau_{\mathbf m}}, \tag{7}
$$

with a fresh white field $w^{(n+1)}$ per frame and $\hat g(t_0)$ drawn from Eq. (1). This is
the exact transition of the Ornstein–Uhlenbeck process for any step (Gillespie 1996, abstract
read; the formula is my derivation from the process's Gaussian transition law, so no equation
number is quoted). Starting from the stationary law makes every frame stationary with
$\mathbb E|\hat g_{\mathbf m}|^2 = v_{\mathbf m}$, and the lag correlation of each mode is
exactly $a_{\mathbf m}^{|n-n'|}$. Measured on one mode over 400 steps, 0.587 against
$e^{-1/2} = 0.607$, within the sampling error of one mode. The correlation time law is my design,
$\tau_{\mathbf m} = \tau_0\,(|\mathbf m|/k_{\min})^{-p}$ with p = 2/3 an eddy-time scaling
(spec 04, A3), and $\tau_0 = 0$ gives independent frames. Every frame is a Gaussian field with
the spectrum of Sect. 3.2, so every per-frame target holds unchanged; the time series adds the
base-period protocol of `tail_exceedance`, for which the rate in and out of a base period is
the same up to the in-base bias of Zhang et al. (2005; spec 04, A3).

### 3.4 Family An: anisotropic Gaussian fields

Evaluating the spectrum at a stretched wavevector,
$v_{\mathbf m} = f\bigl(\sqrt{(a\kappa_x)^2 + (\kappa_y/a)^2}\bigr)$, gives in the continuum a
covariance $C(r_x, r_y) = C_{\rm iso}\bigl(\sqrt{(r_x/a)^2 + (r_y a)^2}\bigr)$ (my derivation, a
change of variables in the Fourier integral). The correlation length along x is multiplied by
$a$ and along y divided by $a$, the area of the correlation ellipse is unchanged, and the ratio
of the two lengths is $a^2$. For a Matérn field both integral scales follow from Eq. (4). On
256² with ρ = 8 cells, ν = 1, a = 2, the discrete integral scales are 17.19 and 3.70 cells
against 17.77 and 4.44 from Eq. (4) (measured); the gap is the grid (ρ/a = 4 cells) and the
periodic images, and the exact discrete S₂ along each axis comes from Eq. (3). The increments
along each axis stay Gaussian, so the flatness is still exactly 3 on each axis, which is the
anchor `increment_flatness` keeps by averaging per-axis flatnesses rather than pooling (its
card, Eq. 4). This family is the known-anisotropy reference that G5 and the anisotropy ideas
need (`FUTURE_EXPERIMENTS_CATALOG.md`, G5, "Serves").

### 3.5 Family T: pointwise transforms with exact increment moments

Let $g$ be a unit-variance Gaussian field with correlation $c(\ell) = C(\ell\mathbf e_j)$.

**(a) The second Hermite polynomial**, $h = g^2 - 1$. With $a = g(\mathbf x)$ and
$b = g(\mathbf x + \ell\mathbf e_j)$, $\delta h = (a-b)(a+b)$, and $a-b$, $a+b$ are
uncorrelated, hence independent, normals of variances $2(1-c)$ and $2(1+c)$ (my derivation).
So $\delta h$ is a product of two independent normals, and

$$
\mathbb E[\delta h^2] = 4(1-c^2), \qquad F = \frac{\mathbb E[\delta h^4]}{\mathbb E[\delta h^2]^2} = \frac{3\cdot 3\,(1-c)^2(1+c)^2\cdot 16}{16\,(1-c^2)^2} = 9 \tag{8}
$$

at **every** separation, whatever the spectrum. This is a non-Gaussian field with a flatness
target that does not move with ℓ.

**(b) The exponential (log-normal) field**, $\rho = \exp(s g)$. The joint moment generating
function of a bivariate normal gives every increment moment (my derivation):

$$
\mathbb E\bigl[(\delta\rho)^q\bigr] = \sum_{j=0}^{q}\binom{q}{j}(-1)^j
\exp\!\Bigl\{\tfrac{s^2}{2}\bigl[(q-j)^2 + j^2 + 2(q-j)\,j\,c(\ell)\bigr]\Bigr\}. \tag{9}
$$

The flatness from Eq. (9) depends on ℓ through $c(\ell)$. As $c \to 1$ the increment is
$\rho\, s\,\delta g$ to leading order, so $F \to 3\,\mathbb E\rho^4/(\mathbb E\rho^2)^2 =
3e^{4s^2}$, and as $c \to 0$ it is the flatness of a difference of two independent log-normals:
a flatness that rises as the separation falls, which is what `increment_flatness` reads on
intermittent flow, with an exact curve. For s = 0.5 and a Matérn g (ρ = 4 cells, ν = 1) Eq. (9)
gives 7.90, 7.48, 6.82, 6.20, 5.97, 5.95 at ℓ = 1, 2, 4, 8, 16, 32 cells. This is the density
transform, since it keeps density positive.

**What was measured, and a caution.** Pooling the moments over 100 frames reproduced Eq. (8)
to within 0.6% (8.95 to 8.98 against 9 at ρ = 4 cells) and Eq. (9) to within 2%. The metric's
own per-frame flatness, a ratio of sample moments, came out **below** the exact value: 8.84 to
8.56 against 9, and 7.72 to 5.82 against 7.90 to 5.95, with the shortfall growing with the
correlation length (8.68 to 7.77 at ρ = 16 cells). It is the downward bias of a sample flatness
when the tails are heavier than Gaussian and the frame holds few independent correlation
areas (my interpretation; not checked against a source). So the exact values are targets for a
frame average with a stated tolerance of a few percent, or for moments pooled over frames, and
short correlation lengths (ρ ≤ N/64) should be the default.

### 3.6 Family MF: a multifractal field with a known flatness law

**The source construction.** Bacry, Delour and Muzy (2001; read in full via ar5iv) define the
multifractal random walk as $X(t) = \lim \sum_k \varepsilon[k]\,e^{\omega[k]}$, with ε Gaussian
white noise and ω Gaussian with covariance $\lambda^2\ln\rho[|k_1-k_2|]$, ρ decaying from $L/\Delta t$
to 1 over a correlation length $L$ (their Eqs. 7–10). Its even moments scale as
$m(2p,\ell) = K_{2p}(\ell/L)^{p-2p(p-1)\lambda^2}$ for ℓ ≤ L (their Eq. 12), so
$\zeta_q = (q - q(q-2)\lambda^2)/2$ (their Eq. 13). Lakhal, Ponson, Benzaquen and Bouchaud
(2025; read via ar5iv) extend it to fields in $d$ dimensions: a log-correlated Gaussian field
ω with $C_\omega(r) \approx -\lambda\log(r/\xi_\omega)$ for $r < \xi_\omega$ (their Eq. 2 with
H = 0 and a cut-off at $\xi_\omega$, App. B), a "volatility" $\sigma = e^\omega$, a symmetrised
product $s\,\sigma$ with $s$ independent white noise, and a fractional integration
$h = (-\Delta)^{-(H+d/2)/2}(s\sigma)$, whose structure functions have

$$
\zeta_q = qH - \frac{\lambda}{2}\,q(q-2) \qquad (\delta r \ll \xi_\omega) \tag{10}
$$

(their Eq. 4), and are monofractal, $\zeta_q = qH$, above $\xi_\omega$. Note the two papers'
λ differ: Lakhal et al.'s λ multiplies the logarithm, Bacry et al.'s λ² does.

**In the repository's construction** this is Eq. (1) with one change: the white field $w$ is
replaced by $s\,e^{\omega - V_\omega}$, where ω is itself drawn by Eq. (1) with the
log-correlated variance $v^\omega_{\mathbf m} = 2\pi\lambda M/(\kappa_\xi^2 + |\boldsymbol\kappa_{\mathbf m}|^2)$
(cells of unit spacing; $\kappa_\xi = 2\pi/\xi_\omega$), and $V_\omega = C_\omega(\mathbf 0)$.
The normalisation is my derivation: the continuum covariance of that density is
$\lambda K_0(\kappa_\xi r) \approx -\lambda\ln r + \text{const}$; on 256² with $\xi_\omega = 256$
the discrete log-slope of $C_\omega$ was −0.0486 at r = 2 to 4 against −λ = −0.05 (measured).
The fractional integration is the power-law spectrum of Sect. 3.2 with β = 2H + 1, so H = 1/3
gives $k^{-5/3}$. Two properties are exact on the grid (my derivations):

1. **The spectrum is the Gaussian field's.** Because $s$ is white and independent of ω,
   $s\,e^{\omega-V_\omega}$ is uncorrelated from cell to cell with unit variance, so
   $\mathbb E|\hat h_{\mathbf m}|^2 = v_{\mathbf m}$ exactly. A multifractal field and a
   Gaussian field from the same $v$ are a pair with **the same expected spectrum and different
   increment statistics**, the reverse of the impostor test.
2. **The flatness at every separation is a finite sum.** Write $h = K * (s\,e^{\omega-V})$ with
   $K = \mathcal F^{-1}[\sqrt{v/M}]$ and $A_\ell(\mathbf y) = [K(\mathbf y + \ell\mathbf e_j) - K(\mathbf y)]^2$.
   Conditional on ω the increment is Gaussian with variance $\sum_{\mathbf y} A_\ell e^{2(\omega-V)}$,
   and $\mathbb E[e^{2(\omega(\mathbf y)-V)+2(\omega(\mathbf y')-V)}] = e^{4C_\omega(\mathbf y-\mathbf y')}$, so
   $$
   F_j(\ell) = 3\,\frac{\sum_{\mathbf y,\mathbf y'} A_\ell(\mathbf y)\,A_\ell(\mathbf y')\,e^{4C_\omega(\mathbf y-\mathbf y')}}{\bigl(\sum_{\mathbf y}A_\ell(\mathbf y)\bigr)^2}, \tag{11}
   $$
   two FFTs per separation. For velocity, $K$ is replaced by $\partial_y K$ (for $u_x$) or
   $-\partial_x K$ (for $u_y$).

In the continuum and deep inside the scaling range, Eq. (10) gives
$F(\ell) \propto \ell^{\zeta_4 - 2\zeta_2} = \ell^{-4\lambda}$, the law `increment_flatness`
measures; for the walk of Bacry et al., their Eq. (12) gives the same law, $\ell^{-4\lambda^2}$ in their
notation, with prefactor
$6(L/\ell)^{4\lambda^2}/[(1-4\lambda^2)(2-4\lambda^2)]$ (my evaluation of their $K_4$ integral
for $p = 2$). On a 256² grid there is no such scaling range: with λ = 0.05, H = 1/3,
$\xi_\omega = 256$, Eq. (11) gives a scalar flatness of 5.81, 5.62, 5.10, 4.58, 4.11, 3.74, 3.48,
3.37 at ℓ = 1 to 128 cells, a local log-slope of −0.15 rather than −0.20. **Eq. (11), not the
power law, is the target.** Measured against it (60 frames): moments pooled over frames gave
5.65 to 3.26, and the metric's per-frame mean 5.64 to 3.05, about 3% below at small ℓ and more
at large ℓ, the same finite-sample bias as Sect. 3.5. For the longitudinal velocity Eq. (11)
gives 5.20, 5.09, 4.67, 4.22, 3.82, 3.50, 3.29, 3.20; the metric's per-frame mean over 40 frames
was 5.25 to 3.01.

### 3.7 Tail families, made by degradations of a Gaussian reference

**(c) Pareto spikes (G2a, X4).** Under the code rule a spiked field is a candidate made by the
`pareto_spikes` operator of X4 applied to a Gaussian reference, not a second implementation
inside the reader. Its known answer on this reference, with my additions to the catalog:

- **Construction.** Exactly $m$ cells, drawn without replacement, each receive $\pm A$ with a
  random sign. I suggest drawing $A$ from a generalised Pareto law of shape ξ, location $a_0$ and
  scale $a_0|\xi|$, $A = a_0 + a_0|\xi|\,[(1-U)^{-\xi} - 1]/\xi$ with U uniform. For ξ = 1/α > 0
  this is the Pareto law $P(A > a) = (a/a_0)^{-\alpha}$ of the proposal; for ξ < 0 it is bounded
  with $P(A > 2a_0 - t) \propto t^{-1/\xi}$, so ξ is the extreme-value index of both signs
  (my derivation). One operator then covers (c) and the light tail (d).
- **Why 1/α is exact.** A spike makes two increments of size about $A$ along each axis. If the
  $k+1$ largest absolute increments are all spike increments, they are pairs of the
  $\lceil k/2\rceil + 1$ largest of $m$ Pareto values, and for Pareto values the log-ratios over
  the $(k'+1)$-th largest are independent exponentials of mean 1/α (the memoryless property;
  my derivation), so the Hill estimate has expectation exactly 1/α with an effective order of
  about k/2.
- **The spike count.** That needs $m \ge k/2 + 1$, a fraction of at least $1/(2\sqrt n)$, which is
  the catalog's G2 rule (Sect. 2.2: "the spike fraction must scale as at least 1/(2√n)"). X4
  states "at least 2/√n with a margin", a factor four larger; its example values, "about 1e-2 at
  128², 4e-3 at 256²", are close to $1/\sqrt n$. The two statements disagree as written.
- **The spike floor**, a condition the catalog does not state: $a_0$ must exceed the reference's
  largest Gaussian increment. Measured with `tail_index` on a β = 5/3 Gaussian field of unit
  rms at 256² (8 frames each; the largest increment is about 1.0):

| Spike fraction | $a_0$ (× fluct. rms) | α = 6 (target 0.167) | α = 4 (0.250) | α = 3 (0.333) | α = 2 (0.500) |
|---|---|---|---|---|---|
| 0.5/√n = 1.95e-3 | 3 | 1.307 | 1.398 | 1.456 | 1.629 |
| 1/√n = 3.91e-3 | 1 | 0.202 | 0.267 | 0.321 | 0.476 |
| 1/√n = 3.91e-3 | 3 | 0.167 | 0.239 | 0.321 | 0.482 |
| 2/√n = 7.81e-3 | 1 | 0.163 | 0.237 | 0.313 | 0.492 |
| 2/√n = 7.81e-3 | 3 | 0.164 | 0.245 | 0.335 | 0.499 |

  At exactly $1/(2\sqrt n)$ (128 spikes, 256 spike increments for k + 1 = 257) the estimate
  fails, as the G2 reviewer found at 1e-3. At $1/\sqrt n$ it matches when $a_0 = 3$ but is 20%
  high at α = 6 when $a_0 = 1$; at $2/\sqrt n$ it matches either way (spread 0.007 to 0.05).
  Keeping spikes off neighbouring cells made no difference, so no placement rule is needed.
  My recommendation: fraction $2/\sqrt n$ and $a_0 = 3$ fluctuation rms.
- **Other exact answers.** If every spike increment exceeds the reference threshold of
  `tail_exceedance`, each spike adds two exceedances per axis, so the bias at θ = 1/2 is about
  $1 + 2m/k$, which is 5 at $m = 2\sqrt n$ (my derivation, not run). The flatness has no finite
  expectation for α ≤ 4, as X4 notes.

**(d) The light-tail fixture (extreme-value index −1).** A field that is 0 on the cells with
$i + j$ even and uniform on $[0, 1]$ on the others (an even grid keeps it periodic) has every
one-cell increment, along either axis, equal to ± a uniform value, so the absolute increments
are uniform with index exactly −1 (my construction). Measured with the moment estimator
$\hat\gamma = M_1 + 1 - \tfrac12(1 - M_1^2/M_2)^{-1}$ at k = 256 over 200 fields: −1.032 ± 0.014
(independent uniforms: −1.009 ± 0.010). The formula is taken from the MTR proposal and a
secondary source (Beirlant and co-authors, as quoted by a search result), **not** from Dekkers,
Einmahl and de Haan (1989), whose scanned text I could not read. This fixture serves a metric
that is not built, so it belongs in that bundle's `test_metric.py`, five lines beside the
independent-Pareto fields `metrics/tail_index/test_metric.py` already draws, not in the reader.

### 3.8 Which degradations act on these references with known answers

| Operator (status) | Acting on | Exact answer |
|---|---|---|
| `additive_noise` (exists) | any Gaussian family field | A Gaussian field with per-mode variance $v + s^2 r^2 M$ (r the fluctuation rms the harness measures). Increment variance $\hat S_2 + 2s^2r^2$; Eqs. (5), (6) and the bias formula give `increment_w1`, `energy_distance`, `tail_exceedance`; flatness 3 and the Hill value 0.0928 are unchanged, an exact blind axis for both. Measured against Eq. (5), using the realised reference increment variance: within 0.2% to 0.7% at s = 0.05 to 0.5 |
| `gaussian_blur`, `box_blur`, `disk_blur`, `epanechnikov_blur`, `lowpass_*`, `highpass_*`, `band_attenuate`, `translate_subpixel` (exist) | Gaussian | Linear and shift-invariant, so the result is Gaussian with variance $|T_{\mathbf m}|^2 v_{\mathbf m}$, where T is read from the operator's response to a unit impulse (no new code). Flatness 3 and the Hill value are unchanged on every severity level: an exact blind axis for `increment_flatness` and `tail_index`, in contrast to issue 036 on kinet data |
| `translate`, `random_large_translation` (exist) | any family | Every single-field statistic is unchanged. Expected MSE at shift $\mathbf d$ is $2[C(\mathbf 0) - C(\mathbf d)]$, Eq. (2), so a pointwise norm's response to displacement is known exactly |
| `gain`, `bias` (exist) | any family | Exact per frame, not only in expectation: `gain` scales every increment by $1+s$, so $W_1 = s\,\overline{|\delta|}$ and the flatness and Hill value are unchanged; `bias` changes no increment |
| `gaussian_impostor` (exists) | scalar Gaussian field | An exact null in distribution: for a complex Gaussian coefficient, modulus and phase are independent and the phase is uniform (my derivation), so new uniform phases give a field with the reference's law. Measured flatness 2.996 ± 0.011. Not a null on velocity, because the impostor draws one phase per channel (G3, correction 2) |
| graded phase randomisation, X2 (to build) | scalar Gaussian field | The same argument at every s: every single-field statistic is unchanged. Expected MSE is $2C(\mathbf 0)[1 - \operatorname{sinc}(s)]$ with $\operatorname{sinc}(s) = \sin(\pi s)/(\pi s)$, the mean of $\cos\theta$ for θ uniform on $[-s\pi, s\pi]$ (my derivation; the self-conjugate modes depend on how X2 rotates them). On families T and MF the flatness falls towards 3 as s → 1, a response with known end points |
| correlated noise, X1 (to build) | Gaussian | Gaussian with per-mode variance $v + q$ for a noise variance q drawn by Eq. (1): S₂ adds, and Eqs. (5), (6) and the expected MSE (the noise variance) are exact |
| `pareto_spikes`, X4a (to build) | Gaussian | Hill target 1/α under the count and floor conditions of Sect. 3.7; bias at θ = 1/2 about $1 + 2m/k$ |
| `tail_compress`, X4b (to build) | Gaussian | The threshold is a known Gaussian quantile and the bulk below it is unchanged by construction; the response above it depends on a compressive map not yet designed |
| anisotropic blur, X6 (to build) | isotropic Gaussian | Gaussian with variance $v\,|T_x|^2|T_y|^2$; S₂ per axis from Eq. (3); compared with family An, the known width ratio becomes a known ratio of correlation lengths |
| `coarsen`, `subsample`, `median_blur`, `multiplicative_noise` (exist) | — | No closed form here: the first two are not shift-invariant, the last two not linear |

### 3.9 Limits

- **Not turbulence.** No energy flux, no third-order structure function (odd moments vanish for
  the Gaussian and multifractal families, since $s$ is symmetric), no coherent vortices. The
  `spectral_energy_flux` reading is zero in expectation and serves only as a null.
- **The targets are expectations.** Per frame, the Gaussian targets hold to a fraction of a
  percent; the heavy-tailed families' flatness is biased low per frame by a few percent
  (Sects. 3.5, 3.6). Tests compare frame averages or pooled moments with stated tolerances.
- **The analysis grid must be the native grid.** Block-averaging onto a coarser analysis grid
  is a further linear filter; its effect on the spectrum is computable but not specified here.
- **Spectral increments are periodic.** The targets assume every axis wraps, which the metrics
  already require.

## 4. Options B and C: simulated systems

No simulated system gives exact increment statistics, which is why Option A is the dataset.
Two simulated counterparts are already specified elsewhere and add what A lacks.

- **Option B, stationary forced Burgers in one dimension** (spec 04, A4; Bec and Khanin 2007,
  as recorded there): a dynamically generated, stationary, intermittent record with a known
  exponent law, $\zeta_p = \min(p, 1)$, and hence a flatness growing as $r^{-1}$. It gives a
  physical intermittency to compare with family MF's synthetic one. Cost: a fifty-line
  integrator, seconds per run (spec 04).
- **Option C, kinet forced two-dimensional turbulence with drag** (spec 04, Option B): the
  physical record whose spectral slopes family G imitates, with fluxes and structures A cannot
  have. Its statistics are known only as scaling laws (spec 04, Eqs. 2–3), and it costs an
  8-hour job plus two kinet additions (BUILD_ORDER step 22).

## 5. Recommendation

Build Option A as one reader with four dataset configs (Sect. 6), in this order: family G with
independent frames (the null for every metric, and the reference for X1, X2, X4 and the existing
linear operators), the stationary time series, family An, and the intermittent pair (T and MF).
The time series costs about ten more lines and turns spec 04's A3 into a dataset. Family An
waits only on a metric or operator that reads anisotropy (X6, the two-point correlation idea).
Options B and C add physics, not exactness, and are built under spec 04.

## 6. What to store: nothing; the reader, its configs and its known statistics

Nothing is written to disk. The design, under the code rule (`BUILD_ORDER.md`):

**Where.** One subclass of `ClosedFormTrajectory`, `RandomField`, registered as `random_field`
in `fmeval/data/analytic.py`. *Why a new subclass rather than an option on an existing reader:*
`synthetic_ensemble` declares `is_ensemble = True` and adds members to every frame, so a
deterministic metric would score a member mean rather than the field
(`configs/cards/default.yaml`, comment on `evidence_dataset_properties`); `taylor_green_2d`, `sod_shock_tube` and `advecting_blobs` are single
solutions with no spectrum. `ClosedFormTrajectory` already supplies the grid, the cell
centres, the time axis, `meta` and `read_frame`, so the subclass writes only its constructor and
`solution`. The draw of Eq. (1) is one module-level function, `gaussian_random_field(variance, white)`,
because the reader calls it three times (density, stream function, chaos field) and X1 and
spec 08's correlated ensemble noise (catalog B3) need the same draw; it goes in
`fmeval/wavenumbers.py`, the spectral module that readers and operators already import. The
reader's wavevectors come from the existing `physical_wavenumber_grid`, so a non-square box is
handled physically and issue 046 does not arise. Seeds come from `fmeval.context.derive_rng`,
as in `synthetic_ensemble`, keyed by (seed, label, frame, field).

**Constructor options** (each with the reader's default): `grid` (256, 256); `length` (1.0, 1.0);
`n_frames` 33; `t_start` 0, `t_end` 32; `spectrum` "power_law" or "matern"; `exponents` (5/3,)
or two values with `k_break`; `k_min` 4, `k_max` 120 (cycles per box; refused at or above
N/2); `matern_length` ρ in cells and `matern_nu`; `anisotropy` a, 1.0; `density_mean` 1.0 and
`density_sigma` 0.05; `transform` "none", "hermite2" or "exp" (density only:
$\rho_0(1+\sigma g)$, $\rho_0[1+\sigma(g^2-1)]$, $\rho_0\exp(\sigma g - \sigma^2/2)$; refused for
"none" when σ ≥ 0.1 and for "hermite2" when σ ≥ 1, the bounds that keep density positive);
`velocity_rms` per component, 0.1; `multifractal_lambda` 0 and `multifractal_scale`
$\xi_\omega$ (default the box); `tau` 0 and `tau_exponent` 2/3 (refused with a nonzero λ, since
Eq. 7 is not defined for the chaos field); `seed` 0. **Fields:** `density`, `velocity` and
`vorticity`, the last as its closed form $-\nabla^2\psi$, which the harness recomputes and
which a test checks against the recomputation, as for `taylor_green_2d`.

**Frame access.** `solution(time)` recovers the frame index from the evenly spaced times; with
`tau = 0` it draws the frame directly, and with `tau > 0` it advances Eq. (7) from a cached
(index, coefficients) pair, restarting from frame 0 only when a run reads frames out of
order.

**Known statistics.** The reader keeps the arrays it builds anyway as attributes: the per-mode
variances of the density's Gaussian and of the stream function, and the chaos covariance
$C_\omega$. Every target of Sect. 3 follows from them in a few lines, and those lines go in
`tests/analytic_fields.py`, the module that already holds closed-form metric responses: the
increment variance of Eq. (3) at the octave separations of `octave_separations`, the flatness of
Eqs. (8), (9) and (11), the Hill population value by quadrature, and Eqs. (5) and (6) inline in
the tests that use them.

**Dataset configs** (`configs/dataset/`, each a few lines over a shared `_random_field.yaml`
fragment; all periodic, not ensembles; every one is admitted to `evidence_datasets` with
`{periodic: true, ensemble: false}`):

| Config | Options beyond the defaults | Claim label (proposed) |
|---|---|---|
| `random_field_gaussian` | `exponents: [1.6667, 3.0]`, `k_break: 32` | "a known-statistics null: Gaussian increments of exactly known variance at every separation, so flatness 3, the Hill value 0.0928 and the distances have closed-form targets; nothing about turbulence" |
| `random_field_gaussian_ou` | as above, `tau: 8`, `n_frames: 201`, `t_end: 200` | the same, "stationary in time with a known correlation time per mode" |
| `random_field_anisotropic` | `spectrum: matern`, `matern_length: 8`, `anisotropy: 2` | "a known-anisotropy check: correlation lengths in the ratio 4 along x and y, Gaussian increments; nothing about turbulence" |
| `random_field_intermittent` | `spectrum: matern`, `matern_length: 4`, `transform: exp`, `density_sigma: 0.5`; and on velocity `multifractal_lambda: 0.05` | "a known-intermittency check: log-normal density and multifractal velocity whose increment flatness at every separation is exact; nothing about turbulence" |

The intermittent config needs the Matérn spectrum for density and the power law for velocity.
That one exception is met either by a second spectrum option for velocity or, with less code,
by giving both fields the Matérn spectrum. I leave that choice to the builder; the targets
above are for the stated spectra. Known values for the first config (measured from Eq. 3):
density $S_2/2C(\mathbf 0)$ = 0.053, 0.161, 0.370, 0.660, 0.980 at ℓ = 1 to 16 cells,
identical along x and y.

## 7. References

- Bacry, E., Delour, J. and Muzy, J. F. (2001). Multifractal random walk. *Phys. Rev. E* 64,
  026103. doi:10.1103/PhysRevE.64.026103; arXiv:cond-mat/0005405. Read in full via ar5iv
  (through a fetch tool's summary): Eqs. 7–10 (construction), 12 (even moments and $K_{2p}$),
  13 (ζ_q), 18–19 (the fractional variant).
- Lakhal, S., Ponson, L., Benzaquen, M. and Bouchaud, J.-P. (2025). Wrapping and unwrapping
  multifractal fields. *Phys. Rev. Research* 7, L012003. doi:10.1103/PhysRevResearch.7.L012003;
  arXiv:2310.01927. Read via ar5iv (fetch summaries, with Eqs. 1–4 quoted): Eqs. 1–4, App. B;
  2D example of their Fig. 3 (512², H = 0.5, λ = 0.1, $\xi_\omega$ = 32).
- Porcu, E., Bevilacqua, M., Schaback, R. and Oates, C. J. (2023). The Matérn model: a journey
  through statistics, numerical analysis and machine learning. arXiv:2303.02759. Read via ar5iv
  (fetch summary): Eq. 9 (correlation function), Eq. 23 (spectral density). Its journal version
  was not checked.
- Lang, A. and Potthoff, J. (2011). Fast simulation of Gaussian random fields. *Monte Carlo
  Methods Appl.* 17, 195–214. doi:10.1515/MCMA.2011.009; arXiv:1105.2737. Abstract only.
- Gillespie, D. T. (1996). Exact numerical simulation of the Ornstein-Uhlenbeck process and its
  integral. *Phys. Rev. E* 54(2), 2084–2091. doi:10.1103/PhysRevE.54.2084. Abstract and
  bibliographic record only (the PDF could not be read); Eq. (7) here is derived, not quoted.
- Peyré, G. and Cuturi, M. (2019). Computational optimal transport. *Found. Trends Mach. Learn.*
  11(5–6), 355–607. doi:10.1561/2200000073; arXiv:1803.00567. Remark 2.30, Eq. 2.36, as cited on
  `metrics/increment_w1/card.md`; not reopened here.
- Székely, G. J. and Rizzo, M. L. (2013). Energy statistics. *J. Stat. Plann. Inference*
  143(8), 1249–1272. doi:10.1016/j.jspi.2013.03.018. Definition 1, Eq. 2.4, as cited on `metrics/energy_distance/card.md`; not
  reopened here.
- Boffetta, G. and Ecke, R. E. (2012). Two-dimensional turbulence. *Annu. Rev. Fluid Mech.* 44,
  427–451. doi:10.1146/annurev-fluid-120710-101240. Eqs. 12–13, as recorded in spec 04 and on `metrics/spectrum_l2/card.md`; not reopened.
- Zhang, X., Hegerl, G., Zwiers, F. W. and Kenyon, J. (2005). Avoiding inhomogeneity in
  percentile-based indices of temperature extremes. *J. Climate* 18(11), 1641–1651. doi:10.1175/JCLI3366.1. As cited on
  `metrics/tail_exceedance/card.md` and in spec 04; not reopened.
- Dekkers, A. L. M., Einmahl, J. H. J. and de Haan, L. (1989). A moment estimator for the index
  of an extreme-value distribution. *Ann. Stat.* 17(4), 1833–1855. doi:10.1214/aos/1176347397.
  **Not read**: the CWI scan could not be decoded; the estimator's formula is quoted from the MTR
  proposal and a secondary snippet only.
- Bec, J. and Khanin, K. (2007). Burgers turbulence. *Phys. Rep.* 447(1–2), 1–66. As recorded in
  spec 04, A4; not reopened.
- Repository sources: `FUTURE_EXPERIMENTS_CATALOG.md` (G2, G3, G5, G10, X1, X2, X4, X6, B3);
  `dataset_specs/04_forced_stationary_turbulence.md` (A3, A4, Option B); the metric cards
  named in Sect. 3.2; `degradations/gaussian_impostor/degradation.py`; issues 036, 037, 044, 046,
  128, 132.

## 8. Confidence

- **Sure (derived and measured):** Eqs. (1)–(3) and the exactness of the Gaussian targets on the
  grid; flatness 3, Eqs. (5) and (6), and the Hill population value 0.0928 at 256², each matched
  by the repository's own metric to within its sampling spread; flatness 9 for the Hermite
  transform and Eq. (9) for the log-normal (pooled moments within 0.6% and 2%); Eq. (11) for the
  multifractal field (within about 3%); that the multifractal and Gaussian fields share their
  expected spectrum (derived; measured shell ratios near 1 within sampling); the spike table.
- **Sure from the sources, read through summaries:** the MRW construction and Eqs. 12–13 of Bacry
  et al.; Eq. 4 of Lakhal et al. and their convention for λ; the Matérn formulas of Porcu et al.
  The equation numbers come from ar5iv renderings read through a fetch tool's summaries, not
  from the journal PDFs.
- **Reasoning, not checked:** that the per-frame flatness shortfall is the finite-sample bias of
  a ratio of moments; that the moment estimator's formula is Dekkers et al.'s; the expected
  `tail_exceedance` answer with spikes ($1 + 2m/k$, not run); the phase-randomisation MSE with
  self-conjugate modes; the reader's line counts.
- **Not done:** no reader was written, so the configs were not run through `evaluate.py` and the
  calibration (`AGENTS.md` Sect. 5) was not checked on them; the OU check used one mode.
- **Connections:** an exact independent realisation (a second seed) is the damage anchor issue 037
  lacks for `increment_flatness`, and the spread of the Hill estimate over many seeds is
  route 2 of issue 132 (measured here: 0.0027 at k = 256 on Gaussian frames, and 0.007 to 0.05 on
  spiked frames). Separations in units of a known correlation length answer the request of
  issue 128 on this dataset. The fields are drawn from the reader's own `seed`, not the run's;
  Kareem decided on 2026-11-27 that the reader does not need to know the run's seed, and
  `run_meta.json` records the reader's under `reader_options`.

## 9. Existing code reused and new code needed

| Piece | Existing file it extends | New lines (rough) |
|---|---|---|
| `RandomField(ClosedFormTrajectory)`, registered `random_field`: validation, per-mode variances (power law, broken, Matérn, anisotropy, band, Nyquist), chaos covariance, `solution` with transforms, velocity and vorticity, and the cached Eq. (7) | `fmeval/data/analytic.py`; reuses `ClosedFormTrajectory`, `physical_wavenumber_grid`, `derive_rng`; already imported by `fmeval/data/readers.py` | 140, about 40 of them docstring |
| `gaussian_random_field(variance, white)`, Eq. (1) | `fmeval/wavenumbers.py` (shared spectral module; its docstring widened by two lines) | 12 |
| Closed-form targets: Eq. (3) at the octave separations, Eqs. (8), (9), (11), the Hill population value | `tests/analytic_fields.py`; reuses `octave_separations` and `radial_shells` from the metric bundles | 45 |
| Tests: 16×8 contract with `u ≠ v`, expected spectrum, vorticity against the harness's recomputation, S₂ and flatness over frames, Eqs. (5) and (6) through `increment_w1` and `energy_distance`, the Hill value, the `additive_noise` and `gaussian_impostor` answers | `tests/test_analytic_datasets.py` | 90 |
| Four dataset configs and one `_random_field.yaml` fragment | `configs/dataset/` (pattern of `taylor_green_2d.yaml`) | 70, mostly comments |
| Four `evidence_datasets` labels and four `evidence_dataset_properties` rows | `configs/cards/default.yaml` | 16 |
| Dataset page | `docs/datasets/random_field.md` (pattern of `taylor_green_vortex.md`) | 80 of prose |
| The decision admitting analytic readers as evidence | `docs/decisions.md`, "Analytic fields are fixtures; Sod is an analytic check" (BUILD_ORDER says it is updated when the first reader lands) | 10 |
| Pareto spikes and the light tail | none here: the X4 bundle (catalog estimate 30 lines) and the moment estimator's own test (5 lines) | 0 here |

About 200 lines of production code and test helpers, 90 of tests, and configuration and prose.
No existing function's behaviour changes.
