# Release decisions and publication sequence

This directory is a local preparation of an analysis repository. No GitHub repository, Zenodo record, public release, or DOI has been created by this preparation.

## Decisions before publication

1. Confirm the GitHub owner and repository name. Proposed name: `bp3d-prescribed-fire-doe`. The connected personal account is `yeshvantmatey`; an institutional owner can be used instead.
2. Confirm the dataset/software creator lists, order, affiliations, and ORCIDs. CITATION.cff is a draft based on the manuscript byline. Dataset authorship and software authorship may differ.
3. Select licenses for code and data and confirm any applicable ownership requirements. Proposed choices for review are MIT for original analysis code and CC BY 4.0 for the data/documentation. No license has been applied yet. Do not assume QUIC-Fire or BurnPro3D engine code can be redistributed under the analysis-code license.
4. Public-data scope is decided: publish processed CSVs and supporting tables only. Keep files for all 1,600 simulations locally and supply them upon request. Exclude arrays, simulation input decks, logs, and simulation archives from both GitHub and Zenodo.
5. Confirm a release version and descriptive title. Use the same version in the repository release, software citation, dataset metadata, and checksums.
6. Review the known provenance limits. Saved outputs support analysis reproduction, but the original simulation-generation workflow and fully reconciled execution inputs have not been recovered. The data availability statement must not promise exact rerunning of the original ensemble.

## Recommended records

Create a Zenodo dataset record for the processed CSVs, derived tables, dictionary, provenance, and checksums. No simulation files are included. Maintain the analysis code in GitHub and archive a matching tagged code snapshot with the Zenodo dataset or as a separate software record. A second DOI is optional. Link the dataset, code release, and paper with related identifiers. Keep the data and code licenses explicit.

For a compact combined record, Zenodo also supports mixed data/software deposits with the applicable licenses. A separate data record makes it easier to update large data independently of code.

## Publication sequence

1. Complete the creator, license, and version choices. The processed-data-only release scope is already decided.
2. Run the documented reproduction command from a clean checkout and retain the validation report and environment versions.
3. Freeze the dataset and record SHA-256 hashes for the release files.
4. Create the chosen GitHub repository, push the reviewed code, and verify the README and citation metadata online.
5. Create a Zenodo dataset draft, upload the reviewed files, fill the metadata, and reserve its DOI if desired.
6. Enable the GitHub repository in Zenodo before making the code release if automatic release archiving is preferred. New releases are ingested automatically after integration is enabled.
7. Publish the data and code records when ready, and verify the DOI landing pages and downloadable files.
8. Update the manuscript data/code availability statement with the actual dataset DOI, GitHub URL and code version, an optional separate software DOI, the supported reproducibility scope, and simulation-file availability upon request.

A DOI reserved in a manual Zenodo draft is not registered until publication. Zenodo's GitHub integration does not allow preregistering the code-release DOI; a manual software upload is an alternative. Do not put invented or placeholder DOIs into the submitted manuscript.

## Official guidance checked on 2026-11-16

- [Create a Zenodo upload and reserve a DOI](https://help.zenodo.org/docs/deposit/create-new-upload/)
- [Files, open formats, and size limits](https://help.zenodo.org/docs/deposit/manage-files/)
- [Licenses and mixed-license uploads](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
- [Enable GitHub integration](https://help.zenodo.org/docs/github/enable-repository/)
- [Archive a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/)
- [CITATION.cff metadata](https://help.zenodo.org/docs/github/describe-software/citation-file/)
- [DOI reservation and GitHub releases](https://support.zenodo.org/help/en-gb/24-github-integration/73-can-i-pre-reserved-a-doi-before-a-github-release)

Zenodo currently permits up to 100 files and 50 GB per record under its standard quota. When both CITATION.cff and .zenodo.json exist, Zenodo uses .zenodo.json for GitHub-release metadata. This draft therefore uses CITATION.cff only; avoid adding a second competing metadata file without maintaining both.
