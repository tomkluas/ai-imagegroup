import csv
from pathlib import Path
FIELDS=("source","sha256","person","decision","status","error","completed_at")
def safe_cell(value):
    text="" if value is None else str(value)
    return "'"+text if text.startswith(("=","+","-","@")) else text
class CsvReport:
    def write_rows(self,rows,path:Path)->Path:
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("w",encoding="utf-8-sig",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=FIELDS);writer.writeheader()
            for row in rows:writer.writerow({field:safe_cell(row.get(field,"")) for field in FIELDS})
        return path

