# Baseline predictors

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A surrogate's score on a metric means little on its own. It becomes informative beside the
scores of simple predictors run on the same data and scored by the same metrics. This idea
is a fixed set of such baseline predictors, from the trivial to the standard neural
architectures:

1. **Persistence**: the next state equals the current one, $\hat U^{n+1} = U^n$.
2. **Interpolation**: for example, a coarse input interpolated onto the fine grid, the floor
   for super-resolution.
3. **A coarse numerical solver**: the trusted solver run at lower resolution, with its cost
   stated beside its score.
4. **Standard neural architectures**: a U-Net or residual network; a Fourier neural operator,
   which learns the solution operator through convolutions applied in Fourier space (Li et
   al. 2021); DeepONet, which learns an operator as the product of a network acting on the
   input function and a network acting on the query point (Lu et al. 2021); and
   MeshGraphNets, a graph network acting on the simulation mesh (Pfaff et al. 2021).
5. **A physics-informed baseline and a generative baseline**, where the task calls for them.

Any metric can then also be reported as a *skill score* relative to a baseline,
$1 - S_{\text{model}} / S_{\text{baseline}}$ for a score $S$ where lower is better, which is
positive when the model beats the baseline.

These are different from what the repository already has. The
[Gaussian impostor](../../degradations/gaussian_impostor.md) is a canary for *metrics*: it
tests whether a metric can be fooled. Baselines calibrate the scores of *surrogates*. The
trusted solver planned under the
[reference and solver predictor](degradation_ladder_reference.md) would also serve as the
coarse-solver baseline.

## Precedent

McGreivy and Hakim surveyed articles claiming that a machine-learning solver for a
fluid-related partial differential equation outperforms a standard numerical method, and
found that 79% of them (60 of 76) compared against a weak baseline (McGreivy & Hakim 2024).

## Pitfalls

- A coarse-solver baseline is informative only with its cost beside it, since a solver can
  always be made more accurate by spending more compute.
- A neural baseline that is poorly tuned is itself a weak baseline. Training several
  architectures well is the expensive part of this idea.
- Persistence is a strong baseline for a slowly evolving flow and a weak one for a rapidly
  evolving flow, so its meaning depends on the time step.

## Rationale

*From the field guide; the team has not yet set a priority.* The guide lists these baselines
as a reporting requirement for any evaluation of a surrogate, and the McGreivy and Hakim
survey shows that comparison against weak baselines is common enough to distort the
literature. Honest metrics and honest baselines are the same discipline.

## Keywords

baseline predictor, persistence forecast, skill score, weak baselines, neural operator
benchmark, Fourier neural operator, DeepONet, MeshGraphNets.

## References

- Li, Z., Kovachki, N., Azizzadenesheli, K., Liu, B., Bhattacharya, K., Stuart, A. &
  Anandkumar, A. (2021). Fourier neural operator for parametric partial differential
  equations. *International Conference on Learning Representations*.
  <https://arxiv.org/abs/2010.08895>
- Lu, L., Jin, P., Pang, G., Zhang, Z. & Karniadakis, G. E. (2021). Learning nonlinear
  operators via DeepONet based on the universal approximation theorem of operators. *Nature
  Machine Intelligence* 3, 218–229. <https://doi.org/10.1038/s42256-021-00302-5>
- McGreivy, N. & Hakim, A. (2024). Weak baselines and reporting biases lead to overoptimism
  in machine learning for fluid-related partial differential equations. *Nature Machine
  Intelligence* 6(10), 1256–1269. <https://doi.org/10.1038/s42256-024-00897-5>
- Pfaff, T., Fortunato, M., Sanchez-Gonzalez, A. & Battaglia, P. W. (2021). Learning
  mesh-based simulation with graph networks. *International Conference on Learning
  Representations*. <https://arxiv.org/abs/2010.03409>
