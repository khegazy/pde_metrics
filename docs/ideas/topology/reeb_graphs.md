# Reeb graphs and Morse–Smale complexes

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

Both objects are skeletons of a scalar field. The *Reeb graph* is a skeleton of level-set
connectivity: it records how the connected pieces of the level sets (the sets where the field
takes a given value) appear, merge, split and vanish as the value changes. The *Morse–Smale
complex* is a skeleton of the gradient flow: it divides the domain into cells within which
every path of steepest ascent starts at the same minimum and ends at the same maximum. Both
say more than a [persistence diagram](persistence_diagrams.md) about *where* structures are
located.

## Precedent

Both are implemented in the Topology ToolKit, TTK (Tierny et al. 2018).

## Pitfalls

- The metrics used to compare two such graphs are less standardised than those for persistence
  diagrams. They include interleaving distances, which measure how far the function values
  must be blurred before each graph maps into the other, and edit distances, which count the
  cost of the elementary changes that turn one graph into the other.

## Rationale

*The team's judgement.* Medium priority: the objects are implemented and locate structures
better than a persistence diagram does, but the distances for comparing them are less
standardised.

## References

- Tierny, J., Favelier, G., Levine, J. A., Gueunet, C. & Michaux, M. (2018). The Topology
  ToolKit. *IEEE Transactions on Visualization and Computer Graphics* 24(1), 832–842.
  <https://doi.org/10.1109/TVCG.2017.2743938>
