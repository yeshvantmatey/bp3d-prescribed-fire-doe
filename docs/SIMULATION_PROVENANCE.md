# Simulation-output and code provenance audit

Checked 2026-11-16. Original files were read only. No simulation was rerun and no manuscript text was changed. The ZIP central directory and small JSON members were inspected; the 4 GB archive was not unpacked. Two density members were loaded for a limited extraction-script check.

## Scope that the release can support

The selected CSVs and portable analysis scripts can support reproduction of the paper's statistical analyses and corrected Figures 4–10 from the archived response data. The authors retain files for all 1,600 simulations locally and make them available upon request. The public release contains processed CSVs and code only; metric re-extraction from simulation fields is an optional workflow for recipients of those files.

The available material does not yet support an unqualified claim that another researcher can rerun all 1,600 QUIC-Fire simulations with the originally executed inputs. Original generation code, solver input decks, complete execution provenance, and the loading-to-density transformation were not found in the inspected project and archive.

## Original notebook pipeline

Notebook cell numbers below are zero based. The notebooks were parsed, not executed.

| Source | Relevant work | Release treatment |
|---|---|---|
| `Codes/Paper_1.ipynb`, cells 1, 5, 22, 38 | Inventory of stored arrays; final surface consumption; active area and patchiness; assembly of the response CSV | Preserve as provenance; extract the paper-relevant computation into portable scripts |
| `Codes/Paper_1.ipynb`, cells 50–51 | Pooled Type II ANOVA and omega-squared | Use the verified pooled implementation and retain the original formula/model scope |
| `Codes/Paper_2.ipynb`, cells 12 and 15 | All-run consumption/active-area trajectories; first threshold crossings and trapezoidal integrals | Preserve extraction rules and explicitly identify minutes as the stored numerical time unit |
| `Codes/Paper_2.ipynb`, other analysis/plotting cells | Layout comparisons, rankings, temporal summaries and plots | Do not distribute as the canonical runnable figure pipeline without reconciling source/output differences |
| `Codes/Paper_3.ipynb` | Clustering/regime analyses beyond the current paper's treatment-analysis scope | Exclude from the minimal release for this manuscript |
| `Codes/papaer_main.ipynb` | Zero-byte file | Empty; cannot serve as the missing ensemble generator |

`Paper_2.ipynb` source and saved outputs represent different analysis scopes in some cells. In particular, separated Broken/Dot comparisons in `paper_2/tables` differ from the four-layout rankings and pooled orientation contrasts required by the current manuscript. Use the verified corrected scripts and CSVs; do not present all similarly named folders as interchangeable.

## Archived output inventory

`Data_Archive.zip` is 4,002,347,148 bytes (about 4.00 GB). The central directory contains 25,821 members totaling 18,165,710,212 uncompressed bytes, including 19,200 NumPy arrays: 1,600 members for each of twelve array types.

The twelve array names are `co_emissions.npy`, `emissions_distribution.npy`, `fire-energy_to_atmos.npy`, `fire-reaction_rate.npy`, `fuels-dens.npy`, `fuels-moist.npy`, `pm_emissions.npy`, `topography.npy`, `water_emissions.npy`, `windu.npy`, `windv.npy`, and `windw.npy`.

The paper's treatment metrics use `fuels-dens.npy` only. The 1,600 density members total 1,649,254,400 bytes uncompressed and **66,931,209 bytes compressed** in the current ZIP. These sizes document the local archive only. No density subset will be publicly deposited; the simulation files remain available upon request.

When fulfilling a request for raw outputs, preserve the original `fuel_model/scenario/ws_..._fm_.../arrays/fuels-dens.npy` hierarchy and identify the supplied files with run IDs and checksums. Configuration metadata supplied with those files retain the qualifications below. Simulation outputs and configuration files are outside the public deposit scope.

Prior all-run validation established that every density array is float16, with 1,088 shapes `(61, 1, 80, 80)` and 512 shapes `(61, 2, 80, 80)`. Only vertical layer zero is used. Every run has 6,084 initially positive surface cells and a 316-cell zero-density border. The initial surface is uniform within the eligible cells. These output properties were checked in the earlier full audit, not rechecked for every run in the current task.

## Input-provenance limitations to disclose

1. **Version metadata:** all 1,599 standalone `inputs.json` records state `quicfire_version = "6.1.2-dist"`. Earlier manuscript wording reported 6.0.0. A configuration version field is not an executable checksum or a complete record of the completed run environment.
2. **Curing and loading:** all standalone records repeat `uniform.curing_live_herbaceous = 25` and `uniform.curing_live_woody = 10`; `uniform.density` and `uniform.fuel_model` are null. Scenario paths identify five curing states, but these JSON fields do not establish the intended five state-specific settings or explain their implementation. The original loading-to-initial-density conversion and complete generator remain unresolved.
3. **One missing standalone input record:** `GR2/GR2_early_spring_before_greenup_Flank_Dot/ws_4.0_fm_0.08` has an archived density array but no standalone `inputs.json`. Earlier clock/unit audits recovered configuration from `run_dict.parameters` in the corresponding failure JSON. That record is marked as an error and must not be described as a verified completed-run input deck.
4. **Time:** the available configuration specifies a 3,600-second run and 60-second stored-output interval. Arrays contain 61 times; notebook output indices 0–60 therefore correspond numerically to minutes. No independent timestamp-coordinate arrays or complete solver input decks were found. Timing provenance should retain the prior audit qualification.
5. **Wind:** configured levels are 1, 4, 8 and 12 mph, with a 6.096 m wind-reference height. Nominal SI display conversion is mph multiplied by 0.44704. A prior failed-attempt log provides approximate conversion evidence, not proof of the exact internal values in every completed run.
6. **Ignition schedules:** archive metadata does not independently establish equal total ignited-cell counts or complete progressive ignition timing. Do not claim that publishing the current CSVs resolves the ignition-effort/timing question.

No `.py`, `.ipynb`, `.inp`, `.in`, `.yaml`, `.yml` or `.sh` solver/generator members were found in the archive. Six failed-attempt JSON files are present; these are troubleshooting history rather than canonical completed-run records.

## Optional portable extraction script prepared

`scripts/recompute_metrics_from_density.py` accepts `--archive` and `--output-dir`. It reads one density member at a time, verifies the ZIP CRC, and writes:

- `run_metrics.csv`: final `C(T)`, `A(T)` and `P(T)` using the existing column names and run factors.
- `consumption_timeseries.csv`: all `C(t)` and `A(t)` values, output indices and explicit elapsed minutes.
- `temporal_milestones.csv`: first threshold times, final and peak responses, and trapezoidal AUC values in minutes. Empty threshold fields mean the threshold was not reached.
- `raw_extraction_audit.json`: processed-run count, partial-run status, conventions, member paths and SHA-256 checksums.

The script uses float64 computation, surface layer zero, initially positive density above `1e-12 kg m^-3`, nonnegative density loss, active area defined by local consumption strictly greater than 0.01, and population standard deviation (`ddof=0`) for patchiness. Its default output interval is 60 seconds, exposed as an argument rather than inferred from filenames. Run/scenario labels are recovered from archived directory names; the script does not claim those labels verify executed input settings.

Full extraction requires all 1,600 unique factor combinations with the study's `5 x 5 x 2 x 2 x 4 x 4` levels and 6,084 eligible cells per processed run. `--limit` explicitly marks a partial check, including if the archive itself contains fewer than 1,600 members. A truncated archive cannot be reported as a complete study extraction.

Partial verification used the first sorted one-layer run. The three final metrics matched the established CSV to a maximum absolute difference of `1.65e-13`; all 61 consumption/active-area points and all temporal milestones matched within `1e-12`, including missing threshold values. A separate two-layer sample, GS1 spring-after-greenup Strip Broken at 1 mph and 6% moisture, matched all three final metrics within `6.67e-16`. This is a two-array smoke check of the new portable script, not a new all-run validation. The earlier independent raw-output audit verified final metrics for all 1,600 runs.

## Portability, privacy and licensing observations

The original analysis code is licensed under the [MIT License](../LICENSE). The processed CSV datasets in `data/source/` and `data/reference/` are licensed under [CC BY 4.0](../LICENSE-DATA.md). QUIC-Fire and BurnPro3D engine code are not included or relicensed by the analysis repository.

Notebook sources contain personal absolute Windows paths (four code cells in Paper_1, two in Paper_2, two in Paper_3); all three notebooks retain stored outputs. Use portable scripts or cleared, reconciled notebooks for release. A keyword scan found no common credential markers (`api_key`, `access_token`, password, authorization, bearer) in these notebook files or six failure logs. This was a limited targeted scan, not a comprehensive secrets certification. Failure logs and irrelevant notebook outputs are unnecessary in the minimal public release.

## Items needed for complete simulation reruns

- Original ensemble generation and submission script/notebook and its source revision.
- Complete per-run solver input decks or an independently verified reconstruction, including five curing settings and the loading-to-density transformation.
- Executable/container version and immutable identifier, dependency/configuration records and any required access instructions.
- Complete ignition masks and time schedules, or the versioned algorithm that generates them.
- A completed-run manifest linking stable run IDs, output hashes, configuration/deck hashes and execution identity.

These missing elements constrain claims about rerunning the simulations. They do not prevent a clearly scoped release of the validated response data and code for reproducing the reported postprocessing analyses.
