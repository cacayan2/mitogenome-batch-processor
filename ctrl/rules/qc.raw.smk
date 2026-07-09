"""Raw-read FastQC rule."""

from pathlib import Path


rule qc_raw:
    """Run FastQC on raw paired-end reads."""

    input:
        r1=lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r1"],
        r2=lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r2"]

    output:
        r1_html=str(JOB_DIR / "qc" / "raw" / "{sample}_R1_fastqc.html"),
        r1_zip=str(JOB_DIR / "qc" / "raw" / "{sample}_R1_fastqc.zip"),
        r2_html=str(JOB_DIR / "qc" / "raw" / "{sample}_R2_fastqc.html"),
        r2_zip=str(JOB_DIR / "qc" / "raw" / "{sample}_R2_fastqc.zip"),
        done=str(JOB_DIR / "qc" / "raw" / "{sample}.qc.raw.done")

    params:
        output_dir=str(JOB_DIR / "qc" / "raw"),
        working_dir=str(Path.cwd()),
        log_file=str(
            JOB_DIR
            / "logs"
            / "fastqc.raw"
            / "{sample}.log"
        )

    threads:
        config["tools"]["fastqc.raw"]["threads"]

    conda:
        "../../envs/qc.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_fastqc_raw \
            --sample-id {wildcards.sample} \
            --r1 {input.r1} \
            --r2 {input.r2} \
            --output-dir {params.output_dir} \
            --working-dir {params.working_dir} \
            --log-file {params.log_file} \
            --threads {threads}

        test -s {output.r1_html}
        test -s {output.r1_zip}
        test -s {output.r2_html}
        test -s {output.r2_zip}
        touch {output.done}
        """
