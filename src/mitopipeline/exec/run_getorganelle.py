"""Execution layer connecting GetOrganelle to Snakemake."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.getorganelle import GetOrganelleRunner
from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.models.sample import Sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--in1", required=True)
    parser.add_argument("--in2", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--organelle-type", required=True)
    parser.add_argument("--threads", type=int, required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--max-rounds", type=int)
    parser.add_argument("--kmer")
    parser.add_argument("--word-size", type=int)
    parser.add_argument("--pre-grouping", type=float)
    parser.add_argument("--max-reads", type=int)
    parser.add_argument("--target-coverage", type=int)
    parser.add_argument("--min-read-length", type=int)
    parser.add_argument("--max-read-length", type=int)
    parser.add_argument("--expected-max-size", type=int)
    parser.add_argument("--expected-min-size", type=int)
    parser.add_argument("--seed-file")
    parser.add_argument("--genes-file")
    parser.add_argument("--exclude-fasta")
    parser.add_argument("--prefix")
    parser.add_argument("--round-output-prefix")
    parser.add_argument("--blast-path")
    parser.add_argument("--bandage-path")
    parser.add_argument("--spades-path")
    parser.add_argument("--disentangle-df", type=float)
    parser.add_argument("--disentangle-time-limit", type=int)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--continue-run", action="store_true")
    parser.add_argument("--fast-mode", action="store_true")
    parser.add_argument("--reverse-lsc", action="store_true")
    parser.add_argument("--no-slim", action="store_true")
    parser.add_argument("--keep-temp-files", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    logger = None

    try:
        args = parse_args()
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        logger = make_logger(
            name="getorganelle",
            log_file_path=args.log_file,
        )

        sample = Sample(
            sample_id=args.sample_id,
            r1=Path(args.in1),
            r2=Path(args.in2),
        )

        options = {
            key: value
            for key, value in vars(args).items()
            if key
            not in {
                "sample_id",
                "in1",
                "in2",
                "output_dir",
                "working_dir",
                "organelle_type",
                "threads",
                "log_file",
            }
        }
        if logger is not None: logger.info(f"Running GetOrganelle for {sample}.")
        result = GetOrganelleRunner(
            working_dir=Path(args.working_dir),
            output_dir=Path(args.output_dir),
            sample=sample,
            organelle_type=args.organelle_type,
            tool_options=options,
            threads=args.threads,
            logger=logger,
        ).run()
        if logger is not None: logger.info(f"GetOrganelle finished for {sample}.")
        return 0 if result.success else result.return_code or 1

    except Exception as error:
        if logger is not None:
            logger.error("GetOrganelle failed: %s", error)
            logger.exception("GetOrganelle failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
