"""pipeline_launcher.py

Launch a MitoPipeline run from production config.

The launcher creates or reuses a job-specific runtime manifest
(`outputs/<job_id>/validated_samples.tsv`) and writes a runtime config that
points Snakemake to that manifest for the duration of the run.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import subprocess

import pandas as pd
import yaml

from mitopipeline.manifest.sample_manifest import parse_sample_manifest
from mitopipeline.models.pipeline_job import PipelineJob


def _configured_job_id(
        value: object,
) -> str | None:
    """Normalize a job_id value from YAML config."""
    if value is None:
        return None

    text = str(
        value
    ).strip()

    if text == "" or text.lower() == "null":
        return None

    return text


def _resolve_manifest_fastq_path(
        value: object,
        manifest_dir: Path,
        input_directory: Path | None = None,
) -> str:
    """Resolve a manifest FASTQ path.

    Resolution order for relative paths:
    1. relative to the manifest directory;
    2. relative to configured input_directory.

    This supports manifests that contain only filenames while the config
    supplies the FASTQ directory.
    """
    raw_value = str(
        value
    ).strip()

    if not raw_value:
        return raw_value

    path = Path(
        raw_value
    ).expanduser()

    if path.is_absolute():
        return str(
            path.resolve()
        )

    manifest_relative = (
        manifest_dir
        / path
    ).resolve()

    if manifest_relative.exists():
        return str(
            manifest_relative
        )

    if input_directory is not None:
        input_relative = (
            input_directory
            / path
        ).resolve()

        if input_relative.exists():
            return str(
                input_relative
            )

        return str(
            input_relative
        )

    return str(
        manifest_relative
    )


def normalize_manifest_paths(
        manifest_path: Path,
        output_manifest: Path,
        input_directory: Path | None = None,
) -> list[str]:
    """Normalize manifest FASTQ paths and write a runtime manifest."""
    manifest_path = Path(
        manifest_path
    )
    output_manifest = Path(
        output_manifest
    )
    manifest_dir = manifest_path.parent

    if input_directory is not None:
        input_directory = Path(
            input_directory
        ).expanduser().resolve()

    table = pd.read_csv(
        manifest_path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    table.columns = [
        str(column).strip().replace(
            "\r",
            "",
        )
        for column in table.columns
    ]

    required_columns = {
        "sample_id",
        "r1",
        "r2",
    }
    missing_columns = (
        required_columns
        - set(table.columns)
    )

    if missing_columns:
        raise ValueError(
            "Sample manifest is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    for column in ["r1", "r2"]:
        table[column] = table[column].map(
            lambda value: _resolve_manifest_fastq_path(
                value=value,
                manifest_dir=manifest_dir,
                input_directory=input_directory,
            )
        )

    output_manifest.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    table.to_csv(
        output_manifest,
        sep="\t",
        index=False,
    )

    return table["sample_id"].tolist()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Launches a mitopipeline run."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the production configuration YAML file.",
    )
    parser.add_argument(
        "--snakefile",
        default="ctrl/Snakefile",
        help="Path to the Snakefile.",
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=1,
        help="Number of cores to use.",
    )
    parser.add_argument(
        "--use-conda",
        action="store_true",
        help="Use conda environments.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Forward --dry-run to Snakemake.",
    )
    parser.add_argument(
        "--printshellcmds",
        action="store_true",
        help="Forward --printshellcmds to Snakemake.",
    )

    return parser.parse_args()


def load_config(
        config_path: Path,
) -> dict:
    """Load a YAML configuration file."""
    config_path = Path(
        config_path
    )

    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open(
            "r",
            encoding="utf-8",
    ) as handle:
        config = yaml.safe_load(
            handle
        )

    if config is None:
        raise ValueError(
            f"Configuration file is empty: {config_path}"
        )

    return config


def discover_fastq_pairs(
        input_dir: Path,
        job: PipelineJob,
) -> list[dict[str, str]]:
    """Discover paired-end FASTQ files from an input directory."""
    input_dir = Path(
        input_dir
    )

    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(
            f"Input directory not found: {input_dir}"
        )

    fastq_suffixes = [
        ".fastq.gz",
        ".fq.gz",
        ".fastq",
        ".fq",
    ]

    fastq_files: list[Path] = []

    for suffix in fastq_suffixes:
        fastq_files.extend(
            input_dir.glob(
                f"*{suffix}"
            )
        )

    fastq_files = sorted(
        set(
            fastq_files
        )
    )

    r1_files: dict[str, Path] = {}
    r2_files: dict[str, Path] = {}

    for fastq in fastq_files:
        name = fastq.name

        if "_R1" in name:
            sample_id = name.split(
                "_R1"
            )[0]
            r1_files[sample_id] = fastq
        elif "_R2" in name:
            sample_id = name.split(
                "_R2"
            )[0]
            r2_files[sample_id] = fastq
        elif "_1" in name:
            sample_id = name.split(
                "_1"
            )[0]
            r1_files[sample_id] = fastq
        elif "_2" in name:
            sample_id = name.split(
                "_2"
            )[0]
            r2_files[sample_id] = fastq

    sample_ids = sorted(
        set(r1_files)
        | set(r2_files)
    )

    if len(sample_ids) == 0:
        if job.job_logger is not None:
            job.job_logger.error(
                f"No FASTQ files found in {input_dir}."
            )
        raise FileNotFoundError(
            f"No FASTQ files found in {input_dir}."
        )

    records: list[dict[str, str]] = []

    for sample_id in sample_ids:
        if sample_id not in r1_files:
            raise ValueError(
                f"Missing R1 FASTQ for sample {sample_id}."
            )

        if sample_id not in r2_files:
            raise ValueError(
                f"Missing R2 FASTQ for sample {sample_id}."
            )

        records.append(
            {
                "sample_id": sample_id,
                "r1": str(r1_files[sample_id].resolve()),
                "r2": str(r2_files[sample_id].resolve()),
                "genus": "",
                "species": "",
                "source": "discovered_fastq",
            }
        )

    return records


def write_sample_manifest(
        manifest_path: Path,
        records: list[dict[str, str]],
        job: PipelineJob | None = None,
) -> None:
    """Write sample records to a TSV runtime manifest."""
    manifest_path = Path(
        manifest_path
    )
    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "sample_id",
        "r1",
        "r2",
        "genus",
        "species",
        "source",
    ]

    with manifest_path.open(
            "w",
            encoding="utf-8",
    ) as handle:
        handle.write(
            "\t".join(columns)
            + "\n"
        )

        for record in records:
            row = [
                str(record.get(column, ""))
                for column in columns
            ]
            handle.write(
                "\t".join(row)
                + "\n"
            )

    if job is not None and job.job_logger is not None:
        job.job_logger.info(
            f"Wrote runtime manifest to {manifest_path}."
        )


def prepare_runtime_manifest(
        config: dict,
        job: PipelineJob,
) -> Path:
    """Validate and prepare the job runtime manifest.

    If a manifest and input_directory are both supplied, manifest FASTQ
    filenames are resolved against input_directory when they are not found
    relative to the manifest file.
    """
    runtime_manifest = (
        job.job_dir
        / "validated_samples.tsv"
    )

    manifest_path = config.get(
        "manifest"
    )

    input_dir = (
        config.get("input_dir")
        or config.get("input_directory")
    )
    input_directory = (
        Path(input_dir)
        if input_dir is not None
        else None
    )

    if manifest_path is not None:
        manifest_path = Path(
            manifest_path
        )

        normalize_manifest_paths(
            manifest_path=manifest_path,
            output_manifest=runtime_manifest,
            input_directory=input_directory,
        )

        parse_sample_manifest(
            runtime_manifest,
            logger=job.job_logger,
        )

        job.job_logger.info(
            f"Copied validated manifest to {runtime_manifest}."
        )

        return runtime_manifest

    if input_directory is None:
        if job.job_logger is not None:
            job.job_logger.error(
                "Input directory not provided."
            )
        raise ValueError(
            "Input directory not provided."
        )

    records = discover_fastq_pairs(
        input_directory,
        job,
    )

    write_sample_manifest(
        runtime_manifest,
        records,
        job,
    )

    parse_sample_manifest(
        runtime_manifest,
        logger=job.job_logger,
    )

    job.job_logger.info(
        "Generated runtime manifest from discovered FASTQ files: "
        f"{runtime_manifest}."
    )

    return runtime_manifest


def sample_ids_from_manifest(
        runtime_manifest: Path,
) -> list[str]:
    """Read sample IDs from the runtime manifest."""
    table = pd.read_csv(
        runtime_manifest,
        sep="\t",
        dtype=str,
        keep_default_na=False,
    )

    if "sample_id" not in table.columns:
        raise ValueError(
            "Runtime manifest is missing required column: sample_id"
        )

    return table["sample_id"].tolist()


def write_runtime_config(
        config: dict,
        job: PipelineJob,
        runtime_manifest: Path,
) -> Path:
    """Write a runtime configuration file for Snakemake."""
    runtime_config = dict(
        config
    )

    runtime_config["job_id"] = job.job_id
    runtime_config["manifest"] = str(
        runtime_manifest
    )
    runtime_config["runtime_manifest"] = str(
        runtime_manifest
    )
    runtime_config["output_root"] = str(
        job.parent_dir
    )

    runtime_config_path = (
        job.job_dir
        / "runtime_config.yaml"
    )

    with runtime_config_path.open(
            "w",
            encoding="utf-8",
    ) as handle:
        yaml.safe_dump(
            runtime_config,
            handle,
            sort_keys=False,
        )

    job.job_logger.info(
        f"Wrote runtime config to {runtime_config_path}."
    )

    return runtime_config_path

def run_snakemake(
        snakefile: Path,
        runtime_config: Path,
        cores: int,
        use_conda: bool,
        logger: logging.Logger,
        dry_run: bool = False,
        printshellcmds: bool = False,
) -> subprocess.CompletedProcess:
    """Run Snakemake using the runtime configuration."""
    command = [
        "snakemake",
        "-s",
        str(snakefile),
        "--configfile",
        str(runtime_config),
        "--cores",
        str(cores),
        "--resources",
        "entrez=1"
    ]

    if use_conda:
        command.append(
            "--use-conda"
        )

    if dry_run:
        command.append(
            "--dry-run"
        )

    if printshellcmds:
        command.append(
            "--printshellcmds"
        )

    logger.info(
        "Starting Snakemake execution."
    )
    logger.debug(
        f"Snakemake command: {command}"
    )

    result = subprocess.run(
        command,
        cwd=Path.cwd(),
        check=False,
    )

    if result.returncode == 0:
        logger.info(
            "Snakemake execution completed successfully."
        )
    else:
        logger.error(
            "Snakemake execution failed with return code "
            f"{result.returncode}."
        )

    return result


def launch_pipeline(
        config_path: Path,
        snakefile: Path,
        cores: int = 1,
        use_conda: bool = False,
        dry_run: bool = False,
        printshellcmds: bool = False,
) -> int:
    """Launch a mitopipeline workflow run."""
    config = load_config(
        config_path
    )

    output_root = Path(
        config["output_root"]
    )
    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    job_id = _configured_job_id(
        config.get(
            "job_id"
        )
    )

    job = PipelineJob(
        parent_dir=output_root,
        job_id=job_id,
    )

    try:
        if job_id is not None:
            job.job_logger.info(
                f"Resuming configured pipeline job: {job_id}."
            )

        runtime_manifest = prepare_runtime_manifest(
            config,
            job,
        )

        job.set_samples(
            sample_ids_from_manifest(
                runtime_manifest
            )
        )

        job.mark_created()

        runtime_config = write_runtime_config(
            config,
            job,
            runtime_manifest,
        )

        result = run_snakemake(
            snakefile=snakefile,
            runtime_config=runtime_config,
            cores=cores,
            use_conda=use_conda,
            logger=job.job_logger,
            dry_run=dry_run,
            printshellcmds=printshellcmds,
        )

        if result.returncode == 0:
            job.mark_completed()
        else:
            job.mark_failed()

        return result.returncode

    except Exception as error:
        job.job_logger.exception(
            f"Pipeline launch failed: {error}"
        )
        job.mark_failed()
        return 1


def main() -> int:
    """Run the pipeline launcher from the command line."""
    args = parse_args()

    return launch_pipeline(
        config_path=Path(args.config),
        snakefile=Path(args.snakefile),
        cores=args.cores,
        use_conda=args.use_conda,
        dry_run=args.dry_run,
        printshellcmds=args.printshellcmds,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
