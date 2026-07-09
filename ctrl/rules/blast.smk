"""BLAST validation rule."""

from pathlib import Path

from mitopipeline.config.blast_config import BlastConfig


BLAST_CONFIG = BlastConfig.from_mapping(config["tools"]["blast"])


def blast_max_hsps_arg():
    if BLAST_CONFIG.max_hsps is None:
        return ""
    return f"--max-hsps {BLAST_CONFIG.max_hsps}"


def blast_database_dependency():
    if BLAST_CONFIG.requires_database_setup:
        return str(
            JOB_DIR
            / "setup"
            / "blast"
            / "blast_database.done"
        )
    return []


def blast_optional_args():
    args = []
    value_options = {
        BLAST_CONFIG.perc_identity: "--perc-identity",
        BLAST_CONFIG.query_coverage: "--query-coverage",
        BLAST_CONFIG.word_size: "--word-size",
    }

    for value, flag in value_options.items():
        if value is not None:
            args.append(f"{flag} {value}")

    return " ".join(args)


rule blast_validation:
    input:
        query_fasta=str(
            JOB_DIR / "assembly" / "{sample}" / "data.fasta"
        ),
        assembly_done=str(
            JOB_DIR / "assembly" / "{sample}" / "assembly.done"
        ),
        database_done=blast_database_dependency()

    output:
        results=str(
            JOB_DIR / "phylogeny" / "{sample}" / "blast.tsv"
        ),
        done=str(
            JOB_DIR / "phylogeny" / "{sample}" / "blast.done"
        )

    params:
        mode=BLAST_CONFIG.mode,
        database=BLAST_CONFIG.database_argument,
        output_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "{sample}"
                / "blast.tsv"
            ).resolve()
        ),
        working_dir=str(Path.cwd()),
        log_file=str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / "{sample}"
                / "blast.log"
            ).resolve()
        ),
        task=BLAST_CONFIG.task,
        output_format=BLAST_CONFIG.output_format,
        evalue=BLAST_CONFIG.evalue,
        max_target_seqs=BLAST_CONFIG.max_target_seqs,
        max_hsps_arg=blast_max_hsps_arg(),
        optional_args=blast_optional_args()

    threads:
        BLAST_CONFIG.threads

    conda:
        "../../envs/blast.yaml"

    shell:
        """
        python -m mitopipeline.exec.run_blast \
            --sample-id {wildcards.sample} \
            --query-fasta {input.query_fasta:q} \
            --database {params.database:q} \
            --mode {params.mode} \
            --output-file {params.output_file:q} \
            --working-dir {params.working_dir:q} \
            --threads {threads} \
            --log-file {params.log_file:q} \
            --task {params.task} \
            --output-format "{params.output_format}" \
            --evalue {params.evalue} \
            --max-target-seqs {params.max_target_seqs} \
            {params.max_hsps_arg} \
            {params.optional_args}

        test -e {output.results:q}
        touch {output.done:q}
        """
