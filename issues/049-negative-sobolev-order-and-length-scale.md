# Negative Sobolev norms of general order: which orders, and the inhomogeneous norm's length scale

**Category:** method
**Priority:** high, the team's priority for the idea
**Status:** open, needs an owner decision

## Context

Idea: [Negative Sobolev norms of general order](../docs/ideas/norms/negative_sobolev_hs.md). Its row in `docs/ideas/README.md` links here, so the idea is not picked up for building until this issue is resolved; the change that then builds it deletes this file.

What remains of this idea beyond the built `h_minus_one` is orders other than −1 and the inhomogeneous norm, which weights a Fourier coefficient by $(1 + |\mathbf{k}|^2)^{-s/2}$ and so keeps the $\mathbf{k} = 0$ mode. The plan for agent-built metrics proposed extending the `h_minus_one` bundle with an order parameter rather than adding a second bundle.

## Why it is not built

The rule this follows: an open question with no obvious answer and no clear published standard is decided by a person, not settled by whoever implements the metric. Three things stop it.

1. **A metric takes no options from configuration.** The harness calls `spec.fn(reference, candidate, ctx=...)` (`fmeval/pipeline.py`), and the decorator has no per-run options, unlike a degradation's keyword-only parameters. An order parameter added to `h_minus_one` would therefore never be exercised by a run: the registered metric stays at order −1. Evaluating another order needs either a new registered name per order or a harness change that lets a metric take options.
2. **No order is standard.** The page's theorem (Peyre 2018, *ESAIM: COCV* 24(4), 1489–1501) concerns order −1 only; the page gives no reason to prefer any other order.
3. **The inhomogeneous norm needs a length scale.** With $\mathbf{k}$ in inverse length, $1 + |\mathbf{k}|^2$ adds a dimensionless number to one with units, so the norm depends on the unit of length unless a reference length $L$ is fixed, as in $1 + (L|\mathbf{k}|)^2$. The page does not fix $L$ (this observation was made in the screening, not on the page).

The inhomogeneous part would be testable: the `bias` degradation changes only the $\mathbf{k} = 0$ mode, to which `h_minus_one` is blind by definition.

## What would unblock it

Decisions on (a) which orders to register and how (new names, or metric options as a harness change), and (b) the reference length of the inhomogeneous norm.

## Related

Found by the screening of `docs/ideas/` for agent-built metrics (2026-10-23).
