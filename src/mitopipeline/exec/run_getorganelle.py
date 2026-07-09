"""Execution layer connecting GetOrganelle to Snakemake."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.getorganelle import GetOrganelleRunner
from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.models.sample import Sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run GetOrganelle on one sample."
    )
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--in1", required=True)
    parser.add_argument("--in2", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--organelle-type", required=True)
    parser.add_argument("--threads", type=int, required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--kmer", default=None)
    parser.add_argument("--word-size", type=int, default=None)
    parser.add_argument("--pre-grouping", type=float, default=None)
    parser.add_argument("--max-reads", type=int, default=None)
    parser.add_argument("--target-coverage", type=int, default=None)
    parser.add_argument("--min-read-length", type=int, default=None)
    parser.add_argument("--max-read-length", type=int, default=None)
    parser.add_argument("--expected-max-size", type=int, default=None)
    parser.add_argument("--expected-min-size", type=int, default=None)
    parser.add_argument("--seed-file", default=None)
    parser.add_argument("--genes-file", default=None)
    parser.add_argument("--exclude-fasta", default=None)
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--round-output-prefix", default=None)
    parser.add_argument("--blast-path", default=None)
    parser.add_argument("--bandage-path", default=None)
    parser.add_argument("--spades-path", default=None)
    parser.add_argument("--disentangle-df", type=float, default=None)
    parser.add_argument("--disentangle-time-limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--continue-run", action="store_true")
    parser.add_argument("--fast-mode", action="store_true")
    parser.add_argument("--reverse-lsc", action="store_true")
    parser.add_argument("--no-slim", action="store_true")
    parser.add_argument("--keep-temp-files", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def build_tool_options(args: argparse.Namespace) -> dict:
    return {
        "max_rounds": args.max_rounds,
        "kmer": args.kmer,
        "word_size": args.word_size,
        "pre_grouping": args.pre_grouping,
        "max_reads": args.max_reads,
        "target_coverage": args.target_coverage,
        "min_read_length": args.min_read_length,
        "max_read_length": args.max_read_length,
        "expected_max_size": args.expected_max_size,
        "expected_min_size": args.expected_min_size,
        "seed_file": args.seed_file,
        "genes_file": args.genes_file,
        "exclude_fasta": args.exclude_fasta,
        "prefix": args.prefix,
        "round_output_prefix": args.round_output_prefix,
        "blast_path": args.blast_path,
        "bandage_path": args.bandage_path,
        "spades_path": args.spades_path,
        "disentangle_df": args.disentangle_df,
        "disentangle_time_limit": args.disentangle_time_limit,
        "overwrite": args.overwrite,
        "continue_run": args.continue_run,
        "fast_mode": args.fast_mode,
        "reverse_lsc": args.reverse_lsc,
        "no_slim": args.no_slim,
        "keep_temp_files": args.keep_temp_files,
        "verbose": args.verbose,
    }


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

        final_output_dir = Path(args.output_dir)
        native_output_dir = (
            final_output_dir
            / args.sample_id
        )

        logger.info(
            f"Starting GetOrganelle execution for sample "
            f"{sample.sample_id}."
        )
        logger.debug(
            f"Native output directory: {native_output_dir}"
        )
        logger.debug(
            f"Normalized output directory: {final_output_dir}"
        )

        runner = GetOrganelleRunner(
            working_dir=Path(args.working_dir),
            output_dir=native_output_dir,
            final_output_dir=final_output_dir,
            sample=sample,
            organelle_type=args.organelle_type,
            tool_options=build_tool_options(args),
            threads=args.threads,
            logger=logger,
        )

        result = runner.run()

        if not result.success:
            logger.error(
                f"GetOrganelle failed for sample {sample.sample_id}."
            )
            logger.debug(f"Return code: {result.return_code}")
            logger.debug(f"stdout: {result.stdout}")
            logger.debug(f"stderr: {result.stderr}")
            return result.return_code or 1

        logger.info(
            f"GetOrganelle completed successfully for sample "
            f"{sample.sample_id}."
        )
        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"GetOrganelle execution failed: {error}"
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
