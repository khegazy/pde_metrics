"""Extract per-run timings from kinet simulate logs and the job runs files (prototype).

Usage: python timings.py RUN_DIR [RUN_DIR ...]   (each holding log.txt and command.txt)
Prints: grid, steps, start-up (process launch to rollout loop), first-step time (includes
torch.compile), steady ms/step (median of the 100-step windows after the first),
cell-steps per second, rollout time, process wall time.
"""

import datetime as dt
import glob
import os
import re
import statistics
import sys

STAMP = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\]")


def stamp(line: str) -> dt.datetime:
    """Parse the leading timestamp of a log line."""
    return dt.datetime.strptime(STAMP.match(line).group(1), "%Y-%m-%d %H:%M:%S")


for run in sys.argv[1:]:
    name = os.path.basename(run.rstrip("/"))
    text = open(os.path.join(run, "log.txt")).read()
    lines = text.splitlines()
    grid = re.search(r"grid=\\?\[(\d+)", open(os.path.join(run, "command.txt")).read()).group(1)
    steps = int(re.search(r"temporal.grid=(\d+)", open(os.path.join(run, "command.txt")).read()).group(1))
    enter = stamp(next(ln for ln in lines if "entering rollout loop" in ln))
    first = float(re.search(r"first accepted step complete in ([\d.]+) s", text).group(1))
    ms = [float(m) for m in re.findall(r"recent 100 steps=[\d.]+s \(([\d.]+) ms/step\)", text)]
    rollout = float(re.search(r"Rollout finished in ([\d.]+) s", text).group(1))
    # A rerun appears in several job records; the latest start is the run whose log this is.
    recs = [ln for f in glob.glob(os.path.join(os.path.dirname(run), "job_*_runs.txt"))
            for ln in open(f) if ln.startswith(name + " ")]
    rec = max(recs, key=lambda ln: float(re.search(r"start=([\d.]+)", ln).group(1)))
    t0 = float(re.search(r"start=([\d.]+)", rec).group(1))
    wall = float(re.search(r"wall_s=([\d.]+)", rec).group(1))
    startup = (enter - dt.datetime.fromtimestamp(t0)).total_seconds()
    med = statistics.median(ms) if ms else float("nan")
    n = int(grid)
    print(
        f"{name:28s} N={n:4d} steps={steps:6d} startup_s={startup:6.0f} first_step_s={first:6.1f} "
        f"steady_ms={med:6.2f} cell_steps_per_s={n * n / (med / 1e3):9.3e} rollout_s={rollout:7.1f} wall_s={wall:6.0f}"
    )
