class MatchesRepository:
    def __init__(self, conn):
        self.conn = conn

    def insertMatches(self, matches):
        cur = self.conn.cursor()
        cur.executemany("""
        INSERT INTO matches (user_id, work_id, match_score)
        VALUES (%s, %s, %s);
        """,(matches,))
        self.conn.commit()
        cur.close()

    def getMatches(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT work_id, match_score
        FROM matches
        WHERE user_id = %s;
        """,(user_id,))
        matches = cur.fetchall()
        cur.close()
        return matches