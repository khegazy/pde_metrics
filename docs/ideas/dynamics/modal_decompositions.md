# Modal decompositions and radiated sound

!!! note "Planned, not built"
    The idea on this page is not built yet. Its gap, cost, priority and owner are in the
    [table of all ideas](../README.md).

## What it is

A modal decomposition writes a sequence of snapshots of a field as a sum of a few spatial
patterns, *modes*, each with its own energy or its own frequency and growth rate. Comparing
the modes of a rollout with those of the reference compares the coherent, organised part of
the dynamics. Taira et al. give an overview of the methods (Taira et al. 2017). The guide
names four comparisons, and a fifth for flows that radiate sound.

1. **Proper orthogonal decomposition (POD).** POD finds the orthogonal modes that capture the
   most energy of the snapshots, ordered by their energies $\lambda_1\ge\lambda_2\ge\dots$
   (Berkooz, Holmes & Lumley 1993). The comparison has two parts. The first compares the
   modal energy spectrum $\{\lambda_n\}$ and its cumulative sum. The second compares the
   *subspaces* spanned by the leading $r$ modes of each, through the largest principal angle
   $\theta_{\max}$ between them:

    $$
    E_{\mathrm{POD}}=\sin\theta_{\max}\big(\hat U_r,\,U_r^{\mathrm{ref}}\big), \tag{1}
    $$

    where $\hat U_r$ and $U_r^{\mathrm{ref}}$ hold the leading predicted and reference modes.
    The principal angles are the angles between the best-aligned pairs of directions in the
    two subspaces, so (1) is zero when the subspaces coincide and one when some direction of
    one is orthogonal to the whole of the other. It is unaffected by the sign and order of
    the modes within each subspace.

2. **Dynamic mode decomposition (DMD).** DMD fits a linear map that advances one snapshot to
   the next and returns its eigenvalues and modes. Each eigenvalue in the complex plane gives
   a frequency and a growth or decay rate (Schmid 2010), and the predicted and reference
   eigenvalues are compared there.

3. **Spectral proper orthogonal decomposition (SPOD).** SPOD performs a POD at each frequency
   separately and so gives the modal energies frequency by frequency. It is related both to
   DMD and to resolvent analysis (Towne, Schmidt & Colonius 2018), which models coherent
   structures as the flow's amplified response to forcing (McKeon & Sharma 2010).

4. **Temporal spectra.** The power spectral density of a probe signal or a global quantity,
   estimated by Welch's method of averaging periodograms over short, windowed, overlapping
   segments (Welch 1967), with the window and overlap declared. For a flow that sheds
   vortices at a dominant frequency $f$, the error in the Strouhal number $St=fL/U$, with $L$
   a body length and $U$ the free-stream speed, is a single-number summary.

5. **Radiated sound.** An acoustic analogy rearranges the equations of motion into a wave
   equation whose source is computed from the unsteady near-field flow, so that the
   far-field sound follows from the flow without simulating the far field (Lighthill 1952).
   Ffowcs Williams and Hawkings extended it to sources on surfaces in arbitrary motion
   (Ffowcs Williams & Hawkings 1969), and Colonius and Lele review its computational use
   (Colonius & Lele 2004). The comparison is of the sound pressure level spectrum, the
   overall sound pressure level in decibels, and the far-field directivity. Because the
   sound depends on the unsteady sources in detail, it is a stringent test of whether a
   surrogate reproduces them.

All five need a time-resolved trajectory rather than single frames, and none needs the
rollout to stay aligned in phase with the reference.

## Pitfalls

- Modal energies alone are blind to the subspace: a model can match the POD energies while
  its modes span the wrong subspace, which is why (1) is reported beside them.
- The decompositions need many time-resolved snapshots, and their results depend on the
  number of snapshots and the sampling interval, which must be declared and matched between
  rollout and reference.
- They describe the coherent part of the dynamics and say little about small-scale
  turbulence, whose energy is spread over many modes.
- The radiated-sound comparison applies only to problems with an acoustic far field, and it
  requires a declared observer geometry.

## Rationale

*From the field guide; the team has not yet set a priority.* Modal comparisons test the
dynamics of coherent structures, frequencies, growth rates and dominant patterns, after a
rollout has decorrelated, and the radiated sound is a stringent test of the fidelity of the
unsteady sources. They connect surrogate evaluation to the established toolset of dynamical
systems and Koopman theory.

## Keywords

proper orthogonal decomposition, POD, principal angles, dynamic mode decomposition, DMD,
spectral POD, SPOD, resolvent analysis, Welch power spectral density, Strouhal number,
acoustic analogy, Ffowcs Williams–Hawkings, sound pressure level, directivity.

## References

- Berkooz, G., Holmes, P. & Lumley, J. L. (1993). The proper orthogonal decomposition in the
  analysis of turbulent flows. *Annual Review of Fluid Mechanics* 25, 539–575.
  <https://doi.org/10.1146/annurev.fl.25.010193.002543>
- Colonius, T. & Lele, S. K. (2004). Computational aeroacoustics: progress on nonlinear
  problems of sound generation. *Progress in Aerospace Sciences* 40, 345–416.
  <https://doi.org/10.1016/j.paerosci.2004.09.001>
- Ffowcs Williams, J. E. & Hawkings, D. L. (1969). Sound generation by turbulence and surfaces
  in arbitrary motion. *Philosophical Transactions of the Royal Society of London. Series A*
  264, 321–342. <https://doi.org/10.1098/rsta.1969.0031>
- Lighthill, M. J. (1952). On sound generated aerodynamically I. General theory. *Proceedings
  of the Royal Society of London. Series A* 211, 564–587.
  <https://doi.org/10.1098/rspa.1952.0060>
- McKeon, B. J. & Sharma, A. S. (2010). A critical-layer framework for turbulent pipe flow.
  *Journal of Fluid Mechanics* 658, 336–382. <https://doi.org/10.1017/s002211201000176x>
- Schmid, P. J. (2010). Dynamic mode decomposition of numerical and experimental data.
  *Journal of Fluid Mechanics* 656, 5–28. <https://doi.org/10.1017/S0022112010001217>
- Taira, K. et al. (2017). Modal analysis of fluid flows: an overview. *AIAA Journal* 55,
  4013–4041. <https://doi.org/10.2514/1.J056060>
- Towne, A., Schmidt, O. T. & Colonius, T. (2018). Spectral proper orthogonal decomposition
  and its relationship to dynamic mode decomposition and resolvent analysis. *Journal of
  Fluid Mechanics* 847, 821–867. <https://doi.org/10.1017/jfm.2018.283>
- Welch, P. D. (1967). The use of fast Fourier transform for the estimation of power spectra:
  A method based on time averaging over short, modified periodograms. *IEEE Transactions on
  Audio and Electroacoustics* 15, 70–73. <https://doi.org/10.1109/tau.1967.1161901>
