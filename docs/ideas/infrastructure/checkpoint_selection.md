# Selecting checkpoints by rollout

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A neural surrogate is usually validated *a priori*, one step ahead from a true input, but
deployed *a posteriori*, stepping forward autoregressively on its own outputs. The two see
different input distributions. Autoregressive sequence models have the same mismatch, called
*exposure bias*: training on true prefixes while inferring on the model's own outputs lets
errors compound, and scheduled sampling was introduced to close the gap (Bengio et al. 2015). Continued training can therefore lower the
one-step validation loss while the stability of the autoregressive rollout gets worse,
because the loss never sees the model's own outputs as inputs. The neural-PDE literature
documents the mechanism and its remedies: solver-in-the-loop training, which places the
numerical solver inside the training loop (Um et al. 2020); the pushforward trick, which
trains on the model's own perturbed outputs (Brandstetter, Worrall & Welling 2022); unrolling
more solver steps during training, with a documented trade-off between accuracy and stability
in the length of the unrolled horizon (List, Chen & Thuerey 2022); the finding that
neglecting low-amplitude, high-wavenumber information is the main cause of rollout divergence
(Lippe et al. 2023); and benchmarks that evaluate temporal stability, spectra and
distributions rather than one-step error (Kohl, Chen & Thuerey 2023).

This idea is a procedure for choosing a checkpoint, and deciding when to stop training, from
rollouts instead of from the one-step validation loss.

1. **Roll out.** At each candidate checkpoint, run $K$ autoregressive rollouts from held-out
   initial conditions for $N$ steps, with $N$ well beyond the decorrelation time. Report every
   horizon in Lyapunov times (the time over which nearby trajectories separate by a factor
   $e$) or in eddy-turnover times.
2. **Check admissibility.** Apply the
   [admissibility checks](../physics_invariants/admissibility_checks.md): no non-finite
   values or blow-up, positivity, conservation drift, divergence. A rollout
   that violates one is non-physical, and the procedure records the violation and does not
   let the checkpoint's other scores offset it.
3. **Score a panel of complementary metrics.**
   - the [valid prediction time](../dynamics/valid_prediction_time.md) and the time until
     correlation with the reference falls below a declared threshold;
   - the error in the [spectral energy flux](../turbulence_statistics/spectral_energy_flux.md),
     or, without a reference, whether the flux is constant and of the right sign across the
     inertial range;
   - the deviation from the
     [four-fifths law](../turbulence_statistics/four_fifths_law.md);
   - the built [increment_w1_by_separation](../../metrics/increment_w1_by_separation.md),
     or the [velocity-derivative skewness](../turbulence_statistics/derivative_skewness.md)
     with the gradient flatness;
   - the long-time spectrum error, restricted to the
     [wavenumber band](../basis_decompositions/spectral_band_error.md) the reference
     resolves.
4. **Select.** Choose the checkpoint by valid prediction time, or by an aggregation of the
   panel declared in advance, among checkpoints whose rollouts pass the admissibility
   checks.
5. **Diagnose exposure bias.** Record the epoch at which the one-step validation loss and the
   rollout panel start to move in opposite directions. An early divergence point is the
   signature of exposure bias, and the response it calls for is a change of training
   objective (pushforward, unrolled or solver-in-the-loop training, or a distributional or
   phase-aware loss) rather than an earlier stop.
6. **Keep an evaluation-only holdout.** A quantity used as a training loss ceases to be an
   independent validation metric. Some metrics are therefore reserved for evaluation and
   never enter any training loss; see [designing an evaluation](../evaluation_design.md).

## Precedent

The procedure is the field guide's own synthesis, and the guide labels it as such. Each of its
parts comes from the works cited above.

## Pitfalls

- It needs a trained surrogate and its saved checkpoints. The degradation ladder damages a
  stored reference and produces neither.
- It is expensive: $K$ rollouts of $N$ steps at every candidate checkpoint, each scored by
  several metrics, most of which are not built yet.
- Choosing among many checkpoints on many noisy scores risks selecting on noise. The
  scores need the intervals of [uncertainty on every metric value](metric_uncertainty.md),
  and the aggregation must be fixed before the scores are seen.
- Several panel members need a resolved inertial range and are not applicable to flows
  without one.

## Rationale

*From the field guide; the team has not yet set a priority.* The one-step validation loss is
computed on an input distribution the deployed surrogate never sees, so a checkpoint chosen
by it can roll out worse than an earlier one. Selecting by rollout measures the surrogate
on the distribution it is used on, and the exposure-bias diagnosis says whether to change
the training rather than only when to stop it. This is the setting in which the metrics of
this project would be used as a selection criterion for a foundation model.

## Keywords

exposure bias, a posteriori evaluation, autoregressive rollout stability, early stopping,
model selection, pushforward trick, solver in the loop, unrolled training, Goodhart's law.

## References

- Bengio, S., Vinyals, O., Jaitly, N. & Shazeer, N. (2015). Scheduled sampling for sequence
  prediction with recurrent neural networks. *Advances in Neural Information Processing
  Systems* 28. <https://arxiv.org/abs/1506.03099>
- Brandstetter, J., Worrall, D. & Welling, M. (2022). Message passing neural PDE solvers.
  *International Conference on Learning Representations*. <https://arxiv.org/abs/2202.03376>
- Kohl, G., Chen, L.-W. & Thuerey, N. (2023). Benchmarking autoregressive conditional
  diffusion models for turbulent flow simulation. <https://arxiv.org/abs/2309.01745>
- Lippe, P., Veeling, B. S., Perdikaris, P., Turner, R. E. & Brandstetter, J. (2023).
  PDE-Refiner: Achieving accurate long rollouts with neural PDE solvers. *Advances in Neural
  Information Processing Systems* 36. <https://arxiv.org/abs/2308.05732>
- List, B., Chen, L.-W. & Thuerey, N. (2022). Learned turbulence modelling with
  differentiable fluid solvers: physics-based loss functions and optimisation horizons.
  *Journal of Fluid Mechanics* 949, A25. <https://doi.org/10.1017/jfm.2022.738>
- Um, K., Brand, R., Fei, Y., Holl, P. & Thuerey, N. (2020). Solver-in-the-loop: learning
  from differentiable physics to interact with iterative PDE-solvers. *Advances in Neural
  Information Processing Systems*. <https://arxiv.org/abs/2007.00016>
