# Synthetic exchangeable ensemble

!!! note "Generated, not simulated"
    This dataset is computed from a formula and a seed. It is not a flow. It exists so that
    the probabilistic metrics have a case whose right answer is known in closed form, and the
    cards of those metrics cite it for that purpose only.

## The problem

No ensemble of independent simulations of the same flow exists yet
([issue 004](https://github.com/khegazy/pde_metrics/blob/main/issues/004-independent-realizations.md)).
A probabilistic metric scores a set of predictions, an *ensemble*, against one truth. It
therefore needs a case where the correct score is known before anything is measured. This
dataset builds one. Each frame holds a truth and $N$ ensemble members, all drawn from the same
distribution:

$$
\text{truth} = b(\mathbf{x}, t) + \sigma\,\varepsilon_0, \qquad
m_i = b(\mathbf{x}, t) + \sigma\,\varepsilon_i, \quad i = 1, \dots, N. \tag{1}
$$

Every $\varepsilon$ is an independent standard normal value per cell. The deterministic part
$b$ is a periodic field with one large and one small scale, whose phase advances by a fixed
amount from frame to frame. Because the truth uses the same $\sigma$ as the members and is
drawn independently of them, it is indistinguishable from one more member. That single
property fixes the right answers:

- **Rank histogram.** The truth's rank among the members is uniform, so a rank histogram
  is flat.
- **Spread and skill.** The spread of the ensemble matches the error of its mean, so the
  spread-to-skill ratio is one, up to a finite-ensemble factor.
- **CRPS.** The continuous ranked probability score matches its closed form for a normal
  distribution.

The construction and its parameters are in `fmeval/data/synthetic_ensemble.py`.

![The truth's density at five frames](_generated/synthetic_ensemble_density.png)

*The truth at five frames: the two-scale pattern drifting from frame to frame, under the
noise. Drawn by `python -m fmeval.cards dynamics synthetic_ensemble`.*

## Variations of this problem in the repository

| Configuration | What it is |
|---|---|
| `synthetic_ensemble` | 16 members, 12 frames, $64^2$ cells, density only. $\sigma$ and the phase step keep the reader's defaults; every option can be overridden, for example `+dataset.reader.n_members=32` |

Reader options for other known answers, each off by default and set with
`+dataset.reader.<option>=...`
(`dataset_specs/08_synthetic_ensemble_extensions.md`, Section 3). With them the truth is
$T(b + \sigma(\mathbf{x})\eta_0)$ and each member $T(b + \delta\sigma(\mathbf{x}) +
\sigma(\mathbf{x})\eta_i)$:

| Option | What it changes | Known answer it gives |
|---|---|---|
| `base`: `case_means` or `zero` | $b$ becomes an independent $N(0, 1)$ value per cell, or nothing | With `sigma=1`, the ideal forecaster of Gneiting, Balabdaoui and Raftery (2007); the ladder `degradation=gneiting_forecasters` adds the other three, with exact CRPS 0.5642, 0.6144, 0.6319, 0.7979 |
| `sigma_ratio` $R \ge 1$ | $\sigma(\mathbf{x}) = \sigma R^{w}$, $w = (1 + \sin 2\pi i/n_x)/2$ along the first axis | A calibrated ensemble whose true spread varies across the domain, on the diagonal of the binned spread-error diagram; the `flow_dependence` axes move it off |
| `noise_length` $\ell$, `noise_covariance` | Noise with covariance $e^{-r/\ell}$ or $(1 + r/\ell)^{-1}$ in the torus distance $r$ (Scheuerer and Hamill 2015, Eq. 5) | Spatially correlated members and truth |
| `member_noise_length`, `member_noise_covariance` | The members' covariance alone | A wrong correlation, which `variogram_score` sees and the per-cell scores do not |
| `member_offset` $\delta$ | The members' centre, in units of $\sigma(\mathbf{x})$ | A calibrated spread around a wrong centre, on which `spread_deflate` and `spread_inflate` act |
| `log_amplitude` $\lambda$ | $T(v) = e^{\lambda v}$ on truth and members | A positive density with every rank unchanged, on which `wasserstein` runs |

None of these has a dataset configuration of its own yet.

The ensemble's seed is the reader's own, not the run's
([issue 044](https://github.com/khegazy/pde_metrics/blob/main/issues/044-synthetic-ensemble-ignores-the-run-seed.md)).

## What the evaluation sees

- **Periodic axes.** Every axis is periodic, so every metric and degradation runs on it.
- **Ensemble degradations.** On an ensemble dataset the degradations damage the members and
  never the truth.
- **Deterministic metrics** score the ensemble mean.
