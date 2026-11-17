"""Launch-Day Lens: kernel-weighted comparable launch trajectories."""

import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path

BANDWIDTH = 1.1
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = dict(zip(LEVELS, [-1.645, -0.674, 0.0, 0.674, 1.645]))


def round2(x: float) -> float | int:
    """Round positive values half up, matching the starter."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value


def inverse_normal(p: float) -> float:
    """Acklam's rational approximation to the inverse normal CDF."""
    if p in Z:
        return Z[p]
    p = min(1 - 1e-15, max(1e-15, p))
    a = (-39.69683028665376, 220.9460984245205, -275.9285104469687,
         138.3577518672690, -30.66479806614716, 2.506628277459239)
    b = (-54.47609879822406, 161.5858368580409, -155.6989798598866,
         66.80131188771972, -13.28068155288572)
    c = (-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783)
    d = (0.007784695709041462, 0.3224671290700398,
         2.445134137142996, 3.754408661907416)
    if p < 0.02425 or p > 0.97575:
        q = math.sqrt(-2 * math.log(p if p < 0.02425 else 1 - p))
        value = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / (
            (((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        return value if p < 0.02425 else -value
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (
        ((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def positive(value):
    """Return a finite positive observation, or None for missing/bad data."""
    try:
        value = float(value)
        return value if math.isfinite(value) and value > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def comparable_curves(case, p1):
    curves = []
    for comparable in case.get("comparables", []) or []:
        try:
            start = datetime.fromisoformat(comparable["day_start"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        points = {row.get("from"): positive(row.get("viewers"))
                  for row in comparable.get("hourly", []) or []}
        values = {k: points.get((start + timedelta(hours=k-1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
                  for k in range(1, 25)}
        v1 = values[1]
        if v1 is None:
            continue
        weight = math.exp(-0.5 * ((math.log(v1) - math.log(p1)) / BANDWIDTH) ** 2)
        curves.append((values, v1, weight))
    return curves


def weighted_quantile(pool, tau, total):
    cumulative = 0.0
    for value, weight in pool:
        cumulative += weight
        if cumulative >= tau * total:
            return value
    return pool[-1][0]


def forecast_case(case, name=None):
    first = next((row for row in case.get("known", []) or [] if row.get("hour") == 1), None)
    p1 = max(1, positive(first.get("viewers")) or 1) if first else 1
    curves = comparable_curves(case, p1) if first else []
    levels = case.get("levels", LEVELS)
    hours = []
    for h in sorted({row["hour"] for row in case.get("forecast", [])}):
        pool = sorted((math.log(values[k] / v1), weight)
                      for values, v1, weight in curves
                      for k in range(max(2, h-1), min(24, h+1)+1)
                      if values[k] is not None and weight > 0)
        total = sum(weight for _, weight in pool)
        quantiles = []
        for tau in levels:
            move = (weighted_quantile(pool, tau, total) if pool and total > 0
                    else inverse_normal(tau) * 0.15 * math.sqrt(max(0, h-1)))
            # Bound before exponentiation as well to avoid numeric overflow.
            if move >= math.log(1e9 / p1):
                value = 1e9
            elif move <= math.log(0.001 / p1):
                value = 0.001
            else:
                value = p1 * math.exp(move)
            q = round2(value)
            q = min(1e9, max(0.01, q, quantiles[-1] if quantiles else 0.01))
            quantiles.append(q)
        hours.append({"hour": h, "q": quantiles})
    return {"hours": hours}


def main():
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(input_dir.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        result = forecast_case(case, path.name)
        (output_dir / f"{path.stem}.out").write_text(
            json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
