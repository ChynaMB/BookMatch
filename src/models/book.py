from sentence_transformers import SentenceTransformer

class Book:
    def __init__(self, workID, title, subtitle, description, isbn10, isbn13, averageRating, ratingUpdateDate, ratingCount):
        self.workID = workID
        self.title = title
        self.subtitle = subtitle
        self.description = description
        self.isbn = isbn10
        self.isbn13 = isbn13
        self.averageRating = averageRating
        self.ratingUpdateDate = ratingUpdateDate
        self.ratingCount = ratingCount

        # self.bookVectorEmbedding = self.createBookVectorEmbedding()
        # #self.bookStringEmbedding = json.dumps(self.bookVectorEmbedding.tolist()) #convert numpy array to list, then to string for database storage
        
        # self.library = library
        # #add book data to database and get the bookData_id for this book
        # self.bookDataID = self.library.addBookData(self.workID, self.title, self.isbn, self.isbn13, self.author, 
        #                                            self.subjects, self.description, self.averageRating, self.ratingCount, 
        #                                            self.bookVectorEmbedding)

        # self.model = SentenceTransformer("all-MiniLM-L6-v2")

    # def createBookVectorEmbedding(self):
    #     """using the three open source APIs, fetch data on the book and create a vector embedding"""
    #     textForEmbedding = f"""
    #     Title: {self.title}
    #     Author: {self.author}
    #     Subjects: {', '.join(self.subjects)}
    #     Description: {self.description}
    #     """
    #     return self.model.encode(textForEmbedding)

    #getter methods
    def getWorkID(self):
        return self.workID
    def getTitle(self):
        return self.title
    def getSubtitle(self):
        return self.subtitle
    def getDescription(self):
        return self.description         
    def getISBN10(self):
        return self.isbn
    def getISBN13(self):
        return self.isbn13      
    def getAverageRating(self):
        return self.averageRating
    def getRatingUpdateDate(self):
        return self.ratingUpdateDate
    def getRatingCount(self):
        return self.ratingCount 
    