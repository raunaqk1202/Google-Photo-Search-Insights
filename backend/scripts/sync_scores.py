import psycopg2
from psycopg2.extras import execute_batch

def sync_scores():
    print("Connecting to local database...")
    local_conn = psycopg2.connect("postgresql://discovery:discovery_secret@localhost:5432/discovery_engine")
    local_cur = local_conn.cursor()

    print("Connecting to production database...")
    remote_url = "postgresql://google_pgotos_discovery_db_user:TZIpsbdv9lJlGHpIlpfgrIFfRBgkQhFM@dpg-dav6lkbncjis739frra0-a.oregon-postgres.render.com/google_pgotos_discovery_db"
    remote_conn = psycopg2.connect(remote_url)
    remote_cur = remote_conn.cursor()

    print("Fetching reach scores from local database...")
    local_cur.execute("SELECT id, reach_score FROM structured_review WHERE reach_score IS NOT NULL")
    scores = local_cur.fetchall()

    print(f"Found {len(scores)} reach scores locally. Pushing to production...")
    
    update_sql = "UPDATE structured_review SET reach_score = %s WHERE id = %s"
    params = [(score, row_id) for row_id, score in scores]

    execute_batch(remote_cur, update_sql, params)
    remote_conn.commit()

    print(f"✅ Successfully updated {len(scores)} reach scores in the production database!")
    
    local_conn.close()
    remote_conn.close()

if __name__ == "__main__":
    sync_scores()
