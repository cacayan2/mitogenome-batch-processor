"""Read trimming and filtering rule."""

from pathlib import Path


def fastp_optional_args(config):
    fastp_config = config["tools"]["fastp"]
    args = []

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

    for key, flag in value_options.items():
        value = fastp_config.get(key)
        if value is not None:
            args.append(f"{flag} {value}")

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

    for key, flag in boolean_options.items():
        if fastp_config.get(key) is True:
            args.append(flag)

    return " ".join(args)


rule trimming:
    input:
        qc_done=str(
            JOB_DIR / "qc" / "raw" / "{sample}" / "qc_raw.done"
        ),
        r1=lambda wc: SAMPLE_TABLE.loc[wc.sample, "r1"],
        r2=lambda wc: SAMPLE_TABLE.loc[wc.sample, "r2"]

    output:
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
        html=str(JOB_DIR / "trimming" / "{sample}" / "fastp.html"),
        json=str(JOB_DIR / "trimming" / "{sample}" / "fastp.json"),
        done=str(JOB_DIR / "trimming" / "{sample}" / "trimming.done")

    params:
        output_dir=str(JOB_DIR / "trimming" / "{sample}"),
        working_dir=str(Path.cwd()),
        log_file=str(
            JOB_DIR / "trimming" / "{sample}" / "trimming.log"
        ),
        optional_args=fastp_optional_args(config)

    threads:
        config["tools"]["fastp"]["threads"]

    conda:
        "../../envs/trimming.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_fastp \
            --sample-id {wildcards.sample} \
            --in1 {input.r1:q} \
            --in2 {input.r2:q} \
            --output-dir {params.output_dir:q} \
            --working-dir {params.working_dir:q} \
            --threads {threads} \
            --log-file {params.log_file:q} \
            {params.optional_args}

        test -s {output.r1:q}
        test -s {output.r2:q}
        test -s {output.html:q}
        test -s {output.json:q}
        touch {output.done:q}
        """
