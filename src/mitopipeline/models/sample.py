"""sample.py

Class definition for a sample within a pipeline job. 

"""

# Imports
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen = True)
class Sample:
    """
    Sample model is a lightweight representation of a sequencing sample. 

    Manifest parsing, validation, and sample discovery occur elsewhere.

    The Sample model simply stores validated sample metadata for use throughout the pipeline. 
    """
    sample_id: str
    r1: Path
    r2: Path
    genus: str | None = None
    species: str | None = None
    source: str | None = None


    # Sample validation functions.
    def has_species(self) -> bool: return self.species is not None
    def has_genus(self) -> bool: return self.genus is not None
    def has_source(self) -> bool: return self.source is not None
    def fastq_files(self) -> tuple[Path, Path]: return (self.r1, self.r2)


    