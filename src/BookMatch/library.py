import sqlite3

class Library:
    def __init__(self):
        self.conn = sqlite3.connect('library.db')
        self.cursor = self.conn.cursor()
        self.createUserTable()
        self.createCSVdataTable()
        self.createUserProfileTable()
        self.createBookDataTable()

    #methods to update data entries in database
    def updateUserProfileMatches(self, userProfileID, matches):
        self.cursor.execute("""
        UPDATE userProfiles
        SET matches = ?
        WHERE profile_id = ?
        """, (matches, userProfileID))
        self.conn.commit()

    #methods to add to database
    def addUser(self) -> int:
        self.cursor.execute("INSERT INTO users DEFAULT VALUES")
        self.conn.commit()

        if self.cursor.lastrowid is None:
            raise Exception("Failed to add user to database")
        return self.cursor.lastrowid  #return the generated user_id

    #TODO: rewrite function to be more efficient
    def addBookData(self, workID, title, author, subjects, average_rating, embedding) -> int:
        """Add book data to the database based on the workID. If the workID already exists, change nothing. 
        If the workID does not exist, add a new entry with the provided data."""
        #check if book data already exists for the workID
        self.cursor.execute("SELECT 1 FROM bookData WHERE work = ?", (workID,))
        if self.cursor.fetchone() is not None:
            #book data already exists, do nothing
            if self.cursor.lastrowid is None:
                raise Exception("Failed to fetch existing book data from database")
            return self.cursor.lastrowid  #return the existing bookData_id
        
        #book data does not exist, insert a new entry
        self.cursor.execute("""
        INSERT INTO bookData (work, title, author, subjects, average_rating, embedding)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (workID, title, author, subjects, average_rating, embedding))

        if self.cursor.lastrowid is None:
            raise Exception("Failed to add book data to database")
        return self.cursor.lastrowid  #return the generated bookData_id

    def addUserProfile(self, user_id, five_star_works, four_star_works, liked_authors, vector_embedding, matches) -> int:
        self.cursor.execute("""
        INSERT OR REPLACE INTO userProfiles (user_id, five_star_works, four_star_works, liked_authors, vector_embedding, matches)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, five_star_works, four_star_works, liked_authors, vector_embedding, matches))
        self.conn.commit()

        if self.cursor.lastrowid is None:
            raise Exception("Failed to add user profile to database")
        return self.cursor.lastrowid  #return the generated profile_id

    #methods to get data from database

    def getTitlesFromBookData(self, workIDS: list) -> list:
        self.cursor.execute("""
        SELECT title 
        FROM bookData 
        WHERE workID IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []

    def getAuthorsFromBookData(self, workIDS: list) -> list:
        self.cursor.execute("""
        SELECT author 
        FROM bookData 
        WHERE workID IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []

    def getSubjectsFromBookData(self, workIDS: list) -> list:
        self.cursor.execute("""
        SELECT subjects 
        FROM bookData 
        WHERE workID IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []
    
    def getDescriptionsFromBookData(self, workIDS: list) -> list:
        self.cursor.execute("""
        SELECT description 
        FROM bookData 
        WHERE workID IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []

    def getAverageRatingsFromBookData(self, workIDS: list) -> list:
        self.cursor.execute("""
        SELECT average_rating 
        FROM bookData 
        WHERE workID IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []
    
    def getRatingCountsFromBookData(self, workIDS: list) -> list:
        self.cursor.execute("""
        SELECT rating_count 
        FROM bookData 
        WHERE workID IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []
    
    
    #methods to search database
    def isBookInLibrary(self, workID):
        self.cursor.execute("SELECT 1 FROM bookData WHERE work = ?", (workID,))
        return self.cursor.fetchone() is not None

    def areBooksInLibrary(self, workIDS: list) -> list:
        """Given a list of workIDs, return a list of workIDs that are NOT in the library database"""
        self.cursor.execute("""
        SELECT workID 
        FROM bookData 
        WHERE workID NOT IN (?)
        """, (workIDS,))
        results = self.cursor.fetchall()
        return [result[0] for result in results] if results else []

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

    #TODO: change data types to match data being stored once finalised
    def createUserProfileTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS userProfiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            five_star_books_workIDs TEXT,
            four_star_books_workIDs TEXT,
            subjectGraph TEXT,
            liked_authors TEXT,
            vector BLOB,
            matches TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """)
        self.conn.commit()
        return self.cursor.lastrowid  #return the generated profile_id

    def createBookDataTable(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookData (
            workID TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            subjects TEXT,  
            average_rating REAL,   
            rating_count INTEGER,           
            embedding BLOB
            bookData_id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """)
        self.conn.commit()