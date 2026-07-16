"""Execution layer for run-level Markdown reporting."""
import argparse
from pathlib import Path
from mitopipeline.logging.logger_factory import make_logger
from mitopipeline.reporting.run_markdown_report import write_run_report
from mitopipeline.reporting.run_report_data import collect_run_report_data
from mitopipeline.reporting.rescue_reporting import run_rescue_section

def parse_args() -> argparse.Namespace:
    parser=argparse.ArgumentParser(description="Generate a run-level MitoPipeline Markdown report.")
    parser.add_argument("--job-id",required=True); parser.add_argument("--job-directory",required=True)
    parser.add_argument("--enabled-stages",nargs="*",default=[]); parser.add_argument("--output",required=True)
    parser.add_argument("--log-file",required=True); return parser.parse_args()

def main() -> int:
    logger=None
    try:
        args=parse_args(); logger=make_logger(name="run_report",log_file_path=args.log_file)
        job_directory=Path(args.job_directory)
        run_data=collect_run_report_data(job_id=args.job_id,job_directory=job_directory,enabled_stages=args.enabled_stages,logger=logger)
        output_path=write_run_report(run_data=run_data,output_path=Path(args.output))
        section=run_rescue_section(job_directory)
        if section: output_path.write_text(output_path.read_text(encoding="utf-8").rstrip()+"\n\n"+section,encoding="utf-8")
        logger.info("Wrote run-level report to %s.",output_path); return 0
    except Exception as error:
        if logger is not None: logger.exception("Run-level report generation failed: %s",error)
        return 1
if __name__=="__main__": raise SystemExit(main())
