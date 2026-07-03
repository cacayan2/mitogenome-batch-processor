"""fastqc_stats.py

The purpose of this module is to parse FastQC output files and convert them into structured metrics that the reporting system can use later.
"""

# Imports
import logging
from pathlib import Path
from typing import Union
import zipfile
import pandas as pd
from mitopipeline.models.fastqc_stats import FastQCStats

def parse_fastqc_summary(
                        zip_path: Path, 
                        sample_id: str, 
                        qc_stage: str, 
                        logger: logging.Logger | None = None
                        ) -> FastQCStats:
    """Parses the fastqc summary file and returns a FastQCStats object for the sample.

    Args:
        zip_path (Path): The path to the fastqc zip file.
        sample_id (str): The sample id.
        qc_stage (str): The quality control stage.
        logger (logging.Logger | None, optional): The logger to use. Defaults to None.

    Returns:
        FastQCStats: A FastQCStats object for the sample.
    """
    # Checking if the zip file exists.
    zip_path = Path(zip_path)
    if not zip_path.exists() or not zip_path.is_file():
        if logger is not None: logger.error(f"Fastqc zip file not found: {zip_path}")
        raise FileNotFoundError(f"Fastqc zip file not found: {zip_path}")
    
    # Verifying if the zip file is a valid zip file, extracting data.
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_obj:
            summary_file = _find_summary_file(zip_obj)
            with zip_obj.open(summary_file, "r") as file_handle:
                df = pd.read_csv(file_handle, sep = "\t", header = None)
    except zipfile.BadZipFile as error:
        if logger is not None: logger.error(f"FastQC zip file is malformed: {zip_path}")
        raise ValueError(f"FastQC zip file is malformed: {zip_path}") from error
    if df.shape[1] < 3:
        if logger is not None: logger.error(f"FastQC summary file is malformed: {zip_path}")
        raise ValueError(f"FastQC summary file is malformed: {zip_path}")

    # Extracting module statuses.
    module_statuses = {}
    for _, row in df.iterrows():
        status = str(row[0]).strip()
        module_name = str(row[1]).strip()
        module_statuses[module_name] = status
    
    # Obtaining source file.
    source_file = str(df.iloc[0, 2]).strip()

    # Creating FastQCStats object.
    stats = FastQCStats(
        sample_id = sample_id,
        qc_stage = qc_stage,
        source_file = source_file,
        overall_status = calculate_overall_fastqc_status(module_statuses),
        module_statuses = module_statuses,
    )

    # Logging and returning.
    if logger is not None: logger.info(f"FastQC summary file parsed successfully: {zip_path}.")
    return stats
    

def calculate_overall_fastqc_status(module_statuses: dict[str, str]) -> str:
    """Calculate overall FastQC status from module statuses.
    
    Args:
        module_statuses (dict[str, str]): A dictionary of module statuses.
    
    Returns:
        str: The overall FastQC status.
    """
    # Obtain set of module statuses.
    statuses = set(module_statuses.values())

    # Logic to determine overall FastQC status.
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"

def _find_summary_file(zip_obj: zipfile.ZipFile) -> str:
    """Find the summary.txt file in the zip object.
    
    Args:
        zip_obj (zipfile.ZipFile): The zip object to search.
    
    Returns:
        str: The path to the summary.txt file.
    """
    for file in zip_obj.namelist():
        if file.endswith("summary.txt"):
            return file
    
    raise ValueError("No summary.txt file found in zip file.")




