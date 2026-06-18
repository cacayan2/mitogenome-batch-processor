""""phylogeny.smk

Contains rules for phylogeny execution.
"""

rule phylogeny:
    """
    Rule for generating a phylogenetic tree for a given sample.
    
    Input:
        fasta = "assembly fasta",
        gff = "annotation gff"

    Output:
        tree = "phylogenetic tree"
    """
    # Specifying input assembly and annotation files.
    input:
        fasta = str(JOB_DIR / "assembly" / "{sample}.fasta"),
        gff = str(JOB_DIR / "annotation" / "{sample}.gff")
    # Specifying output phylogenetic tree file.
    output:
        tree = str(JOB_DIR / "phylogeny" / "{sample}.nwk")
    # Specifying conda environment.
    conda: 
        "../../envs/phylogeny.yaml"
    # Shell script for running the phylogenetic tree.
    shell:
        """
        mkdir -p $(dirname {output.tree})
        echo "({wildcards.sample});" > {output.tree}
        """