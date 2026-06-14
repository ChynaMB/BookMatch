from database.library import Library

class UsersRepository:
    def __init__(self, library: Library):
        self.library = library

    def createUser(self):
        result = self.library.fetchone("INSERT INTO users DEFAULT VALUES RETURNING user_id;")
        return result[0] if result else None

    def getUserID(self, user_id):
        result = self.library.fetchone("SELECT * FROM users WHERE user_id = %s;", (user_id,))
        return result if result else None
    