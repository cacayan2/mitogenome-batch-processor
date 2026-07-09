"""Collect assembled mitogenome files for NCBI/GenBank archival."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from pathlib import Path
import shutil

import pandas as pd


ANNOTATION_FILENAMES = {
    "annotation_gff": "result.gff",
    "annotation_fasta": "result.fas",
    "annotation_tbl": "result.tbl",
    "annotation_bed": "result.bed",
}

MITOGENOME_METADATA_COLUMNS = [
    "sample_id",
    "organism",
    "submission_folder",
    "assembly_fasta",
    "annotation_gff",
    "annotation_fasta",
    "annotation_tbl",
    "annotation_bed",
    "sequence_length_bp",
    "molecule_type",
    "genome_location",
    "topology",
    "assembly_method",
    "annotation_method",
    "missing_files",
    "missing_metadata",
    "review_status",
]

REQUIRED_METADATA_FIELDS = [
    "sample_id",
    "organism",
    "assembly_fasta",
    "molecule_type",
    "genome_location",
    "topology",
    "assembly_method",
    "annotation_method",
]


@dataclass(frozen=True)
class MitogenomeSubmissionRecord:
    sample_id: str
    organism: str
    submission_folder: str
    assembly_fasta: str
    annotation_gff: str
    annotation_fasta: str
    annotation_tbl: str
    annotation_bed: str
    sequence_length_bp: str
    molecule_type: str
    genome_location: str
    topology: str
    assembly_method: str
    annotation_method: str
    missing_files: str
    missing_metadata: str
    review_status: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _first_value(
    row: pd.Series,
    names: tuple[str, ...],
    default: str = "",
) -> str:
    for name in names:
        if name in row.index:
            value = _clean(row[name])
            if value:
                return value
    return default


def _organism_name(row: pd.Series) -> str:
    organism = _first_value(
        row,
        ("organism", "scientific_name"),
    )
    if organism:
        return organism

    return " ".join(
        value
        for value in (
            _first_value(row, ("genus",)),
            _first_value(row, ("species",)),
        )
        if value
    )


def _safe_folder_name(value: str) -> str:
    cleaned = "".join(
        char
        if char.isalnum() or char in {"-", "_", "."}
        else "_"
        for char in value.strip()
    )
    return cleaned.strip("_") or "unknown_sample"


def _copy_or_symlink(
    source: Path,
    destination: Path,
    mode: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() or destination.is_symlink():
        destination.unlink()

    if mode == "copy":
        shutil.copy2(source, destination)
    elif mode == "symlink":
        destination.symlink_to(source.resolve())
    else:
        raise ValueError("mode must be 'copy' or 'symlink'.")


def _sequence_length(fasta_path: Path) -> str:
    if not fasta_path.exists():
        return ""

    total = 0

    with fasta_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith(">"):
                total += len(line)

    return str(total)


def build_mitogenome_submission(
    runtime_manifest_path: str | Path,
    job_directory: str | Path,
    output_directory: str | Path,
    defaults: dict[str, object] | None = None,
    mode: str = "copy",
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    runtime_manifest_path = Path(runtime_manifest_path)
    job_directory = Path(job_directory)
    output_directory = Path(output_directory)
    defaults = defaults or {}

    table = pd.read_csv(
        runtime_manifest_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    if "sample_id" not in table.columns:
        raise ValueError(
            "Runtime manifest is missing required column: sample_id"
        )

    output_directory.mkdir(parents=True, exist_ok=True)
    records = []

    for _, row in table.iterrows():
        sample_id = _first_value(row, ("sample_id",))
        organism = _organism_name(row)

        folder_label = _safe_folder_name(
            f"{sample_id}_{organism}"
            if organism
            else sample_id
        )
        sample_submission_dir = output_directory / folder_label
        sample_submission_dir.mkdir(parents=True, exist_ok=True)

        source_assembly_fasta = (
            job_directory
            / "assembly"
            / sample_id
            / "data.fasta"
        )
        destination_assembly_fasta = (
            sample_submission_dir
            / f"{sample_id}.mitogenome.fasta"
        )

        missing_files = []
        copied_paths = {
            "assembly_fasta": "",
            "annotation_gff": "",
            "annotation_fasta": "",
            "annotation_tbl": "",
            "annotation_bed": "",
        }

        if source_assembly_fasta.exists():
            _copy_or_symlink(
                source_assembly_fasta,
                destination_assembly_fasta,
                mode,
            )
            copied_paths["assembly_fasta"] = str(
                destination_assembly_fasta
            )
        else:
            missing_files.append(str(source_assembly_fasta))

        annotation_directory = (
            job_directory / "annotation" / sample_id
        )

        for key, filename in ANNOTATION_FILENAMES.items():
            source = annotation_directory / filename
            destination = sample_submission_dir / filename

            if source.exists():
                _copy_or_symlink(source, destination, mode)
                copied_paths[key] = str(destination)
            else:
                missing_files.append(str(source))

        record_data = {
            "sample_id": sample_id,
            "organism": organism,
            "submission_folder": str(sample_submission_dir),
            **copied_paths,
            "sequence_length_bp": _sequence_length(
                source_assembly_fasta
            ),
            "molecule_type": _first_value(
                row,
                ("molecule_type",),
                _clean(defaults.get("molecule_type", "DNA")),
            ),
            "genome_location": _first_value(
                row,
                ("genome_location",),
                _clean(
                    defaults.get(
                        "genome_location",
                        "mitochondrion",
                    )
                ),
            ),
            "topology": _first_value(
                row,
                ("topology", "circular"),
                _clean(defaults.get("topology", "circular")),
            ),
            "assembly_method": _first_value(
                row,
                ("assembly_method",),
                _clean(
                    defaults.get(
                        "assembly_method",
                        "GetOrganelle",
                    )
                ),
            ),
            "annotation_method": _first_value(
                row,
                ("annotation_method",),
                _clean(
                    defaults.get(
                        "annotation_method",
                        "MITOS2",
                    )
                ),
            ),
        }

        missing_metadata = [
            field
            for field in REQUIRED_METADATA_FIELDS
            if not record_data.get(field, "")
        ]

        records.append(
            MitogenomeSubmissionRecord(
                **record_data,
                missing_files=";".join(missing_files),
                missing_metadata=";".join(missing_metadata),
                review_status=(
                    "READY"
                    if not missing_files and not missing_metadata
                    else "MANUAL_REVIEW_REQUIRED"
                ),
            )
        )

    result = pd.DataFrame(
        [record.to_dict() for record in records],
        columns=MITOGENOME_METADATA_COLUMNS,
    )

    if logger is not None:
        logger.info(
            "Prepared mitogenome submission files for %d samples.",
            len(result),
        )

    return result


def write_mitogenome_submission(
    runtime_manifest_path: str | Path,
    job_directory: str | Path,
    output_directory: str | Path,
    metadata_output_path: str | Path | None = None,
    defaults: dict[str, object] | None = None,
    mode: str = "copy",
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    output_directory = Path(output_directory)
    metadata_output_path = (
        Path(metadata_output_path)
        if metadata_output_path is not None
        else output_directory / "mitogenome_metadata.tsv"
    )

    table = build_mitogenome_submission(
        runtime_manifest_path=runtime_manifest_path,
        job_directory=job_directory,
        output_directory=output_directory,
        defaults=defaults,
        mode=mode,
        logger=logger,
    )

    metadata_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    table.to_csv(
        metadata_output_path,
        sep="\t",
        index=False,
    )

    return table
