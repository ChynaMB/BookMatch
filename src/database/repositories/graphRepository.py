class GraphRepository:
    def __init__(self, conn):
        self.conn = conn


    # book similarity
    def upsertBookSimilarity(self, w1, w2, score):
        """insert the similarity score between two book embeddings,
        if a similarity score already exists then update it"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO book_similarity (work_id_1, work_id_2, similarity_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id_1, work_id_2)
            DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
        """, (w1, w2, score))
        self.conn.commit()
        cur.close()

    def getSimilarBooks(self, work_id) -> list[(tuple)]: 
        """Go through all the similarity scores connected to a book using their work id
        return all the rows in descending order (highest similiarity is first"""
        
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

   
    #user similarity
    def upsertUserSimilarity(self, user1, user2, score):
        """insert the similarity score between two user profile embeddings,
        if a similarity score already exists then update it """
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO user_similarity (user_id_1, user_id_2, similarity_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id_1, user_id_2)
            DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
        """, (user1, user2, score))
        self.conn.commit()
        cur.close()

    def getSimilarUsers(self, user_id) -> list[(tuple)]:
        """Go through all the similarity scores connected to a user using
        return all the rows in descending order (highest similiarity is first"""
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