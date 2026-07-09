"""Sample model for one paired-end sequencing sample."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Sample:
    """Validated sample paths plus all manifest metadata.

    The commonly used biological fields remain explicit attributes for
    compatibility. Every nonblank manifest column is also retained in
    ``metadata`` so reporting, archival, and future stages can use it without
    repeatedly expanding this model.
    """

    sample_id: str
    r1: Path
    r2: Path
    genus: str | None = None
    species: str | None = None
    source: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize paths and freeze a complete metadata mapping."""
        object.__setattr__(self, "r1", Path(self.r1))
        object.__setattr__(self, "r2", Path(self.r2))

        normalized = {
            str(key).strip(): str(value).strip()
            for key, value in dict(self.metadata).items()
            if key is not None
            and value is not None
            and str(key).strip()
            and str(value).strip()
        }

        canonical = {
            "sample_id": self.sample_id,
            "r1": str(self.r1),
            "r2": str(self.r2),
        }

        optional = {
            "genus": self.genus,
            "species": self.species,
            "source": self.source,
        }

        normalized.update(canonical)
        normalized.update(
            {
                key: value
                for key, value in optional.items()
                if value is not None and str(value).strip()
            }
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(normalized),
        )

    def has_species(self) -> bool:
        """Return whether species metadata is present."""
        return self.species is not None

    def has_genus(self) -> bool:
        """Return whether genus metadata is present."""
        return self.genus is not None

    def has_source(self) -> bool:
        """Return whether source metadata is present."""
        return self.source is not None

    def fastq_files(self) -> tuple[Path, Path]:
        """Return the paired FASTQ paths."""
        return self.r1, self.r2

    def get_metadata(
        self,
        field_name: str,
        default: str | None = None,
    ) -> str | None:
        """Return one manifest metadata value."""
        return self.metadata.get(field_name, default)

    @property
    def scientific_name(self) -> str | None:
        """Return the best available scientific name."""
        explicit = self.metadata.get("organism")
        if explicit:
            return explicit

        parts = [
            self.genus or "",
            self.species or "",
            self.metadata.get("subspecies", ""),
        ]
        name = " ".join(part for part in parts if part).strip()
        return name or None
