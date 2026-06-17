"""trimming.smk

Contains rules for read trimming and filtering execution.
"""

# Imports
import pandas as pd

rule trimming:
    input:
        qc_done = f"{JOB_DIR}/qc/{{sample}}.qc.done"
        r1 = lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r1"],
        r2 = lambda wildcards: SAMPLE_TABLE.loc[wildcards.sample, "r2"]
    output:
        r1 = f"{JOB_DIR}"