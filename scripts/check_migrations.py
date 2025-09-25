import sqlite3
from pathlib import Path
root = Path(__file__).resolve().parents[1]
print('project root:', root)
db = root / 'db.sqlite3'
print('db exists:', db.exists())
print('\nMigration files:')
for p in sorted(root.glob('**/migrations/000*_*.py')):
    print('-', p.relative_to(root))

if db.exists():
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    try:
        cur.execute('SELECT app, name FROM django_migrations ORDER BY app, name')
        rows = cur.fetchall()
        print('\nApplied migrations in db:')
        for r in rows:
            print('-', r[0], r[1])
    except sqlite3.OperationalError as e:
        print('\nError querying django_migrations:', e)
    finally:
        conn.close()
else:
    print('\nNo database file found')
