"""qc.smk

Contains rules for quality control execution.
"""
rule qc_trimmed:
    """Run FastQC on raw sequencing reads.
    
    Input:
        r1 = "raw reads 1",
        r2 = "raw reads 2"

    Output:
        r1_html = "raw reads 1 fastqc html",
        r1_zip = "raw reads 1 fastqc zip",
        r2_html = "raw reads 2 fastqc html",
        r2_zip = "raw reads 2 fastqc zip",
        done = "qc done" (this is a placeholder so the DAG can be constructed)
    """
    # Wildcard expansion for samples.
    input:
        r1 = str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        r2 = str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz")
    # Define output files. 
    output:
        r1_html = str(JOB_DIR / "qc" / "trimmed" / "{sample}_R1.trimmed_fastqc.html"),
        r1_zip  = str(JOB_DIR / "qc" / "trimmed" / "{sample}_R1.trimmed_fastqc.zip"),
        r2_html = str(JOB_DIR / "qc" / "trimmed" / "{sample}_R2.trimmed_fastqc.html"),
        r2_zip  = str(JOB_DIR / "qc" / "trimmed" / "{sample}_R2.trimmed_fastqc.zip"),
        done    = str(JOB_DIR / "qc" / "trimmed" / "{sample}.qc.trimmed.done"),
    # Define params.
    params:
        output_dir = str(JOB_DIR / "qc" / "trimmed"),
        log_file = str(JOB_DIR / "logs" / "fastqc.trimmed" / "{sample}.log")
    # Define conda environment.
    conda: 
        "../../envs/qc.yaml"
    # Shell commands.
    shell:
        """
        python -m mitopipeline.exec.run_fastqc_trimmed \
            --sample-id {wildcards.sample} \
            --r1 {input.r1} \
            --r2 {input.r2} \
            --output-dir {params.output_dir} \
            --working-dir . \
            --log-file {params.log_file}
        
        touch {output.done}
        """