---
name: gneiting_forecaster
kind: degradation
---

## Definition

Gneiting, Balabdaoui and Raftery [@gneiting2007] (Section 1, Table 1) let nature draw a case
mean $\mu \sim N(0, 1)$ and an observation $y \sim N(\mu, 1)$. The ideal forecaster issues
$N(\mu, 1)$. Three others are calibrated, or nearly, and still worse:

| kind | predictive distribution |
|---|---|
| `climatological` | $N(0, 2)$ |
| `unfocused` | $\tfrac{1}{2}\{N(\mu, 1) + N(\mu + \tau, 1)\}$, $\tau = \pm 1$ with probability $\tfrac{1}{2}$ |
| `hamill` | $N(\mu + \delta, s^2)$, $(\delta, s^2) \in \{(\tfrac{1}{2}, 1), (-\tfrac{1}{2}, 1), (0, 1.69)\}$ with probability $\tfrac{1}{3}$ each |

On the `synthetic_ensemble` reader with `base: case_means` and `sigma: 1`, every cell is one
case and the clean members are draws from the ideal forecaster. The operator turns them into
draws from another kind without knowing $\mu$. With $x_i$ an ideal member, $B_i \in \{0, 1\}$
and $\zeta_i \sim N(0, 1)$ drawn per member and cell, and $\tau$ and $(\delta, s^2)$ drawn once
per cell,

$$
x_i^{\mathrm{clim}} = \sqrt{2}\,\zeta_i, \qquad
x_i^{\mathrm{unf}} = x_i + \tau B_i, \qquad
x_i^{\mathrm{ham}} = x_i + \delta + \sqrt{s^2 - 1}\,\zeta_i. \tag{1}
$$

Each is an exact draw from its row of the table, because $s^2 \ge 1$. From the kernel form of
the CRPS, $E|X - y| - \tfrac{1}{2}E|X - X'|$, the exact expected scores are 0.5642 (ideal),
0.6144 (Hamill's), 0.6319 (unfocused) and 0.7979 (climatological)
(`dataset_specs/08_synthetic_ensemble_extensions.md`, Equation 2). The paper's Table 5 reports
0.56, 0.61, 0.63 and 0.78 from 10 000 cases.

The operator declares that its levels carry no order and that severity zero is not the
identity. Its configuration is `configs/degradation/gneiting_forecasters.yaml`.

### Boundary handling

None. Every draw is made cell by cell; no neighbourhood is consulted.

## Intuition

This stands in for a forecast that passes every calibration check and is still a poor
forecast. The climatological forecaster always predicts the long-run spread of outcomes, so
it is never surprised on average, yet it knows nothing about the case in front of it. The
unfocused forecaster mixes the right answer with a wrong one. Hamill's forecaster is off by
half a unit in a third of the cases each way and too wide in the rest, and its departure from
calibration is too small to see in a rank histogram.

All four give a flat rank histogram and a spread-to-skill ratio near one. Only a proper score
such as the CRPS ranks them in the right order. A metric that rates the climatological
forecaster as well as the ideal one measures calibration and not skill.

One cell, ideal members 0.3, -0.8 and 1.1 about a case mean of 0.2, with the unfocused shift
of +1 applied to the second and third members:

```
ideal        unfocused
0.3          0.3
-0.8         0.2
1.1          2.1
```

What this leaves untouched depends on the kind: the unfocused and Hamill's forecasters keep
each ideal member's own noise and add to it, while the climatological one discards it.

## Severity scale

There is no severity scale. The configured value 0 is a placeholder that the operator ignores.
Each kind is a separate ladder entry chosen by its `kind` option, and the reference level of
that ladder is the ideal forecaster.

## Limitations

The constants of Table 1 presuppose the reader settings above. On any other ensemble the
climatological kind replaces every member by noise of variance two, and the other two add
unit-scale shifts; the results are defined but have no known answer. The operator never sees
$\mu$, so it cannot draw a forecaster whose spread depends on the case mean.

## What the degradation looks like

### The picture

<!-- GENERATED exemplars: written by `python -m fmeval.cards exemplars gneiting_forecaster`, do not edit -->

Not generated yet. Run `python -m fmeval.cards exemplars gneiting_forecaster`.

<!-- END GENERATED exemplars -->

The panel, once drawn, shows the climatological kind on a flow field, where it has no meaning:
each member becomes noise of variance two. The operator's meaning is on the case-means
reader, whose frames are themselves noise, so no picture of a flow shows it.

## References

\bibliography
