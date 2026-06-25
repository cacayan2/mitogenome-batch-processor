"""assembly.smk

Contains rules for assembly execution.
"""

def getorganelle_database_input(config):
    """Return GetOrganelle database setup dependency if enabled."""

    getorganelle_config = config["tools"]["getorganelle"]

    if getorganelle_config.get("initialize_database") is True:
        database_type = getorganelle_config["database_type"]
        return str(JOB_DIR / "setup" / "getorganelle" / f"{database_type}.done")

    return []

def getorganelle_optional_args(config):
    """Build optional GetOrganelle CLI arguments from config.
    
    Args:
        config (dict): Configuration dictionary.
    
    Returns:
        list: List of optional GetOrganelle CLI arguments.
    """

    # Extracting GetOrganelle options from config.
    getorganelle_config = config["tools"]["getorganelle"]
    args = []

    # Creating dictionary of optional GetOrganelle arguments.
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
    }

    # Iterating through options and adding them to the command, if present.
    for key, flag in value_options.items():
        value = getorganelle_config.get(key)
        if value is not None:
            args.append(f"{flag} {value}")

    # Creating dictionary of boolean GetOrganelle arguments.
    boolean_options = {
        "overwrite": "--overwrite",
        "continue_run": "--continue-run",
        "fast_mode": "--fast-mode",
        "disentangle": "--disentangle",
        "reverse_lsc": "--reverse-lsc",
        "no_slim": "--no-slim",
        "keep_temp_files": "--keep-temp-files",
        "verbose": "--verbose",
    }

    # Iterating through options and adding them to the command, if present.
    for key, flag in boolean_options.items():
        if getorganelle_config.get(key) is True:
            args.append(flag)

    # Joining the arguments into a single string.
    return " ".join(args)


rule assembly:
    """
    Run mitochondrial genome assembly with GetOrganelle.
    """

    # Wildcard # Wildcard expansion for samples, and trimming done files.
    input:
        r1=str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        r2=str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz"),
        trimming_done=str(JOB_DIR / "trimming" / "{sample}.trimming.done"),
        getorganelle_db = getorganelle_database_input(config),

    # Define output files.
    output:
        fasta=str(JOB_DIR / "assembly" / "{sample}.fasta"),
        gfa=str(JOB_DIR / "assembly" / "{sample}.gfa"),
        done=str(JOB_DIR / "assembly" / "{sample}.assembly.done"),

    # Define parameters.
    params:
        output_dir=str(JOB_DIR / "assembly"),
        working_dir = workflow.basedir,
        log_file=str(JOB_DIR / "logs" / "assembly" / "{sample}.log"),
        threads=config["tools"]["getorganelle"]["threads"],
        organelle_type=config["tools"]["getorganelle"]["database_type"],
        optional_args = getorganelle_optional_args(config),

    # Define conda environment.
    conda:
        "../../envs/assembly.yaml"

    # Shell script for running GetOrganelle.
    shell:
        """
        python -m pip install -e . --quiet

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

        touch {output.done}
        """