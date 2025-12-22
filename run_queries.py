import duckdb
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
con = duckdb.connect(database=':memory:')

# Register CSVs as tables
csvs = {
    'customers': BASE / 'data' / 'customers.csv',
    'orders': BASE / 'data' / 'orders.csv',
    'payments': BASE / 'data' / 'payments.csv',
    'order_items': BASE / 'data' / 'order_items.csv'
}

for name, path in csvs.items():
    if not path.exists():
        print(f"Missing CSV for {name}: {path}")
        sys.exit(1)
    print(f"Loading {name} from {path}")
    path_str = str(path).replace('\\', '/')
    con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{path_str}', HEADER=True)")

sql_files = [
    BASE / 'sql' / '01_funnel.sql',
    BASE / 'sql' / '02_retention.sql',
    BASE / 'sql' / '03_revenue.sql',
    BASE / 'sql' / '04_segments.sql'
]

for sql_file in sql_files:
    print('\n' + '='*40)
    print(f"Running {sql_file.name}")
    sql = sql_file.read_text()
    try:
        # Execute and fetch up to 10 rows
        res = con.execute(sql).fetchdf()
        print(f"Rows returned: {len(res)}")
        print(res.head(10).to_string(index=False))
    except Exception as e:
        print(f"Error running {sql_file.name}: {e}")

print('\nDone')
