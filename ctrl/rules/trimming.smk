"""trimming.smk

Contains rules for read trimming and filtering execution.
"""

# Imports
import pandas as pd

rule trimming:
    """
    Run the trimming and filtering workflow.

    Input:
        qc_done = "qc done",
        r1 = "raw reads 1",
        r2 = "raw reads 2"

    Output:
        r1 = "trimmed reads 1",
        r2 = "trimmed reads 2"
    """
    # Wildcard expansion for samples, including finished quality control. 
    input:
        qc_done = str(JOB_DIR / "qc" / "raw" / "{sample}.qc.raw.done"),
        r1 = lambda wc: SAMPLE_TABLE.loc[wc.sample, "r1"],
        r2 = lambda wc: SAMPLE_TABLE.loc[wc.sample, "r2"]
    # Specifying the output trimmed reads. 
    output:
        r1 = str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        r2 = str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz")
    # Specifying the conda environment.
    conda: 
        "../../envs/trimming.yaml"
    # Shell script for running the trimming and filtering.
    shell:
        """
        mkdir -p $(dirname {output.r1})
        touch {output.r1}
        touch {output.r2}
        """