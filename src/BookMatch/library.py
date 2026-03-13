import sqlite3

class Library:
    def __init__(self):
        self.conn = sqlite3.connect('library.db')
        self.cursor = self.conn.cursor()
        self.createUserTable()
        self.createCSVdataTable()
        self.createuserProfileTable()
        self.createBookDataTable()

    #Add a new user to the users table and return the generated user_id
    def add_user(self):
        self.cursor.execute("INSERT INTO users DEFAULT VALUES")
        self.conn.commit()
        return self.cursor.lastrowid  #return the generated user_id

    #Table creation methods
    def createUserTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def createCSVdataTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS csvData (
            CSVdata_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bookID TEXT,
            Title TEXT,
            Author TEXT,
            AuthorLF TEXT,
            AdditionalAuthors TEXT,
            ISBN TEXT,
            ISBN13 TEXT,
            MyRating INTEGER,
            AverageRating REAL,
            NumOfPages INTEGER,
            Bookshelves TEXT,
            ExclusiveShelf TEXT,
            MyReview TEXT,
            ReadCount INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        self.conn.commit()

    def createuserProfileTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS userProfiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            vector BLOB,
            matches TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        self.conn.commit()

    def createBookDataTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookData (
            bookID TEXT PRIMARY KEY,
            Title TEXT,
            Author TEXT,
            AuthorLF TEXT,
            AdditionalAuthors TEXT,
            ISBN TEXT,
            ISBN13 TEXT,
            AverageRating REAL,
            NumOfPages INTEGER
        )
        """)
        self.conn.commit()