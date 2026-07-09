"""Execution layer for raw-read FastQC."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.fastqc import FastQCRunner
from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.models.sample import Sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run FastQC on raw paired-end reads."
    )
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--r1", required=True)
    parser.add_argument("--r2", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--threads", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    logger = None

    try:
        args = parse_args()
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        logger = make_logger(
            name="fastqc.raw",
            log_file_path=args.log_file,
        )
        sample = Sample(
            sample_id=args.sample_id,
            r1=Path(args.r1),
            r2=Path(args.r2),
        )

        final_output_dir = Path(args.output_dir)
        native_output_dir = (
            final_output_dir
            / "work"
            / args.sample_id
        )

        logger.info(
            f"Starting FastQC execution for raw sample "
            f"{sample.sample_id}."
        )

        runner = FastQCRunner(
            sample=sample,
            output_dir=native_output_dir,
            final_output_dir=final_output_dir,
            r1_output_stem=f"{sample.sample_id}_R1",
            r2_output_stem=f"{sample.sample_id}_R2",
            working_dir=Path(args.working_dir),
            logger=logger,
            threads=args.threads,
            tool_name="fastqc.raw",
        )

        result = runner.run()

        if not result.success:
            logger.error(
                f"FastQC failed for raw sample {sample.sample_id}."
            )
            logger.debug(f"Return code: {result.return_code}")
            logger.debug(f"stdout: {result.stdout}")
            logger.debug(f"stderr: {result.stderr}")
            return result.return_code or 1

        logger.info(
            f"FastQC completed successfully for raw sample "
            f"{sample.sample_id}."
        )
        return 0

    except Exception as error:
        if logger is not None:
            logger.exception(
                f"FastQC raw execution failed: {error}"
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
