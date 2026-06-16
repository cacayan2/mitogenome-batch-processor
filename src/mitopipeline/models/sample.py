"""sample.py

Class definition for a sample within a pipeline job. 

"""

# Imports
from pathlib import Path
from dataclasses import dataclass

class Sample():
    """
    Sample class for a sample within a pipeline job.
    """
    def __init__(self, sample_id: str, r1: Path, r2: Path, species: str | None = None, condition: str | None = None):
        self._sample_id = sample_id
        self._r1 = r1
        self._r2 = r2
        self._species = species
        self._condition = condition

    # Getters
    def get_sample_id(self): return self._sample_id
    def get_r1(self): return self._r1
    def get_r2(self): return self._r2
    def get_species(self): return self._species
    def get_condition(self): return self._condition

    # Setters
    def set_sample_id(self, sample_id): self._sample_id = sample_id
    def set_r1(self, r1): self._r1 = r1
    def set_r2(self, r2): self._r2 = r2
    def set_species(self, species): self._species = species
    def set_condition(self, condition): self._condition = condition

    # Deleters
    def del_sample_id(self): del self._sample_id
    def del_r1(self): del self._r1
    def del_r2(self): del self._r2
    def del_species(self): del self._species
    def del_condition(self): del self._condition
    


    