"""Trimmed-read FastQC rule."""

from pathlib import Path


rule qc_trimmed:
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
        )

    output:
        r1_html=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}"
            / "R1_fastqc.html"
        ),
        r1_zip=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}"
            / "R1_fastqc.zip"
        ),
        r2_html=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}"
            / "R2_fastqc.html"
        ),
        r2_zip=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}"
            / "R2_fastqc.zip"
        ),
        done=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}"
            / "qc_trimmed.done"
        )

    params:
        output_dir=str(
            JOB_DIR / "qc" / "trimmed" / "{sample}"
        ),
        working_dir=str(Path.cwd()),
        log_file=str(
            JOB_DIR
            / "qc"
            / "trimmed"
            / "{sample}"
            / "qc_trimmed.log"
        )

    threads:
        config["tools"]["fastqc.trimmed"]["threads"]

    conda:
        "../../envs/qc.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_fastqc_trimmed \
            --sample-id {wildcards.sample} \
            --r1 {input.r1:q} \
            --r2 {input.r2:q} \
            --output-dir {params.output_dir:q} \
            --working-dir {params.working_dir:q} \
            --log-file {params.log_file:q} \
            --threads {threads}

        test -s {output.r1_html:q}
        test -s {output.r1_zip:q}
        test -s {output.r2_html:q}
        test -s {output.r2_zip:q}
        touch {output.done:q}
        """
