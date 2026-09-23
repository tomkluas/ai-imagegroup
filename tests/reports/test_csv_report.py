from image_group.reports.csv_report import CsvReport


def test_csv_has_bom_and_escapes_formula_cells(tmp_path):
    rows=[{"source":"=危险.jpg","sha256":"abc","person":"张小明","decision":"自动","status":"完成","error":"","completed_at":"2026"}]
    path=CsvReport().write_rows(rows,tmp_path/"报告.csv");raw=path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") and "'=危险.jpg" in raw.decode("utf-8-sig")

