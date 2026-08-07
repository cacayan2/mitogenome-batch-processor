"""
sample.py

Data model which stores information about a sample for a single paired-end sequencing run.
"""

# Imports
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

# We use this tag so that the object when instantiated is immutable. 
@dataclass(frozen = True)
class Sample:
    """
    A sample contains the paths to the paired-end reads and all associated manifest metadata.

    The commonly used biological fields remain explicit attributes for compatibility.
    Every nonblank manifest column is also retained in metadata so reporting, archival,
    and future stages can use it without repeatedly expanding this model.

    Attributes:
        sample_id (str): The unique identifier for the sample.
        r1 (Path): The absolute path to the R1 read file.
        r2 (Path): The absolute path to the R2 read file.
        genus (str | None = None): The genus of the sample, if available.
        species (str | None = None): The species of the sample, if available.
        source (str | None = None): The source of the sample, if available.
        metadata (Mapping[str, str | None]): A mapping of all available metadata columns.

    Methods:
        has_species(self) -> bool: Checks if the sample has a species defined.
        has_genus(self) -> bool: Checks if the sample has a genus defined.
        has_source(self) -> bool: Checks if the sample has a source defined.
        fastq_files(self) -> tuple[Path, Path]: Returns the paths to the R1 and R2 fastq files.
        get_metadata(self, field_name: str, default: str | None = None) -> str | None: Retrieves the value of a metadata field by its name.
        scientific_name(self) -> str | None: Returns the best available scientific name for the sample, constructed from genus and species if not explicitly provided in the metadata.
    """
    # Instantiating all of the member variables for the Sample class.
    sample_id: str
    r1: Path
    r2: Path
    genus: str | None = None
    species: str | None = None
    source: str | None = None

    # For metadata, we use a MappingProxyType to ensure that the metadata is immutable after instantiation.
    metadata: Mapping[str, str] = field(default_factory = dict)

    def __post_init__(self):
        """
        Following instantiation (hence __post_init__), we normalize paths and
        freeze the metadata mapping.     
        """
        # We resolve the paths to R1 and R2 ensuring they are absolute paths.
        object.__setattr__(self, "r1", Path(self.r1).resolve())
        object.__setattr__(self, "r2", Path(self.r2).resolve())

        # Then we normalize (remove any problematic characters) and freeze the metadata mapping.
        # First, we strip whitespace from keys and values, and then remove any entries with None or empty strings.
        normalized_metadata = {
            str(key).strip(): str(value).strip() for key, value in dict(self.metadata).items()
            if key is not None and value is not None and str(key).strip() and str(value).strip()
        }

        # Now we define values that are explicitly necessary to run the pipeline (namely the sample_id, r1, and r2 files).
        required = {"sample_id": self.sample_id,
                    "r1": str(self.r1),
                    "r2": str(self.r2)
        }

        # We then add optional metadata fields (genus, species, and source) to the normalized metadata dictionary if they are not None.
        optional = {"genus": self.genus, 
                    "species": self.species, 
                    "source": self.source
        }

        # We defined instantiation of metadata in line 55. We reuse the same logic to add the required fields. 
        # We then update the normalized data with the optional fields - we must check that they are not empty strings.
        normalized_metadata.update(required)
        normalized_metadata.update(
            {
                key: value for key, value in optional.items()
                if value is not None and str(value).strip()
            }
        )

        # Finally we set the attribute for metadata with the normalized and frozen mapping.
        object.__setattr__(self, "metadata", MappingProxyType(normalized_metadata))

    def has_species(self) -> bool:
        """
        Checks if the sample has a species defined.

        Returns:
            bool: True if species is defined and not empty, False otherwise.
        """
        return self.species is not None

    def has_genus(self) -> bool:
        """
        Checks if the sample has a genus defined.

        Returns:
            bool: True if genus is defined and not empty, False otherwise.
        """
        return self.genus is not None

    def has_source(self) -> bool:
        """
        Checks if the sample has a source defined.

        Returns:
            bool: True if source is defined and not empty, False otherwise.
        """
        return self.source is not None

    def fastq_files(self) -> tuple[Path, Path]:
        """
        Returns the paths to the R1 and R2 fastq files.

        Returns:
            tuple[Path, Path]: A tuple containing the paths to the R1 and R2 fastq files.
        """
        return self.r1, self.r2

    def get_metadata(self, field_name: str, default: str | None = None) -> str | None:
        """
        Retrieves the value of a metadata field by its name.

        Args:
            field_name (str): The name of the metadata field to retrieve.
            default (str | None): The default value to return if the field is not found.

        Returns:
            str | None: The value of the metadata field, or the default value if not found.
        """
        return self.metadata.get(field_name, default)


    # This property tag ensures that the scientific name is immutable after instantiation.
    @property
    def scientific_name(self) -> str | None:
        """
        Returns the best available scientific name for the sample.

        Returns: 
            str | None: The scientific name in the format "Genus species subspecies" if all are available,
                        "Genus" if only genus is available, "species" if only species is available, or None if none is available.
        """
        # If a scientific anme is explicitly provided in the metadata, we return that. Otherwise, we construct it from genus and species.
        explicit = self.metadata.get("organism")
        if explicit: 
            return explicit

        # If no explicit scientific name is provided, we construct it from genus, species, and subspecies.
        parts = [
            self.genus or "",
            self.species or "",
            self.metadata.get("subspecies", "")
        ]

        # We join the non-empty parts with a space and strip any leading/trailing whitespace to form the scientific name.
        name = " ".join(part for part in parts if part).strip()

        # If the constructed name is empty, we return None; otherwise, we return the constructed name.
        return name if name else None

        