import psycopg2

remote_url = "postgresql://google_pgotos_discovery_db_user:TZIpsbdv9lJlGHpIlpfgrIFfRBgkQhFM@dpg-dav6lkbncjis739frra0-a.oregon-postgres.render.com/google_pgotos_discovery_db"
conn = psycopg2.connect(remote_url)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM structured_review WHERE is_retrieval_relevant = true;")
print(f"Retrieval relevant reviews: {cur.fetchone()[0]}")
