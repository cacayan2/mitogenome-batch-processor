"""GetOrganelle assembly rule."""

from pathlib import Path


def getorganelle_database_input(config):
    tool_config = config["tools"]["getorganelle"]

    if tool_config.get("initialize_database") is True:
        return str(
            JOB_DIR
            / "setup"
            / "getorganelle"
            / f"{tool_config['database_type']}.done"
        )

    return []


def getorganelle_optional_args(config):
    tool_config = config["tools"]["getorganelle"]
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
        "disentangle_df": "--disentangle-df",
        "disentangle_time_limit": "--disentangle-time-limit",
    }

    for key, flag in value_options.items():
        value = tool_config.get(key)
        if value is not None:
            args.append(f"{flag} {value}")

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
        if tool_config.get(key) is True:
            args.append(flag)

    return " ".join(args)


rule assembly:
    input:
        r1=str(
            JOB_DIR
            / "trimming"
            / "{sample}"
            / "R1.trimmed.fastq.gz"
        ),
        r2=str(
            JOB_DIR
            / "trimming"
            / "{sample}"
            / "R2.trimmed.fastq.gz"
        ),
        trimming_done=str(
            JOB_DIR / "trimming" / "{sample}" / "trimming.done"
        ),
        database_done=getorganelle_database_input(config)

    output:
        fasta=str(JOB_DIR / "assembly" / "{sample}" / "data.fasta"),
        gfa=str(JOB_DIR / "assembly" / "{sample}" / "graph.gfa"),
        done=str(JOB_DIR / "assembly" / "{sample}" / "assembly.done")

    params:
        output_dir=str(JOB_DIR / "assembly" / "{sample}"),
        working_dir=str(Path.cwd()),
        log_file=str(
            JOB_DIR / "assembly" / "{sample}" / "assembly.log"
        ),
        organelle_type=config["tools"]["getorganelle"][
            "database_type"
        ],
        optional_args=getorganelle_optional_args(config)

    threads:
        config["tools"]["getorganelle"]["threads"]

    conda:
        "../../envs/assembly.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_getorganelle \
            --sample-id {wildcards.sample} \
            --in1 {input.r1:q} \
            --in2 {input.r2:q} \
            --output-dir {params.output_dir:q} \
            --working-dir {params.working_dir:q} \
            --organelle-type {params.organelle_type} \
            --threads {threads} \
            --log-file {params.log_file:q} \
            {params.optional_args}

        test -s {output.fasta:q}
        test -s {output.gfa:q}
        touch {output.done:q}
        """
