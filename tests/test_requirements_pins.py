"""Dependency pinning policy tests."""


def test_requirements_files_use_exact_pins():
    """Direct dependencies should be exact pins for reproducible installs."""

    def assert_exact_pins(path: str) -> None:
        with open(path) as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or line.startswith("-r "):
                    continue
                assert "==" in line, f"{path}: dependency must be pinned with == ({line})"

    assert_exact_pins("requirements.txt")
    assert_exact_pins("requirements-dev.txt")
