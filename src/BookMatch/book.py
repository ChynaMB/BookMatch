from sentence_transformers import SentenceTransformer

#hashed out all hardcover API code for now since - seems a little unreliable and requires an API key. 
#Can add back in later if we want to use it as a source for ratings and embeddings.
class Book:
    def __init__(self, work, ISBN, title, author, subjects, description, averageRating, ratingCount, library):
        self.work = work
        self.ISBN = ISBN
        self.title = title
        self.author = author
        self.subjects = subjects
        self.description = description
        self.averageRating = averageRating
        self.ratingCount = ratingCount
        self.bookVectorEmbedding = self.createBookVectorEmbedding()
        #self.bookStringEmbedding = json.dumps(self.bookVectorEmbedding.tolist()) #convert numpy array to list, then to string for database storage
        
        self.library = library
        #add book data to database and get the bookData_id for this book
        self.bookData_id = self.library.addBookData(self.work, self.title, self.author, self.averageRating, self.subjects, self.bookVectorEmbedding)

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def createBookVectorEmbedding(self):
        """using the three open source APIs, fetch data on the book and create a vector embedding"""
        textForEmbedding = f"""
        Title: {self.title}
        Author: {self.author}
        Subjects: {', '.join(self.subjects)}
        Description: {self.description}
        """
        return self.model.encode(textForEmbedding)

    #getter methods
    def getTitle(self):
        return self.title

    def getAuthor(self):
        return self.author

    def getSubjects(self):
        return self.subjects

    def getDescription(self):
        return self.description

    def getAverageRating(self):
        return self.averageRating

    def getRatingCount(self):
        return self.ratingCount
    
    def getBookVectorEmbedding(self):
        return self.bookVectorEmbedding

    