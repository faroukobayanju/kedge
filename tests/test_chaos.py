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
