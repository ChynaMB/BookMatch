import sqlite3

class Library:
    def __init__(self):
        self.conn = sqlite3.connect('library.db')
        self.cursor = self.conn.cursor()
        self.createUserTable()
        self.createCSVdataTable()
        self.createuserProfileTable()
        self.createBookDataTable()

    #methods to add to database
    def addUser(self):
        self.cursor.execute("INSERT INTO users DEFAULT VALUES")
        self.conn.commit()
        return self.cursor.lastrowid  #return the generated user_id

    def addBookData(self, workID, title, average_rating, subjects, embedding):
        self.cursor.execute("""
        INSERT OR REPLACE INTO bookData (workID, title, average_rating, subjects, embedding)
        VALUES (?, ?, ?, ?, ?)
        """, (workID, title, average_rating, subjects, embedding))
        self.conn.commit()


    #methods to get data from database
    def getSubjectsFromBookData(self, work):
        self.cursor.execute("SELECT subjects FROM bookData WHERE work = ?", (work,))
        result = self.cursor.fetchone()
        return result[0] if result else None


    #methods to search database
    def isBookInLibrary(self, work):
        self.cursor.execute("SELECT 1 FROM bookData WHERE work = ?", (work,))
        return self.cursor.fetchone() is not None


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
            work TEXT PRIMARY KEY,
            title TEXT,
            subjects TEXT,  
            average_rating REAL,   
            rating_count INTEGER,           
            embedding BLOB
            bookData_id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """)
        self.conn.commit()