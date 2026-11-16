# Data dictionary

## Scope and identifiers

The experiment contains 1,600 runs: five fuel models, five curing-state categories, four ignition layouts, four wind speeds, and four surface fuel-moisture levels. Ignition layout combines two orientations and two continuity patterns. The source filenames and column names are retained so published calculations can be traced to the original analysis. In prose, vegetation describes plants and their condition; fuel is retained for combustible material, model names, moisture inputs, and consumption metrics.

`run_id` is the stable join key for one simulation. Its text encodes fuel model, condition, layout, wind, and moisture. Treat the complete string as an identifier. The final-state table has one row per run. The time-series table has 61 rows per run; its unique key is `(run_id, time_index)`.

## Experimental inputs

| Column | Meaning | Values or units |
|---|---|---|
| `run_id` | Simulation identifier | Text; unique in the final-state table |
| `fuel_model` | Scott and Burgan fuel-model category | GR2, GS1, GS2, SH2, SH5 |
| `curing_state` | Seasonal condition label used in the archived analysis | Five categories listed below |
| `ignition_pattern` | Implemented ignition layout | Strip_Broken, Strip_Dot, Flank_Broken, Flank_Dot |
| `ignition_family` | Ignition-line orientation | Strip: perpendicular to the fixed wind direction; Flank: parallel |
| `ignition_structure` | Ignition continuity | Broken: nominal 40 m segments and 20 m gaps; Dot: nominal 2 m segments and 20 m gaps |
| `wind_speed_mph` | Prescribed wind speed stored in the source CSV | 1, 4, 8, 12 mph; multiply by 0.44704 for m/s |
| `surface_moisture` | Surface fuel moisture, expressed relative to dry mass | 0.06, 0.08, 0.10, 0.12; multiply by 100 for percent |

The five curing-state labels are `early_spring_before_greenup`, `spring_after_greenup`, `early_summer_senescence`, `fall_with_greenup`, and `fall_without_greenup`. These labels identify analysis groups. The archived request metadata does not independently establish the five executed curing configurations; see the provenance and release notes.

The exact wind conversion gives 0.44704, 1.78816, 3.57632, and 5.36448 m/s. Display rounding must not change the stored values or grouping.

The conversion describes the nominal CSV input levels. The available archive does not establish the exact internal conversion used by every completed simulator run.

## Final-state response columns

Let T be the final output time, 3,600 s. The metrics use the surface density layer, not all vertical vegetation layers. Eligible cells have initial density greater than 10^-12 kg/m^3. The archived runs contain 6,084 eligible cells on an 80 by 80 horizontal grid; the initially zero-density border is excluded.

| Column | Manuscript notation | Definition | Units |
|---|---|---|---|
| `consumption_fraction_surface` | C(T) | Sum of nonnegative surface density loss divided by the initial density sum over eligible cells | Fraction, dimensionless |
| `active_consumed_area_fraction_1pct` | A(T) | Fraction of eligible cells whose local consumption fraction is strictly greater than 0.01 | Fraction, dimensionless |
| `cell_consumption_cv` | P(T) | Spatial population standard deviation of local consumption fraction divided by its spatial mean, over all eligible cells | Dimensionless coefficient of variation |

The local consumption fraction is the nonnegative density decrease divided by the initial density of the same cell. Cells with zero consumption remain in the spatial mean and standard deviation. The population standard deviation uses a denominator equal to the number of eligible cells (`ddof=0`). Patchiness is undefined if mean local consumption is zero; do not replace that condition with a physical zero. All final-state metrics in the supplied ensemble are populated.

## Time-series columns

| Column | Meaning | Units |
|---|---|---|
| `time_index` | Stored-output index, 0 through 60 | Integer index; elapsed seconds = 60 times index; elapsed minutes = index |
| `consumption_fraction_t` | C(t), evaluated with the same density-loss definition | Fraction, dimensionless |
| `active_area_fraction_t` | A(t), evaluated with the same eligible-cell definition and strict 1% threshold | Fraction, dimensionless |

The source has 97,600 rows (1,600 runs times 61 outputs). Keep `time_index` as the archived column name and use elapsed time, with stated units, on plots. No time-series patchiness column was stored in this CSV; spatial density arrays are required to recompute P(t).

The 60-second spacing is supported by archived duration/output settings and available logs. Independent timestamp-coordinate arrays were not saved for every completed run.

## Derived quantities

Threshold time is the first stored output at or above a specified consumption or active-area fraction. A blank threshold time means the threshold was not reached during the 60 min simulation. It is not a failed run or a time of zero. Threshold medians include only runs that reach the threshold; reach percentages use all 400 runs per layout.

Area under the curve (AUC) integrates C(t) or A(t) using the trapezoidal rule. AUC in the release is expressed in minutes because the responses are dimensionless and successive outputs are one minute apart. AUC combines response magnitude and timing; it is not a pure rate.

Final-state group means pool 64 runs per fuel-model/curing-state combination and 16 runs per individual layout within a combination. Pooled Strip-minus-Flank contrasts average across both continuity patterns and the 16 wind/moisture combinations, giving 32 runs per orientation mean. Four-layout rankings compare means of 16 runs per layout. Consumption margins subtract the second-largest layout mean C(T) from the largest.

The pooled analysis of variance (ANOVA) treats the six factors as categorical and includes the selected interactions documented in the analysis script. Omega-squared effect sizes describe variation within the saved ensemble. The deterministic runs do not supply independent field-replicate uncertainty.

## Public export

The public final-state CSV retains the identifier, seven factor/layout columns, and three final-state metric columns. Personal filesystem paths and fields for unrelated energy, emissions, and vertical-wind analyses are excluded. Retained CSV values must match the original cells exactly. The time-series CSV contains no filesystem paths and can be preserved unchanged. No source numerical values are rescaled or overwritten during export.
