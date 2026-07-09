"""Raw-read FastQC rule."""

from pathlib import Path


rule qc_raw:
    input:
        r1=lambda wc: SAMPLE_TABLE.loc[wc.sample, "r1"],
        r2=lambda wc: SAMPLE_TABLE.loc[wc.sample, "r2"]

    output:
        r1_html=str(JOB_DIR / "qc" / "raw" / "{sample}" / "R1_fastqc.html"),
        r1_zip=str(JOB_DIR / "qc" / "raw" / "{sample}" / "R1_fastqc.zip"),
        r2_html=str(JOB_DIR / "qc" / "raw" / "{sample}" / "R2_fastqc.html"),
        r2_zip=str(JOB_DIR / "qc" / "raw" / "{sample}" / "R2_fastqc.zip"),
        done=str(JOB_DIR / "qc" / "raw" / "{sample}" / "qc_raw.done")

    params:
        output_dir=str(JOB_DIR / "qc" / "raw" / "{sample}"),
        working_dir=str(Path.cwd()),
        log_file=str(
            JOB_DIR / "qc" / "raw" / "{sample}" / "qc_raw.log"
        )

    threads:
        config["tools"]["fastqc.raw"]["threads"]

    conda:
        "../../envs/qc.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_fastqc_raw \
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
