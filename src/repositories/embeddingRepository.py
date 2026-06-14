from database.library import Library

class EmbeddingRepository:
    def __init__(self, library: Library):
        self.library = library

    def addBookEmbedding(self, work_id, embedding):
        """add a book embedding to the database only if an embedding for the book does not already exist"""
        if embedding is not None:
            self.library.execute("""
                INSERT INTO book_embeddings (work_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (work_id)
                DO NOTHING;
            """, (work_id, embedding))

    def addUserEmbedding(self, user_id, embedding):
        """add a user embedding to the database only if an embedding for the user does not already exist"""
        if embedding is not None:
            self.library.execute("""
                INSERT INTO user_embeddings (user_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO NOTHING;
            """, (user_id, embedding))
           

    def upsertSimilarityScore(self, type,id1, id2, similarityScore):
        """upsert a similarity score between two books or two user profiles in the database"""
        if type == 'book':
            self.library.execute("""
                INSERT INTO book_similarity (work_id_1, work_id_2, similarity_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (work_id_1, work_id_2)
                DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
            """, (id1, id2, similarityScore))
        elif type == 'user':
            self.library.execute("""
                INSERT INTO user_similarity (user_id_1, user_id_2, similarity_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id_1, user_id_2)
                DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
            """, (id1, id2, similarityScore))

    def getEmbedding(self, type, id):
        """get a book or user embedding from the database"""
        if type == 'book':
            result = self.library.fetchone("""
                SELECT embedding FROM book_embeddings
                WHERE work_id = %s;
            """, (id,))
        elif type == 'user':
            result = self.library.fetchone("""
                SELECT embedding FROM user_embeddings
                WHERE user_id = %s;
            """, (id,))
        return result[0] if result else None

    def getAllEmbeddings(self, type) -> dict:
        """get all book or all user embeddings from the database
        returns a dictionary of id: embedding pairs"""
        if type == 'book':
            result = self.library.fetchall("""
                SELECT work_id, embedding FROM book_embeddings;
            """)
        elif type == 'user':
            result = self.library.fetchall("""
                SELECT user_id, embedding FROM user_embeddings;
            """)
        return {result[0]: result[1] for result in result} if result else {}

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