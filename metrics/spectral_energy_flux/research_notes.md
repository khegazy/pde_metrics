# Research notes: spectral_energy_flux

This bundle was built by a metric-building agent from the idea page
`docs/ideas/turbulence_statistics/spectral_energy_flux.md`, which the build narrowed and renamed
to [energy_transfer_checks.md](../../docs/ideas/turbulence_statistics/energy_transfer_checks.md).
The work is pull request #26, built on 2026-10-30, reworked in an adversarial review round on
2026-10-30, given a CI waiver on 2026-10-31 and merged on 2026-10-31. This file holds what the
builder and the reviewer read, tried and concluded that the card does not carry, condensed from
their work log and records. The card is the source of truth for what the metric is, and where the
two disagree the card wins. The coding record is in [code_notes.md](code_notes.md).

## Summary

The bundle compares the spectral energy flux curves $\Pi(K)$ of a candidate velocity and the
reference at the octave wavenumbers, and registers their relative L2 distance (card, Definition).
The first version used the incompressible advective form. The review showed that on a divergent
velocity this form leaves a non-conservative residual, $-\langle(\nabla\cdot u)\lvert u\rvert^2\rangle/2$,
which on `kinet_re5e4` made up much of the curve. The curve is now Aluie's (2013) sharp-filter
"unsubtracted flux" at uniform density, which sums to zero over all modes. The metric is not
phase-blind: the Gaussian impostor scores damage 1.9. Two pre-registered axes, `highpass_ideal`
and `lowpass_ideal`, are contradicted on velocity, because each keeps only two usable strengths.
The main caveats are four. The velocity-only flux omits baropycnal work and pressure dilatation
([judgements/003](../../judgements/003-spectral-flux-from-velocity-alone.md)). The summary and the
octave sampling are conventions
([issues/105](../../issues/105-spectral-energy-flux-summary-is-a-convention.md)). The curve's
dominance is low, so the summary decides the order of neighbouring strengths in most frames. And
part of the high-octave flux of noisy or coarsened fields is aliasing.

## Sources

Equation numbers are those of the arXiv copies. Every source was first read as HTML on ar5iv
through a fetch tool that answers through a summarising model, because no PDF renderer was
available. In the review the agent downloaded the arXiv TeX sources of four papers and re-checked
the cited equations there. The equation environments were counted to confirm the numbering.

| Source | How it was read | Locator | What it gave | Where it is used |
|---|---|---|---|---|
| Alexakis & Biferale 2018, Physics Reports 767-769, 1-101 (arXiv:1808.06186), DOI 10.1016/j.physrep.2018.08.001 | Full text (first through the summarising fetch, three times with offsets; Eqs. 16, 18 and 21-22 checked in the TeX source in the review) | Eq. 16, Eq. 18, Sect. 2.3; Eqs. 21-22; Sect. 3.2.1 | The energy flux through $k$ is $\Pi_E(k) = \sum_{k'<k} T(k') = \langle u^{<k}\cdot(u\cdot\nabla)u\rangle$, with $u^{<k}$ the velocity keeping only the modes inside the sphere of radius $k$ (Eqs. 16 and 18). Positive $\Pi_E$ is a forward cascade (Eq. 22), and negative an inverse one (Eq. 21). In forced 2D turbulence energy goes to large scales with $\Pi_E = -\epsilon_{in}$, while enstrophy goes forward (Sect. 3.2.1, attributed to Kraichnan 1967). The review's 2D discussion assumes forcing and large-scale drag and says nothing about decaying 2D flow. The orchestrator checked Eq. 18 in the arXiv PDF. | `metric.py`, card, `refs.bib` |
| Alexakis & Biferale 2018, the same review | Secondary (summarising fetch only; changed from full text in the review) | Eqs. 53-55, Sect. 3.2.1 | The 2D enstrophy flux $\Pi_Z(k) = \langle w^{<k}(u\cdot\nabla)w\rangle$ (Eq. 53), the forward-cascade counterpart of the energy flux in 2D. The summariser reported a sign inconsistency between Eq. 54 ($\Pi_Z$ positive in the forward range) and the text ($-\zeta_{in}$), which was not checked. | Proposal only (Open questions) |
| Aluie 2013, Physica D 247(1), 54-65 (arXiv:1012.5877), DOI 10.1016/j.physd.2012.12.009 | Full text. The first read was through a summarising fetch truncated at 100,000 of 138,791 characters (Sects. 4.1-4.3 fell within it). It was re-read in full in the TeX source of arXiv:1012.5877v2 in the review. | Eq. 13 (Sect. 3.1); Eq. 14 (Sect. 4.1); Eq. 15 (Sect. 4.2); Sect. 4.3; Eq. 21; the unnumbered display of Sect. 4.1 | Eq. 13 is the large-scale kinetic-energy budget. Eq. 14 is deformation work, $\Pi_\ell = -\bar\rho\,\partial_j\tilde u_i\,\tilde\tau(u_i,u_j)$, "similar to its incompressible counterpart except that the strain is not traceless" (Sect. 4.1). Eq. 15 is baropycnal work, which "vanishes in the absence of density variations" (Sect. 4.2). Large-scale pressure dilatation vanishes at every point in the incompressible limit (Sect. 4.3). Eq. 21 is the sharp spectral filter, $\lvert k\rvert \le K$. Sect. 4.1 gives the compressible unsubtracted flux for the sharp filter, $\tilde u_i\,\overline{\partial_j(\rho u_i u_j)} - \tfrac12\lvert\tilde u\rvert^2\,\overline{\partial_j(\rho u_j)}$, which differs from Eq. 14 by a total gradient and whose space average vanishes at $K_{max}$. At uniform density this is the flux the bundle computes. | `metric.py`, card, `refs.bib`, judgement 003 |
| Aluie 2011, Physical Review Letters 106(17), 174502 (arXiv:1101.0455), DOI 10.1103/PhysRevLett.106.174502 | Full text (first through a summarising fetch; Eqs. 1-5 checked in the TeX source in the review; Eqs. 12 and 15-17 not re-checked) | Eqs. 3-5, Eq. 12, Eqs. 15-17 | The coarse-grained budget (Eq. 3) moves kinetic energy across scale $\ell$ only through deformation work (Eq. 4) and baropycnal work (Eq. 5). With a pressure-dilatation cospectrum decaying faster than $1/k$ (Eq. 15), the mean flux is constant over an inertial range (Eq. 17). The letter says incompressible turbulence "may be viewed as a limiting case" and that its density condition is "readily satisfied in incompressible or nearly-incompressible flows". These are remarks, not a low-Mach derivation. | Card, `refs.bib`, judgement 003 |
| Aluie, Li & Li 2012, Astrophysical Journal Letters 751(2), L29 (arXiv:1107.5771), DOI 10.1088/2041-8205/751/2/L29 | Full text (first through a summarising fetch; Table 1 and the captions of Figs. 2-3 checked in the TeX source in the review; equation numbers not re-checked) | Eqs. 9-16, Figs. 2-3, Table 1 | 3D periodic simulations at rms Mach 0.43-0.44 (forced, isothermal) and decaying ideal-gas runs. The pressure-dilatation cospectrum falls faster than $1/k$ (fitted slopes $-1.88$ and $-1.61$, Fig. 2), and the cumulative pressure dilatation reaches a plateau (Fig. 3), so the kinetic-energy flux is approximately constant beyond a transitional conversion range. The evidence is three-dimensional and subsonic to transonic, and says nothing about 2D flow. | Card, `refs.bib`, judgement 003 |
| Kraichnan 1967, Physics of Fluids 10(7), 1417-1423, DOI 10.1063/1.1762301 | Secondary (through Alexakis & Biferale Sect. 3.2.1; the paywalled original was not opened) | none | 2D turbulence conserves energy and enstrophy, so energy cascades to large scales and enstrophy to small ones. The consequence for this metric is that no sign or constancy test tuned to three dimensions was built. | Card, `refs.bib` |
| Kritsuk 2018, arXiv:1802.08228, "Energy transfer and spectra in simulations of two-dimensional compressible turbulence" | Secondary (one summarising fetch on ar5iv; recorded as full text at first, corrected in the review) | Sect. 3, Fig. 6, Table 1 | Forced 2D compressible turbulence at Mach 0.33-0.54 shows a flux loop: solenoidal kinetic energy cascades inversely while acoustic energy goes forward. The kinetic spectrum there is the density-weighted cospectrum $P(\rho u, u; k)/2$, not a velocity-only spectrum, and the fluxes follow a formalism of Banerjee & Kritsuk (2017) that the paper does not restate. This is the nearest published setting to kinet (2D, weakly compressible), and it shows that at finite Mach number a velocity-only flux misses the exchange with potential energy. | The EXP proposal (Open questions) |
| Falkovich & Kritsuk 2017, Physical Review Fluids 2(9), 092603(R), DOI 10.1103/PhysRevFluids.2.092603 | Abstract (from search results) | none | In steady forced 2D compressible turbulence at finite Mach number, a box-size pair of long-lived vortices linked by shocks forms. Energy goes to large scales through the vortices and returns to small-scale dissipation through acoustic waves, a flux loop. A candidate benchmark for a compressible energy-transfer metric once data at higher Mach number exist. | The EXP proposal (Open questions) |
| Germano, Piomelli, Moin & Cabot 1991, Physics of Fluids A 3(7), 1760-1765, DOI 10.1063/1.857955; Meneveau & Katz 2000, Annual Review of Fluid Mechanics 32, 1-32, DOI 10.1146/annurev.fluid.32.1.1 | Not opened | none | The idea page's Germano-identity check (its Eq. 2) tests a learned subgrid closure's stresses at two filter widths. It does not apply to this metric, because no prediction in the repository carries a subgrid stress and the built metric compares the resolved flux of two fields. Both references stay on the narrowed idea page; neither is cited by the bundle. | Narrowed idea page |

## Method choices

- **Velocity alone, constant density**
  ([judgements/003](../../judgements/003-spectral-flux-from-velocity-alone.md)). The options were
  to wait for [issues/096](../../issues/096-several-fields-handed-to-one-metric.md) and pressure,
  or to build the velocity-only flux. The second was taken because Aluie (2013, Sects. 4.1-4.3)
  shows that the omitted terms vanish, or reduce to the kept one, at uniform density. This is
  source-backed, but the decision to proceed is the agent's. The judgement first gave kinet's
  density variation as 1.8e-4 rms and argued that the omitted terms are small by construction;
  the review corrected both (Review round, the dilatational residual and the density figure).
- **The form of the flux.** The first version used the advective form $(u\cdot\nabla)u$, the one
  the cited definition uses (Alexakis & Biferale Eq. 18; the idea page's Eq. 1). It stated on the
  card that for a divergent velocity the total is $-\langle\nabla\cdot u\,\lvert u\rvert^2\rangle/2$
  rather than zero. The review replaced it with Aluie's sharp-filter unsubtracted flux at uniform
  density. Three options were weighed.
  1. Keep the advective form and correct the documentation. That would have kept a
     non-conservative residual that measured as most of the curve on kinet.
  2. Implement Eq. 14 literally per octave. It gives the same space average at more cost.
  3. Use the unsubtracted flux, the form the source gives for the sharp filter. This was taken.

  Because the new form is source-backed, judgement 003 was revised in place rather than a new
  judgement written.
- **No dealiasing.** The metric is a diagnostic of a given field, not a time step, and truncating
  modes would change the field being judged. This is the agent's own choice, stated as a
  limitation. The review kept it after measuring the aliasing (Review round, the noise reading).
- **Two dimensions.** Only a curve comparison against the reference is registered, with no sign
  or constancy test. In 2D energy moves to large scales (Kraichnan 1967, through Alexakis &
  Biferale Sect. 3.2.1), and kinet is decaying and unforced.
- **Octave sampling and the relative L2 summary**, both conventions without a source, recorded in
  [issues/105](../../issues/105-spectral-energy-flux-summary-is-a-convention.md). Octaves match
  `increment_w1_by_separation` and weigh each octave of scale once. Because $\Pi$ is cumulative,
  no transfer inside the sampled range is dropped. The summary is the one `spectrum_l2` uses for
  the spectrum. The alternatives considered were a sign-disagreement fraction (Rejected
  formulations) and the largest normalised gap. Why the curve could not be sampled at every shell
  is a harness limit (code_notes.md, Implementation).
- **The companion is a one-field curve**, the candidate's $\Pi$, not a comparison curve, because
  the literature plots $\Pi(k)$ itself.
- **`fields = ("velocity",)`**, because the flux is defined on the velocity.
- **The NaN bound** on a reference curve at round-off is the agent's own. Its form is in
  code_notes.md.
- **Narrowing the idea page rather than deleting it.** The brief spoke of deleting the page, but
  `docs/recipes/add-a-metric.md`, step 7.3, says to narrow it when the metric covers only part of
  the idea. The built metric covers only the curve comparison against a reference. The compressible
  budget, the local (coarse-grained) flux, the reference-free constancy check, the backscatter sign
  fraction and the Germano identity remain. The page was renamed because
  `tests/test_documentation.py` refuses an idea page named after a built metric.
- **Pre-registration** (in commit 324e7f5 on #26, which added `metric.py`, before any full-ladder
  run, and unchanged since). Ten axes were declared to follow with direction +1: `gaussian_blur`,
  `box_blur`, `median_blur`, `lowpass_ideal`, `lowpass_butterworth`, `highpass_ideal`,
  `highpass_butterworth`, `coarsen`, `coarsen_bandlimited` and `additive_noise`. The reason for
  each was that the degradation removes or adds triads that carry the flux. Blind: `translate_x`.
  Fields `velocity`, lower is better, units "dimensionless". The reduction is the relative L2
  distance at the octaves, with no field map. No sign test could be pre-registered, because the
  reference's direction of transfer is not fixed on this trajectory (Evidence runs).

## Rejected formulations and negative results

- **The advective form on a divergent velocity**, replaced in the review (Method choices; Review
  round, the point about the uniform-density limit).
- **A direction-of-transfer disagreement fraction**: the fraction of octaves where the two curves
  have opposite signs. It generalises the idea page's forward-cascade backscatter fraction to 2D,
  but it needs a fixed round-off threshold.
- **A comparison of the shell-by-shell transfer $T(k)$** instead of the cumulative flux. It would
  localise gains and losses rather than crossings.

  Both of these can be computed from the stored companion curves. They were not built and are
  written up in
  [MTR-spectral_energy_flux-flux-sign-agreement](../../proposals/MTR-spectral_energy_flux-flux-sign-agreement.md).
- **A reference-free reading.** The idea page's reference-free form (a flux constant and equal to
  the dissipation rate) and its backscatter sign fraction both presume a forward cascade with an
  inertial range. `kinet_re5e4` is two-dimensional, unforced and decaying, so it has no forcing
  scale, and neither form has a target on it.
  [issues/085](../../issues/085-inviscid-invariants-need-other-data.md) makes the same point for
  the 2D cascade checks. Both forms stay on the narrowed page with this stated.

## Evidence runs

1. **Smoke run** `results/spectral_energy_flux_1793354039`, on `kinet_re5e4_dev` with
   `degradation=quick`. It produced 1000 rows in 36 s. Values were finite, and the impostor scored
   about 0.98 there (dev data, not physical).
2. **First full run** `results/spectral_energy_flux_1793354140`, at commit 324e7f5 on #26, 1096 s.
   Its `run_meta` records `git.dirty: true`, because documentation was edited while it ran and
   `evaluate.py` reads the git status at the end. It was not used. The reviewer found that its rows
   agree exactly with the clean run's (9499 rows, largest absolute difference 0).
3. **First evidence run** `results/spectral_energy_flux_1793355291`, at commit 2492966 on #26 with
   a clean tree, 9499 rows in 777 s. It used the advective form and is superseded.
   - Every declared axis had direction +1 and $\rho = 1$. `rho_ci_lo` was 1 everywhere except on
     `highpass_ideal`: on velocity two of its four levels are no-ops or repeats, leaving two
     strengths, so `rho_ci_lo` was $-1$ (with $\rho$ 1 and 0.627 of frames in order). This
     contradicts the declaration and was left standing, as the brief requires. `translate_x` and
     `translate_subpixel` were in velocity's `blind_axes`.
   - The impostor scored damage 2.35, so the metric is not phase-blind.
   - The curve's dominance was 0 to 0.342 on every degradation of velocity, against at least 0.92
     on most degradations for `increment_w1_by_separation`
     ([issues/098](../../issues/098-increment-w1-registered-number-is-a-convention.md)). The
     harsher strength's curve rarely moved further at every octave, so the registered summary
     decides the order of neighbouring strengths in most frames. This went into issue 105.
   - **The reference's own flux** (from the clean rows of `companions.csv`). It was negative
     (energy moving to larger scales) at octaves 1, 2, 4 and 8 in 0.683, 0.696, 0.702 and 0.634 of
     frames, and at octaves 16-128 in only 0.55-0.57. Its median was $-5.7\times10^{-9}$,
     $-7.4\times10^{-9}$, $-4.0\times10^{-9}$ and $-2.3\times10^{-9}$ at octaves 1-8. Beyond octave
     16 the curve was flat at a median 19% of its largest magnitude. The agent interpreted that
     plateau, without verifying it, as the compressibility residual
     $-\langle\nabla\cdot u\,\lvert u\rvert^2\rangle/2$ rather than transfer, and the review
     confirmed the interpretation (Review round, the dilatational residual). The direction of transfer is therefore not fixed on
     this decaying 2D trajectory, so no sign test could be pre-registered.
   - The reviewer reproduced every card number from this run (the largest damages, the impostor,
     the fractions in order, the dominance, the sign fractions and the plateau median).
4. **Evidence run after the review** `results/spectral_energy_flux_1793391588`, at commit c33f769
   on #26 with a clean tree, run as `python evaluate.py metrics=[spectral_energy_flux]
   dataset=kinet_re5e4 dataset.time.start=2000 dataset.time.reduction=50 paths.data_url=null`. It
   produced 9499 rows in 1312 s, of which 640 s was the metric and 662 s the degradations.
   - `lowpass_ideal` changed from passed to **not passed**: `rho_ci_lo` is $-1$ with two usable
     strengths. `highpass_ideal` still fails in the same way.
   - `lowpass_butterworth` passes with $\rho$ 0.5 and `rho_ci_lo` 0.5, below the advisory 0.90,
     which is reported, not failed.
   - Every other declared axis passes, and `translate_x` is still blind.
   - The impostor's damage is now 1.9.
   - On the clean rows the reference's flux is negative at octaves 1-8 in 67%-80% of frames and
     positive at octaves 32-128 in at least 90%. $\Pi(128)$ is round-off: the median of
     $\lvert\Pi(128)\rvert/\max\lvert\Pi\rvert$ is $1.4\times10^{-6}$, against 0.189 before.

The card now cites `results/comparison_1793657627` (card, Results), a later multi-metric refresh
outside this build's records. Some of its numbers differ from those above; for example, it gives
the dominance as 0 to 0.168.

## Corrections to the rest of the repository

- **The idea page, narrowed and renamed** to
  [energy_transfer_checks.md](../../docs/ideas/turbulence_statistics/energy_transfer_checks.md).
  Every reference of the old page is either in the bundle's `refs.bib` or still on the narrowed
  page (Germano et al. 1991; Meneveau & Katz 2000). Its pitfalls "noisy on coarse grids" (needing
  phase-resolved fields and resolved gradients) and "costs more than the spectrum" were carried
  into the card. The first became the aliasing and few-modes limitations; the second is measured
  by the run's cost column. The page's Eq. 1 is implemented through Alexakis & Biferale Eq. 18,
  which is identical up to Parseval. At the orchestrator's request, two pitfalls were added to the
  narrowed page, labelled as added by this agent: the reference-free and backscatter forms have no
  target on 2D, decaying kinet (Rejected formulations); and the sign of Aluie's Eq. 13 (Review
  round, the sign in Aluie's Eq. 13). The README row and the theme bullet were updated. Links to the old page
  were rewritten in `docs/ideas/background.md`, `evaluation_design.md`,
  `basis_decompositions/bispectrum.md`, `infrastructure/checkpoint_selection.md`,
  `physics_invariants/admissibility_checks.md`, `physics_invariants/helmholtz_split.md` and
  `turbulence_statistics/inviscid_invariants.md`. The reviewer found that they follow the existing
  link convention.
- **kinet's density variation.** AGENTS.md (section 4) said kinet's density is "1.0 ± 1.8e-4". In
  the evidence window of `kinet_re5e4`, the density's rms over its mean is $2.13\times10^{-3}$ at
  frame 2000, $6.71\times10^{-3}$ at 6000 and $6.61\times10^{-3}$ at 10000, and its range over its
  mean is 1.3% to 4.5%. The 1.8e-4 figure may describe another frame or another normalisation; it
  understates the evidence window by 10 to 37 times. The dataset page's "a few percent" agrees with
  the measured range. The figure stood in eight places. The orchestrator re-measured it
  (2.1e-3 to 6.7e-3 rms over mean, frames 2000-10000) and corrected it everywhere on the
  `metric_build` branch.
- **`docs/ideas/background.md`** said that a Gaussian field carries no flux. It now says "no cascade
  on average, and any one realisation carries a random flux" and "whose flux is zero on average for
  a Gaussian field" (Review round, the random-phase claim).
- **The NaN guards of `spectrum_l2` and `nrmse`** fail in the same way this bundle's did. See
  code_notes.md, Bugs and fixes, and
  [issues/110](../../issues/110-uniform-reference-nan-guard-needs-round-off-bound.md).

## Review round

The reviewer raised eleven critiques: no present bug, one likely future bug, three on theory or
citation, three on documentation and four minor. Ten were fixed and one was rejected. The code fix
is commit c33f769 on #26, and the evidence commit is 8dd88cd on #26. The critique of the NaN guard is
a code bug and is in code_notes.md under Bugs and fixes, as are the tests that pin the
fix of the flux form.

- **The advective flux is not the uniform-density limit of Aluie's deformation work** (theory; high confidence). Judgement 003 said the velocity-only flux is the uniform-density limit
  of the cross-scale transfer, and the card said deformation work reduces to the incompressible
  flux at uniform density. Both are false for a divergent velocity. The reviewer derived, and the
  agent re-derived, that at uniform density with a sharp filter the domain average of Eq. 14 is

  $$\langle\Pi_\ell\rangle = \langle\bar u\cdot(u\cdot\nabla)u\rangle + \langle(\bar u\cdot u)\,\nabla\cdot u\rangle - \tfrac12\langle(\nabla\cdot\bar u)\,\lvert\bar u\rvert^2\rangle .$$

  The last two terms vanish only when $\nabla\cdot u = 0$. With every mode kept the three cancel,
  while the advective form leaves $-\langle\nabla\cdot u\,\lvert u\rvert^2\rangle/2$. The card's
  quotation, "similar to its incompressible counterpart except that the strain is not traceless",
  concerns the strain-stress form, which equals the advective form only for a divergence-free
  field. On nine kinet frames from 2000 to 10000 the two forms differed by 0.216, 0.010, 0.319,
  0.127, 0.568, 0.519, 0.592, 0.987 and 0.833 of the curve's norm. The deformation work at
  $K = 128$ was $10^{-8}$ to $4\times10^{-6}$ of its largest magnitude, against $-0.16$ to 0.86 for
  the advective form. **Fixed** by changing the curve to Aluie's unsubtracted flux, read in the TeX
  source (Sources), and revising judgement 003 and the card's Definition. On kinet frames 2000,
  5000 and 9000 the new $\Pi(128)$ is $2.0\times10^{-15}$, $5.1\times10^{-14}$ and
  $5.2\times10^{-15}$, against curve maxima near $10^{-8}$. A search of `metrics/` for other users
  of `spectral_derivative` or of advective products found none that form a transfer: `palinstrophy`
  and `h1_seminorm` are quadratic in the field.
- **Much of the curve was the dilatational residual** (theory; high confidence for the
  measurement). The plateau equalled $-\langle\nabla\cdot u\,\lvert u\rvert^2\rangle/2$ to $10^{-4}$
  relative; for frame 9000, $\Pi(N/2)$, the all-mode sum and the residual were
  $5.2541\times10^{-9}$, $5.2541\times10^{-9}$ and $5.2543\times10^{-9}$. The velocity's divergence
  is only 0.4-1% of its gradient (ratio of rms values). Even so, removing the divergent part by an
  exact Helmholtz projection changed the old curve by 1.5% to 115% of its norm, with a median near
  60%. It also flipped the sign at low octaves in several frames; at frame 9000, octave 2, the value
  was $+6.0\times10^{-9}$ before the projection and $-4.2\times10^{-10}$ after. The reason is that
  the triadic transfer of this decaying 2D flow is itself weak, with about 85% of the energy in
  shell 1. **Fixed by the change of flux form, and documented.** After the fix the divergent part still
  moves the curve by 0.102, 0.076 and 0.552 of its norm on frames 2000, 5000 and 9000. In Aluie's
  budget that is genuine transfer through the compressive modes, so the card says the metric
  charges a prediction that gets the divergence wrong (card, Limitations). Because the cited source
  settles this, no further judgement was needed.
- **Judgement 003's density figure** (documentation). It was cited to CLAUDE.md, but the
  figure was in AGENTS.md, and it understated the evidence window (Corrections, above). **Fixed**:
  the judgement cites AGENTS.md's figure and gives the measurements.
- **"A random-phase field carries no flux"** (documentation; high confidence for the
  measurements). This holds only on average over draws. On the old curve, the impostor's flux per
  realisation was larger than the reference's at every octave, with median ratios 2.19, 1.66, 2.22,
  4.72, 5.80, 6.06, 5.99 and 5.99 at octaves 1 to 128. `gaussian_impostor` randomises each velocity
  component's phases independently, which destroys the divergence-free structure. With the
  corrected flux, measured on frames 2000, 5000 and 9000:
  - the impostor's ratio of rms divergence to rms gradient is 0.29-0.50, against 0.003-0.007 for the
    reference;
  - its score is 2.70, 2.63 and 1.82;
  - with both fields projected onto their divergence-free parts it is 1.97, 0.46 and 1.06.

  So the metric still catches the impostor, but partly through divergence. **Fixed**: the docstring
  phrase was removed, and the card's Intuition and trap-test reading and `background.md` were
  reworded. The message of commit 324e7f5 could not be changed, being pushed history.
- **The noise reading credited grid-scale gradients for what is about half aliasing** (documentation; medium-high confidence). With every product formed exactly on a doubled grid
  (agreeing with the native grid to $2\times10^{-15}$ on the clean field), the corrected metric at
  noise amplitude 0.5 of the rms scores 2.63, 11.6 and 17.0 aliased against 1.69, 6.31 and 8.00
  dealiased. At amplitude 0.1 dealiasing raises the score slightly (0.114 to 0.139, 0.143 to 0.211,
  0.130 to 0.213). The reviewer's figures on the old flux were 20.47 against 10.94 (frame 5000) and
  15.42 against 5.96 (frame 9000) at amplitude 0.5, and 0.419 against 0.488 at 0.1. **Fixed in the
  reading**: the noise and coarsen readings say part of the high-octave flux is aliased and point to
  Limitations. The dealiased values are not in the card, because the brief allows only numbers from
  the generated tables there. Dealiasing was not added (Method choices).
- **"The sampling drops no transfer" overlooks the corner modes** (minor). The shells
  from $\mathrm{round}(N/2)+1$ to $\mathrm{round}(N\sqrt2/2)$, 129 to 181 on a $256^2$ grid, hold
  about 21% of the modes, and no sampled coordinate includes them. On the old curve the difference
  was negligible on clean frames ($6.6642\times10^{-10}$ against $6.6639\times10^{-10}$ on frame
  5000), and it was not measured on noisy fields. **Fixed** in the card, the docstring and issue
  105: the corner shells enter only through the flux out of the last octave.
- **The Nyquist derivative is silently zeroed** (minor; medium confidence, reasoned and
  not measured in isolation). The vendored spectral derivative multiplies the Nyquist mode by
  $ik_N$ and takes the real part. For a real field that coefficient is real, so the product is
  imaginary and is discarded. On the clean data only $10^{-8}$ to $8\times10^{-8}$ of the energy lies
  beyond the 2/3 cutoff. **Fixed** in the docstring and the card's Definition and Limitations.
- **Findings marked as read in full text that a summariser read in part** (citation;
  high confidence). Each Aluie paper and Kritsuk was fetched once with no offset, and the ar5iv page
  of Aluie (2013) is 138,791 characters against the tool's 100,000. A record for Falkovich & Kritsuk
  (2017) carried "full text" while saying it was read only as an abstract. **Fixed in the records**:
  the TeX sources were read (Sources). Kritsuk 2018 and the enstrophy-flux equations are now
  "secondary".
- **The sign in Aluie's Eq. 13** (minor). The narrowed idea page recorded as unresolved
  that Eq. 13 prints $+\bar P\,\nabla\cdot\bar u$ on its right-hand side, while the text calls
  $-\bar P\,\nabla\cdot\bar u$ the large-scale pressure dilatation. In the TeX source Eq. 13 reads
  $\ldots = -\Pi - \Lambda + \bar P\,\nabla\cdot\bar u - D + \epsilon$. The + sign is the one the
  momentum equation gives, since $-u\cdot\nabla P = -\nabla\cdot(Pu) + P\,\nabla\cdot u$. It is the
  same term named as a sink, a naming convention and not an inconsistency. **Fixed**: the idea
  page's pitfall now records it as resolved.
- **The pitfall labels' date** (minor). The labels read 2026-10-31 while the commits
  read 2026-10-30. **Rejected**: the label text was prescribed verbatim by the orchestrator, and
  its date is that of the archive folder. The orchestrator confirmed the rejection.

The reviewer also checked and found sound:
- an independent rebuild of $\Pi(K)$ in physical space with a sharp filter, which matched the
  companion to $8\times10^{-16}$ to $5\times10^{-15}$ on three frames;
- the sign, and the hand derivation of the first worked example;
- the axis-component pairing, the $1/\text{spacing}$ scaling, and translation and Galilean
  invariance;
- negligible aliasing on clean data;
- that `radial_energy_spectrum`'s default path is bitwise identical to main's;
- that the cache cannot go stale across fields, frames or variants;
- that `translate_subpixel`'s largest values occur at exactly half a cell, as
  [issues/041](../../issues/041-subpixel-shift-drops-the-nyquist-mode.md) predicts;
- that the pre-registration and run provenance are as recorded.

## Open questions and follow-ups

- **The summary and the sampling are conventions**:
  [issues/105](../../issues/105-spectral-energy-flux-summary-is-a-convention.md), which includes the
  measured dominance.
- **The compressible budget** needs density, pressure and velocity together in one metric:
  [judgements/003](../../judgements/003-spectral-flux-from-velocity-alone.md) and
  [issues/096](../../issues/096-several-fields-handed-to-one-metric.md). The other parts of the
  idea are on [energy_transfer_checks.md](../../docs/ideas/turbulence_statistics/energy_transfer_checks.md).
- **A graded phase randomisation.** It rotates each Fourier mode's phase by a uniform angle of
  half-width $s\pi$, with Hermitian symmetry kept. That gives an ordinal axis between the reference
  and the Gaussian impostor which preserves the amplitude spectrum exactly. By the agent's own
  derivation, the expected value of any triple correlation, the spectral energy flux included, is
  multiplied by $\mathrm{sinc}(s\pi)^3$, a known monotone answer. The proposal is
  [EXP-spectral_energy_flux-graded-phase-randomisation](../../proposals/EXP-spectral_energy_flux-graded-phase-randomisation.md).
- **A forced 2D compressible benchmark.** Forced 2D compressible turbulence at rms Mach 0.33-0.54
  has known transfer signatures (an inverse solenoidal cascade and a forward acoustic one forming a
  flux loop) and shocklets. It is what
  [issues/085](../../issues/085-inviscid-invariants-need-other-data.md) asks for, with
  compressibility added. The proposal is
  [EXP-spectral_energy_flux-forced-2d-compressible-flux-loop](../../proposals/EXP-spectral_energy_flux-forced-2d-compressible-flux-loop.md),
  after Kritsuk 2018 and Falkovich & Kritsuk 2017.
- **The 2D enstrophy flux**, not yet in the catalog or the ideas:
  [MTR-spectral_energy_flux-enstrophy-flux](../../proposals/MTR-spectral_energy_flux-enstrophy-flux.md).
  Check the sign in the published version of Alexakis & Biferale before building it.
- **The sign-agreement variant**:
  [MTR-spectral_energy_flux-flux-sign-agreement](../../proposals/MTR-spectral_energy_flux-flux-sign-agreement.md).
- **The same NaN-guard fault in `spectrum_l2` and `nrmse`**:
  [issues/110](../../issues/110-uniform-reference-nan-guard-needs-round-off-bound.md).

## For the next agent

- The equation numbers of all four papers are those of the arXiv copies, now checked in the TeX
  sources; the published versions were not seen. Aluie (2011) Eqs. 12 and 15-17 and the equation
  numbers of Aluie, Li & Li were not re-checked.
- The builder was not sure the velocity-only flux is good enough on kinet. Baropycnal work was not
  measured, because it needs pressure.
- The low dominance means the registered number's ordering depends on the summary convention, and
  a reviewer may prefer a different summary (issue 105).
- The sign inconsistency the summariser reported in Alexakis & Biferale's enstrophy-flux text was
  not checked.
- The builder's first checks were an independent rebuild of $\Pi(K)$ for one kinet frame, and
  confirmation that `spectrum_l2`'s numbers are unchanged. The reviewer has done the first, and the
  reviewer and the orchestrator the second.
- The agent named three passages of the narrowed idea page and the rewritten links to check for
  accuracy: `evaluation_design.md` line 149, and `background.md` lines 175 and 268. Those line
  numbers refer to the branch as it was during the build.
