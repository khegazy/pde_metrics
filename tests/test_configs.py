"""The Hydra configuration must compose, and its documented overrides must work.

These are cheap and they catch a class of failure the rest of the suite cannot: a config that
only breaks when Hydra composes it, or an override form that a README promises and the config
rejects. A wrong command in the documentation is worse than none.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from omegaconf import OmegaConf

from degradations import registry as deg_registry
from fmeval.data import kinet_raw, well  # noqa: F401  (register the formats)
from fmeval.data.base import READERS
from metrics import registry as metric_registry
from tests.conftest import CONFIGS, build


def test_default_config_composes():
    cfg = build()
    assert cfg.metrics
    assert cfg.dataset.name and cfg.dataset.format and cfg.dataset.path
    assert cfg.degradation.ladder
    assert cfg.seed


def test_hydra_job_chdir_is_false():
    """With chdir=true the relative datasets symlink and the package imports both break."""
    assert build().hydra.job.chdir is False


def test_hydra_output_dirs_resolve_without_a_live_hydra_context():
    """`hydra.sweep.dir` is resolved before HydraConfig exists.

    Interpolating `${paths.results}` there reaches `${hydra:runtime.cwd}` and fails with
    "HydraConfig was not set", which breaks every multirun. Keep these plain and relative.
    """
    cfg = build()
    for key in ("run.dir", "sweep.dir"):
        value = OmegaConf.select(cfg.hydra, key)
        assert "${" not in str(value), f"hydra.{key} still contains an interpolation"
        assert not str(value).startswith("/"), f"hydra.{key} should be relative"


#: Directories under `configs/` that Hydra never composes, so their files are not group
#: options and cannot be checked by composing them.
#:
#: `dataset_family` holds shared fragments referenced by dataset configs rather than
#: selected on the command line. `cards` holds the settings for generating documentation
#: -- the canonical exemplar frame, which datasets a card may cite, figure DPI -- read
#: directly with OmegaConf by `python -m fmeval.cards`. Generating documentation is not an
#: experiment: it must not create a run folder or a `.hydra` directory, so it does not go
#: through Hydra at all.
NOT_HYDRA_GROUPS = {"dataset_family", "cards"}

#: Every group option on disk, so a new config file is composed without editing this file.
GROUP_OPTIONS = sorted(
    (d.name, f.stem)
    for d in Path(CONFIGS).iterdir() if d.is_dir() and d.name not in NOT_HYDRA_GROUPS
    for f in d.glob("*.yaml")
)


@pytest.mark.parametrize("group,option", GROUP_OPTIONS)
def test_every_config_group_option_composes(group, option):
    """Every file offered as a group option must actually work when selected."""
    cfg = build(f"{group}={option}")
    assert OmegaConf.select(cfg, group) is not None


# --- the override forms the documentation promises ------------------------------------


@pytest.mark.parametrize("override,check", [
    # The headline case: choose the metric on the command line.
    ("metrics=[mse]", lambda c: list(c.metrics) == ["mse"]),
    ("metrics=[mae,mse,nrmse]", lambda c: len(c.metrics) == 3),
    # Sizing knobs.
    ("dataset.time.reduction=100", lambda c: c.dataset.time.reduction == 100),
    ("dataset.time.start=2000", lambda c: c.dataset.time.start == 2000),
    ("dataset.time.max_frames=5", lambda c: c.dataset.time.max_frames == 5),
    ("analysis_grid.resolution=128", lambda c: c.analysis_grid.resolution == 128),
    ("analysis_grid.method=subsample", lambda c: c.analysis_grid.method == "subsample"),
    # Fields and seed.
    ("fields=[vorticity]", lambda c: list(c.fields) == ["vorticity"]),
    ("seed=1", lambda c: c.seed == 1),
    ("analysis.anchor=mean_field", lambda c: c.analysis.anchor == "mean_field"),
    # Ladder selection.
    ("degradation.only=[translate_x]", lambda c: list(c.degradation.only) == ["translate_x"]),
    ("degradation.skip=[median_blur]", lambda c: list(c.degradation.skip) == ["median_blur"]),
    # Reporting.
    ("report.error_map.enabled=false", lambda c: c.report.error_map.enabled is False),
    ("report=none", lambda c: c.report.error_map.enabled is False
     and c.report.thresholds.spearman == 0.90),
    # Data root, for someone whose data is not where the symlink points.
    ("paths.data=/tmp/data", lambda c: str(c.paths.data) == "/tmp/data"),
    # Refusing the HTTP fallback, for a run that must read a local copy or fail.
    ("paths.data_url=null", lambda c: c.paths.data_url is None),
    ("paths.data_url=http://example.invalid/d",
     lambda c: c.paths.data_url == "http://example.invalid/d"),
])
def test_documented_override_works(override, check):
    assert check(build(override)), f"override {override!r} did not take effect"


def test_nested_ladder_overrides_need_no_plus_prefix():
    """`enabled` must be declared on every entry, or overriding it is inconsistent.

    Hydra's struct mode refuses to *add* a key, so an entry that omits `enabled` can only be
    disabled with a `+` prefix while an entry that declares it cannot. Declaring it
    everywhere removes that asymmetry.
    """
    cfg = build("degradation=default",
                "degradation.ladder.gaussian_blur.enabled=false",
                "degradation.ladder.disk_blur.enabled=true",
                "degradation.ladder.gaussian_blur.severities=[1,2]")
    assert cfg.degradation.ladder.gaussian_blur.enabled is False
    assert cfg.degradation.ladder.disk_blur.enabled is True
    assert list(cfg.degradation.ladder.gaussian_blur.severities) == [1, 2]


def test_every_ladder_entry_declares_enabled():
    for option in ("default", "quick"):
        ladder = build(f"degradation={option}").degradation.ladder
        missing = [name for name, entry in ladder.items() if "enabled" not in entry]
        assert not missing, (
            f"degradation/{option}.yaml entries {missing} omit `enabled`, so a CLI override "
            "of it would need a `+` prefix on those and not on the others"
        )


def test_every_ladder_entry_names_a_registered_operator():
    registered = deg_registry.available()
    for option in ("default", "quick"):
        ladder = build(f"degradation={option}").degradation.ladder
        for label, entry in ladder.items():
            op = entry.get("op", label)
            assert op in registered, (
                f"degradation/{option}.yaml entry {label!r} names operator {op!r}, "
                f"which is not registered"
            )


def test_every_dataset_names_a_registered_reader():
    for option in ("kinet_re5e4_dev", "kinet_re5e4", "well_re5e4"):
        cfg = build(f"dataset={option}")
        assert cfg.dataset.format in READERS, (
            f"dataset/{option}.yaml declares format {cfg.dataset.format!r}, "
            f"which has no reader"
        )


@pytest.mark.parametrize("group,keys", [
    ("dataset", ("name", "format", "path", "time", "recompute_derived")),
    ("degradation", ("include_reference", "only", "skip", "ladder")),
])
def test_every_option_defines_the_keys_evaluate_reads_without_a_default(group, keys):
    """`evaluate.py` reads these with no fallback, so each option of the group must set them.

    The config is their one source, so a missing key stops the run; this finds it in the
    suite instead.
    """
    for option in sorted(p.stem for p in Path(CONFIGS, group).glob("*.yaml")):
        cfg = build(f"{group}={option}")[group]
        missing = [k for k in keys if k not in cfg]
        assert not missing, f"{group}/{option}.yaml does not set {missing}"


def test_default_metrics_are_registered():
    for name in build().metrics:
        metric_registry.get(name)  # raises KeyError with the available list if absent


def test_the_card_settings_are_readable_without_hydra():
    """`configs/cards/default.yaml` is read directly, so it must stand on its own.

    It is excluded from the group-composition test above because it is not a Hydra group.
    That exclusion would be a hiding place if nothing else read the file, so this checks
    the keys the generators depend on are present and that no Hydra interpolation has
    crept in -- one would resolve under `evaluate.py` and fail under `python -m
    fmeval.cards`, which is the kind of difference that shows up only in the artifact.
    """
    raw = (Path(CONFIGS) / "cards" / "default.yaml").read_text()
    assert "${" not in raw, "card settings must not interpolate; nothing resolves them"

    cfg = OmegaConf.load(Path(CONFIGS) / "cards" / "default.yaml")
    assert "kinet_re5e4_dev" not in list(cfg.evidence_datasets), (
        "the dev dataset must never be a source of card evidence: it is the first 100 "
        "solver steps, before the flow develops"
    )
    assert cfg.exemplar_frame.dataset in list(cfg.evidence_datasets)


def test_every_evidence_dataset_is_a_real_config():
    """A card may only cite a dataset someone can actually rerun.

    An entry naming a dataset that no longer exists would let a card keep its numbers
    while the run behind them became unreproducible.
    """
    cfg = OmegaConf.load(Path(CONFIGS) / "cards" / "default.yaml")
    on_disk = {f.stem for f in (Path(CONFIGS) / "dataset").glob("*.yaml")}
    missing = [d for d in cfg.evidence_datasets if d not in on_disk]
    assert not missing, f"evidence_datasets names datasets with no config: {missing}"


def test_a_generated_dataset_declares_itself_non_physical():
    """Any generated dataset admitted as evidence must rank below every physical one.

    `synthetic_ensemble` is allowed as card evidence because it validates estimators
    against closed-form answers, which is a claim about arithmetic rather than about a
    flow. That is only safe while the dataset says so about itself: a negative complexity
    rank is what keeps it from being read, or plotted, as if it sat on the physical
    ladder. A generated dataset that ranked alongside the real ones could have its
    numbers quoted as evidence about turbulence.
    """
    cfg = OmegaConf.load(Path(CONFIGS) / "cards" / "default.yaml")
    for name in cfg.evidence_datasets:
        dataset = OmegaConf.load(Path(CONFIGS) / "dataset" / f"{name}.yaml")
        if dataset.get("format") != "synthetic_ensemble":
            continue
        assert int(dataset.complexity.rank) < 0, (
            f"{name} is generated and cited as evidence, so its complexity rank must be "
            "negative to keep it off the physical ladder"
        )
    assert int(cfg.exemplar_frame.index) >= int(cfg.evidence_window.start), (
        "the exemplar frame must lie inside the developed-flow window"
    )
    assert int(cfg.figures.dpi) > 0


def test_the_published_data_url_is_configured():
    """Without it a colleague with no CFS mount gets a FileNotFoundError, not the data."""
    cfg = build()
    assert cfg.paths.data_url, "paths.data_url is unset; the HTTP fallback cannot fire"
    assert str(cfg.paths.data_url).startswith("https://")
    assert not str(cfg.paths.data_url).endswith("/"), "a trailing slash doubles in the URL"


def test_every_dataset_path_is_under_the_data_root():
    """The published tree mirrors `paths.data`, so a path outside it has no URL to derive.

    `fmeval.data.locate` refuses to guess one rather than fabricating a URL that 404s, so a
    dataset config that wandered outside the root would silently lose the fallback.
    """
    cfg = build()
    root = Path(str(cfg.paths.data))
    for name in sorted(p.stem for p in Path(CONFIGS, "dataset").glob("*.yaml")):
        dataset = build(f"dataset={name}").dataset
        path = Path(str(dataset.path))
        assert path == root or root in path.parents, (
            f"{name} points at {path}, which is not under paths.data ({root}), "
            "so no published URL can be derived for it"
        )
