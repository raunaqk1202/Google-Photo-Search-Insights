import psycopg2

remote_url = "postgresql://google_pgotos_discovery_db_user:TZIpsbdv9lJlGHpIlpfgrIFfRBgkQhFM@dpg-dav6lkbncjis739frra0-a.oregon-postgres.render.com/google_pgotos_discovery_db"
conn = psycopg2.connect(remote_url)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM raw_review;")
print(f"Raw reviews: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM structured_review;")
print(f"Structured reviews: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM failure_mode;")
print(f"Failure modes: {cur.fetchone()[0]}")
