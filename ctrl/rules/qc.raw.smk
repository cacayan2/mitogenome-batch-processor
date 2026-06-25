"""qc.smk

Contains rules for quality control execution.
"""

# Imports
from pathlib import Path

rule qc_raw:
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
        r1 = lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r1"],
        r2 = lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r2"]
    # Define output files. 
    output:
        r1_html = str(JOB_DIR / "qc" / "raw" / "{sample}_R1_fastqc.html"),
        r1_zip = str(JOB_DIR / "qc" / "raw" /  "{sample}_R1_fastqc.zip"),
        r2_html = str(JOB_DIR / "qc" / "raw" / "{sample}_R2_fastqc.html"),
        r2_zip = str(JOB_DIR / "qc" / "raw" / "{sample}_R2_fastqc.zip"),
        done = str(JOB_DIR / "qc" / "raw" / "{sample}.qc.raw.done")
    # Define params.
    params:
        output_dir = str(JOB_DIR / "qc" / "raw"),
        working_dir = str(Path.cwd()),
        log_file = str(JOB_DIR / "logs" / "fastqc.raw" / "{sample}.log"),
        threads = config["tools"]["fastqc.raw"]["threads"]
    # Define conda environment.
    conda: 
        "../../envs/qc.yaml"
    # Shell commands.
    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.run_fastqc_raw \
            --sample-id {wildcards.sample} \
            --r1 {input.r1} \
            --r2 {input.r2} \
            --output-dir {params.output_dir} \
            --working-dir {params.working_dir} \
            --log-file {params.log_file} \
            --threads {params.threads}
        
        touch {output.done}
        """