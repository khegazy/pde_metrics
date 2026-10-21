# Spectral coherence and phase error

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

While a rollout is still aligned in phase with the reference, two spectra say at which scales
the prediction has drifted. The *magnitude-squared coherence* between prediction $u$ and
reference $v$ in a wavenumber shell $k$ is

$$
\gamma^2(k)=\frac{\big|\langle \hat u(\mathbf{k})\,\hat v^{*}(\mathbf{k})\rangle_{k}\big|^2}
{\langle |\hat u(\mathbf{k})|^2\rangle_{k}\,\langle |\hat v(\mathbf{k})|^2\rangle_{k}}
\in[0,1], \tag{1}
$$

where $\langle\cdot\rangle_k$ averages over the modes in the shell, and over realizations or
times where those are available. It equals one when the prediction's modes in the shell are a
fixed multiple of the reference's, and falls toward zero as their relative phases become
random. The companion *phase-error spectrum* reports, for each band, a summary of the phase
difference $\Delta\phi(\mathbf{k})=\arg\big(\hat u(\mathbf{k})\,\hat v^{*}(\mathbf{k})\big)$,
such as its mean absolute value.

Together they localise the wavenumber at which phase decoherence begins. In practice that is
typically the high wavenumbers first. PDE-Refiner identifies the neglect of non-dominant
spatial frequencies, usually the low-amplitude high wavenumbers, as the primary cause of
rollout divergence in neural PDE solvers (Lippe et al. 2023), and the coherence spectrum
shows that process scale by scale.

The built [spectrum_l2](../../metrics/spectrum_l2.md) compares only the amplitudes in each
shell and is blind to phase; the coherence is its phase-sensitive complement.
[Error by wavenumber band](spectral_band_error.md) mixes the two, since a mode-by-mode
difference is sensitive to both amplitude and phase.

## Pitfalls

- The coherence is meaningful only before global decorrelation. Once the whole rollout has
  decorrelated from the reference it is near zero at every wavenumber and carries no further
  information; the [valid prediction time](../dynamics/valid_prediction_time.md) and
  comparisons of the [invariant measure](../dynamics/invariant_measure.md) take over.
- By construction (1) is insensitive to amplitude: a prediction whose modes are all scaled
  by the same factor has coherence one. It must be read beside an amplitude comparison.
- Without the average in (1), a single mode always has coherence one, so the shells must
  hold enough modes, or the comparison enough realizations, for the estimate to mean
  anything; the lowest shells hold few modes.

## Rationale

*From the field guide; the team has not yet set a priority.* The coherence localises the
wavenumber where phase decoherence begins, which is the mechanism PDE-Refiner identifies as
the cause of rollout divergence. The guide lists it among the most sensitive metrics both for
high-wavenumber spectral collapse and for phase decoherence with an intact spectrum.

## Keywords

magnitude-squared coherence, cross-spectrum, phase-error spectrum, phase decoherence,
spectral bias, PDE-Refiner.

## References

- Lippe, P., Veeling, B. S., Perdikaris, P., Turner, R. E. & Brandstetter, J. (2023).
  PDE-Refiner: Achieving accurate long rollouts with neural PDE solvers. *NeurIPS* 36.
  <https://arxiv.org/abs/2308.05732>
