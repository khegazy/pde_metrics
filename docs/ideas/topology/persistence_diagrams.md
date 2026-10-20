# Persistence diagrams

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Sweep a threshold through a scalar field such as vorticity magnitude or density, and watch the
*sublevel set*, the region where the field lies below the threshold. Structures such as
connected regions and loops are born and die as the threshold moves, and each is recorded as a
point $(\text{birth}, \text{death})$ in the *persistence diagram*. Long-lived features lie far
from the diagonal, while noise hugs it. Two diagrams are then compared using the *bottleneck
distance*, the largest displacement in the best one-to-one matching between their points, or
using a Wasserstein distance defined on diagrams.

## Precedent

The stability theorem guarantees that a small perturbation of the field produces a
correspondingly small change in the diagram (Cohen-Steiner et al. 2007), so the distance
cannot blow up in the way $L^2$ does under a spatial shift. Off-the-shelf software
exists, including GUDHI, Ripser, giotto-tda and TTK (Tierny et al. 2018), so building it is a
pure implementation task.

There is direct precedent at Lawrence Berkeley National Laboratory (LBNL). Muszynski et al.
recognise atmospheric rivers in climate data using topological data analysis and machine
learning (Muszynski et al. 2019). Two details matter. First, the method is explicitly
threshold-free, and the authors argue on that basis that it "may be useful in evaluating model
biases" in atmospheric-river statistics, which is close to this project's use case. Second,
the ground-truth labels were produced by the TECA software, and the paper's acknowledgements
thank researchers in LBNL's Computational Research Division for their expertise in
computational mathematics. Experience with this method is close at hand.

## Pitfalls

- A persistence diagram is invariant to a great deal, including where in the domain the
  features actually sit. Similar topology does not imply correct amplitudes, shock speeds or
  energy transfer, so this metric belongs in a panel of metrics rather than standing alone.

## Rationale

*The team's judgement.* High priority, and first among the ideas to build next. Persistence
diagrams are the low-hanging fruit of topological data analysis: the theory is stable, the
software is mature, there is direct institutional precedent, and they are sensitive to
structure in a way that no norm is.

## References

- Cohen-Steiner, D., Edelsbrunner, H. & Harer, J. (2007). Stability of persistence diagrams.
  *Discrete & Computational Geometry* 37(1), 103–120.
  <https://doi.org/10.1007/s00454-006-1276-5>
- Muszynski, G., Kashinath, K., Kurlin, V., Wehner, M. & Prabhat (2019). Topological data
  analysis and machine learning for recognizing atmospheric river patterns in large climate
  datasets. *Geoscientific Model Development* 12(2), 613–628.
  <https://doi.org/10.5194/gmd-12-613-2019>
- Tierny, J., Favelier, G., Levine, J. A., Gueunet, C. & Michaux, M. (2018). The Topology
  ToolKit. *IEEE Transactions on Visualization and Computer Graphics* 24(1), 832–842.
  <https://doi.org/10.1109/TVCG.2017.2743938>
