```{=typst}
#set page(
  paper: "us-letter",
  margin: (x:0.5in, y:0.5in)
)
```

# NCBI Archival Requirements

## Purpose

One of the long-term goals of the mitopipeline project is to prepare mitochondrial genome projects for archival within the National Center for Biotechnology Information (NCBI). While the primary objective of the pipeline is the automated assembly, annotation, and analysis of mitochondrial genomes, the resulting biological data ultimately become most valuable when deposited into publicly accessible databases where they may be reproduced, cited, and reused by other researchers.

At present, the mitopipeline does **not** submit data directly to NCBI. Instead, the objective is to prepare submission-ready files and metadata that minimize the amount of manual work required by investigators. Submission itself should remain a human-reviewed process, allowing principal investigators to verify metadata, approve release dates, and resolve validation warnings before data become publicly available.

This document summarizes the NCBI submission ecosystem, identifies the information required for archival, distinguishes automatically generated metadata from manually supplied metadata, and proposes an architecture for integrating archival preparation into future versions of the pipeline.

---

# Overview of the NCBI Submission Ecosystem

Archiving a mitochondrial sequencing project typically involves four independent but interconnected NCBI databases.

## BioProject

A BioProject represents the research project itself. It provides high-level information describing the scientific objectives, investigators, funding sources, and overall scope of the study.

A single BioProject may contain hundreds or even thousands of biological samples.

Typical information includes:

- Project title
- Project description
- Investigators
- Institution
- Funding information
- Public release date

Once created, the BioProject receives a unique accession number (for example, **PRJNA123456**) that links every downstream submission associated with the project.

---

## BioSample

A BioSample describes the biological specimen from which sequencing data were obtained.

Unlike a BioProject, which describes the research effort as a whole, each BioSample corresponds to a single organism, tissue, environmental sample, or collection event.

Examples include:

- One individual fish
- One environmental DNA filter
- One tissue biopsy

Each BioSample receives its own accession number (for example, **SAMN12345678**).

Multiple sequencing runs may reference the same BioSample.

---

## Sequence Read Archive (SRA)

The Sequence Read Archive stores the original sequencing data generated during the experiment.

Typical submissions include:

- Paired-end FASTQ files
- Single-end FASTQ files
- BAM or CRAM files (when appropriate)

The SRA does **not** store assembled mitochondrial genomes.

Instead, it preserves the original sequencing reads used to generate downstream assemblies.

Each sequencing run receives an accession such as:

- SRRxxxxxxx (Run)
- SRXxxxxxxx (Experiment)

---

## GenBank

GenBank stores assembled nucleotide sequences together with their biological annotations.

For mitopipeline, GenBank is the ultimate destination for assembled mitochondrial genomes produced by GetOrganelle and annotated using MITOS2.

Typical submissions include:

- assembled FASTA
- annotation feature table
- source modifiers
- organism metadata

Accepted genomes receive an accession number such as

```
OQ123456
```

which may subsequently be cited in publications.

The pipeline should therefore prepare outputs compatible with each stage of this hierarchy rather than treating submissions as independent tasks.

---

# Pipeline-Generated Metadata

One design objective of mitopipeline is to automatically generate every piece of metadata that can be inferred from the analysis itself.

Examples include:

| Metadata | Source |
|-----------|--------|
| Sample ID | Manifest |
| FASTQ filenames | Manifest |
| FASTA assembly | GetOrganelle |
| Assembly statistics | Assembly parser |
| GC content | Assembly parser |
| Genome length | Assembly parser |
| Annotation feature counts | MITOS2 parser |
| GFF annotation | MITOS2 |
| Gene order | MITOS2 |
| MD5 checksums | Pipeline |
| Software versions | Pipeline |
| Runtime statistics | Pipeline |

These values should require no manual intervention.

---

# Investigator-Supplied Metadata

Many submission fields cannot be inferred computationally and therefore must be provided by the principal investigator or laboratory personnel.

Examples include:

| Metadata | Source |
|-----------|--------|
| Organism name | PI |
| Collection date | PI |
| Collection locality | PI |
| Latitude | PI |
| Longitude | PI |
| Isolation source | PI |
| Voucher information | PI |
| Sequencing platform | PI |
| Library preparation method | PI |
| BioProject title | PI |
| Project description | PI |
| Publication information | PI |

The pipeline should never attempt to fabricate these values.

Instead, missing information should be reported clearly to the user before submission preparation completes.

---

# Proposed Metadata Architecture

Rather than embedding archival metadata directly into the sample manifest, mitopipeline should maintain a dedicated metadata table describing BioSample- and submission-specific information.

An example organization is shown below.

```
metadata/

    submission_metadata.tsv
```

Each row corresponds to one biological sample and contains only information requiring investigator input.

During archival preparation, the pipeline combines this metadata with automatically generated assembly and annotation statistics to produce submission-ready files.

Separating biological metadata from sequencing manifests improves maintainability and allows metadata to evolve independently of workflow execution.

---

# Proposed Pipeline Outputs

Future versions of mitopipeline should generate an archival package rather than performing automatic submission.

An example directory structure is shown below.

```
outputs/

    ncbi/

        biosample/
            biosample_metadata.tsv

        sra/
            sra_metadata.tsv
            fastq_manifest.tsv
            md5_checksums.tsv

        genbank/

            sample_001/
                sample_001.fasta
                sample_001.tbl
                sample_001.gff
                sample_001_source_modifiers.tsv

            sample_002/
                ...

        submission_checklist.md
```

These files should be immediately suitable for review and upload through the NCBI Submission Portal.

---

# Submission Validation

Before archival preparation is considered complete, the pipeline should validate that every required component is available.

Examples include:

✓ Assembly FASTA exists

✓ MITOS2 annotation completed

✓ Raw FASTQ files available

✓ Required metadata present

✓ Checksums generated

If required metadata are missing, the pipeline should produce a human-readable report describing outstanding issues.

For example,

```
Submission Blockers

Sample:
Common Carp

✓ Assembly present

✓ Annotation present

✓ FASTQ files present

✗ Latitude missing

✗ Longitude missing

✗ Voucher information missing
```

This approach allows investigators to resolve missing information before beginning the submission process.

---

# Scope of the Pipeline

The mitopipeline should prepare submission-ready files but should **not** perform automatic submission to NCBI.

Maintaining a human review step provides several advantages.

- Metadata may be verified before publication.
- Release dates may be adjusted.
- Validation warnings may be reviewed.
- Submission credentials remain outside the pipeline.
- Investigators retain complete control over public data release.

Future versions of the software may investigate automated interaction with NCBI submission APIs, but this functionality is intentionally considered outside the scope of the current project.

---

# Future Development Roadmap

Several future epics naturally follow this design document.

1. Generate BioSample metadata tables from pipeline outputs.
2. Generate SRA metadata tables and FASTQ manifests.
3. Convert MITOS2 annotations into GenBank feature tables.
4. Generate source modifier files.
5. Produce MD5 checksum manifests.
6. Validate submission completeness.
7. Generate submission-ready archival packages.
8. Investigate automated interaction with NCBI submission services.

---

# Key Takeaways

- NCBI archival consists of BioProject, BioSample, SRA, and GenBank submissions.
- The pipeline can automatically generate much of the required technical metadata.
- Investigator-supplied biological metadata should remain separate from sequencing manifests.
- The pipeline should prepare submission-ready packages rather than performing automatic submission.
- Future archival support should focus on reproducibility, validation, and minimizing manual effort while preserving investigator oversight.