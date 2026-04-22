#TODO: fix this code and then integrate into reposotitories - can i use psycopg2 instead of psycopg
import psycopg2
from library.libraryConnection import connectToLibrary

class Library:
    def __init__(self, dsn):
        self.conn = psycopg2.connect(dsn)

    def execute(self, query, params=None, fetchone=False, fetchall=False):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())

                if fetchone:
                    result = cur.fetchone()
                elif fetchall:
                    result = cur.fetchall()
                else:
                    result = None

            self.conn.commit()
            return result

        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Database error: {e}")