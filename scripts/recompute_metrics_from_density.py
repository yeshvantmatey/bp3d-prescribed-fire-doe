"""Recompute the paper's treatment metrics from archived density arrays.

Accepts the original ZIP or a density-only ZIP preserving run directory names.
No simulation software is invoked. This script does not reconstruct input decks
or establish which curing inputs were executed. See the provenance notes.

Example:
    python scripts/recompute_metrics_from_density.py --archive /path/to/density.zip --output-dir raw_recomputed

Use --limit 1 for a partial smoke check. The default stored-output interval is
60 seconds, as recorded in archived run configuration; output times are minutes.
"""

import argparse
import csv
import hashlib
import io
import itertools
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from zipfile import ZipFile

import numpy as np


EPS = 1e-12
EXPECTED_RUNS = 1600
STUDY_LEVELS = {
    "fuel_model": ["GR2", "GS1", "GS2", "SH2", "SH5"],
    "curing_state": ["early_spring_before_greenup", "spring_after_greenup", "early_summer_senescence", "fall_with_greenup", "fall_without_greenup"],
    "ignition_family": ["Strip", "Flank"],
    "ignition_structure": ["Broken", "Dot"],
    "wind_speed_mph": [1.0, 4.0, 8.0, 12.0],
    "surface_moisture": [.06, .08, .10, .12],
}
FACTOR_FIELDS = [
    "run_id", "fuel_model", "curing_state", "ignition_pattern",
    "ignition_family", "ignition_structure", "wind_speed_mph", "surface_moisture",
]
FINAL_FIELDS = FACTOR_FIELDS + [
    "consumption_fraction_surface", "active_consumed_area_fraction_1pct",
    "cell_consumption_cv",
]
TIME_FIELDS = FACTOR_FIELDS + [
    "time_index", "elapsed_time_min", "consumption_fraction_t", "active_area_fraction_t",
]
MILESTONE_FIELDS = FACTOR_FIELDS + [
    "final_consumption", "final_active_area", "t10_consumption", "t50_consumption",
    "t80_consumption", "t10_active_area", "t50_active_area", "peak_active_area",
    "t_peak_active_area", "peak_consumption", "t_peak_consumption",
    "auc_consumption", "auc_active_area",
]


def factors_from_member(member):
    """Recover the study's labels from the preserved archive-relative path."""
    parts = PurePosixPath(member).parts
    if len(parts) < 5 or parts[-2:] != ("arrays", "fuels-dens.npy"):
        raise ValueError(f"Unexpected density member path: {member}")
    fuel, scenario, run_folder = parts[-5:-2]
    if not scenario.startswith(fuel + "_"):
        raise ValueError(f"Scenario does not begin with its fuel model: {member}")
    match = re.fullmatch(r"(.+)_(Strip|Flank)_(Broken|Dot)", scenario[len(fuel) + 1:])
    conditions = re.fullmatch(r"ws_([0-9.]+)_fm_([0-9.]+)", run_folder)
    if match is None or conditions is None:
        raise ValueError(f"Cannot recover factors from: {member}")
    curing, orientation, continuity = match.groups()
    return dict(zip(FACTOR_FIELDS, [
        "|".join((fuel, scenario, run_folder)), fuel, curing,
        orientation + "_" + continuity, orientation, continuity,
        float(conditions.group(1)), float(conditions.group(2)),
    ]))


def treatment_trajectories(density):
    """Use surface z=0, positive initial cells, float64 and population SD."""
    if density.ndim != 4 or density.shape[0] != 61 or density.shape[2:] != (80, 80):
        raise ValueError(f"Unexpected study density shape: {density.shape}")
    surface = np.asarray(density[:, 0, :, :], dtype=np.float64)
    if not np.isfinite(surface).all() or (surface < 0).any():
        raise ValueError("Surface density contains nonfinite or negative values")
    initial = surface[0]
    eligible = initial > EPS
    if int(eligible.sum()) != 6084:
        raise ValueError(f"Expected 6,084 eligible surface cells for this study, found {eligible.sum()}")
    local_loss = np.maximum(initial[eligible][None, :] - surface[:, eligible], 0.0)
    local_fraction = local_loss / initial[eligible][None, :]
    consumption = local_loss.sum(axis=1) / initial[eligible].sum()
    active_area = np.mean(local_fraction > 0.01, axis=1)
    spatial_mean = np.mean(local_fraction, axis=1)
    spatial_sd = np.std(local_fraction, axis=1, ddof=0)
    patchiness = np.divide(spatial_sd, spatial_mean, out=np.full_like(spatial_mean, np.nan), where=spatial_mean > EPS)
    return consumption, active_area, patchiness, int(eligible.sum())


def first_reached(values, times, threshold):
    indices = np.flatnonzero(values >= threshold)
    return float(times[indices[0]]) if indices.size else None


def auc(values, times):
    return float(np.sum((values[1:] + values[:-1]) * 0.5 * np.diff(times)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-interval-seconds", type=float, default=60.0)
    parser.add_argument("--limit", type=int, help="Process only the first N runs; explicitly marked partial")
    args = parser.parse_args()
    if args.output_interval_seconds <= 0 or not np.isfinite(args.output_interval_seconds):
        parser.error("--output-interval-seconds must be finite and positive")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    with ZipFile(args.archive) as archive, tempfile.TemporaryDirectory(dir=args.output_dir) as temp:
        members = sorted(i.filename for i in archive.infolist() if i.filename.endswith("/arrays/fuels-dens.npy"))
        if not members:
            raise ValueError("Archive contains no run/arrays/fuels-dens.npy members")
        observed_combinations = [tuple(factors_from_member(member)[key] for key in STUDY_LEVELS) for member in members]
        expected_combinations = set(itertools.product(*STUDY_LEVELS.values()))
        complete_factorial = len(members) == EXPECTED_RUNS and len(set(observed_combinations)) == EXPECTED_RUNS and set(observed_combinations) == expected_combinations
        if args.limit is None and not complete_factorial:
            raise ValueError("A full extraction requires exactly 1,600 unique study factor combinations (5 x 5 x 2 x 2 x 4 x 4). Use --limit explicitly for a partial smoke check.")
        selected = members[:args.limit] if args.limit is not None else members
        staging = Path(temp)
        with (staging / "run_metrics.csv").open("w", newline="", encoding="utf-8") as f_final, (staging / "consumption_timeseries.csv").open("w", newline="", encoding="utf-8") as f_time, (staging / "temporal_milestones.csv").open("w", newline="", encoding="utf-8") as f_milestone:
            final_writer = csv.DictWriter(f_final, fieldnames=FINAL_FIELDS)
            time_writer = csv.DictWriter(f_time, fieldnames=TIME_FIELDS)
            milestone_writer = csv.DictWriter(f_milestone, fieldnames=MILESTONE_FIELDS)
            for writer in (final_writer, time_writer, milestone_writer):
                writer.writeheader()
            for member in selected:
                factors = factors_from_member(member)
                if factors["run_id"] in seen:
                    raise ValueError(f"Duplicate run ID in archive: {factors['run_id']}")
                seen.add(factors["run_id"])
                payload = archive.read(member)  # ZIP CRC validated; one array at a time.
                density = np.load(io.BytesIO(payload), allow_pickle=False)
                c, a, p, eligible_count = treatment_trajectories(density)
                minutes = np.arange(c.size) * args.output_interval_seconds / 60.0
                final_writer.writerow({**factors, "consumption_fraction_surface": float(c[-1]), "active_consumed_area_fraction_1pct": float(a[-1]), "cell_consumption_cv": float(p[-1])})
                for index, (minute, consumption, area) in enumerate(zip(minutes, c, a)):
                    time_writer.writerow({**factors, "time_index": index, "elapsed_time_min": float(minute), "consumption_fraction_t": float(consumption), "active_area_fraction_t": float(area)})
                milestone_writer.writerow({**factors,
                    "final_consumption": float(c[-1]), "final_active_area": float(a[-1]),
                    "t10_consumption": first_reached(c, minutes, .10),
                    "t50_consumption": first_reached(c, minutes, .50),
                    "t80_consumption": first_reached(c, minutes, .80),
                    "t10_active_area": first_reached(a, minutes, .10),
                    "t50_active_area": first_reached(a, minutes, .50),
                    "peak_active_area": float(a.max()), "t_peak_active_area": float(minutes[np.argmax(a)]),
                    "peak_consumption": float(c.max()), "t_peak_consumption": float(minutes[np.argmax(c)]),
                    "auc_consumption": auc(c, minutes), "auc_active_area": auc(a, minutes),
                })
                rows.append({"run_id": factors["run_id"], "archive_member": member, "array_shape": list(density.shape), "dtype": str(density.dtype), "eligible_surface_cells": eligible_count, "density_member_sha256": hashlib.sha256(payload).hexdigest()})
        report = {"archive_filename": args.archive.name, "expected_study_runs": EXPECTED_RUNS, "available_density_members": len(members), "archive_contains_complete_study_factorial": complete_factorial, "processed_runs": len(rows), "partial": args.limit is not None or not complete_factorial or len(rows) != EXPECTED_RUNS, "limit_requested": args.limit, "output_interval_seconds": args.output_interval_seconds, "time_and_auc_units": "minutes", "unreached_threshold_encoding": "empty CSV field", "surface_layer": 0, "expected_eligible_surface_cells_per_run": 6084, "eligible_initial_density_threshold_kg_m3": EPS, "active_area_threshold_strictly_greater_than": .01, "patchiness_population_sd_ddof": 0, "scope": "Re-extraction from archived output, not a simulation rerun or validation of executed input settings.", "runs": rows}
        (staging / "raw_extraction_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for generated in staging.iterdir():
            generated.replace(args.output_dir / generated.name)
    print(f"Recomputed {len(rows)} of {len(members)} runs; outputs: {args.output_dir}")


if __name__ == "__main__":
    main()
