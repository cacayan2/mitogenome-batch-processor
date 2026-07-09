"""Trimmed-read FastQC rule."""

from pathlib import Path


rule qc_trimmed:
    """Run FastQC on trimmed paired-end reads."""

    input:
        r1=str(
            JOB_DIR
            / "trimming"
            / "{sample}_R1.trimmed.fastq.gz"
        ),
        r2=str(
            JOB_DIR
            / "trimming"
            / "{sample}_R2.trimmed.fastq.gz"
        )

    output:
        r1_html=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}_R1.trimmed_fastqc.html"
        ),
        r1_zip=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}_R1.trimmed_fastqc.zip"
        ),
        r2_html=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}_R2.trimmed_fastqc.html"
        ),
        r2_zip=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}_R2.trimmed_fastqc.zip"
        ),
        done=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}.qc.trimmed.done"
        )

    params:
        output_dir=str(JOB_DIR / "qc" / "trimmed"),
        working_dir=str(Path.cwd()),
        log_file=str(
            JOB_DIR
            / "logs"
            / "fastqc.trimmed"
            / "{sample}.log"
        )

    threads:
        config["tools"]["fastqc.trimmed"]["threads"]

    conda:
        "../../envs/qc.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_fastqc_trimmed \
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
