# Mitopipeline

Mitopipeline is a reproducible Snakemake/Python workflow for recovering and analyzing mitochondrial genomes from paired-end whole-genome sequencing reads. Version 0.1.0 was developed for a fish mitogenomics dataset of approximately 140 samples, with an emphasis on reproducibility, error handling, event reporting, and portability to future datasets.

> **Status:** v0.1.0 is a functional research pipeline and development foundation. It has been exercised on real sequencing data, but difficult assemblies, rescue behavior, full-dataset validation, and archival/submission workflows remain areas of active development.

## Features

Mitopipeline integrates the major stages of mitogenome analysis into a single configurable workflow:

- **Raw-read quality control** with FastQC
- **Read filtering and trimming** with fastp
- **Post-trimming quality control** with FastQC
- **Mitochondrial genome assembly** with GetOrganelle
- **Assembly assessment and rescue logic** for incomplete/problematic assemblies
- **Sequence identification** using BLAST
- **Mitochondrial genome annotation** using MITOS2
- **Circular genome visualization** from annotation results
- **Phylogenetic analysis** using MAFFT and IQ-TREE
- **Sample- and run-level reporting**, including optional PDF export
- **Submission/archival output generation**, including SRA-related metadata
- **Configurable stages and tool parameters** through YAML
- **Runtime sample manifests** for reproducible sample tracking
- **Structured job outputs, logging, validation, and status tracking**
- **Snakemake orchestration** for dependency-aware execution and restartable workflows

## Requirements

Mitopipeline v0.1.0 requires **Python 3.11 or newer**. The Python package declares the following dependencies:

- pandas
- openpyxl
- Biopython
- matplotlib
- pytest
- PyYAML
- Snakemake

The complete workflow also relies on external bioinformatics tools/environments for the enabled stages (for example FastQC, fastp, GetOrganelle, BLAST, MITOS2, MAFFT, and IQ-TREE). Conda environments are provided under `envs/` for workflow stages that use them.

## Repository layout

```text
mitogenome-batch-processor/
├── ctrl/
│   ├── Snakefile              # top-level Snakemake workflow
│   ├── config/                # runtime/testing configuration and manifests
│   └── rules/                 # stage-specific Snakemake rules
├── envs/                      # Conda environment definitions
├── src/mitopipeline/          # Python implementation
├── tests/                     # automated tests and fixtures
├── archival/                  # archival-related project files
└── pyproject.toml             # Python package metadata/dependencies
```

## Quick start: test the code

Clone the repository and switch to v0.1.0:

```bash
git clone https://github.com/cacayan2/mitogenome-batch-processor.git
cd mitogenome-batch-processor
git checkout feature/version-0.1.0
```

Create a Python environment and install the package in editable mode:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Run the default test suite:

```bash
pytest
```

The project configures pytest to exclude tests marked `slow` by default. Slow tests may invoke external tools, Conda, or Snakemake. To run the complete suite, including slow tests:

```bash
pytest -m "slow or not slow"
```

## Quick start: test the workflow with bundled FASTQ data

A testing configuration is provided at:

```text
ctrl/config/home_testing_config.yaml
```

It points to bundled paired-end FASTQ fixtures under:

```text
tests/fixtures/fastq_real/
```

Before running it, edit `output_root` in `ctrl/config/home_testing_config.yaml` to a writable location on your system. Review the enabled stages and external-tool paths/environments as well; the supplied testing configuration was written for the development environment and is not guaranteed to be portable without modification.

A safe first check is a Snakemake dry run:

```bash
python -m mitopipeline.launcher.pipeline_launcher \
  --config ctrl/config/home_testing_config.yaml \
  --snakefile ctrl/Snakefile \
  --cores 4 \
  --use-conda \
  --dry-run \
  --printshellcmds
```

If the dry run resolves successfully and the required external tools/environments are available, remove `--dry-run` to execute the workflow:

```bash
python -m mitopipeline.launcher.pipeline_launcher \
  --config ctrl/config/home_testing_config.yaml \
  --snakefile ctrl/Snakefile \
  --cores 4 \
  --use-conda \
  --printshellcmds
```

The launcher validates/discovers the sample inputs, creates a job-specific runtime manifest and runtime configuration, and then invokes Snakemake.

## Running your own paired-end FASTQ data

Mitopipeline can operate from either a sample manifest or an input directory containing paired FASTQ files.

The minimum manifest fields are:

```text
sample_id    r1    r2
```

For example:

```text
sample_id    r1                    r2
sample_001   sample_001_1.fastq.gz sample_001_2.fastq.gz
```

Alternatively, set `manifest: null` and provide `input_directory` in the YAML configuration. The launcher can discover paired FASTQ files and write a validated runtime manifest automatically.

At minimum, review these configuration fields before a run:

```yaml
output_root: /path/to/outputs
manifest: /path/to/samples.tsv   # or null when using input_directory
input_directory: /path/to/fastq
job_id: my_job

stages:
  qc_raw: true
  trimming: true
  qc_trimmed: true
  assembly: true
  annotation: true
  visualization: true
  phylogeny: true
  reporting: true
  pdf_export: true
```

Individual stages can be enabled or disabled, and tool-specific parameters are defined under the `tools:` section of the YAML configuration.

## Outputs

Each run is organized beneath its configured output root and job ID. Depending on the enabled stages, outputs include directories such as:

```text
<output_root>/<job_id>/
├── qc/
├── trimming/
├── assembly/
├── annotation/
├── visualization/
├── phylogeny/
├── reporting/
└── submission/
```

The launcher also creates job-level runtime metadata, including a validated sample manifest and runtime configuration. Stage completion files and structured outputs allow Snakemake and Mitopipeline to track what has been produced and what still needs to run.

## Configuration

Example configurations are available under `ctrl/config/`. The configuration controls:

- input/output locations
- job ID
- enabled pipeline stages
- thread counts
- fastp filtering parameters
- GetOrganelle settings
- MITOS2 settings
- BLAST behavior
- visualization settings
- phylogenetic settings
- reporting and archival stages

For reproducible analyses, preserve the runtime configuration and validated sample manifest associated with each job.

## Development status

Version 0.1.0 established the initial end-to-end architecture and demonstrated major pipeline components on real sequencing data. Current limitations include robust recovery of difficult/fragmented mitochondrial assemblies, completion and validation across the entire dataset, further architectural refinement, documentation/maintenance work, and completion of NCBI archival/submission workflows.

Development after v0.1.0 is intended to improve these areas without changing the core goal: reproducible, scalable recovery and analysis of mitochondrial genomes from whole-genome sequencing data.
