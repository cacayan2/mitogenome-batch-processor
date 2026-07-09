"""Validate NCBI archival readiness across files and metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import logging

import pandas as pd


VALIDATION_COLUMNS = [
    "sample_id",
    "organism",
    "raw_fastq_ready",
    "assembly_ready",
    "annotation_ready",
    "biosample_ready",
    "sra_ready",
    "mitogenome_ready",
    "ready_for_review",
    "missing_files",
    "missing_metadata",
    "submission_blockers",
]


@dataclass(frozen=True)
class ArchivalSampleValidation:
    """Per-sample archival validation result."""

    sample_id: str
    organism: str
    raw_fastq_ready: bool
    assembly_ready: bool
    annotation_ready: bool
    biosample_ready: bool
    sra_ready: bool
    mitogenome_ready: bool
    ready_for_review: bool
    missing_files: str
    missing_metadata: str
    submission_blockers: str

    def to_dict(self) -> dict:
        """Convert result to dictionary."""
        return asdict(self)


def _clean(value: object) -> str:
    """Normalize a value."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _read_optional_tsv(path: Path) -> pd.DataFrame:
    """Read a TSV if it exists, otherwise return an empty table."""
    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )


def _indexed_by_sample_name(
        table: pd.DataFrame,
) -> dict[str, dict[str, str]]:
    """Index metadata rows by sample_id or sample_name."""
    if table.empty:
        return {}

    key_column = None

    for candidate in ("sample_id", "sample_name"):
        if candidate in table.columns:
            key_column = candidate
            break

    if key_column is None:
        return {}

    return {
        _clean(row[key_column]): {
            column: _clean(row[column])
            for column in table.columns
        }
        for _, row in table.iterrows()
        if _clean(row[key_column])
    }


def _organism_name(row: pd.Series) -> str:
    """Build organism from organism/scientific_name or genus/species."""
    for column in ("organism", "scientific_name"):
        if column in row.index and _clean(row[column]):
            return _clean(row[column])

    genus = _clean(row.get("genus", ""))
    species = _clean(row.get("species", ""))

    return " ".join(
        value
        for value in (genus, species)
        if value
    )


def _path_exists(value: object) -> bool:
    """Return True if a nonblank filesystem path exists."""
    text = _clean(value)

    return bool(text) and Path(text).exists()


def _split_semicolon(value: object) -> list[str]:
    """Split a semicolon-delimited field."""
    text = _clean(value)

    if not text:
        return []

    return [
        item.strip()
        for item in text.split(";")
        if item.strip()
    ]


def validate_archival_readiness(
        runtime_manifest_path: str | Path,
        job_directory: str | Path,
        submission_directory: str | Path | None = None,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Validate archival files and metadata for every sample."""
    runtime_manifest_path = Path(
        runtime_manifest_path
    )
    job_directory = Path(
        job_directory
    )
    submission_directory = (
        Path(
            submission_directory
        )
        if submission_directory is not None
        else job_directory / "submission"
    )

    if not runtime_manifest_path.exists():
        raise FileNotFoundError(
            f"Runtime manifest does not exist: "
            f"{runtime_manifest_path}"
        )

    manifest = pd.read_csv(
        runtime_manifest_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    if "sample_id" not in manifest.columns:
        raise ValueError(
            "Runtime manifest is missing required column: sample_id"
        )

    biosample_rows = _indexed_by_sample_name(
        _read_optional_tsv(
            submission_directory
            / "biosample"
            / "biosample_metadata.tsv"
        )
    )
    sra_rows = _indexed_by_sample_name(
        _read_optional_tsv(
            submission_directory
            / "sra"
            / "sra_metadata.tsv"
        )
    )
    mitogenome_rows = _indexed_by_sample_name(
        _read_optional_tsv(
            submission_directory
            / "mitogenomes"
            / "mitogenome_metadata.tsv"
        )
    )

    records: list[ArchivalSampleValidation] = []

    for _, row in manifest.iterrows():
        sample_id = _clean(
            row["sample_id"]
        )

        if not sample_id:
            raise ValueError(
                "Runtime manifest contains a blank sample_id."
            )

        organism = _organism_name(
            row
        )
        missing_files: list[str] = []
        missing_metadata: list[str] = []
        blockers: list[str] = []

        raw_fastq_ready = True

        for label in ("r1", "r2"):
            value = _clean(
                row.get(
                    label,
                    "",
                )
            )
            if not value or not Path(value).exists():
                raw_fastq_ready = False
                missing_files.append(
                    value or label
                )
                blockers.append(
                    f"Missing raw FASTQ: {label}"
                )

        assembly_fasta = (
            job_directory
            / "assembly"
            / f"{sample_id}.fasta"
        )
        assembly_ready = assembly_fasta.exists()

        if not assembly_ready:
            missing_files.append(
                str(
                    assembly_fasta
                )
            )
            blockers.append(
                "Missing assembled mitogenome FASTA"
            )

        annotation_files = [
            job_directory
            / "annotation"
            / sample_id
            / filename
            for filename in [
                "result.gff",
                "result.fas",
                "result.tbl",
                "result.bed",
            ]
        ]
        missing_annotation = [
            path
            for path in annotation_files
            if not path.exists()
        ]
        annotation_ready = not missing_annotation

        if missing_annotation:
            missing_files.extend(
                str(path)
                for path in missing_annotation
            )
            blockers.append(
                "Missing MITOS2 annotation outputs"
            )

        if not organism:
            missing_metadata.append(
                "organism"
            )
            blockers.append(
                "Missing organism/species metadata"
            )

        biosample_row = biosample_rows.get(
            sample_id,
            {},
        )
        biosample_ready = bool(
            biosample_row
        )

        if not biosample_row:
            missing_files.append(
                str(
                    submission_directory
                    / "biosample"
                    / "biosample_metadata.tsv"
                )
            )
            blockers.append(
                "Missing BioSample metadata row"
            )
        elif biosample_row.get("review_status") != "READY":
            biosample_ready = False
            missing_metadata.extend(
                f"biosample:{field}"
                for field in _split_semicolon(
                    biosample_row.get(
                        "missing_fields",
                        "",
                    )
                )
            )
            blockers.append(
                "BioSample metadata requires review"
            )

        sra_row = sra_rows.get(
            sample_id,
            {},
        )
        sra_ready = bool(
            sra_row
        )

        if not sra_row:
            missing_files.append(
                str(
                    submission_directory
                    / "sra"
                    / "sra_metadata.tsv"
                )
            )
            blockers.append(
                "Missing SRA metadata row"
            )
        else:
            if sra_row.get("review_status") != "READY":
                sra_ready = False
                missing_metadata.extend(
                    f"sra:{field}"
                    for field in _split_semicolon(
                        sra_row.get(
                            "missing_fields",
                            "",
                        )
                    )
                )
                blockers.append(
                    "SRA metadata requires review"
                )

            for field in ("filename", "filename2"):
                if field in sra_row and not _path_exists(
                    sra_row[field]
                ):
                    sra_ready = False
                    missing_files.append(
                        sra_row.get(
                            field,
                            field,
                        )
                    )
                    blockers.append(
                        f"SRA {field} does not exist"
                    )

        mitogenome_row = mitogenome_rows.get(
            sample_id,
            {},
        )
        mitogenome_ready = bool(
            mitogenome_row
        )

        if not mitogenome_row:
            missing_files.append(
                str(
                    submission_directory
                    / "mitogenomes"
                    / "mitogenome_metadata.tsv"
                )
            )
            blockers.append(
                "Missing mitogenome metadata row"
            )
        elif mitogenome_row.get("review_status") != "READY":
            mitogenome_ready = False
            missing_files.extend(
                _split_semicolon(
                    mitogenome_row.get(
                        "missing_files",
                        "",
                    )
                )
            )
            missing_metadata.extend(
                f"mitogenome:{field}"
                for field in _split_semicolon(
                    mitogenome_row.get(
                        "missing_metadata",
                        "",
                    )
                )
            )
            blockers.append(
                "Mitogenome archival metadata requires review"
            )

        ready_for_review = all(
            [
                raw_fastq_ready,
                assembly_ready,
                annotation_ready,
                biosample_ready,
                sra_ready,
                mitogenome_ready,
            ]
        )

        records.append(
            ArchivalSampleValidation(
                sample_id=sample_id,
                organism=organism,
                raw_fastq_ready=raw_fastq_ready,
                assembly_ready=assembly_ready,
                annotation_ready=annotation_ready,
                biosample_ready=biosample_ready,
                sra_ready=sra_ready,
                mitogenome_ready=mitogenome_ready,
                ready_for_review=ready_for_review,
                missing_files=";".join(
                    sorted(
                        set(
                            missing_files
                        )
                    )
                ),
                missing_metadata=";".join(
                    sorted(
                        set(
                            missing_metadata
                        )
                    )
                ),
                submission_blockers=";".join(
                    sorted(
                        set(
                            blockers
                        )
                    )
                ),
            )
        )

    result = pd.DataFrame(
        [
            record.to_dict()
            for record in records
        ],
        columns=VALIDATION_COLUMNS,
    )

    if logger is not None:
        logger.info(
            "Validated archival readiness for %d samples; "
            "%d are ready for review.",
            len(result),
            int(
                result["ready_for_review"].sum()
            ),
        )

    return result


def render_validation_report(
        summary_table: pd.DataFrame,
) -> str:
    """Render a human-readable archival validation report."""
    total = len(
        summary_table
    )
    ready = int(
        summary_table["ready_for_review"].sum()
    )
    incomplete = total - ready

    lines = [
        "# NCBI archival validation report",
        "",
        "## Summary",
        "",
        f"- Total samples: {total}",
        f"- Ready for review: {ready}",
        f"- Incomplete samples: {incomplete}",
        "",
        "## Sample status",
        "",
        "| Sample | Organism | Ready | Blockers |",
        "|---|---|---:|---|",
    ]

    for _, row in summary_table.iterrows():
        blockers = row["submission_blockers"] or "None"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(
                        row["sample_id"]
                    ),
                    str(
                        row["organism"]
                    ),
                    "yes" if row["ready_for_review"] else "no",
                    blockers.replace(
                        "|",
                        "\\|",
                    ),
                ]
            )
            + " |"
        )

    incomplete_rows = summary_table[
        ~summary_table["ready_for_review"]
    ]

    if not incomplete_rows.empty:
        lines.extend(
            [
                "",
                "## Details for incomplete samples",
                "",
            ]
        )

        for _, row in incomplete_rows.iterrows():
            lines.extend(
                [
                    f"### {row['sample_id']}",
                    "",
                    f"- Missing files: {row['missing_files'] or 'None'}",
                    f"- Missing metadata: {row['missing_metadata'] or 'None'}",
                    f"- Submission blockers: {row['submission_blockers'] or 'None'}",
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Rows marked ready are suitable for PI/submission review. "
            "Rows marked incomplete should be corrected before any NCBI "
            "upload attempt.",
            "",
        ]
    )

    return "\n".join(
        lines
    )


def write_archival_validation_outputs(
        runtime_manifest_path: str | Path,
        job_directory: str | Path,
        summary_output_path: str | Path,
        report_output_path: str | Path,
        submission_directory: str | Path | None = None,
        logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Write validation summary TSV and Markdown report."""
    summary_output_path = Path(
        summary_output_path
    )
    report_output_path = Path(
        report_output_path
    )

    summary_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    report_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = validate_archival_readiness(
        runtime_manifest_path=runtime_manifest_path,
        job_directory=job_directory,
        submission_directory=submission_directory,
        logger=logger,
    )

    summary.to_csv(
        summary_output_path,
        sep="\t",
        index=False,
    )

    report_output_path.write_text(
        render_validation_report(
            summary
        ),
        encoding="utf-8",
    )

    if logger is not None:
        logger.info(
            "Wrote archival validation outputs: %s and %s.",
            summary_output_path,
            report_output_path,
        )

    return summary
