# Release procedure

Repository: [yeshvantmatey/bp3d-prescribed-fire-doe](https://github.com/yeshvantmatey/bp3d-prescribed-fire-doe).

## Confirmed release scope

- Original analysis code uses the [MIT License](../LICENSE).
- Processed CSV datasets in `data/source/` and `data/reference/` use [CC BY 4.0](../LICENSE-DATA.md).
- The software citation lists Yeshvant Matey, Raymond de Callafon, Melissa Floca, Daniel Crawl, Leticia Lee, and Ilkay Altintas in that order, as confirmed by the corresponding author. The citation metadata are in [CITATION.cff](../CITATION.cff).
- Files for all 1,600 simulations remain with the authors and are available upon request. Simulation arrays, input decks, logs, and simulation archives are excluded from the public repository and deposit.
- The public package reproduces analyses and Figures 4-10 from processed data. Complete reconstruction and rerunning of the original simulations requires additional execution provenance; see [SIMULATION_PROVENANCE.md](SIMULATION_PROVENANCE.md).

## Prepare and publish a version

1. Review the changed files and select a release version. Keep the version in the software citation consistent with the GitHub release tag. Add a release date and archival DOI only when the values are known.
2. Run `python run_all.py` when code, dependencies, or input data change. Compare the generated results with the reference tables and inspect affected figures. For documentation-only edits, verify links, licensing scope, and file integrity.
3. Refresh `SHA256SUMS.txt` after all file edits. The list covers every distributed file except itself; it excludes generated outputs, caches, and Git's internal directory. The hashes identify the exact release files.
4. Commit the reviewed files, confirm that simulation files are absent, and create the GitHub release from the checked commit. Set repository visibility according to the intended publication stage.
5. Archive the matching processed CSVs, supporting results, documentation, and code version on Zenodo or another suitable archive. Confirm dataset creators, version, descriptive metadata, and the applicable code/data licenses. The data may be included with a frozen code snapshot or linked to a separate software record; a second DOI is optional.
6. If using Zenodo's GitHub integration, enable the repository before creating the release intended for automatic archiving. If the release already exists, a manual software upload is also available.
7. Verify the published archive, DOI landing page, and downloadable files. Add the actual archival identifier to the repository citation and manuscript availability statement. Describe the processed data as public only after publication, and retain simulation-file availability upon request.

## Supporting documentation

The [data dictionary](DATA_DICTIONARY.md) explains variables and units. [Code provenance](CODE_PROVENANCE.md), [data export mapping](DATA_EXPORT_MANIFEST.json), and [reproduction checks](REPRODUCTION_CHECK.json) document the verified analysis and export. No simulation rerun is implied by successful postprocessing checks.

## Official guidance

- [Create a Zenodo upload and reserve a DOI](https://help.zenodo.org/docs/deposit/create-new-upload/)
- [Licenses and mixed-license uploads](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
- [Enable GitHub integration](https://help.zenodo.org/docs/github/enable-repository/)
- [Archive a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/)
- [CITATION.cff metadata](https://help.zenodo.org/docs/github/describe-software/citation-file/)

A DOI reserved in a manual Zenodo draft is registered when the record is published. If both CITATION.cff and .zenodo.json are supplied to Zenodo's GitHub integration, Zenodo uses .zenodo.json for its metadata. Maintain one authoritative metadata source for the archive.
