from dbcomparator.mysql_check import load_test_data


def test_load_test_data_accepts_list(tmp_path):
    path = tmp_path / "tables.json"
    path.write_text('[{"tablename": ["users"]}]', encoding="utf-8")
    assert load_test_data(path) == [{"tablename": ["users"]}]
