"""Top BLAST-hit selection and taxonomy-enrichment rule."""

from pathlib import Path
import shlex


def build_entrez_api_key_argument() -> str:
    """Return the optional Entrez API-key command-line argument."""
    api_key = config["tools"]["blast"].get(
        "entrez_api_key"
    )

    if not api_key:
        return ""

    return (
        "--entrez-api-key "
        f"{shlex.quote(str(api_key))}"
    )


rule select_blast_hits:
    input:
        blast_results=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "blast.tsv"
        ),
        blast_done=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "blast.done"
        )

    output:
        matches=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "top_hits.tsv"
        ),
        done=str(
            JOB_DIR
            / "phylogeny"
            / "{sample}"
            / "top_hits.done"
        )

    params:
        maximum_matches=config[
            "tools"
        ][
            "blast"
        ].get(
            "maximum_matches",
            6,
        ),
        entrez_email=config[
            "tools"
        ][
            "blast"
        ][
            "entrez_email"
        ],
        entrez_api_key_arg=build_entrez_api_key_argument(),
        log_file=lambda wildcards: str(
            (
                Path.cwd()
                / JOB_DIR
                / "phylogeny"
                / wildcards.sample
                / "top_hits.log"
            ).resolve()
        )

    conda:
        "../../envs/mitopipeline.yaml"

    shell:
        r"""
        python -m mitopipeline.exec.parse_blast_hits \
            --sample-id {wildcards.sample:q} \
            --blast-results {input.blast_results:q} \
            --output-file {output.matches:q} \
            --maximum-matches {params.maximum_matches} \
            --entrez-email {params.entrez_email:q} \
            {params.entrez_api_key_arg} \
            --log-file {params.log_file:q}

        test -s {output.matches:q}
        touch {output.done:q}
        """