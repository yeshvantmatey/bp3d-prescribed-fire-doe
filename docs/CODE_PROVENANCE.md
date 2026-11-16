# Code provenance and reproducibility scope

The repository reproduces the manuscript's statistical comparisons and corrected Figures 4–10 from archived response metrics. The scripts do not launch new QUIC-Fire runs. The scripts were prepared from the independently verified revision scripts on 2026-11-16, preserving the calculations and plotting settings.

## Source data

- `data/source/doe_analysis_ready_response_table.csv` contains 1,600 runs and 11 retained columns. The public export preserves every retained CSV field as text, including the original numerical precision. The export removes local filesystem paths, unrelated response variables, and diagnostic columns unused by the manuscript analyses.
- `data/source/paper2_fuel_consumption_active_area_timeseries.csv` contains 97,600 rows, representing 61 output times for each of 1,600 runs. The table is a byte-for-byte copy of the canonical archived table. Each run's metadata is checked against the final-state response table.
- `data/reference/` contains small, frozen reference tables from the earlier independent verification. The reference tables let `verify_results.py` test newly recomputed results. The reference tables are not substituted for the recomputation.

The data dictionary explains the metric names and units. The archived configuration/log audit established 60 seconds between stored outputs, so `time_index` from 0 to 60 corresponds to elapsed minutes from 0 to 60. Generated trajectory tables include explicit `elapsed_time_min` and `elapsed_time_s` columns.

## Script origins

Paths in the final column identify the archived workspace revision directories used to prepare the release, rather than runtime dependencies. The full workspace is not needed to run the portable repository.

| Portable script | Role | Verified source in the archived workspace |
|---|---|---|
| `scripts/anova.py` | Pooled categorical ANOVA and independent regression check | `Paper/revisions/fig4_validation_2026-11-16/validate_anova.py` |
| `scripts/analysis.py` | Group means, contrasts, rankings, margins, threshold times, AUC and temporal means | The calculation conventions in `fig4_validation_2026-11-16`, `fig7_validation_2026-11-16`, `fig8_validation_2026-11-16` and `fig9_fig10_validation_2026-11-16` |
| `scripts/regenerate_fig4.py` | Pooled omega-squared heatmap | `Paper/revisions/fig4_pooled_2026-11-16/regenerate_fig4.py` |
| `scripts/regenerate_fig5.py` | Final-state response heatmaps | `Paper/revisions/fig5_readable_2026-11-16/regenerate_fig5.py` |
| `scripts/regenerate_fig6.py` | Wind and moisture response curves | `Paper/revisions/fig6_si_2026-11-16/regenerate_fig6.py` |
| `scripts/regenerate_fig7.py` | Strip-minus-Flank differences pooled across Broken and Dot | `Paper/revisions/fig7_pooled_2026-11-16/regenerate_fig7.py` |
| `scripts/regenerate_fig8.py` | Four-layout rankings and top-two consumption margins | `Paper/revisions/fig8_four_layouts_2026-11-16/regenerate_fig8.py` |
| `scripts/regenerate_fig9_fig10.py` | Temporal layout summary and selected consumption trajectories | `Paper/revisions/fig9_fig10_temporal_2026-11-16/regenerate_fig9_fig10.py` |
| `scripts/verify_results.py` | Independent comparison with frozen verified tables | Reference values from the corresponding figure-validation revisions |

## Statistical conventions preserved

All six experimental factors are categorical. The pooled model contains six main effects and the six selected two-way interactions recorded in `scripts/anova.py`. The design is a complete balanced factorial with one response per factor combination. Orthogonal marginal contrasts yield Type II sums of squares for this design; an independent least-squares design-matrix calculation checks the results. The helper is not intended for incomplete or unbalanced datasets, and assertions reject a broken factorial structure.

Omega-squared uses the term sum of squares minus its degrees of freedom multiplied by the residual mean square, divided by the total sum of squares plus the residual mean square. Negative estimates are set to zero to preserve the original analysis convention. The residual includes omitted interactions; it is not interpreted as independently estimated simulation noise.

Group means pool 64 runs per fuel-model/curing-state combination, 80 per fuel-model/wind or fuel-model/moisture point, 32 per fuel-model/curing-state/orientation mean, and 16 per fuel-model/curing-state/layout mean. Rankings compare all four implemented layouts. Consumption and active area are maximized; patchiness is minimized. Margins are the difference between the two best means in the objective's preferred direction. Alphabetical layout ordering is a deterministic fallback for an exact tie; the verified winning values and top-two consumption margins contain no exact tie.

Time to threshold is the first stored time with a response at or above the threshold. The scripts do not interpolate between outputs. A blank threshold time means the threshold was not reached by the end of the 60-minute run. Reach percentages include all 400 runs per layout; median threshold times include only runs reaching the threshold. Trapezoidal AUC is calculated in minutes, matching the corrected figures. The `std` column in `final_metric_summary.csv` uses the sample standard deviation (`ddof=1`); the spatial standard deviation defining each run's patchiness is a separate calculation.

The nominal wind inputs of 1, 4, 8 and 12 mph are multiplied by the exact conversion factor 0.44704 for the figure coordinates in m/s. Tick labels show 0.45, 1.79, 3.58 and 5.36. Surface moisture fractions are multiplied by 100 for percentage display.

## Completed validation

The full `python run_all.py` command passed with Python 3.12 and the versions pinned in `requirements.txt`. The checks reproduce all nine bundled reference tables to an absolute tolerance of 1e-11. The reference comparisons include all 36 pooled omega-squared values, 75 condition/metric means, 40 wind/moisture response points, 75 pooled orientation differences, 25 common winning layouts, all top-two margins, the temporal layout summaries, and 976 selected trajectory points.

All seven regenerated PNG files are byte-for-byte identical to the corrected Figures 4–10 previously delivered for the manuscript. PDF checks in the relevant figure scripts verify notation, time labels, percentage labels and numerical annotations. Rendered plots may differ in font metrics or PDF metadata on another environment; numerical comparisons are the primary reproducibility test.

Generated outputs stay under `outputs/`. The pipeline does not depend on the local manuscript PDF, personal Downloads paths, local audit JSON files, notebooks with execution history, or platform-specific artifact-authoring hooks. Source CSV files remain unchanged during execution.

## Limits

The present pipeline supports reproducibility of the archived analysis. Reproducing all original simulation inputs and rerunning the 1,600 simulations requires separate confirmation of the original generator, exact software build, model configuration and input transformations. A code release should not claim that the original simulations can be rerun from these two response tables alone.

The optional density-array extractor can reconstruct final-state and temporal metrics when the authors supply simulation outputs upon request. No density arrays or simulation archives will be publicly deposited. The normal public analysis workflow uses the processed CSVs and does not require this optional extractor.
