"""trimming.smk

Contains rules for read trimming and filtering execution.
"""

def fastp_optional_args(config):
    """Build optional fastp CLI arguments from config.
    
    Args:
        config (dict): Configuration dictionary.
    
    Returns:
        list: List of optional fastp CLI arguments.
    """

    # Extracting fastp options from config.
    fastp_config = config["tools"]["fastp"]
    args = []

    # Creating dictionary of optional fastp arguments.
    value_options = {
        "qualified_quality_phred": "--qualified_quality_phred",
        "length_required": "--length_required",
        "trim_front1": "--trim_front1",
        "trim_tail1": "--trim_tail1",
        "trim_front2": "--trim_front2",
        "trim_tail2": "--trim_tail2",
        "cut_window_size": "--cut_window_size",
        "cut_mean_quality": "--cut_mean_quality",
        "n_base_limit": "--n_base_limit",
        "unqualified_percent_limit": "--unqualified_percent_limit",
        "average_qual": "--average_qual",
    }

    # Iterating through options and adding them to the command, if present.
    for key, flag in value_options.items():
        value = fastp_config.get(key)
        if value is not None:
            args.append(f"{flag} {value}")

    # Creating dictionary of boolean fastp arguments.
    boolean_options = {
        "detect_adapter_for_pe": "--detect_adapter_for_pe",
        "cut_front": "--cut_front",
        "cut_tail": "--cut_tail",
        "cut_right": "--cut_right",
        "disable_quality_filtering": "--disable_quality_filtering",
        "disable_length_filtering": "--disable_length_filtering",
        "trim_poly_g": "--trim_poly_g",
        "disable_trim_poly_g": "--disable_trim_poly_g",
        "trim_poly_x": "--trim_poly_x",
    }

    # Iterating through options and adding them to the command, if present.
    for key, flag in boolean_options.items():
        if fastp_config.get(key) is True:
            args.append(flag)

    # Returning the command as a string.
    return " ".join(args)

rule trimming:
    """
    Run read trimming and filtering with fastp.
    """

    # Wildcard expansion for samples, including finished raw quality control.
    input:
        qc_done=str(JOB_DIR / "qc" / "raw" / "{sample}.qc.raw.done"),
        r1=lambda wc: SAMPLE_TABLE.loc[wc.sample, "r1"],
        r2=lambda wc: SAMPLE_TABLE.loc[wc.sample, "r2"],

    # Specifying fastp outputs.
    output:
        r1=str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        r2=str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz"),
        html=str(JOB_DIR / "trimming" / "{sample}.fastp.html"),
        json=str(JOB_DIR / "trimming" / "{sample}.fastp.json"),
        done=str(JOB_DIR / "trimming" / "{sample}.trimming.done"),

    # Defining params.
    params:
        output_dir=str(JOB_DIR / "trimming"),
        log_file=str(JOB_DIR / "logs" / "trimming" / "{sample}.log"),
        threads=config["tools"]["fastp"]["threads"],
        optional_args=fastp_optional_args(config),

    # Specifying the conda environment.
    conda:
        "../../envs/trimming.yaml"

    # Shell script for running fastp through the execution layer.
    shell:
        """
        python -m mitopipeline.exec.run_fastp \
            --sample-id {wildcards.sample} \
            --in1 {input.r1} \
            --in2 {input.r2} \
            --output-dir {params.output_dir} \
            --working-dir . \
            --threads {params.threads} \
            --log-file {params.log_file} \
            {params.optional_args}

        touch {output.done}
        """