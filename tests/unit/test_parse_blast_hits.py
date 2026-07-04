"""test_parse_blast_hits.py

Unit tests for the BLAST top-hit execution layer.
"""

# Imports
from pathlib import Path
from types import SimpleNamespace

from mitopipeline.exec import parse_blast_hits


class DummyLogger:
    """Minimal logger for execution-layer unit tests."""

    def __init__(self) -> None:
        """Initialize captured logger messages."""
        self.info_messages = []
        self.warning_messages = []
        self.exception_messages = []

    def info(self, message: str) -> None:
        """Capture an informational message."""
        self.info_messages.append(message)

    def warning(self, message: str) -> None:
        """Capture a warning message."""
        self.warning_messages.append(message)

    def exception(self, message: str) -> None:
        """Capture an exception message."""
        self.exception_messages.append(message)


def make_args(tmp_path: Path) -> SimpleNamespace:
    """Create valid execution-layer arguments.

    Args:
        tmp_path (Path): Temporary pytest directory.

    Returns:
        SimpleNamespace: Parsed-argument substitute.
    """
    return SimpleNamespace(
        sample_id="sample_001",
        blast_results=str(tmp_path / "sample_001.blast.tsv"),
        output_file=str(tmp_path / "sample_001.top_hits.tsv"),
        maximum_matches=6,
        log_file=str(tmp_path / "sample_001.blast_hits.log"),
    )


def test_parse_args_reads_required_and_optional_arguments(
    tmp_path,
    monkeypatch,
):
    """Test parse_args reads execution-layer arguments."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "parse_blast_hits",
            "--sample-id",
            "sample_001",
            "--blast-results",
            str(tmp_path / "sample.blast.tsv"),
            "--output-file",
            str(tmp_path / "sample.top_hits.tsv"),
            "--maximum-matches",
            "8",
            "--log-file",
            str(tmp_path / "sample.log"),
        ],
    )

    args = parse_blast_hits.parse_args()

    assert args.sample_id == "sample_001"
    assert args.blast_results == str(tmp_path / "sample.blast.tsv")
    assert args.output_file == str(tmp_path / "sample.top_hits.tsv")
    assert args.maximum_matches == 8
    assert args.log_file == str(tmp_path / "sample.log")


def test_main_runs_complete_selection_workflow(
    tmp_path,
    monkeypatch,
):
    """Test main parses, selects, and writes BLAST matches."""
    args = make_args(tmp_path)
    logger = DummyLogger()

    parsed_matches = [
        {"sseqid": "NC_000001.1"},
        {"sseqid": "NC_000002.1"},
    ]
    selected_matches = [
        {"sseqid": "NC_000001.1", "rank": 1},
        {"sseqid": "NC_000002.1", "rank": 2},
    ]

    captured = {}

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "make_logger",
        lambda **kwargs: logger,
    )

    def fake_parse(blast_path, logger=None):
        captured["blast_path"] = blast_path
        captured["parse_logger"] = logger
        return parsed_matches

    def fake_select(matches, maximum_matches):
        captured["matches"] = matches
        captured["maximum_matches"] = maximum_matches
        return selected_matches

    def fake_write(
        matches,
        output_path,
        sample_id,
        logger=None,
    ):
        captured["selected_matches"] = matches
        captured["output_path"] = output_path
        captured["sample_id"] = sample_id
        captured["write_logger"] = logger

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_blast_tsv",
        fake_parse,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "select_top_blast_matches",
        fake_select,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "write_top_blast_matches",
        fake_write,
    )

    return_code = parse_blast_hits.main()

    assert return_code == 0

    assert captured["blast_path"] == Path(args.blast_results)
    assert captured["parse_logger"] is logger

    assert captured["matches"] == parsed_matches
    assert captured["maximum_matches"] == 6

    assert captured["selected_matches"] == selected_matches
    assert captured["output_path"] == Path(args.output_file)
    assert captured["sample_id"] == "sample_001"
    assert captured["write_logger"] is logger


def test_main_warns_when_fewer_matches_are_available(
    tmp_path,
    monkeypatch,
):
    """Test main warns when fewer than the requested hits are found."""
    args = make_args(tmp_path)
    logger = DummyLogger()

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "make_logger",
        lambda **kwargs: logger,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "parse_blast_tsv",
        lambda blast_path, logger=None: [],
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "select_top_blast_matches",
        lambda matches, maximum_matches: [
            {"sseqid": "NC_000001.1", "rank": 1},
            {"sseqid": "NC_000002.1", "rank": 2},
        ],
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "write_top_blast_matches",
        lambda **kwargs: None,
    )

    assert parse_blast_hits.main() == 0

    assert len(logger.warning_messages) == 1
    assert "Only 2" in logger.warning_messages[0]
    assert "6 were requested" in logger.warning_messages[0]


def test_main_does_not_warn_when_requested_matches_are_available(
    tmp_path,
    monkeypatch,
):
    """Test main does not warn when six matches are selected."""
    args = make_args(tmp_path)
    logger = DummyLogger()

    selected_matches = [
        {
            "sseqid": f"NC_{rank:06d}.1",
            "rank": rank,
        }
        for rank in range(1, 7)
    ]

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "make_logger",
        lambda **kwargs: logger,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "parse_blast_tsv",
        lambda blast_path, logger=None: selected_matches,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "select_top_blast_matches",
        lambda matches, maximum_matches: selected_matches,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "write_top_blast_matches",
        lambda **kwargs: None,
    )

    assert parse_blast_hits.main() == 0
    assert logger.warning_messages == []


def test_main_returns_one_when_parsing_fails(
    tmp_path,
    monkeypatch,
):
    """Test main returns one when BLAST parsing raises an exception."""
    args = make_args(tmp_path)
    logger = DummyLogger()

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "make_logger",
        lambda **kwargs: logger,
    )

    def raise_error(*args, **kwargs):
        raise ValueError("invalid BLAST output")

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_blast_tsv",
        raise_error,
    )

    assert parse_blast_hits.main() == 1
    assert len(logger.exception_messages) == 1
    assert "invalid BLAST output" in logger.exception_messages[0]


def test_main_returns_one_when_selection_fails(
    tmp_path,
    monkeypatch,
):
    """Test main returns one when ranking or selection fails."""
    args = make_args(tmp_path)
    logger = DummyLogger()

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "make_logger",
        lambda **kwargs: logger,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "parse_blast_tsv",
        lambda blast_path, logger=None: [],
    )

    def raise_error(*args, **kwargs):
        raise ValueError("invalid maximum matches")

    monkeypatch.setattr(
        parse_blast_hits,
        "select_top_blast_matches",
        raise_error,
    )

    assert parse_blast_hits.main() == 1
    assert len(logger.exception_messages) == 1
    assert "invalid maximum matches" in logger.exception_messages[0]


def test_main_returns_one_when_output_writing_fails(
    tmp_path,
    monkeypatch,
):
    """Test main returns one when output writing raises an exception."""
    args = make_args(tmp_path)
    logger = DummyLogger()

    monkeypatch.setattr(
        parse_blast_hits,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "make_logger",
        lambda **kwargs: logger,
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "parse_blast_tsv",
        lambda blast_path, logger=None: [],
    )
    monkeypatch.setattr(
        parse_blast_hits,
        "select_top_blast_matches",
        lambda matches, maximum_matches: [],
    )

    def raise_error(*args, **kwargs):
        raise OSError("unable to write output")

    monkeypatch.setattr(
        parse_blast_hits,
        "write_top_blast_matches",
        raise_error,
    )

    assert parse_blast_hits.main() == 1
    assert len(logger.exception_messages) == 1
    assert "unable to write output" in logger.exception_messages[0]