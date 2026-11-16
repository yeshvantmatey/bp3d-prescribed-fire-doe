# BurnPro3D prescribed-fire DOE analysis

Reproduce the statistical analyses and corrected Figures 4–10 for a 1,600-run prescribed-fire simulation ensemble. BurnPro3D is the simulation workflow used for the study, QUIC-Fire is the fire model, and DOE means design of experiments.

The analysis compares consumption fraction C(T), active treatment area A(T), and consumption patchiness P(T) at the final time T, along with consumption and active-area development over time. The experiments span five fuel models, five curing-state categories, four ignition layouts, four wind speeds, and four surface fuel-moisture levels.

**Release status:** local candidate prepared for review. Repository owner, licenses, creator metadata, release version, and archival DOIs remain to be finalized. No public availability is claimed by this draft.

## Run the analysis

Use Python 3.12 in a separate environment. From the repository root:

```sh
python -m pip install -r requirements.txt
python run_all.py
```

The command recalculates the pooled analysis of variance (ANOVA), omega-squared effect sizes, condition means, wind/moisture responses, pooled Strip-minus-Flank contrasts, four-layout rankings and top-two margins, threshold times, reach percentages, and area under the curve (AUC). It checks the recalculated values against independently verified reference tables, then generates Figures 4–10 as PDF and PNG files.

Outputs are written to `outputs/`. The source CSVs are never modified. Any failed verification stops the pipeline. A successful process produces `outputs/analysis_verification.json` and `outputs/reproduction_verification.json` plus figure-specific checks. The checked dependencies are pinned in `requirements.txt`.

## Data and code

| Location | Contents |
|---|---|
| `data/source/doe_analysis_ready_response_table.csv` | 1,600 rows with the run identifier, experimental categories, and C(T), A(T), P(T); local paths and unrelated response fields removed |
| `data/source/paper2_fuel_consumption_active_area_timeseries.csv` | 97,600 rows containing C(t) and A(t), with 61 stored outputs per run |
| `data/reference/` | Verified numeric results used to detect changes in the reproduced analyses |
| `scripts/analysis.py` and `scripts/anova.py` | Statistical and comparative calculations |
| `scripts/regenerate_fig*.py` | Corrected Figures 4–10 |
| `scripts/verify_results.py` | Checks against the independent reference CSVs |
| `scripts/recompute_metrics_from_density.py` | Optional metric extraction from archived density arrays |
| `docs/DATA_DICTIONARY.md` | Variables, units, denominator rules, missing values, and aggregation |
| `docs/CODE_PROVENANCE.md` | Origins and adaptation of analysis and figure scripts |
| `docs/SIMULATION_PROVENANCE.md` | Available simulation evidence and unresolved execution provenance |
| `docs/RELEASE_CHECKLIST.md` | Remaining metadata and publication steps |
| `CITATION.cff` | Draft software citation metadata |

The source CSV preserves `wind_speed_mph` and moisture ratios. Figures convert nominal wind values to m/s using 0.44704 and moisture ratios to percentages using 100. `time_index` is an output index with 60-second spacing, so indices 0–60 correspond to 0–60 minutes. Threshold blanks mean the threshold was not reached, while reach percentages include all 400 runs per layout. See the dictionary for full definitions.

## Optional use with simulation files supplied upon request

Files for all 1,600 simulations are retained locally by the authors and are available upon request. Simulation arrays, solver inputs, logs, and simulation archives are excluded from the public GitHub and Zenodo release. The normal analysis workflow requires only the processed CSVs. The optional extraction script is provided for readers who separately obtain the simulation outputs upon request; it accepts an output ZIP retaining the archive-relative run paths:

```sh
python scripts/recompute_metrics_from_density.py --archive /path/to/density_outputs.zip --output-dir outputs/from_density
```

For a deliberately partial smoke check, append `--limit 1`. The extraction report identifies the processed runs, array hashes, eligible-cell counts, output interval, and whether the extraction is partial. The command does not invoke a simulator. It writes separate results so the supplied source CSVs remain available for comparison.

Zenodo will hold the versioned processed CSVs, summary tables, figure-value tables, and documentation. The processed CSV copies currently included in this local GitHub candidate make the example self-contained; they may remain as convenience mirrors of the same versioned Zenodo data. They are derived response tables, not simulation files.

## Reproducibility scope

The public processed CSVs support reproducing the statistical analyses and Figures 4–10. Independent extraction of metrics from spatial density fields, or reconstruction of the spatial example in Figure 3, requires the simulation outputs supplied separately upon request. The public CSVs contain the final patchiness values; they do not contain spatial density arrays.

The original simulation-generation workflow has not been recovered. Saved request metadata contain a QUIC-Fire version label and repeated curing defaults that do not establish all five executed curing configurations. Complete solver input decks and the loading-to-density conversion remain unresolved. The repository therefore documents analysis of saved outputs; it does not claim exact rerunning of the original simulation ensemble.

## Citation and licensing

The draft creator list in CITATION.cff follows the manuscript byline and needs review for the software release. Add the final dataset DOI, code version, and repository URL before publication. Archive the matching code snapshot with the dataset or link a separate software DOI if one is created.The [MIT License](LICENSE) applies to the analysis code only. A separate license for the processed datasets will be specified in the Zenodo record. QUIC-Fire and BurnPro3D engine code are not included.

The manuscript availability statement should be updated only after the actual deposited files and links are confirmed. See the release checklist for the recommended GitHub and Zenodo sequence.
