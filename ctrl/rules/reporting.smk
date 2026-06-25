"""reporting.smk

Contains rules for reporting execution.
"""

# Imports
from pathlib import Path

rule reporting:
    """
    Rule for generating a report for a given sample.
    
    Input:
        qc_done = "qc done",
        trimmed_r1 = "trimmed reads 1",
        trimmed_r2 = "trimmed reads 2",
        fasta = "assembly fasta",
        gff = "annotation gff",
        tree = "phylogenetic tree"

    Output:
        report = "report"
    """
    # Specifying input files.
    input:
        qc_raw_done = str(JOB_DIR / "qc" / "raw" / "{sample}.qc.raw.done"),
        qc_trimmed_done = str(JOB_DIR / "qc" / "trimmed" / "{sample}.qc.trimmed.done"),
        trimmed_r1 = str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        trimmed_r2 = str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz"),
        fasta = str(JOB_DIR / "assembly" / "{sample}.fasta"),
        gff = str(JOB_DIR / "annotation" / "{sample}.gff"),
        tree = str(JOB_DIR / "phylogeny" / "{sample}.nwk")
    # Specifying output report file.
    output:
        report = str(JOB_DIR / "reporting" / "{sample}.report.md")
    # Specifying conda environment.
    conda: 
        "../../envs/reporting.yaml"
    # Shell script for generating the report.
    shell:
        """
        python -m pip install -e . --quiet

        mkdir -p $(dirname {output.report})
        echo "# Report for {wildcards.sample}" > {output.report}
        """