"""assembly.smk

Contains rules for assembly execution.
"""

rule assembly:
    """
    Starts the assembly portion of the pipeline.

    Input:
        r1 = "trimmed reads 1",
        r2 = "trimmed reads 2"

    Output:
        fasta = "assembly fasta"
    """
    # Specifying input fastq files. 
    input:
        r1 = str(JOB_DIR / "trimming" / "{sample}_R1.trimmed.fastq.gz"),
        r2 = str(JOB_DIR / "trimming" / "{sample}_R2.trimmed.fastq.gz")
    # Specifying the output asssembly file.
    output:
        fasta = str(JOB_DIR / "assembly" / "{sample}.fasta")
    # Shell script for running the assembly. 
    shell:
        """
        mkdir -p $(dirname {output.fasta})
        echo ">{wildcards.sample}" > {output.fasta}
        echo "ATGC" >> {output.fasta}
        """