# How a metric that compares curves reports its result

**Category:** method
**Priority:** high — it blocks seven of the planned metrics whose mathematics is otherwise settled
**Status:** open, needs an owner decision

## Context

Seven ideas in `docs/ideas/` compare a *curve* (a function of separation, wavenumber, threshold
or filter size) between the prediction and the reference, or report several separate numbers.
The harness records one number per (metric, field, frame, severity level). The decorator already
accepts `returns="vector"`, and the pipeline expands a vector into one row per component with a
`component` column (`fmeval/pipeline.py`), but no metric uses it and nothing reports it:
[012](012-vector-valued-metrics.md) records that no renderer consumes vector output and that the
analysis treats every component as an independent scalar.

The one curve comparison already built, `spectrum_l2`, reduces two radial energy spectra to one
number, the relative L2 distance between them.

| Idea | What it compares | What its page says about a single number |
|---|---|---|
| [Increment W1 at every separation](../docs/ideas/optimal_transport/gradient_pdf_w1.md) | W1 between increment distributions, one value per separation | "A single value pooled over separations hides which scale failed; the per-separation curve is what localises it" |
| [Structure functions](../docs/ideas/turbulence_statistics/structure_functions.md) | $S_p(\ell)$ for several orders $p$, and fitted exponents $\zeta_p$ | compare curves "order by order" and the exponents; the fit range "must be fixed by the evaluator" |
| [Spectral energy flux](../docs/ideas/turbulence_statistics/spectral_energy_flux.md) | $\Pi(k)$ | "Report the error of the curve $\Pi(k)$ across the inertial range" |
| [Minkowski functionals](../docs/ideas/topology/minkowski_functionals.md) | area, boundary length and Euler characteristic as functions of the threshold | "the metric compares the predicted curves with the reference's" |
| [Delta-variance](../docs/ideas/basis_decompositions/delta_variance.md) | $\sigma_\Delta^2(l)$ | "compares the predicted and reference Δ-variance curves, or the slopes fitted to them" |
| [Error by wavenumber band](../docs/ideas/basis_decompositions/spectral_band_error.md) | three band errors (The Well, Ohana et al. 2024, Appendix E.3) | "reported separately in each band" |
| [Spectral coherence](../docs/ideas/basis_decompositions/spectral_coherence.md) | $\gamma^2(k)$ and a phase-error spectrum | "localise the wavenumber at which phase decoherence begins" |

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is
decided by a person, not settled by whoever implements the metric. The repository's own rule
points two ways here. Reporting a metric "in its standard literature form" and adapting the
harness to it argues for curves and per-band numbers (vector output). The precedent of
`spectrum_l2` argues for one scalar per comparison. Each choice changes what the ladder statistics
(rank correlation, damage, sensitivity) are computed on.

## Decision needed

One of, possibly per idea:

1. **One number per comparison, as `spectrum_l2` does.** The relative L2 distance between the two
   curves over a fixed, declared set of points (separations, thresholds, filter sizes,
   wavenumbers). Cheap and uniform; it gives up the per-scale localisation several pages say is
   the point.
2. **Vector output.** Build [012](012-vector-valued-metrics.md) first (a store for curves, and a
   renderer that overlays them), report the curve, and register a scalar summary beside it for
   the ladder statistics. This is a harness change and runs alone, before these metrics.
3. **One registered metric per component** where the components are few and named, as for the
   three wavenumber bands (`spectral_band_error_low`, `_mid`, `_high`), sharing one function.

Recommendation, for the decision rather than in place of it: option 1 for the five curve
comparisons, where it follows a built precedent and the curve itself is a diagnostic that option 2
can add later; option 3 for the three named bands; and spectral coherence held until option 2
exists, because its page's purpose is the wavenumber where decoherence begins, which a single
distance does not report.

## Related

Found while screening `docs/ideas/` for agent-built metrics (2026-10-23); written up 2026-10-26.
