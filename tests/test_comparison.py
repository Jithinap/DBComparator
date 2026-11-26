from dbcomparator.comparison import row_diff, rows_to_json, write_json, read_json


def test_rows_to_json():
    rows = [("users", "public")]
    description = [("table_name",), ("table_schema",)]
    assert rows_to_json(rows, description) == [{"table_name": "users", "table_schema": "public"}]


def test_row_diff_is_deterministic():
    source = [{"table_name": "alpha"}, {"table_name": "beta"}]
    destination = [{"table_name": "beta"}, {"table_name": "gamma"}]
    source_only, destination_only = row_diff(source, destination)
    assert source_only == [{"table_name": "alpha"}]
    assert destination_only == [{"table_name": "gamma"}]


def test_write_and_read_json(tmp_path):
    path = tmp_path / "rows.json"
    write_json(path, [{"name": "test"}])
    assert read_json(path) == [{"name": "test"}]
