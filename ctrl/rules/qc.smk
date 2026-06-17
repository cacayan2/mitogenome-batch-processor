"""qc.smk

Contains rules for quality control execution.
"""
# Imports
import pandas as pd

rule qc:
    """Run FastQC on raw sequencing reads.
    
    Input:
        r1 = "raw reads 1",
        r2 = "raw reads 2"

    Output:
        done = "qc done"

    Shell:
        mkdir -p $(dirname {output.done})
        touch {output.done}
    """
    input:
        # Wildcard expansion for samples.
        r1 = lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r1"],
        r2 = lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r2"],
    output:
        # Define output files. 
        done = f"{JOB_DIR}/qc/{{sample}}.qc.done"
    shell:
        # Shell commands, these are placeholder commands for now. 
        """
        mkdir -p $(dirname {output.done})
        touch {output.done}
        """