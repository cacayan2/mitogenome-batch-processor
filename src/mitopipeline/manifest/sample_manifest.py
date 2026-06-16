"""sample_manifest.py

This module contains functionality for extracting data from the sample.tsv file.
"""

# Imports
import logging
from pathlib import Path
import pandas as pd
from mitopipeline.models.sample import Sample

def parse_sample_manifest(manifest_path: Path, logger: logging.Logger | None = None) -> list[Sample]:
    """Parses a sample manifest file and returns a list of Sample objects.

    Args:
        sample_manifest_path (Path): The path to the sample manifest file.
        mode (str, optional): The mode to use for parsing the sample manifest. Defaults to "minimal".

    Returns:
        list[Sample]: A list of Sample objects.
    """
    # Normalizing the manifest path.
    manifest_path = Path(manifest_path)
    manifest_dir = manifest_path.parent

    # Sets the columns required for each mode.
    REQUIRED_COLUMNS = {"sample_id", "r1", "r2"}

    # Sanity Checking Part 1
    ## Verifies that the manifest exists.
    if not manifest_path.exists(): 
        if logger is not None: logger.error(f"Sample manifest file {manifest_path} does not exist.")
        raise FileNotFoundError(f"Sample manifest file {manifest_path} does not exist.")
    ## Checking if the manifest is empty.
    if manifest_path.stat().st_size == 0:
        if logger is not None: logger.error(f"Sample manifest file {manifest_path} is empty.")
        raise ValueError(f"Sample manifest file {manifest_path} is empty.")

    if logger is not None: logger.info(f"Attempting to parse sample manifest file at {manifest_path}.")

    # Reading the manifest.
    df = pd.read_csv(manifest_path, sep = "\t")

    # Sanity Checking Part 2
    ## Verifies the manifest isn't empty.
    if df.empty: 
        if logger is not None: logger.error(f"Sample manifest file {manifest_path} is empty.")
        raise ValueError(f"Sample manifest file {manifest_path} is empty.")
    ## Verifies that the manifest has at least the required columns (minimal).
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if len(missing_columns) > 0:
        if logger is not None: logger.error(f"Sample manifest file {manifest_path} is missing the following columns: {missing_columns}.")
        raise ValueError(f"Sample manifest file {manifest_path} is missing the following columns: {missing_columns}.")

    # Instantiating sample list.
    samples = []

    # Parsing dataset
    for index, row in df.iterrows():
        ## Obtaining the line number.
        line_number = index + 2
        
        ## Validating sample_id.
        sample_id = row["sample_id"]
        if pd.isna(sample_id) or str(sample_id).strip() == "":
            if logger is not None: logger.error(f"Row {line_number} of sample manifest file is missing sample_id.")
            raise ValueError (f"Row {line_number} of sample manifest file is missing sample_id.")
        sample_id = str(sample_id).strip()
        
        ## Validating r1 and r2.
        r1_value = row["r1"]
        r2_value = row["r2"]
        if pd.isna(r1_value) or str(r1_value).strip() == "":
            if logger is not None: logger.error(f"Row {line_number} of sample manifest file is missing r1.")
            raise ValueError (f"Row {line_number} of sample manifest file is missing r1.")
        if pd.isna(r2_value) or str(r2_value).strip() == "":
            if logger is not None: logger.error(f"Row {line_number} of sample manifest file is missing r2.")
            raise ValueError (f"Row {line_number} of sample manifest file is missing r2.")

        ## Resolving r1/r2 relative to manifest location.
        manifest_dir = manifest_path.parent
        r1_path = _resolve_manifest_path(r1_value, manifest_dir)
        r2_path = _resolve_manifest_path(r2_value, manifest_dir)

        ## Check that the FASTQ file exists.
        if not r1_path.exists():
            if logger is not None: logger.error(f"Row {line_number} of sample manifest file {manifest_path} is missing r1.")
            raise FileNotFoundError(f"Row {line_number} of sample manifest file {manifest_path} is missing r1.")
        if not r2_path.exists():
            if logger is not None: logger.error(f"Row {line_number} of sample manifest file {manifest_path} is missing r2.")
            raise FileNotFoundError(f"Row {line_number} of sample manifest file {manifest_path} is missing r2.")
        
        ## Converts blank species to None.
        species = _optional_field(row, "species")
        
        ## Converts blank condition to None.
        condition = _optional_field(row, "condition")
        
        ## Creates the sample object.
        samples.append(Sample(sample_id, r1_path, r2_path, species, condition))

    # Logging success:
    if logger is not None: logger.info(f"Successfully parsed sample manifest file at {manifest_path}, loaded {len(samples)} samples.")
    
    # Returning sample list.
    return samples

def _resolve_manifest_path(value: str, manifest_dir: Path) -> Path:
    """
    Helper function to resolve a path relative to the manifest directory.

    Args:
        value (str): The path to resolve.
        manifest_dir (Path): The manifest directory.

    Returns:
        Path: The resolved path.
    """
    path = Path(str(value).strip())
    if path.is_absolute():
        return path.resolve()
    return (manifest_dir / path).resolve()

def _optional_field(row, column_name: str) -> str:
    """
    Helper function to resolve a path relative to the manifest directory.

    Args:
        value (str): The path to resolve.
        manifest_dir (Path): The manifest directory.

    Returns:
        Path: The resolved path.
    """
    # Checks if the column exists.
    if column_name not in row.index:
        return None
    
    # Retrieves the value.
    value = row[column_name]

    # Checks if the value is empty.
    if pd.isna(row[column_name]) or str(row[column_name]).strip() == "":
        return None
    return str(row[column_name]).strip()

    


   
    
    

    




    
    
