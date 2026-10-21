# Rollouts and long-time dynamics

A surrogate of a time-dependent PDE is usually used autoregressively: each prediction is fed
back in as the input for the next step, so the model runs on its own outputs for hundreds or
thousands of steps. In a chaotic system two trajectories that start infinitesimally close
separate exponentially, at a rate set by the leading Lyapunov exponent. After a few Lyapunov
times, the e-folding times of that separation, even a perfect model has decorrelated from
the reference trajectory, and a pointwise comparison with it no longer says anything about
the model's quality. From then on the right comparison is of *invariants*: quantities that
every correct trajectory shares, such as long-time distributions, spectra and Lyapunov
exponents.

The ideas in this theme need a predicted trajectory rather than a single predicted frame.
The first two measure how long a rollout stays faithful and how fast it forgets its past. The
last two compare what the rollout settles into, as a statistical state and as a set of
coherent, time-periodic structures.

## Ideas in this theme

- [Valid prediction time](valid_prediction_time.md): how long a rollout stays within a
  declared error of the reference, measured in Lyapunov times.
- [Temporal autocorrelation](temporal_autocorrelation.md): how quickly a rollout forgets its
  own past compared with the reference, which exposes dynamics that evolve too slowly.
- [Invariant measure and attractor comparison](invariant_measure.md): long-time
  distributions, Lyapunov exponents and attractor dimension, which stay meaningful after
  decorrelation.
- [Modal decompositions and radiated sound](modal_decompositions.md): the energies,
  subspaces, frequencies and growth rates of coherent modes, and the sound a flow radiates.
