"""test_stage_config.py

Unit tests for stage configuration fixtures.
"""

# Imports
from pathlib import Path
import yaml


def test_qc_raw_only_config_has_expected_stages():
    """Test qc_raw-only stage configuration."""

    config_path = Path("tests/fixtures/config/config_qc_raw_only.yaml")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["stages"]["qc_raw"] is True
    assert config["stages"]["trimming"] is False
    assert config["stages"]["qc_trimmed"] is False
    assert config["stages"]["assembly"] is False
    assert config["stages"]["annotation"] is False
    assert config["stages"]["phylogeny"] is False
    assert config["stages"]["reporting"] is False


def test_preprocessing_only_config_has_expected_stages():
    """Test preprocessing-only stage configuration."""

    config_path = Path("tests/fixtures/config/config_preprocessing_only.yaml")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["stages"]["qc_raw"] is True
    assert config["stages"]["trimming"] is True
    assert config["stages"]["qc_trimmed"] is True
    assert config["stages"]["assembly"] is False
    assert config["stages"]["annotation"] is False
    assert config["stages"]["phylogeny"] is False
    assert config["stages"]["reporting"] is False