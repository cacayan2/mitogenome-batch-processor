"""Execution script for MITOS2 annotation."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.mitos2 import MITOS2Runner
from mitopipeline.logging.logger_factory import make_logger


def parse_bool(value: str) -> bool:
    value = value.strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Cannot parse boolean: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--conda-env", default="mito-annotation")
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--input-fasta", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--genetic-code", type=int, required=True)
    parser.add_argument("--refseqver", required=True)
    parser.add_argument("--refdir", required=True)
    parser.add_argument("--zip-output", action="store_true")
    parser.add_argument("--circular", required=True)
    parser.add_argument("--noplots", required=True)
    parser.add_argument("--best", required=True)
    parser.add_argument("--ncbicode", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    logger = make_logger(f"mitos2.{args.sample_id}", args.log_file)
    logger.info("Starting MITOS2 annotation for sample %s.", args.sample_id)

    try:
        runner = MITOS2Runner(
            sample_id=args.sample_id,
            input_fasta=Path(args.input_fasta).resolve(),
            output_dir=Path(args.output_dir).resolve(),
            working_dir=Path(args.working_dir).resolve(),
            conda_env=args.conda_env,
            genetic_code=args.genetic_code,
            refseqver=args.refseqver,
            refdir=Path(args.refdir).resolve(),
            circular=parse_bool(args.circular),
            noplots=parse_bool(args.noplots),
            zip_output=args.zip_output,
            best=parse_bool(args.best),
            ncbicode=parse_bool(args.ncbicode),
            logger=logger,
        )
        result = runner.run()
        return 0 if result.success else (result.return_code or 1)
    except Exception as error:
        logger.exception("MITOS2 annotation failed for sample %s: %s", args.sample_id, error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
