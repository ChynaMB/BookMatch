import networkx as nx
from database.library import Library

class GraphRepository:
    def __init__(self, library: Library):
        self.library = library
        
    # book similarity graph
    def upsertBookSimilarity(self, w1, w2, score):
        """insert the similarity score between two book embeddings,
        if a similarity score already exists then update it"""
        self.library.execute("""
            INSERT INTO book_similarity (work_id_1, work_id_2, similarity_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (work_id_1, work_id_2)
            DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
        """, (w1, w2, score))

    def getSimilarBooks(self, work_id) -> list[tuple[str, float]]: 
        """Return similar books as (other_work_id, similarity_score), highest similarity first."""
        result = self.library.fetchall("""
            SELECT work_id_1, work_id_2, similarity_score
            FROM book_similarity
            WHERE work_id_1 = %s OR work_id_2 = %s
            ORDER BY similarity_score DESC;
        """, (work_id, work_id))
        return [
            (work_id_2 if work_id_1 == work_id else work_id_1, similarity_score)
            for work_id_1, work_id_2, similarity_score in result
        ]

    #user similarity graph
    def upsertUserSimilarity(self, user1, user2, score):
        """insert the similarity score between two user profile embeddings,
        if a similarity score already exists then update it """
        self.library.execute("""
            INSERT INTO user_similarity (user_id_1, user_id_2, similarity_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id_1, user_id_2)
            DO UPDATE SET similarity_score = EXCLUDED.similarity_score;
        """, (user1, user2, score))

    def getSimilarUsers(self, user_id) -> list[tuple[int, float]]:
        """Return similar users as (other_user_id, similarity_score), highest similarity first."""
        result = self.library.fetchall("""
            SELECT user_id_1, user_id_2, similarity_score
            FROM user_similarity
            WHERE user_id_1 = %s OR user_id_2 = %s
            ORDER BY similarity_score DESC;
        """, (user_id, user_id))
        return [
            (user_id_2 if user_id_1 == user_id else user_id_1, similarity_score)
            for user_id_1, user_id_2, similarity_score in result
        ]
    
    #TODO: Optimise and simplify this method
    #subject graph
    def addSubjectGraph(self, userID, graph: nx.Graph):
        """add a subject graph to the database, replacing any existing graph"""
        cur = self.conn.cursor()

        # Clear old graph
        self.library.execute("""
            DELETE FROM user_subject_graph
            WHERE user_id = %s
        """, (userID,))

        self.library.execute("""
            DELETE FROM user_subject_nodes
            WHERE user_id = %s
        """, (userID,))

        # Insert nodes
        for subjectID, data in graph.nodes(data=True):
            magnitude = data.get("magnitude", 0)

            self.library.execute("""
                INSERT INTO user_subject_nodes (user_id, subject_id, magnitude)
                VALUES (%s, %s, %s)
            """, (userID, subjectID, magnitude))

        # Insert edges
        for subjectID1, subjectID2, data in graph.edges(data=True):
            weight = data.get("weight", 0)

            lowID = min(subjectID1, subjectID2)
            highID = max(subjectID1, subjectID2)

            self.library.execute("""
                INSERT INTO user_subject_graph 
                    (user_id, subject_id_1, subject_id_2, weight)
                VALUES (%s, %s, %s, %s)
            """, (userID, lowID, highID, weight))

        self.conn.commit()
        cur.close()