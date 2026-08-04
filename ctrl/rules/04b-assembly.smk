"""
05-assembly.smk

Executes and validates GetOrganelle on trimmed data.
"""

# Imports
from pathlib import Path

# To make things easier, we'll subset the portion of the config related to GetOrganelle.
GETORGANELLE_CONFIG = config["tools"]["getorganelle"]

def getorganelle_database_input(config: dict) -> list[str]:
    """
    If the database needs to be initialized, returns a path to the database.done file,
    otherwise returns an empty string. 

    Args:
        config: A dictionary - this is a global variable Snakemake generates whenever --configfile is passed.
    Returns:
        list[str]: A list containing either an empty string or path, depending on whether initialize_database is T/F. 
    """
    if GETORGANELLE_CONFIG.get("initialize_database") is True:
        #TODO pass db_type into exec script and validate that it is present and an acceptable type.
        # Extracts the database type and returns the path to the database.
        db_type = GETORGANELLE_CONFIG.get("database_type")
        return str(JOB_DIR / "setup" / "getorganelle" / f"{db_type}.done")
    # Returning a list with an empty string, which is generally safe for Snakemake input parsing.
    return [""]

def getorganelle_optional_args(config: dict) -> str:
    """
    This function parses the config and checks for optional command-line arguments.
    It then returns a string to append to the original command.

    Args:
        config: A dictionary - this is a global variable Snakemake generates whenever --configfile is passed.
    Returns:
        str: A string containing the optional command-line arguments to be appended.
    """
    # We'll eventually return this but joined together.
    args = []

    # Dictionary mapping options that require a value - the config name is mapped to the true flag passed to GetOrganelle. 
    # For more information about these flags, see GetOrganelle documentation or see this repository's README to view
    # how to configure config.yaml.
    value_options = {
        "max_rounds": "--max-rounds",
        "kmer": "--kmer",
        "word_size": "--word-size",
        "pre_grouping": "--pre-grouping",
        "max_reads": "--max-reads",
        "target_coverage": "--target-coverage",
        "min_read_length": "--min-read-length",
        "max_read_length": "--max-read-length",
        "expected_max_size": "--expected-max-size",
        "expected_min_size": "--expected-min-size",
        "seed_file": "--seed-file",
        "genes_file": "--genes-file",
        "exclude_fasta": "--exclude-fasta",
        "prefix": "--prefix",
        "round_output_prefix": "--round-output-prefix",
        "blast_path": "--blast-path",
        "bandage_path": "--bandage-path",
        "spades_path": "--spades-path",
        "disentangle_df": "--disentangle-df",
        "disentangle_time_limit": "--disentangle-time-limit",
    }

    # Now we iterate through each of the value options and
    # append values that are not None to args.
    for key, flag in value_options.items():
        value = GETORGANELLE_CONFIG.get(key)
        if value is not None:
            args.append(f"{flag} {value}")

    # Dictionary mapping options that are boolean - the config name is mapped to the true flag passed to GetOrganelle.
    # For more information about these flags, see GetOrganelle documentation or see this repository's README to view
    # how to configure config.yaml.
    boolean_options = {
        "overwrite": "--overwrite",
        "continue_run": "--continue-run",
        "fast_mode": "--fast-mode",
        "reverse_lsc": "--reverse-lsc",
        "no_slim": "--no-slim",
        "keep_temp_files": "--keep-temp-files",
        "verbose": "--verbose",
    }

    # Now we iterate through each of the boolean options and
    # append values that are True to args.
    for key, flag in boolean_options.items():
        if tool_config.get(key) is True:
            args.append(flag)

    # Then we join args and return - this will eventually be appended to the final command sent to the terminal.
    return " ".join(args)

rule assembly:
    """
    This takes the trimmed r1 and r2 as inputs, alongside the .done file for both trimming
    and database creation.

    Remember: This file is a sequential extension of ctrl/Snakefile, so variables defined there
    are also in scope for this rule. 

    Args:
         
    """
    input:
        r1 = str(JOB_DIR / "trimming" / "{sample}" / "{sample}.R1.trimmed.fastq.gz"),
        r2 = str(JOB_DIR / "trimming" / "{sample} / {sample}.R2.trimmed.fastq.gz"),
        trimming_done = str(JOB_DIR / "trimming" / "{sample}" / "{sample}.trimming.done"),
        database_done = getorganelle_database_input(config)[0]
    
