from database.library import Library

class MatchesRepository:
    def __init__(self, library: Library):
        self.library = library

    def insertMatches(self, matches):
        self.library.executemany("""
        INSERT INTO matches (user_id, work_id, match_score)
        VALUES (%s, %s, %s);
        """,(matches,))

    def getMatches(self, user_id):
        result = self.library.fetchall("""
        SELECT work_id, match_score
        FROM matches
        WHERE user_id = %s;
        """,(user_id,))
        return result