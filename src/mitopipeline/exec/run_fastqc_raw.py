"""Execution layer for raw-read FastQC."""

from __future__ import annotations

import argparse
from pathlib import Path

from mitopipeline.api.fastqc import FastQCRunner
from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.models.sample import Sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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
        if logger is not None: logger.info(f"Starting FastQC raw execution for raw sample {sample.sample_id}.")
        result = FastQCRunner(
            working_dir=Path(args.working_dir),
            output_dir=Path(args.output_dir),
            sample=sample,
            r1_output_stem="R1",
            r2_output_stem="R2",
            threads=args.threads,
            logger=logger,
            tool_name="fastqc.raw",
        ).run()
        if logger is not None: logger.info(f"FastQC raw execution for raw sample {sample.sample_id} finished.")
        return 0 if result.success else result.return_code or 1

    except Exception as error:
        if logger is not None:
            logger.exception("FastQC raw failed: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
