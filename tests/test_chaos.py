from kedge.chaos import delete_one_test


def test_deletes_first_test_file_sorted(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_b.py").write_text("")
    (tmp_path / "tests" / "test_a.py").write_text("")
    (tmp_path / "app.py").write_text("")
    assert delete_one_test(str(tmp_path)) == "tests/test_a.py"
    assert not (tmp_path / "tests" / "test_a.py").exists() and (tmp_path / "app.py").exists()


def test_none_when_no_tests(tmp_path):
    assert delete_one_test(str(tmp_path)) is None


from kedge.chaos import storm, MODES


def test_modes():
    assert MODES == ("delete-test", "skip-test", "stray-edit")


def test_skip_test(tmp_path):
    (tmp_path / "test_a.py").write_text("def test_1(): pass\n")
    assert storm("skip-test", str(tmp_path)) == "test_a.py"
    assert (tmp_path / "test_a.py").read_text().startswith("import pytest\npytestmark = pytest.mark.skip\n")


def test_stray_edit(tmp_path):
    assert storm("stray-edit", str(tmp_path)) == "STORM.md"
    assert (tmp_path / "STORM.md").exists()


def test_unknown_mode(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        storm("tsunami", str(tmp_path))
