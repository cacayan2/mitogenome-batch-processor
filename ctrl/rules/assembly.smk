"""assembly.smk

Contains rules for assembly execution.
"""

from pathlib import Path


def getorganelle_database_input(config):
    """Return GetOrganelle database setup dependency if enabled."""
    getorganelle_config = config["tools"]["getorganelle"]

    if getorganelle_config.get("initialize_database") is True:
        database_type = getorganelle_config["database_type"]
        return str(
            JOB_DIR
            / "setup"
            / "getorganelle"
            / f"{database_type}.done"
        )

    return []


def getorganelle_optional_args(config):
    """Build optional GetOrganelle CLI arguments from config."""
    getorganelle_config = config["tools"]["getorganelle"]
    args = []

    value_options = {
        "max_rounds": "--max-rounds",
        "kmer": "--kmer",
        "word_size": "--word-size",
        "pre_grouping": "--pre-grouping",
        "max_reads": "--max-reads",
        "target_coverage": "--target-coverage",
        "min_read_length": "--min-read-length",
        "max_read_length": "--max-read-length",
        "expected_max_size": "--expected-max-size",
        "expected_min_size": "--expected-min-size",
        "seed_file": "--seed-file",
        "genes_file": "--genes-file",
        "exclude_fasta": "--exclude-fasta",
        "prefix": "--prefix",
        "round_output_prefix": "--round-output-prefix",
        "blast_path": "--blast-path",
        "bandage_path": "--bandage-path",
        "spades_path": "--spades-path",

        # Real GetOrganelle disentangling controls.
        "disentangle_df": "--disentangle-df",
        "disentangle_time_limit": "--disentangle-time-limit",

        "extra_args": "--extra-args",
    }

    for key, flag in value_options.items():
        value = getorganelle_config.get(key)

        if value is not None:
            args.append(
                f"{flag} {value}"
            )

    boolean_options = {
        "overwrite": "--overwrite",
        "continue_run": "--continue-run",
        "fast_mode": "--fast-mode",
        "reverse_lsc": "--reverse-lsc",
        "no_slim": "--no-slim",
        "keep_temp_files": "--keep-temp-files",
        "verbose": "--verbose",
    }

    for key, flag in boolean_options.items():
        if getorganelle_config.get(key) is True:
            args.append(
                flag
            )

    if getorganelle_config.get("disentangle") is True:
        print(
            "WARNING: tools.getorganelle.disentangle is deprecated and "
            "will be ignored. Use disentangle_df and/or "
            "disentangle_time_limit instead."
        )

    return " ".join(
        args
    )


rule assembly:
    """Run mitochondrial genome assembly with GetOrganelle."""

    input:
        r1=str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        r2=str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz"),
        trimming_done=str(JOB_DIR / "trimming" / "{sample}.trimming.done"),
        getorganelle_db=getorganelle_database_input(config),

    output:
        fasta=str(JOB_DIR / "assembly" / "{sample}.fasta"),
        gfa=str(JOB_DIR / "assembly" / "{sample}.gfa"),
        done=str(JOB_DIR / "assembly" / "{sample}.assembly.done"),

    params:
        output_dir=str(JOB_DIR / "assembly"),
        working_dir=str(Path.cwd()),
        log_file=str(JOB_DIR / "logs" / "assembly" / "{sample}.log"),
        threads=config["tools"]["getorganelle"]["threads"],
        organelle_type=config["tools"]["getorganelle"]["database_type"],
        optional_args=getorganelle_optional_args(config),

    conda:
        "../../envs/assembly.yaml"

    shell:
        """

        python -m mitopipeline.exec.run_getorganelle \
            --sample-id {wildcards.sample} \
            --in1 {input.r1} \
            --in2 {input.r2} \
            --output-dir {params.output_dir} \
            --working-dir {params.working_dir} \
            --organelle-type {params.organelle_type} \
            --threads {params.threads} \
            --log-file {params.log_file} \
            {params.optional_args}
        test -s {output.fasta}
        test -s {output.gfa}
        touch {output.done}
        """
