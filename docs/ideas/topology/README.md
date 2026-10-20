# Topological data analysis

Topological data analysis summarises the shape of a field: which structures it contains, how
they connect, and how robust each one is as a threshold is varied. Comparing these summaries
measures whether a prediction has the right structures, which no norm is sensitive to in the
same way. The team's view is that one-parameter persistence diagrams are the
low-hanging fruit of this theme, because the stability theory is settled and off-the-shelf
software exists. The richer variants, multiparameter persistence and well groups, face
immature theory or tooling and are parked. Reeb graphs, Morse–Smale complexes and Jacobi sets
say more about where structures sit, and Jacobi sets are unusual in comparing two fields
directly.

## Ideas in this theme

- [Persistence diagrams](persistence_diagrams.md): record when each structure appears and
  disappears as a threshold sweeps through the field, and compare the records.
- [Multiparameter persistence](multiparameter_persistence.md): filter by two parameters at
  once, such as field value and spatial scale.
- [Well groups](well_groups.md): measure how robust the level sets of a field are to
  perturbation.
- [Reeb graphs and Morse–Smale complexes](reeb_graphs.md): skeletons of how level sets
  connect and of how the gradient flows, which locate structures in the domain.
- [Jacobi sets](jacobi_sets.md): the points where the gradients of two fields are parallel, a
  topological object built for comparing two fields.
