class GraphRepository:
    def __init__(self, conn):
        self.conn = conn

    # -------------------------
    # BOOK SIMILARITY
    # -------------------------
    def upsert_book_similarity(self, w1, w2, score):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO book_similarity (work_id_1, work_id_2, similarity_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id_1, work_id_2)
            DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
        """, (w1, w2, score))
        self.conn.commit()
        cur.close()

    def get_similar_books(self, work_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT *
            FROM book_similarity
            WHERE work_id_1 = %s OR work_id_2 = %s
            ORDER BY similarity_score DESC;
        """, (work_id, work_id))
        result = cur.fetchall()
        cur.close()
        return result

    # -------------------------
    # USER SIMILARITY
    # -------------------------
    def upsert_user_similarity(self, u1, u2, score):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO user_similarity (user_id_1, user_id_2, similarity_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id_1, user_id_2)
            DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
        """, (u1, u2, score))
        self.conn.commit()
        cur.close()

    def get_similar_users(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT *
            FROM user_similarity
            WHERE user_id_1 = %s OR user_id_2 = %s
            ORDER BY similarity_score DESC;
        """, (user_id, user_id))
        result = cur.fetchall()
        cur.close()
        return result