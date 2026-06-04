"""test_imports.py

Unit tests for package imports within the project.

"""

def test_package_imports():
    """Unit test verifies that repo is set up correctly and that imports work as expected."""
    # Importing all associated packages into python.
    import mitopipeline
    import mitopipeline.api as api
    import mitopipeline.exec as exec
    import mitopipeline.logging as logging
    import mitopipeline.reporting as reporting
    import mitopipeline.stats as stats
    import mitopipeline.utils as utils

    # Running assert statements.
    assert mitopipeline is not None
    assert api is not None
    assert exec is not None
    assert logging is not None
    assert reporting is not None
    assert stats is not None
    assert utils is not None