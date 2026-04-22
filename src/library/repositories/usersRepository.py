class UsersRepository:
    def __init__(self, conn):
        self.conn = conn

    def createUser(self):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO users DEFAULT VALUES RETURNING user_id;")
        user_id = cur.fetchone()[0]
        self.conn.commit()
        cur.close()
        return user_id

    def getUser(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
        result = cur.fetchone()
        cur.close()
        return result