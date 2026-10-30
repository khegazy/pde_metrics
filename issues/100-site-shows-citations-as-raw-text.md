# The documentation site shows a card's citations as raw text, and the reference lists disagree

**Category:** documentation
**Priority:** medium — every card's References section on the published site is unreadable
**Status:** open. Reproduced and pinned by a strict xfail; not fixed.

## Context

A card cites a work as `[@key]` in `card.md`, ends with a References section containing only
`\bibliography`, and keeps the entries in the bundle's `refs.bib` (`metrics/_template/card.md`).
`pyproject.toml`, beside the docs extra, says "references are rendered from each bundle's
refs.bib with pybtex instead", and pybtex is installed with that extra (added in `29e426e`).
No code does it: `docs/gen_pages.py` copies the card text onto the site unchanged apart from
link and asset paths (`_for_site`), and nothing under `fmeval/` or `docs/` reads `refs.bib`
except `fmeval/cards/loader.py`, which lists it as a bundle file.

The card schema also has a `references:` list in `card.yaml` (`fmeval/cards/schema.py`), a
second copy of the `refs.bib` keys that nothing reads.

Found by the adversarial review of the orchestrator's metric-building plan (2026-10-30),
re-measured before this issue was filed.

## Evidence

Running `docs/gen_pages.py` with its output captured (the test below) gives a `metrics/crps.md`
page that still contains the literal `\bibliography` and `[@ferro2014]`; the site built on
2026-10-26 (`site/metrics/crps/index.html`) shows the same.

The three places a bundle's references live, on every bundle with a non-empty `refs.bib`:

| bundle | `refs.bib` keys | in `refs.bib`, never cited as `[@key]` | `card.yaml` `references` |
|---|---|---|---|
| crps | ferro2014, gneitingraftery2007, hersbach2000 | hersbach2000 | empty |
| h1_seminorm | pope2000 | | same as `refs.bib` |
| h_minus_one | peyre2018, pope2000 | | same |
| increment_flatness | granero2024 | granero2024 | same |
| increment_w1 | granero2024, peyrecuturi2019 | granero2024 | same |
| increment_w1_by_separation | granero2024, peyrecuturi2019 | | same |
| palinstrophy | boffetta2012, pope2000 | | same |
| rank_histogram | anderson1996, dellemonache2006, hamill2001 | | empty |
| spectrum_l2 | boffetta2012, pope2000 | | same |
| spread_skill | fortin2014 | | empty |
| mean_field (degradation) | murphy1988, rasp2020 | | empty |

No card cites a key missing from its `refs.bib`. The same work also appears in several bundles'
`refs.bib` (pope2000 in four, granero2024 in three), each with its own `note` saying what that
bundle took from it; that per-use note is worth keeping.

## What would fix it

1. In `docs/gen_pages.py`, render each card's `refs.bib` with pybtex in place of
   `\bibliography`, and turn each `[@key]` into a link to its entry. The card text in the
   repository stays as it is, so GitHub readers see the same source as today.
2. Decide the `card.yaml` `references` field: delete it (nothing reads it, and four bundles
   already disagree with their `refs.bib`), or have the card checker require that it equals the
   `refs.bib` keys.
3. Have the card checker require that the set of `[@key]` in `card.md` equals the set of keys in
   `refs.bib`, which would flag the three uncited entries above.
4. Optionally, a generated Bibliography page merging every `refs.bib` by DOI, listing the cards
   that cite each work.

## Acceptance

`tests/test_card_links_resolve_on_the_site.py::test_a_card_reaches_the_site_with_its_citations_rendered`
passes and its marker is removed; the References section of every card on the built site lists
its entries.
