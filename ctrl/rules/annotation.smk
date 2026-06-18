"""annotation.smk

Contains rules for annotation execution. 
"""

rule annotation:
    """
    Creates a GFF file from an assembly file.

    Input:
        fasta = "assembly fasta"

    Output:
        gff = "annotation gff"
    """
    # Specifying input assembly file. 
    input:
        fasta = str(JOB_DIR / "assembly" / "{sample}.fasta")
    # Specifying output annotation file.
    output:
        gff = str(JOB_DIR / "annotation" / "{sample}.gff")
    # Shell script for running the annotation. 
    shell:
        """
        mkdir -p $(dirname {output.gff})
        echo "##gff-version 3" > {output.gff}
        """