# Periodic random fields with known statistics

!!! note "Computed, not simulated"
    This dataset is a formula and a seed, evaluated whenever a frame is read. Its increment
    statistics are known before any metric runs, so it checks the spectral, increment and tail
    metrics against exact answers. It has no energy cascade, no flux and no coherent
    structures, so it is not evidence about a flow and is not registered as evidence.

## The problem

No flow in the repository has a known increment law: the kinet flows decay, and the other
closed forms are single features whose increments are degenerate. A periodic Gaussian random
field drawn from a prescribed spectrum has Gaussian increments whose variance is known exactly
at every separation, on the grid itself. Its increment flatness is therefore exactly 3, its
Hill estimate at a fixed order has a population value, and the 1-Wasserstein distance between
the increments of two such fields is closed-form. Three non-Gaussian families built from the
same draw keep exact answers while moving the flatness and the tail. The construction and every
answer are derived in `dataset_specs/09_random_fields_known_statistics.md`; the tests in
`tests/test_analytic_datasets.py` assert them through the evaluation pipeline.

## Configurations

| Configuration | What it is | Readable here |
|---|---|---|
| `random_field` | Gaussian density, velocity and vorticity on $256^2$ cells, 12 independent frames, shell spectrum $k^{-5/3}$ below $k = 32$ and $k^{-3}$ above, on the band $4 \le \lvert k \rvert \le 120$ | Yes, computed |

The other families are reader options on the same configuration:

| Family | Override |
|---|---|
| Stationary in time (Ornstein–Uhlenbeck modes) | `+dataset.reader.tau=8 dataset.reader.n_frames=201 dataset.reader.t_end=200` |
| Anisotropic (Matérn, length 8 cells, ratio 4) | `dataset.reader.slopes=[-1,3] dataset.reader.k_break=7.2 +dataset.reader.k_min=1 +dataset.reader.anisotropy=2` |
| Intermittent (log-normal density, multifractal velocity) | `dataset.reader.slopes=[-1,3] dataset.reader.k_break=14.4 +dataset.reader.k_min=1 +dataset.reader.transform=exp +dataset.reader.density_sigma=0.5 +dataset.reader.multifractal_lambda=0.05 dataset.reader.n_frames=48 dataset.reader.t_end=47` |
| Flatness exactly 9 | `+dataset.reader.transform=hermite2 +dataset.reader.density_sigma=0.3 dataset.reader.n_frames=48 dataset.reader.t_end=47` |
| Pareto spikes of index 2 on density | `'+dataset.reader.spikes={fraction:0.0078125,alpha:2,floor:0.3}' dataset.reader.n_frames=24 dataset.reader.t_end=23` |

A candidate with a known error is the reader option `candidate`, scored against the reader's
frames as a forecast is: `'+dataset.reader.candidate={seed:1,density_sigma:0.075}'` is an
independent realisation at 1.5 times the density amplitude, and with `tau` set,
`'+dataset.reader.candidate={tau:inf}'` repeats the first frame (persistence).

**What part is evaluated.** Each frame is an independent draw, so each is an independent sample.
The configuration keeps 12 frames on $256^2$, the grid of every kinet analysis and of the
registered `tail_index` order; the intermittent and Pareto families need more frames, because
their answers are frame averages of heavy-tailed statistics, and their override lines say how
many. The measured costs and the reasons are in the configuration's comments.

## Equations

On the unit square with $M$ cells, every frame filters unit white noise $w$ by a transfer
function $T$:

$$
g = \mathcal{F}^{-1}\left[T_{\mathbf k}\, \mathcal{F}[w]_{\mathbf k}\right], \qquad
C(\mathbf r) = \mathbb{E}[g(\mathbf x)\, g(\mathbf x + \mathbf r)] = \mathcal{F}^{-1}\left[T^2\right](\mathbf r). \tag{1}
$$

The field is exactly Gaussian, being linear in $w$, and its covariance is known on the grid
(spec 09, Eqs. 1–2). On the band $k_{\min} \le \lvert \mathbf k \rvert \le k_{\max}$, in cycles
per domain, the per-mode variance is

$$
T_{\mathbf k}^2 \propto \kappa^{-(\beta_1 + 1)} \left(1 + \kappa^2 / k_b^2\right)^{-(\beta_2 - \beta_1)/2},
\qquad \kappa = \sqrt{(a k_x)^2 + (k_y / a)^2}, \tag{2}
$$

so the shell spectrum falls as $k^{-\beta_1}$ and, above $k_b$, as $k^{-\beta_2}$. With
$\beta_1 = -1$ and $\beta_2 = 2\nu + 1$ this is the Matérn spectral density
$(1 + \alpha^2 \lvert 2\pi\mathbf k \rvert^2)^{-(\nu + 1)}$ of two dimensions (Porcu,
Bevilacqua, Schaback and Oates 2023, arXiv:2303.02759, Eq. 23), with $k_b = 1/(2\pi\alpha)$.
The stretch $a$ multiplies the correlation lengths along $x$ by $a$ and divides those along $y$
by it. $T$ is scaled so $g$ has unit expected variance, and $k_{\max}$ lies below every Nyquist
line, so the harness's spectral curl of the velocity returns the stored vorticity.

The fields are:

- density $1 + \sigma g$; or $1 + \sigma(g^2 - 1)$, whose increments have flatness exactly 9 at
  every separation (spec 09, Eq. 8); or $\exp(\sigma g - \sigma^2/2)$, log-normal, whose
  increment moments are a finite sum (spec 09, Eq. 9);
- vorticity drawn by Eq. (1) with transfer $2\pi\lvert\mathbf k\rvert T$, and velocity its
  periodic Biot–Savart inversion through a stream function, so the velocity has the spectrum of
  Eq. (2) and zero divergence;
- with $\lambda > 0$, the vorticity's white noise replaced by $s\, e^{\omega - V}$, with $s$
  independent white noise and $\omega$ a Gaussian field of covariance $\lambda K_0(2\pi r)$,
  about $-\lambda \ln r$ below the box size, and variance $V$: the multifractal construction of
  Lakhal, Ponson, Benzaquen and Bouchaud (2025, Phys. Rev. Research 7, L012003, Eqs. 1–4), after
  Bacry, Delour and Muzy (2001, Phys. Rev. E 64, 026103, Eqs. 7–10). Its expected spectrum is
  the Gaussian field's, and its increment flatness at every separation is a finite sum
  (spec 09, Eq. 11);
- with `spikes`, a fraction of the density cells raised by a floor times a Pareto variable of
  index $\alpha$, so the Hill estimate reads $1/\alpha$ when the fraction is at least
  $2/\sqrt{M}$ (spec 09, Sect. 3.7).

With `tau` $> 0$, each Fourier mode is an Ornstein–Uhlenbeck process sampled exactly at the
frame spacing $\Delta t$ (spec 09, Eq. 7):

$$
\hat g_{\mathbf k}(t_{n+1}) = a_{\mathbf k}\, \hat g_{\mathbf k}(t_n)
+ \sqrt{1 - a_{\mathbf k}^2}\; T_{\mathbf k}\, \hat w^{(n+1)}_{\mathbf k}, \qquad
a_{\mathbf k} = e^{-\Delta t / \tau_{\mathbf k}}, \quad
\tau_{\mathbf k} = \tau \left(\lvert \mathbf k \rvert / k_{\min}\right)^{-p}, \tag{3}
$$

started from the stationary law, so every frame has the law of an independent one and each
mode's correlation at a lag of $n$ frames is $a_{\mathbf k}^n$.

## What the tests assert

Through the pipeline, on non-square grids except where a stated value needs $256^2$:

| Known answer | Tolerance |
|---|---|
| Increment variance along each axis, spec 09 Eq. 3, through `mse` under whole-cell translation, isotropic and anisotropic | four exact standard errors of a 12-frame mean |
| Increment flatness 3 on density, velocity and vorticity | 0.08 |
| `increment_w1` between two Gaussian fields, $\lvert\sigma_1 - \sigma_2\rvert\sqrt{2/\pi}$ | 6% |
| `tail_index` of a Gaussian field, 0.0928 at $k = 256$ on $256^2$ | 0.004 |
| `tail_index` with Pareto spikes, $1/\alpha$ at $\alpha = 2$ and 4 | 7% |
| Flatness at every separation: 9 (Hermite), the log-normal sum, the multifractal sum | 8%, 12%, 8% of a 48-frame mean |
| Ornstein–Uhlenbeck lag correlation, through `mse` against the persistence candidate | four exact standard errors per frame |
| Flatness 3 on every severity level of the default ladder's linear operators | four standard errors of each level's mean |

The heavy-tailed flatness is noisy and biased low per frame on few independent areas, so its
targets are frame averages; the tolerances and the measurements behind them are in each test's
docstring.

**Boundaries.** Periodic on both axes. Spectral and increment metrics need nothing else.
