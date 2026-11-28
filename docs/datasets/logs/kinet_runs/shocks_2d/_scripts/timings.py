"""Per-run throughput of kinet PonD simulate runs, from their logs (prototype).

Usage: python timings.py RUNS_RECORD RUN_DIR [RUN_DIR ...]
  RUNS_RECORD: the job's ``job_<id>_runs.txt`` (one line per run with start=, wall_s=).
  RUN_DIR: a run folder holding ``log.txt`` (written by run_kinet_job.sh).

For each run it prints the grid, the accepted steps, the start-up (process launch to the
rollout loop), the first accepted step (which includes torch.compile), the time per step of
every progress window, the steady time per step (median of the windows after the first, which
holds the compilation), cell-steps per second at that steady rate, the rollout time, the
process wall time and the stop reason. A cell-step is one cell advanced one accepted step.
"""

import datetime as dt
import os
import re
import statistics
import sys

STAMP = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\]")
GRID = re.compile(r"IC initialization .* grid=\[(\d+), (\d+)\]")
WINDOW = re.compile(r"recent (\d+) steps=[\d.a-z ]+ \(([\d.]+) ms/step\)")
FIRST = re.compile(r"first accepted step complete in ([\d.]+) s")
FINISHED = re.compile(r"Rollout finished in ([\d.]+) s \(stop_reason=(\w+), accepted=(\d+)")


def stamp(line: str) -> dt.datetime:
    """Parse the leading timestamp of a log line."""
    return dt.datetime.strptime(STAMP.match(line).group(1), "%Y-%m-%d %H:%M:%S")


def main(record: str, runs: list[str]) -> None:
    """Print one line per run; a run without a finished rollout is reported as such."""
    records = {ln.split()[0]: ln for ln in open(record) if ln.strip()}
    for run in runs:
        name = os.path.basename(run.rstrip("/"))
        text = open(os.path.join(run, "log.txt")).read()
        lines = text.splitlines()
        nx, ny = (int(v) for v in GRID.search(text).groups())
        windows = [(int(k), float(ms)) for k, ms in WINDOW.findall(text)]
        first = FIRST.search(text)
        done = FINISHED.search(text)
        enter = next((stamp(ln) for ln in lines if "entering rollout loop" in ln), None)
        rec = records.get(name, "")
        t0 = re.search(r"start=([\d.]+)", rec)
        wall = re.search(r"wall_s=([\d.]+)", rec)
        startup = (enter - dt.datetime.fromtimestamp(float(t0.group(1)))).total_seconds() \
            if enter and t0 else float("nan")
        steady = statistics.median(ms for _, ms in windows[1:]) if len(windows) > 1 else float("nan")
        print(f"{name:22s} grid={nx}x{ny} cells={nx * ny:8d} "
              f"accepted={done.group(3) if done else 'n/a':>5s} startup_s={startup:6.0f} "
              f"first_step_s={float(first.group(1)) if first else float('nan'):6.1f} "
              f"steady_ms={steady:8.1f} cell_steps_per_s={nx * ny / (steady / 1e3):9.3e} "
              f"rollout_s={float(done.group(1)) if done else float('nan'):7.1f} "
              f"wall_s={float(wall.group(1)) if wall else float('nan'):6.0f} "
              f"stop={done.group(2) if done else 'not finished'} "
              f"windows_ms={[ms for _, ms in windows]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
