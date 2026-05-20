from sentence_transformers import SentenceTransformer

class EmbeddingRepository:
    def __init__(self, conn):
        self.conn = conn

    def addBookEmbedding(self, work_id, embedding):
        """add a book embedding to the database only if an embedding for the book does not already exist"""
        if embedding is not None:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO book_embeddings (work_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (work_id)
                DO NOTHING;
            """, (work_id, embedding))
            self.conn.commit()
            cur.close()

    def addUserEmbedding(self, user_id, embedding):
        """add a user embedding to the database only if an embedding for the user does not already exist"""
        if embedding is not None:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO user_embeddings (user_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO NOTHING;
            """, (user_id, embedding))
            self.conn.commit()
            cur.close()

    def upsertSimilarityScore(self, type,id1, id2, similarityScore):
        """upsert a similarity score between two books or two user profiles in the database"""
        cur = self.conn.cursor()
        if type == 'book':
            cur.execute("""
                INSERT INTO book_similarity (work_id_1, work_id_2, similarity_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (work_id_1, work_id_2)
                DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
            """, (id1, id2, similarityScore))
        elif type == 'user':
            cur.execute("""
                INSERT INTO user_similarity (user_id_1, user_id_2, similarity_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id_1, user_id_2)
                DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
            """, (id1, id2, similarityScore))
        self.conn.commit()
        cur.close()

#when updating an embedding, we want to update the created_at timestamp 
#we also have to update the similarity scores in the graph repository because they will be based on the old embedding, 
#but we can do that in the graph repository by fetching all the books/users 
#connected to the book/user with the updated embedding and recalculating the similarity scores for those connections

    # def updateBookEmbedding(self, work_id, embedding):
    #     """update a book embedding in the database"""
    #     if embedding is not None:
    #         cur = self.conn.cursor()
    #         cur.execute("""
    #             UPDATE book_embeddings
    #             SET embedding = %s, created_at = CURRENT_TIMESTAMP
    #             WHERE work_id = %s;
    #         """, (embedding, work_id))
    #         self.conn.commit()
    #         cur.close()

    # def updateUserEmbedding(self, user_id, embedding):
    #     """update a user embedding in the database"""
    #     if embedding is not None:
    #         cur = self.conn.cursor()
    #         cur.execute("""
    #             UPDATE user_embeddings
    #             SET embedding = %s, created_at = CURRENT_TIMESTAMP
    #             WHERE user_id = %s;
    #         """, (embedding, user_id))
    #         self.conn.commit()
    #         cur.close()