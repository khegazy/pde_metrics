# How to read a metric page

Every metric has one page, and every page is laid out the same way. This guide walks
through that layout section by section, and explains the three measured quantities that
recur throughout. The pages are called **cards** in this repository, and a card lives in
the same directory as the code it describes.

The sections run in a fixed order, from what the metric *is* to what the metric *did on
our data*. The break between those two halves matters: the first four sections hold for
any dataset, so a reader adopting a metric for their own work can stop at Limitations.
The last two report findings from recorded runs on our data.

## Definition

The equation, how the equation is turned into arithmetic on a grid, and how the edges of
the domain are handled. "None." is a common and perfectly good answer to that last one — a
metric that never looks beyond a single grid cell has no edge to treat. It is worth
reading, because the choices available at the edge (wrapping around to the opposite side,
mirroring, padding with zeros) give different numbers from the same formula, and two
implementations of one published equation can disagree on nothing else.

## Intuition

The same content in words, with no notation at all, written for an early graduate student
in any field. The section opens with what the metric measures and which way of being
wrong the metric reveals, explains the mechanism, and includes a small worked example —
usually a four-by-four grid — whose numbers are taken from the metric's own test file. The
section closes by naming what the metric ignores, because every metric is blind to
something.

## Reading the output

What to do with a number you are holding: the range the number can take, its units,
whether lower or higher is better, what makes a value good and what that depends on, and
which comparisons are valid. That last part is the one most often needed. Comparing a
cell-by-cell metric across two grid resolutions, for instance, is invalid without first
putting both fields on a common grid, because the value is an average over cells and
refining the grid changes how much weight the small scales get.

## Limitations

At least one concrete situation where the metric gives a misleading answer, described so
that you can recognise the situation in your own results.

## Performance and Results

The measured half of the page. Every number in Performance, and in Results outside the
subsections headed with another experiment, comes from one recorded evaluation run, named at
the top of Results along with the dataset, the grid and the number of snapshots it covered.

**Performance** opens with the figure the metric's own field draws, then two figures that
every metric page shares, and then the table they summarise, so that the shape of the
metric's behaviour is seen before any number is read.

The field's own figure is the one a reader from that field would look for first, drawn from
the recorded run and marked *As this metric's own field draws it*. Which figure that is
follows from what the metric is:

- **A curve behind the number**, such as an energy spectrum, a structure function or a rank
  histogram: the curve against its coordinate, one panel per way of damaging the field, the
  undamaged field's curve in black and each strength in the damage's colour, darker for
  harsher. There is one such figure for each physical field.
- **A set of points behind the number**, such as a persistence diagram or the positions of
  detected shocks: each damaged field's points over the reference's, which are grey rings. A
  persistence diagram carries its diagonal, where a feature is born and dies at once; on a
  one-dimensional grid the points sit on the field's line-out, the reference's in grey.
- **A property of one field**, such as the energy or the enstrophy: its value against time,
  the undamaged field's history in black. A damaged line is the damage applied to each
  snapshot on its own; it is not a simulation run forward from a damaged start, so it shows
  what the damage does at each time, not how an error would grow.
- **A comparison of two fields** with none of the above: when the page cites a run of real
  forecasts, its error against lead time from that run, as the forecasting benchmarks draw it,
  and the caption names that run; everything else in Performance still comes from the main
  run. Otherwise its damage against the applied shift beside the pointwise baselines, the
  figure that also heads *Damage beside the other metrics* below.
- **An ensemble score** with none of the above has no such figure yet, and the page says why.

The next figure, the *sensitivity profile*, has one row per way of damaging the field,
grouped by family, and four panels that share those rows. Each marker is one physical
field (circle, square, triangle). From left to right the panels show: whether the metric
put the strengths in the right order (the rank correlation, with a short line for its
resampling interval); whether the metric can tell one strength from the next (Cliff's
delta, where 0 means neighbouring strengths are indistinguishable and the faint ticks are
reference anchors for scale, not grades); how much damage the metric charged per unit of
change to the field; and the upper bound on the largest damage it ever assigned, beside
the fixed margin below which a response counts as provably small. A hollow marker is a
field and degradation on which the metric's response lies provably below that margin.
A missing marker is a statistic the analysis withheld, which happens on an axis the
metric cannot see at all.

The figure after it, the *response curves*, shows median damage against severity level,
with one row per family of degradation and one column per field, every panel on the same
0-to-1 scale. The solid grey line is damage 1, the field's own mean. The dotted black line is
the damage the metric assigned to the fake prediction with the right spectrum. The hollow
ring marks the first strength at which the metric moved a tenth of the way to the anchor.
Hollow grey markers are strengths that were excluded because they repeated a milder
one or did nothing. A grey panel means the field has no damage scale for this metric, and
the raw value is drawn instead.

Below the figures sits the table, one row per test family and physical field, so that two
metrics can be compared at a glance. To compare every metric on the same figures, see
[Sensitivity at a glance](sensitivity.md).

**Results** opens with a table headed *Across the experiments*. Every metric is run on every
experiment where it makes sense, and the table has one row per experiment: the developed flow,
the synthetic ensemble, the shock tube and the real forecasts. Each row says what a run on that
experiment is evidence of, and whether the page reports one. Where it does not, the row says
why. The metric cannot be computed there, because the experiment lacks a periodic domain, an
ensemble or the field the metric needs. Or a person judged the result would carry no
information. Or nobody has run it yet. The main results come from one run, named just above the
table. A run on another experiment has its own subsection at the end of Results, headed with
the experiment's name. Its first line says what kind of evidence it is: an analytic check, for
instance, says nothing about turbulence. The [coverage page](coverage.md) puts these tables for
every metric on one page.

The subsection on the real forecasts reads differently, because a forecast is not damaged by a
chosen amount. It shows the metric against lead time, the physical time since a forecast
started: one panel per starting time and one line per run, darker for a finer grid. Beneath the
figure, one table per field gives the metric at every prediction step of every forecast, one row
per lead time and one column per forecast, named by its run's grid and its starting time;
nothing is averaged over steps, starts or runs. A second table gives the same predictions as
damage, each step against its own target's spatial mean, so a growing or shrinking target does
not read as a growing or shrinking error. A property of one field, such as the enstrophy, also
gets a table of its value on the target, the truth the prediction is read against.

The rest of **Results** breaks the summary down one test at a time. Each subsection links to the
way of damaging the field that it reports, shows the numbers for that damage, and then
says in a few sentences what those numbers mean for this metric. The last subsection,
*Damage beside the other metrics*, opens with a third figure: this metric's damage against
the applied shift, log-log, beside the four cell-by-cell baselines drawn thin and grey. Two
parallel lines charge in the same proportion at every shift; a steeper line charges
relatively more for the larger shifts. That is the difference between two metrics that
order models alike and two that could replace each other as training losses, and the table
beneath gives the same numbers.

Three measured quantities recur in those tables, and they are worth understanding before
you read one.

**Damage** puts every metric on the same 0-to-1 scale. A raw mean squared error and a raw
transport distance are not comparable numbers, so each metric's raw value is rescaled:
0 is what the metric gives the undamaged reference, and 1 is what the metric gives the
reference's own spatial mean: a prediction that knows the mean and nothing else. Damage
is what makes a result on density comparable with a result on vorticity. A damage above 1
means the metric considers the prediction *worse* than knowing only the mean, which a field
with the right statistics in the wrong place usually is: for mean squared error an unrelated
field of the same variance scores 2.

**Rank correlation** asks whether the metric puts increasing damage in increasing order.
It is the Spearman rank correlation between the strength of the damage applied and the
value the metric returned, and it runs from -1 (exactly backwards) through 0 (no
relationship) to 1 (perfectly ordered every time). It is computed within a single
snapshot in time and never pooled across a whole trajectory, because these flows decay:
pooling would measure the decay rather than the metric.

**Separation** asks whether the metric can tell one strength of damage from the next
one up. A metric can put the strengths in the right order on average and still overlap so
much between neighbouring strengths that it cannot distinguish two models one step apart.
The reported number is the smallest such overlap along the whole sequence, where 1 means
two neighbouring strengths never overlap and 0.5 means the metric cannot separate them at
all.

## About the figures

Colour limits are shared across each row of a figure and printed at the row's edge. This
matters more than it sounds. If each panel were autoscaled separately, a badly damaged
field would be drawn with exactly the same colours as the original and would look
identical to it — and it would do so with nothing on the page to warn you.

Every figure on a metric page is drawn from the one recorded run named at the top of
Results, by the same code that draws the evaluation report, and the numbers behind each
figure are published beside it as a JSON file of the same name. Colour means the family
of degradation throughout — smoothing is always the same blue — and marker shape means
the physical field, so the figures can be read in greyscale. Reference lines mark fixed
conventions of the analysis, never a judgement: damage 1 is what the field's own mean
scores, and the blindness margin is where a response counts as provably small. Nothing
on a figure is coloured good or bad.

The field's own figure keeps that field's axes. A spectrum or a structure function may be
drawn on logarithmic axes, and a quantity that changes sign, such as an energy flux, on a
*symmetric logarithmic* axis: logarithmic on both sides of zero and linear in a thin band
around it, six decades below the largest value drawn, with the zero line marked. The
caption names the axes whenever they are not plain linear ones. A histogram over fixed
bins, such as a rank histogram, is drawn as bars. A set of several thousand points is drawn
as an image inside the figure so the page stays light; its numbers are still in the JSON
beside it. A metric page shows at most four panels of point sets, and the evaluation report
shows up to twelve.
