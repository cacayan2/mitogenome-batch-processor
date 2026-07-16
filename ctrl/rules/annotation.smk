"""MITOS2 annotation rule using the final evidence-selected assembly."""

from pathlib import Path


rule annotation:
    input:
        fasta=str(JOB_DIR / "assembly" / "{sample}" / "resolved.fasta"),
        rescue_done=str(JOB_DIR / "assembly" / "{sample}" / "rescue.done"),
        mitos2_done=str(JOB_DIR / "setup" / "mitos2" / "mitos2.done"),
        reference_ready=str(MITOS2_READY_FILE)

    output:
        gff=str(JOB_DIR / "annotation" / "{sample}" / "result.gff"),
        fasta=str(JOB_DIR / "annotation" / "{sample}" / "result.fas"),
        done=str(JOB_DIR / "annotation" / "{sample}" / "annotation.done")

    params:
        output_dir=str((Path.cwd() / JOB_DIR / "annotation" / "{sample}").resolve()),
        working_dir=str(Path.cwd()),
        log_file=str((Path.cwd() / JOB_DIR / "annotation" / "{sample}" / "annotation.log").resolve()),
        conda_env=config["tools"]["mitos2"].get("conda_env", "mito-annotation"),
        genetic_code=config["tools"]["mitos2"].get("genetic_code", 2),
        refdir=str(Path(config["tools"]["mitos2"]["refdir"]).resolve()),
        refseqver=config["tools"]["mitos2"]["refseqver"],
        circular=str(config["tools"]["mitos2"].get("circular", True)),
        noplots=str(config["tools"]["mitos2"].get("noplots", True)),
        best=str(config["tools"]["mitos2"].get("best", False)),
        ncbicode=str(config["tools"]["mitos2"].get("ncbicode", False))

    threads: 1

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        """
        set -euo pipefail
        python -m mitopipeline.exec.run_mitos2 \
            --conda-env {params.conda_env:q} \
            --sample-id {wildcards.sample:q} \
            --input-fasta {input.fasta:q} \
            --output-dir {params.output_dir:q} \
            --working-dir {params.working_dir:q} \
            --log-file {params.log_file:q} \
            --genetic-code {params.genetic_code} \
            --refdir {params.refdir:q} \
            --refseqver {params.refseqver:q} \
            --circular {params.circular:q} \
            --noplots {params.noplots:q} \
            --best {params.best:q} \
            --ncbicode {params.ncbicode:q}
        test -s {output.gff:q}
        test -s {output.fasta:q}
        touch {output.done:q}
        """
