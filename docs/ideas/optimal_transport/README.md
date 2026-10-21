# Optimal transport and displacement-aware distances

A pointwise norm compares two fields cell by cell, so a sharp feature that is correct in
shape but slightly displaced is penalised twice: once where it should be and once where it
is. Transport distances instead measure how far mass must move to turn one field into the
other, so a small displacement costs a small amount. Two communities, seismic inversion and
weather verification, hit this wall before and solved it, and this theme imports their
solutions. Its central obstacle is that transport is defined for nonnegative quantities of
fixed total mass, which pressure and velocity are not.

Built already, and so not listed here: the Wasserstein distance between one-cell increment
distributions ([increment_w1](../../metrics/increment_w1.md)).

## Ideas in this theme

- [Wasserstein distance for horizontal displacement](wasserstein.md): the cost of moving one
  field onto the other, which grows with the size of a displacement instead of saturating.
- [Transport between signed fields](signed_field_transport.md): the four standard ways to
  apply transport to fields that take negative values or do not conserve their total.
- [Sliced Wasserstein distance](sliced_wasserstein.md): the average of cheap one-dimensional
  transport distances along many projections.
- [Entropic relaxation and Sinkhorn divergences](sinkhorn.md): a smoothed, differentiable
  approximation to transport, relevant once transport has proved useful.
- [Wasserstein distance between increment distributions at every
  separation](gradient_pdf_w1.md): transport between the distributions of increments at each
  separation, extending the built one-cell comparison to a curve over scale.
