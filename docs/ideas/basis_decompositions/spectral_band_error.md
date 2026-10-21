# Error by wavenumber band

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

The wavenumbers of the domain are split into a few bands, typically low, intermediate and
high, and the error between prediction $u$ and reference $v$ is reported separately in each
band. This localises an error by scale. The Well defines the binned spectral mean squared
error as the mean squared error after band-pass filtering both fields (Ohana et al. 2024,
Appendix E.3):

$$
\mathrm{BSMSE}_{\mathcal{B}}(u,v)=\big\langle \lvert u_{\mathcal{B}}-v_{\mathcal{B}}\rvert^{2}
\big\rangle,\qquad u_{\mathcal{B}}=\mathcal{F}^{-1}\big[\mathcal{F}[u]\,
\mathbf{1}_{\mathcal{B}}\big], \tag{1}
$$

where $\mathcal{F}$ is the discrete Fourier transform and $\mathbf{1}_{\mathcal{B}}$ is one
on the wavenumbers in band $\mathcal{B}$ and zero elsewhere. Its three bands partition the
wavenumber magnitudes evenly on a logarithmic scale. The normalised form divides each band's
error by the reference's energy in that band, so that a band carrying little energy still
contributes on the same footing as an energetic one. PDEBench's Fourier-space error, fRMSE,
does the same with low, middle and high bands of radial wavenumber (Takamoto et al. 2022).

The reason to split by band is that a pointwise error weights each wavenumber by its error
energy. By Parseval's theorem, on a periodic domain $\Omega$,

$$
\frac{1}{|\Omega|}\int_\Omega |u(\mathbf{x})-v(\mathbf{x})|^2\, d\mathbf{x}
= \sum_{\mathbf{k}} \big|\hat u(\mathbf{k})-\hat v(\mathbf{k})\big|^2 . \tag{2}
$$

In an inertial range the energy spectrum falls as $E(k)\sim k^{-5/3}$, so the small scales
carry little energy, and a model can erase the entire high-wavenumber range while
incurring a negligible total error. Neural networks compound this by fitting low frequencies
first, a tendency known as spectral bias or the frequency principle (Xu et al. 2020). The
band-normalised error exposes exactly this high-wavenumber collapse.

The built [spectrum_l2](../../metrics/spectrum_l2.md) compares whole energy spectra, the
amplitudes of the modes summed over shells, and is blind to phase. The band error in (1)
instead differences the complex Fourier coefficients mode by mode, so by (2) it is the
pointwise error of the band-pass-filtered fields and is sensitive to phase. The field guide
calls the family phase-blind; that holds for a band comparison of energies, not for (1) or
for PDEBench's fRMSE, whose reference implementation also differences the complex
coefficients.

**The bands are a property of the reference.** A band is meaningful only where the reference
itself is trustworthy, its resolved support, below the wavenumbers where its own numerical
dissipation or grid cutoff dominates. The band edges are therefore declared once from the
reference and fixed in the evaluator, never tuned per model.

## Pitfalls

- Because (1) is a pointwise error within each band, it loses its meaning once a rollout has
  decorrelated from the reference, exactly as the total error does. After decorrelation the
  comparison that remains meaningful is between band energies, restricted to the
  reference-resolved band (see [invariant measure](../dynamics/invariant_measure.md)).
- A comparison of band energies alone is phase-blind and is passed by a Gaussian random field
  with the reference spectrum, such as the
  [gaussian_impostor](../../degradations/gaussian_impostor.md).
- Band edges set from a resolution the reference does not actually resolve turn the
  reference's own error into a model's apparent error.

## Rationale

*From the field guide; the team has not yet set a priority.* Splitting the error by band
localises it by scale and directly targets the most common way a surrogate trained with a
pointwise loss fails, the loss of low-energy small scales. The guide lists band-limited
spectral error as the most sensitive metric for high-wavenumber collapse and as part of the
minimal panel for smooth surrogates and super-resolution.

## Keywords

fRMSE, binned spectral MSE, band-pass error, spectral bias, frequency principle,
scale-resolved error.

## References

- Ohana, R. et al. (2024). The Well: a large-scale collection of diverse physics simulations
  for machine learning. *NeurIPS*. <https://arxiv.org/abs/2412.00568>
- Takamoto, M. et al. (2022). PDEBench: an extensive benchmark for scientific machine
  learning. *NeurIPS Datasets & Benchmarks*. <https://arxiv.org/abs/2210.07182>
- Xu, Z.-Q. J., Zhang, Y., Luo, T., Xiao, Y. & Ma, Z. (2020). Frequency principle: Fourier
  analysis sheds light on deep neural networks. *Communications in Computational Physics*
  28, 1746–1767. <https://doi.org/10.4208/cicp.oa-2020-0085>
