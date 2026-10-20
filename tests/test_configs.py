"""The Hydra configuration must compose, and its documented overrides must work.

These are cheap and they catch a class of failure the rest of the suite cannot: a config that
only breaks when Hydra composes it, or an override form that a README promises and the config
rejects. A wrong command in the documentation is worse than none.

They also hold the rule that every setting has one source: a block's defaults belong to the
schema dataclass or the callable it feeds (`fmeval/config.py`), shared values to a `_`-prefixed
fragment, and a YAML file states a key only to change it.
"""

from __future__ import annotations

import ast
import inspect
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from hydra.core.hydra_config import HydraConfig
from hydra.errors import ConfigCompositionException
from omegaconf import MissingMandatoryValue, OmegaConf
from omegaconf.errors import ConfigKeyError

from degradations import registry as deg_registry
from fmeval import CONFIGS, REPO
from fmeval.config import Config, DatasetConfig, ReportConfig, build_job, compose_config
from fmeval.data import kinet_raw, synthetic_ensemble, well  # noqa: F401  (register the formats)
from fmeval.data.base import READERS, TimeSelection
from fmeval.io import read_config, read_run_meta
from fmeval.ladder import DegradationConfig
from fmeval.pipeline import MapRequest
from metrics import registry as metric_registry


def test_default_config_composes():
    cfg = compose_config()
    assert cfg.metrics
    assert cfg.dataset.name and cfg.dataset.format and cfg.dataset.path
    assert cfg.degradation.ladder
    assert cfg.seed


def test_hydra_job_chdir_is_false():
    """With chdir=true the relative datasets symlink and the package imports both break."""
    compose_config()
    assert HydraConfig.get().job.chdir is False


def test_hydra_output_dirs_resolve_without_a_live_hydra_context():
    """`hydra.sweep.dir` is resolved before HydraConfig exists.

    Interpolating `${paths.results}` there reaches `${hydra:runtime.cwd}` and fails with
    "HydraConfig was not set", which breaks every multirun. Keep these plain and relative.
    """
    compose_config()
    for key in ("run.dir", "sweep.dir"):
        value = OmegaConf.select(HydraConfig.get(), key)
        assert "${" not in str(value), f"hydra.{key} still contains an interpolation"
        assert not str(value).startswith("/"), f"hydra.{key} should be relative"


#: Directories under `configs/` that Hydra never composes, so their files are not group
#: options and cannot be checked by composing them.
#:
#: `dataset_family` is not yet consumed (issues/011). `cards` holds the settings for
#: generating documentation -- the canonical exemplar frame, which datasets a card may cite,
#: figure DPI -- read directly with OmegaConf by `python -m fmeval.cards`. Generating
#: documentation is not an experiment: it must not create a run folder or a `.hydra`
#: directory, so it does not go through `hydra.main`.
NOT_HYDRA_GROUPS = {"dataset_family", "cards"}

#: The Hydra groups on disk.
GROUPS = sorted(d.name for d in CONFIGS.iterdir()
                if d.is_dir() and d.name not in NOT_HYDRA_GROUPS)


def _options(group: str) -> list[str]:
    """The selectable options of a group. A file starting with `_` is a fragment that options
    inherit through `defaults:`, not an option."""
    return sorted(f.stem for f in (CONFIGS / group).glob("*.yaml") if not f.name.startswith("_"))


#: Every group option on disk, so a new config file is composed without editing this file.
GROUP_OPTIONS = [(group, option) for group in GROUPS for option in _options(group)]


@pytest.mark.parametrize("group,option", GROUP_OPTIONS)
def test_every_option_composes_into_a_complete_schema(group, option):
    """Every option must compose, and building it into its schema must find every key set.

    `build_job` is what `evaluate.py` does first, so a key an option forgot fails here, named,
    rather than when the run first reads it.
    """
    build_job(compose_config(f"{group}={option}"))


def test_default_config_builds_the_objects_the_code_takes():
    """Each block becomes the dataclass that owns its defaults, so the run reads no copy."""
    job = build_job(compose_config())
    assert isinstance(job, Config)
    assert isinstance(job.dataset.time, TimeSelection)
    assert isinstance(job.degradation, DegradationConfig)
    assert isinstance(job.report.error_map, MapRequest)


@pytest.mark.parametrize("override,key", [
    # A value its dataclass refuses.
    ("dataset.time.reduction=0", "reduction"),
    # A fragment selected as if it were a dataset leaves the required keys unset.
    ("dataset=_re5e4_simulation", "name"),
])
def test_a_bad_value_is_refused_before_any_data_is_read(override, key):
    with pytest.raises((ValueError, MissingMandatoryValue), match=key):
        build_job(compose_config(override))


def test_a_misspelt_key_is_refused_rather_than_ignored():
    with pytest.raises(ConfigCompositionException, match="maxframes"):
        compose_config("dataset.time.maxframes=3")


@pytest.mark.parametrize("override", ["+dataset.time.max_frame=3", "+analysis_grid.resolutoin=64",
                                      "+seeed=1", "+degradation.onl=[translate_x]"])
def test_a_misspelt_key_added_with_plus_is_refused_too(override):
    """`+` adds a key struct mode would refuse, so only the build can catch a misspelling."""
    key = override.split("=")[0].rsplit(".", 1)[-1].lstrip("+")
    with pytest.raises(ConfigKeyError, match=key):
        build_job(compose_config(override))


# --- the override forms the documentation promises ------------------------------------


@pytest.mark.parametrize("override,check", [
    # The headline case: choose the metric on the command line.
    ("metrics=[mse]", lambda c: list(c.metrics) == ["mse"]),
    ("metrics=[mae,mse,nrmse]", lambda c: len(c.metrics) == 3),
    # Sizing knobs. No dataset file states `max_frames`; the schema declares it.
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
    # Options of a reader or an operator that the YAML leaves at their default sit in an
    # untyped mapping, so setting one adds a key and takes `+`.
    ("+dataset.reader.chunk_cache_mb=8", lambda c: c.dataset.reader.chunk_cache_mb == 8),
    ("+degradation.ladder.lowpass_butterworth.options.order=2",
     lambda c: c.degradation.ladder.lowpass_butterworth.options.order == 2),
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
    assert check(compose_config(override)), f"override {override!r} did not take effect"


def test_nested_ladder_overrides_need_no_plus_prefix():
    """`enabled` must be declared on every entry, or overriding it is inconsistent.

    Hydra's struct mode refuses to *add* a key, so an entry that omits `enabled` can only be
    disabled with a `+` prefix while an entry that declares it cannot. Declaring it
    everywhere removes that asymmetry.
    """
    cfg = compose_config("degradation=default",
                         "degradation.ladder.gaussian_blur.enabled=false",
                         "degradation.ladder.disk_blur.enabled=true",
                         "degradation.ladder.gaussian_blur.severities=[1,2]")
    assert cfg.degradation.ladder.gaussian_blur.enabled is False
    assert cfg.degradation.ladder.disk_blur.enabled is True
    assert list(cfg.degradation.ladder.gaussian_blur.severities) == [1, 2]


@pytest.mark.parametrize("option", _options("degradation"))
def test_every_ladder_entry_declares_enabled_and_a_registered_operator(option):
    registered = deg_registry.available()
    ladder = compose_config(f"degradation={option}").degradation.ladder
    missing = [name for name, entry in ladder.items() if "enabled" not in entry]
    assert not missing, (
        f"degradation/{option}.yaml entries {missing} omit `enabled`, so a CLI override "
        "of it would need a `+` prefix on those and not on the others"
    )
    unknown = {label: entry.get("op", label) for label, entry in ladder.items()
               if entry.get("op", label) not in registered}
    assert not unknown, f"degradation/{option}.yaml names unregistered operators {unknown}"


@pytest.mark.parametrize("option", _options("dataset"))
def test_every_dataset_names_a_registered_reader(option):
    fmt = compose_config(f"dataset={option}").dataset.format
    assert fmt in READERS, f"dataset/{option}.yaml declares format {fmt!r}, which has no reader"


def test_default_metrics_are_registered():
    for name in compose_config().metrics:
        metric_registry.get(name)  # raises KeyError with the available list if absent


# --- one source for every setting ----------------------------------------------------------

#: The schema each group's files are built into; `config.yaml` itself is `Config`.
SCHEMAS = {"dataset": DatasetConfig, "degradation": DegradationConfig, "report": ReportConfig}


def _body(path: Path) -> dict[str, Any]:
    """A config file's own keys, unresolved, without its `defaults:` list."""
    body = OmegaConf.to_container(OmegaConf.load(path), resolve=False)
    body.pop("defaults", None)
    return body


def _inherited(path: Path, schema: type) -> Any:
    """What a config file receives before its own keys: the schema, then each fragment it lists."""
    node = OmegaConf.structured(schema)
    for parent in OmegaConf.load(path).get("defaults", []):
        if isinstance(parent, str) and parent not in ("_self_", "_schema"):
            fragment = path.parent / f"{parent}.yaml"
            node = OmegaConf.merge(node, _inherited(fragment, schema), _body(fragment))
    return node


def _leaves(tree: Any, prefix: str = "") -> dict[str, Any]:
    """Dotted key -> value; a list or an empty mapping is one leaf."""
    if isinstance(tree, dict) and tree:
        return {k: v for key, sub in tree.items()
                for k, v in _leaves(sub, f"{prefix}{key}.").items()}
    return {prefix[:-1]: tree}


CONFIG_FILES = [CONFIGS / "config.yaml",
                *sorted(f for group in SCHEMAS for f in (CONFIGS / group).glob("*.yaml"))]


@pytest.mark.parametrize("path", CONFIG_FILES, ids=lambda p: str(p.relative_to(CONFIGS)))
def test_a_config_states_a_key_only_to_change_it(path):
    """A key whose value equals what the file would inherit anyway is a second copy of it.

    The inherited value is the schema's default (`fmeval/config.py`), a fragment's value, a
    reader constructor's keyword default, an operator's keyword-only default, or the entry
    label an `op` defaults to. A second copy is the one that goes stale when the first changes.
    A fragment names no reader, so its reader options are checked in each option inheriting it.
    """
    group = path.parent.name
    body = _leaves(_body(path))
    inherited = _leaves(OmegaConf.to_container(
        _inherited(path, SCHEMAS.get(group, Config)), resolve=False, throw_on_missing=False))
    restated = [f"{k}: {v!r} (schema or fragment)" for k, v in body.items()
                if k in inherited and inherited[k] == v]

    fmt = body.get("format", inherited.get("format"))
    if fmt in READERS:
        reader = inspect.signature(READERS[fmt]).parameters
        restated += [f"{k}: {v!r} (the reader's default)" for k, v in {**inherited, **body}.items()
                     if k.startswith("reader.") and k.split(".")[1] in reader
                     and reader[k.split(".")[1]].default == v]

    for key, value in body.items():
        parts = key.split(".")
        if len(parts) == 4 and parts[0] == "ladder" and parts[2] == "options":
            op = body.get(f"ladder.{parts[1]}.op", parts[1])
            if deg_registry.get(op).defaults.get(parts[3], object()) == value:
                restated.append(f"{key}: {value!r} (the operator's default)")
        if parts[0] == "ladder" and parts[2:] == ["op"] and value == parts[1]:
            restated.append(f"{key}: {value!r} (an entry's op defaults to its label)")

    assert not restated, (
        f"{path.relative_to(REPO)} restates values it would inherit; delete them: {restated}"
    )


@pytest.mark.parametrize("edited,text,checked", [
    ("dataset/kinet_re5e4.yaml", "time: {start: 1}\n", "dataset/kinet_re5e4.yaml"),
    ("dataset/_re5e4_simulation.yaml", "reader: {chunk_cache_mb: 32}\n",
     "dataset/kinet_re5e4.yaml"),
    ("report/none.yaml", "  frames: [-1]\n", "report/none.yaml"),
    ("degradation/quick.yaml", "  lowpass_butterworth: {enabled: true, severities: [0.3], "
     "options: {order: 4}}\n", "degradation/quick.yaml"),
    ("degradation/quick.yaml", "  lowpass_ideal: {enabled: true, op: lowpass_ideal, "
     "severities: [0.3]}\n", "degradation/quick.yaml"),
])
def test_the_restatement_guard_catches_a_planted_copy(edited, text, checked, tmp_path,
                                                      monkeypatch):
    """The guard above passes on clean files; this proves it fails on a restated value."""
    shutil.copytree(CONFIGS, tmp_path / "configs")
    with open(tmp_path / "configs" / edited, "a") as f:
        f.write(text)
    monkeypatch.setitem(globals(), "REPO", tmp_path)
    with pytest.raises(AssertionError, match="restates"):
        test_a_config_states_a_key_only_to_change_it(tmp_path / "configs" / checked)


@pytest.mark.parametrize("group", GROUPS)
def test_every_fragment_is_inherited_by_an_option(group):
    """A fragment that no option lists is dead configuration."""
    fragments = {f.stem for f in (CONFIGS / group).glob("_*.yaml")}
    listed = {parent for option in _options(group)
              for parent in OmegaConf.load(CONFIGS / group / f"{option}.yaml").get("defaults", [])
              if isinstance(parent, str)}
    assert fragments <= listed, (
        f"configs/{group}/ has fragments no option inherits: {sorted(fragments - listed)}")


def test_evaluate_reads_the_config_without_fallbacks():
    """`cfg.x.get(key, default)` would be a second default for a key the schema declares."""
    def rooted_at_cfg(node: ast.AST) -> bool:
        while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
            node = node.func if isinstance(node, ast.Call) else node.value
        return isinstance(node, ast.Name) and node.id in ("cfg", "job")

    tree = ast.parse((REPO / "evaluate.py").read_text())
    fallbacks = [n.lineno for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "get" and rooted_at_cfg(n.func.value)]
    assert not fallbacks, f"evaluate.py reads the config with a fallback at lines {fallbacks}"


def test_a_run_records_the_reader_options_its_config_leaves_out(tmp_path):
    """`config.yaml` holds only what a file or override states, so a reader's defaults, which
    can change with the code, are recorded beside it in `run_meta.json`."""
    subprocess.run(
        [sys.executable, str(REPO / "evaluate.py"), "dataset=synthetic_ensemble",
         "degradation=ensemble_miscalibration", "degradation.only=[bias]", "metrics=[crps]",
         "+dataset.reader.sigma=0.2", f"paths.results={tmp_path}", f"hydra.run.dir={tmp_path}/h"],
        check=True, capture_output=True, cwd=tmp_path,
    )
    (folder,) = tmp_path.glob("crps_*")
    recorded = read_run_meta(folder)["reader_options"]
    stated = read_config(folder)["dataset"]["reader"]
    signature = inspect.signature(READERS["synthetic_ensemble"]).parameters
    assert "omega" not in stated and recorded["omega"] == signature["omega"].default
    assert stated["sigma"] == recorded["sigma"] == 0.2
    assert recorded["n_members"] == stated["n_members"]
    assert set(recorded) == set(signature) - {"path"}


def test_the_data_root_does_not_depend_on_the_working_directory(tmp_path, monkeypatch):
    """The `datasets` link sits beside the code, so a run started elsewhere still reads the local
    copy instead of falling back to the network."""
    monkeypatch.chdir(tmp_path)
    assert compose_config().paths.data == str(REPO / "datasets")


# --- the card settings, read without Hydra --------------------------------------------------


def test_the_card_settings_are_readable_without_hydra():
    """`configs/cards/default.yaml` is read directly, so it must stand on its own.

    It is excluded from the group-composition test above because it is not a Hydra group.
    That exclusion would be a hiding place if nothing else read the file, so this checks
    the keys the generators depend on are present and that no Hydra interpolation has
    crept in -- one would resolve under `evaluate.py` and fail under `python -m
    fmeval.cards`, which is the kind of difference that shows up only in the artifact.
    """
    raw = (CONFIGS / "cards" / "default.yaml").read_text()
    assert "${" not in raw, "card settings must not interpolate; nothing resolves them"

    cfg = OmegaConf.load(CONFIGS / "cards" / "default.yaml")
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
    cfg = OmegaConf.load(CONFIGS / "cards" / "default.yaml")
    missing = [d for d in cfg.evidence_datasets if d not in _options("dataset")]
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
    cfg = OmegaConf.load(CONFIGS / "cards" / "default.yaml")
    for name in cfg.evidence_datasets:
        dataset = compose_config(f"dataset={name}").dataset
        if dataset.format != "synthetic_ensemble":
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
    cfg = compose_config()
    assert cfg.paths.data_url, "paths.data_url is unset; the HTTP fallback cannot fire"
    assert str(cfg.paths.data_url).startswith("https://")
    assert not str(cfg.paths.data_url).endswith("/"), "a trailing slash doubles in the URL"


@pytest.mark.parametrize("name", _options("dataset"))
def test_every_dataset_path_is_under_the_data_root(name):
    """The published tree mirrors `paths.data`, so a path outside it has no URL to derive.

    `fmeval.data.locate` refuses to guess one rather than fabricating a URL that 404s, so a
    dataset config that wandered outside the root would silently lose the fallback.
    """
    cfg = compose_config(f"dataset={name}")
    root = Path(str(cfg.paths.data))
    path = Path(str(cfg.dataset.path))
    assert path == root or root in path.parents, (
        f"{name} points at {path}, which is not under paths.data ({root}), "
        "so no published URL can be derived for it"
    )
