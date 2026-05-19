import psycopg2

class Library:
    def __init__(self):
        self.conn = self.connectToLibrary()

    def connectToLibrary(self):
        try:
            conn = psycopg2.connect(
                
            )
            print("Connected to PostgreSQL database")
            return conn
        except Exception as e:
            raise RuntimeError(f"Failed to connect to database: {e}")

    def execute(self, query, params=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Database error: {e}") from e

    def fetchone(self, query, params=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchone()

        except Exception as e:
            raise RuntimeError(f"Database error: {e}") from e

    def fetchall(self, query, params=None) -> list:
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()

        except Exception as e:
            raise RuntimeError(f"Database error: {e}") from e

    def close(self):
        self.conn.close()