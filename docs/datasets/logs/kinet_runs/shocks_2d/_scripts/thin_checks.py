"""Keep, from check_dmr.py outputs of a run saved every 2 steps, the line of the saved frame
nearest in time to each time of the 480 x 120 run's check (check_dmr_N120.txt), so that the two
read line by line, and append the minimum density and pressure over every saved frame and the
frames below 99 % of the ambient state (1.386, 0.99). Prototype quality, one summary.

Usage: python -B thin_checks.py check_dmr_N120.txt CHECK.txt [CHECK.txt ...] > OUT.txt
"""

import re
import sys

LINE = re.compile(r"\s+t=([\d.]+) nonfinite=(\d+) min_rho=(\S+) max_rho=\S+ min_p=(\S+) ")


def rows(path: str) -> list[tuple[float, int, float, float, str]]:
    """(time, non-finite count, min density, min pressure, line) of every frame line."""
    out = []
    for line in open(path):
        m = LINE.match(line)
        if m:
            out.append((float(m[1]), int(m[2]), float(m[3]), float(m[4]), line.rstrip("\n")))
    return out


reference = [r[0] for r in rows(sys.argv[1])]
for path in sys.argv[2:]:
    frames = rows(path)
    header = [line.rstrip("\n") for line in open(path) if line.startswith(("==", "   grid"))]
    print("\n".join(header))
    for t in reference:
        print(min(frames, key=lambda r: abs(r[0] - t))[4])
    low = [f"t={r[0]:.5f} min_rho={r[2]:.4g} min_p={r[3]:.4g}" for r in frames
           if r[2] < 0.99 * 1.4 or r[3] < 0.99]
    print(f"   over all {len(frames)} saved frames: non-finite {sum(r[1] for r in frames)}, "
          f"min density {min(r[2] for r in frames):.4g}, min pressure {min(r[3] for r in frames):.4g}; "
          f"{len(low)} frames below 99 % of the ambient state" + (": " + "; ".join(low[:20]) if low else "")
          + (" ..." if len(low) > 20 else ""))
