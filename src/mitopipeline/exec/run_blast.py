"""Execution layer for BLAST."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.blast import BlastRunner
from mitopipeline.logging.logger_factory import make_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--query-fasta", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--mode", choices=["local", "remote"], required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--threads", type=int, required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--output-format", required=True)
    parser.add_argument("--evalue", type=float, required=True)
    parser.add_argument("--max-target-seqs", type=int, required=True)
    parser.add_argument("--max-hsps", type=int)
    parser.add_argument("--perc-identity", type=float)
    parser.add_argument("--query-coverage", type=float)
    parser.add_argument("--word-size", type=int)
    return parser.parse_args()


def main() -> int:
    logger = None

    try:
        args = parse_args()
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        logger = make_logger(
            name=f"blast.{args.sample_id}",
            log_file_path=args.log_file,
        )

        if logger is not None: logger.info(f"Running BLAST for sample {args.sample_id}.")
        result = BlastRunner(
            query_fasta=Path(args.query_fasta),
            database=args.database,
            output_file=Path(args.output_file),
            working_dir=Path(args.working_dir),
            sample_id=args.sample_id,
            mode=args.mode,
            threads=args.threads,
            task=args.task,
            output_format=args.output_format,
            evalue=args.evalue,
            max_target_seqs=args.max_target_seqs,
            max_hsps=args.max_hsps,
            perc_identity=args.perc_identity,
            query_coverage=args.query_coverage,
            word_size=args.word_size,
            logger=logger,
        ).run()
        if logger is not None: logger.info(f"BLAST finished for sample {args.sample_id}.")
        return 0 if result.success else result.return_code or 1

    except Exception as error:
        if logger is not None:
            logger.exception("BLAST failed: %s", error)
        logger.error("BLAST failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
