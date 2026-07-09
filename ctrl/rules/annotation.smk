"""annotation.smk

Contains rules for mitochondrial genome annotation.
"""

# Imports
from pathlib import Path


rule annotation:
    """Run MITOS2 annotation on assembled mitochondrial genomes."""

    input:
        fasta=str(JOB_DIR / "assembly" / "{sample}.fasta"),
        assembly_done=str(JOB_DIR / "assembly" / "{sample}.assembly.done"),
        mitos2_done=str(JOB_DIR / "setup" / "mitos2" / "mitos2.done")

    output:
        done=str(JOB_DIR / "annotation" / "{sample}.annotation.done"),
        gff=str(JOB_DIR / "annotation" / "{sample}" / "result.gff"),
        fasta=str(JOB_DIR / "annotation" / "{sample}" / "result.fas")

    params:
        output_dir=str((Path.cwd() / JOB_DIR / "annotation" / "{sample}").resolve()),
        working_dir=str(Path.cwd()),
        log_file=str((Path.cwd() / JOB_DIR / "logs" / "annotation" / "{sample}.log").resolve()),
        conda_env=config["tools"]["mitos2"].get("conda_env", "mito-annotation"),
        genetic_code=config["tools"]["mitos2"].get("genetic_code", 2),
        refdir=str(Path(config["tools"]["mitos2"]["refdir"]).resolve()),
        refseqver=config["tools"]["mitos2"]["refseqver"],
        circular=str(config["tools"]["mitos2"].get("circular", True)),
        noplots=str(config["tools"]["mitos2"].get("noplots", False)),
        best=str(config["tools"]["mitos2"].get("best", False)),
        ncbicode=str(config["tools"]["mitos2"].get("ncbicode", False))

    threads:
        1

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        python -m pip install -e . --quiet

        python -m mitopipeline.exec.run_mitos2 \
            --conda-env {params.conda_env} \
            --sample-id {wildcards.sample} \
            --input-fasta {input.fasta} \
            --output-dir {params.output_dir} \
            --working-dir {params.working_dir} \
            --log-file {params.log_file} \
            --genetic-code {params.genetic_code} \
            --refdir {params.refdir} \
            --refseqver {params.refseqver} \
            --circular {params.circular} \
            --noplots {params.noplots} \
            --best {params.best} \
            --ncbicode {params.ncbicode}

        touch {output.done}
        """