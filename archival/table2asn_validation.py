"""table2asn-based validation prototype for mitogenome submission packages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import logging
import re
import shutil
import subprocess

import pandas as pd


SEVERITY_PATTERN = re.compile(
    r"\b(REJECT|FATAL|ERROR|WARNING|INFO)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class Table2AsnValidationResult:
    """Result of one table2asn validation run."""

    sample_id: str
    status: str
    return_code: int
    input_fasta: str
    input_feature_table: str
    submission_template: str
    sqn_file: str
    validation_file: str
    stats_file: str
    discrepancy_file: str
    genbank_flatfile: str
    reject_count: int
    fatal_count: int
    error_count: int
    warning_count: int
    info_count: int
    blockers: str
    command: str

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return asdict(self)


def find_table2asn(
        executable: str = "table2asn",
) -> Path:
    """Resolve the table2asn executable."""
    resolved = shutil.which(
        executable
    )

    if resolved is None:
        raise FileNotFoundError(
            f"table2asn executable was not found: {executable}"
        )

    return Path(
        resolved
    ).resolve()


def _copy_fasta_with_ncbi_defline(
        source_fasta: Path,
        destination_fasta: Path,
        sample_id: str,
        organism: str,
        topology: str,
        genome_location: str,
) -> None:
    """Copy FASTA while adding required source modifiers to its defline."""
    lines = source_fasta.read_text(
        encoding="utf-8"
    ).splitlines()

    sequence_lines = [
        line.strip()
        for line in lines
        if line.strip()
        and not line.startswith(">")
    ]

    if not sequence_lines:
        raise ValueError(
            f"No sequence was found in {source_fasta}."
        )

    defline = (
        f">{sample_id} "
        f"[organism={organism}] "
        f"[topology={topology}] "
        f"[location={genome_location}]"
    )

    destination_fasta.write_text(
        defline
        + "\n"
        + "\n".join(sequence_lines)
        + "\n",
        encoding="utf-8",
    )


def prepare_table2asn_input(
        sample_id: str,
        organism: str,
        assembly_fasta: str | Path,
        feature_table: str | Path,
        output_directory: str | Path,
        topology: str = "circular",
        genome_location: str = "mitochondrion",
) -> tuple[Path, Path]:
    """Prepare basename-matched .fsa and .tbl inputs for table2asn."""
    assembly_fasta = Path(
        assembly_fasta
    )
    feature_table = Path(
        feature_table
    )
    output_directory = Path(
        output_directory
    )

    if not organism.strip():
        raise ValueError(
            f"Sample {sample_id} is missing organism metadata."
        )

    if not assembly_fasta.exists():
        raise FileNotFoundError(
            f"Assembly FASTA not found: {assembly_fasta}"
        )

    if not feature_table.exists():
        raise FileNotFoundError(
            f"Feature table not found: {feature_table}"
        )

    sample_directory = (
        output_directory
        / sample_id
        / "input"
    )
    sample_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    fasta_output = (
        sample_directory
        / f"{sample_id}.fsa"
    )
    feature_output = (
        sample_directory
        / f"{sample_id}.tbl"
    )

    _copy_fasta_with_ncbi_defline(
        source_fasta=assembly_fasta,
        destination_fasta=fasta_output,
        sample_id=sample_id,
        organism=organism,
        topology=topology,
        genome_location=genome_location,
    )

    shutil.copy2(
        feature_table,
        feature_output,
    )

    return fasta_output, feature_output


def parse_table2asn_messages(
        paths: list[Path],
) -> dict[str, int]:
    """Count table2asn messages by severity across output files."""
    counts = {
        "reject": 0,
        "fatal": 0,
        "error": 0,
        "warning": 0,
        "info": 0,
    }

    for path in paths:
        if not path.exists():
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        for match in SEVERITY_PATTERN.finditer(
            text
        ):
            severity = match.group(
                1
            ).lower()
            counts[
                severity
            ] += 1

    return counts


def run_table2asn_validation(
        sample_id: str,
        organism: str,
        assembly_fasta: str | Path,
        feature_table: str | Path,
        submission_template: str | Path,
        output_directory: str | Path,
        executable: str = "table2asn",
        topology: str = "circular",
        genome_location: str = "mitochondrion",
        logger: logging.Logger | None = None,
) -> Table2AsnValidationResult:
    """Prepare and validate one mitogenome package with table2asn."""
    executable_path = find_table2asn(
        executable
    )
    submission_template = Path(
        submission_template
    )
    output_directory = Path(
        output_directory
    )

    if not submission_template.exists():
        raise FileNotFoundError(
            "GenBank submission template (.sbt) was not found: "
            f"{submission_template}"
        )

    fasta_input, feature_input = prepare_table2asn_input(
        sample_id=sample_id,
        organism=organism,
        assembly_fasta=assembly_fasta,
        feature_table=feature_table,
        output_directory=output_directory,
        topology=topology,
        genome_location=genome_location,
    )

    sample_root = (
        output_directory
        / sample_id
    )
    result_directory = (
        sample_root
        / "output"
    )
    result_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_basename = (
        result_directory
        / sample_id
    )

    command = [
        str(executable_path),
        "-t",
        str(
            submission_template.resolve()
        ),
        "-i",
        str(
            fasta_input.resolve()
        ),
        "-f",
        str(
            feature_input.resolve()
        ),
        "-o",
        str(
            output_basename.with_suffix(
                ".sqn"
            )
        ),
        "-V",
        "vb",
        "-Z",
    ]

    if logger is not None:
        logger.info(
            "Running table2asn validation for %s.",
            sample_id,
        )

    completed = subprocess.run(
        command,
        cwd=sample_root,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout_path = (
        result_directory
        / "table2asn.stdout.txt"
    )
    stderr_path = (
        result_directory
        / "table2asn.stderr.txt"
    )

    stdout_path.write_text(
        completed.stdout,
        encoding="utf-8",
    )
    stderr_path.write_text(
        completed.stderr,
        encoding="utf-8",
    )

    expected = {
        "sqn": output_basename.with_suffix(".sqn"),
        "val": output_basename.with_suffix(".val"),
        "stats": output_basename.with_suffix(".stats"),
        "dr": output_basename.with_suffix(".dr"),
        "gbf": output_basename.with_suffix(".gbf"),
    }

    counts = parse_table2asn_messages(
        [
            expected["val"],
            expected["stats"],
            expected["dr"],
            stdout_path,
            stderr_path,
        ]
    )

    blockers: list[str] = []

    if completed.returncode != 0:
        blockers.append(
            f"table2asn exited with code {completed.returncode}"
        )

    if counts["reject"]:
        blockers.append(
            f"{counts['reject']} reject-level message(s)"
        )

    if counts["fatal"]:
        blockers.append(
            f"{counts['fatal']} fatal message(s)"
        )

    if counts["error"]:
        blockers.append(
            f"{counts['error']} error message(s)"
        )

    if not expected["sqn"].exists():
        blockers.append(
            "No .sqn submission file was generated"
        )

    status = (
        "PASS"
        if not blockers
        else "FAIL"
    )

    return Table2AsnValidationResult(
        sample_id=sample_id,
        status=status,
        return_code=completed.returncode,
        input_fasta=str(
            fasta_input
        ),
        input_feature_table=str(
            feature_input
        ),
        submission_template=str(
            submission_template
        ),
        sqn_file=str(
            expected["sqn"]
        ),
        validation_file=str(
            expected["val"]
        ),
        stats_file=str(
            expected["stats"]
        ),
        discrepancy_file=str(
            expected["dr"]
        ),
        genbank_flatfile=str(
            expected["gbf"]
        ),
        reject_count=counts["reject"],
        fatal_count=counts["fatal"],
        error_count=counts["error"],
        warning_count=counts["warning"],
        info_count=counts["info"],
        blockers=";".join(
            blockers
        ),
        command=" ".join(
            command
        ),
    )


def validate_mitogenome_table(
        mitogenome_metadata_path: str | Path,
        submission_template: str | Path,
        output_directory: str | Path,
        executable: str = "table2asn",
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Run table2asn validation for every usable mitogenome metadata row."""
    metadata_path = Path(
        mitogenome_metadata_path
    )

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Mitogenome metadata table not found: {metadata_path}"
        )

    table = pd.read_csv(
        metadata_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    required_columns = {
        "sample_id",
        "organism",
        "assembly_fasta",
        "annotation_tbl",
    }
    missing_columns = (
        required_columns
        - set(
            table.columns
        )
    )

    if missing_columns:
        raise ValueError(
            "Mitogenome metadata is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    results: list[dict] = []

    for _, row in table.iterrows():
        sample_id = str(
            row["sample_id"]
        ).strip()

        try:
            result = run_table2asn_validation(
                sample_id=sample_id,
                organism=str(
                    row["organism"]
                ).strip(),
                assembly_fasta=row[
                    "assembly_fasta"
                ],
                feature_table=row[
                    "annotation_tbl"
                ],
                submission_template=submission_template,
                output_directory=output_directory,
                executable=executable,
                topology=str(
                    row.get(
                        "topology",
                        "circular",
                    )
                ).strip()
                or "circular",
                genome_location=str(
                    row.get(
                        "genome_location",
                        "mitochondrion",
                    )
                ).strip()
                or "mitochondrion",
                logger=logger,
            )
            results.append(
                result.to_dict()
            )

        except Exception as error:
            if logger is not None:
                logger.exception(
                    "table2asn validation failed for %s.",
                    sample_id,
                )

            results.append(
                Table2AsnValidationResult(
                    sample_id=sample_id,
                    status="FAIL",
                    return_code=-1,
                    input_fasta=str(
                        row.get(
                            "assembly_fasta",
                            "",
                        )
                    ),
                    input_feature_table=str(
                        row.get(
                            "annotation_tbl",
                            "",
                        )
                    ),
                    submission_template=str(
                        submission_template
                    ),
                    sqn_file="",
                    validation_file="",
                    stats_file="",
                    discrepancy_file="",
                    genbank_flatfile="",
                    reject_count=0,
                    fatal_count=0,
                    error_count=1,
                    warning_count=0,
                    info_count=0,
                    blockers=str(
                        error
                    ),
                    command="",
                ).to_dict()
            )

    return pd.DataFrame(
        results
    )


def render_table2asn_summary(
        results: pd.DataFrame,
) -> str:
    """Render a Markdown validation summary."""
    passed = int(
        (
            results["status"]
            == "PASS"
        ).sum()
    )
    failed = len(
        results
    ) - passed

    lines = [
        "# table2asn validation summary",
        "",
        f"- Samples validated: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| Sample | Status | Reject | Fatal | Error | Warning | Blockers |",
        "|---|---|---:|---:|---:|---:|---|",
    ]

    for _, row in results.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(
                        row["sample_id"]
                    ),
                    str(
                        row["status"]
                    ),
                    str(
                        row["reject_count"]
                    ),
                    str(
                        row["fatal_count"]
                    ),
                    str(
                        row["error_count"]
                    ),
                    str(
                        row["warning_count"]
                    ),
                    str(
                        row["blockers"]
                    ).replace(
                        "|",
                        "\\|",
                    )
                    or "None",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "Passing this prototype means local table2asn validation completed "
            "without reject-, fatal-, or error-level blockers. It does not "
            "replace portal review or GenBank curator review.",
            "",
        ]
    )

    return "\n".join(
        lines
    )


def write_table2asn_validation_outputs(
        mitogenome_metadata_path: str | Path,
        submission_template: str | Path,
        output_directory: str | Path,
        summary_tsv_path: str | Path,
        summary_markdown_path: str | Path,
        executable: str = "table2asn",
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Run validation and write TSV/Markdown summaries."""
    results = validate_mitogenome_table(
        mitogenome_metadata_path=mitogenome_metadata_path,
        submission_template=submission_template,
        output_directory=output_directory,
        executable=executable,
        logger=logger,
    )

    summary_tsv_path = Path(
        summary_tsv_path
    )
    summary_markdown_path = Path(
        summary_markdown_path
    )

    summary_tsv_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    summary_markdown_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        summary_tsv_path,
        sep="\t",
        index=False,
    )

    summary_markdown_path.write_text(
        render_table2asn_summary(
            results
        ),
        encoding="utf-8",
    )

    return results
