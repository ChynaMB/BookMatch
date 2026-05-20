from database.repositories.embeddingRepository import EmbeddingRepository
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Embedder:
    def __init__(self, conn):
        self.embeddingRepo = EmbeddingRepository(conn)
        
    def embedder(self, text):
        """takes in a string of text and returns a vector embedding using the sentence transformer model"""
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2")
            return model.encode(text)
        except Exception as e:
            print(f"Error occurred while embedding text: {e}")
            return None

    def createBookEmbedding(self, workID, title, subtitle, description, subjects):
        """create a vector embedding for a single book and store it in the database"""
        embeddingText = title + " " + subtitle + " " + description + " " + " ".join(subjects)
        embedding = self.embedder(embeddingText)
        self.embeddingRepo.addBookEmbedding(workID, embedding)

    def calculateCosineSimilarity(self, embedding1, embedding2):
        """calculate cosine similarity scores between two vector embeddings"""
        if embedding1 is not None and embedding2 is not None:
            try:
                similarityScore = cosine_similarity([embedding1], [embedding2])[0][0]
                return similarityScore
            except Exception as e:
                print(f"Error occurred while calculating cosine similarity: {e}")
                return None
        else:
            print("One or both embeddings are None, cannot calculate cosine similarity.")
            return None

    #TODO: improve this method to handle cases where the embedding does not exist for one or both of the books/users 
    # and create the embedding if it does not exist before trying to add the similarity score again
    def addSimilarityScore(self, type, id1, id2, similarityScore):
        """add a similarity score between two books or two user profiles to the database"""
        result = None
        while result is None:
            result = self.embeddingRepo.upsertSimilarityScore(type, id1, id2, similarityScore)
            if result is not None:
                break
            else:
                #create the embedding for the book/user if it does not exist and try again
                if type == 'book':
                    #fetch the book details from the database and create the embedding
                    pass
                elif type == 'user':
                    #fetch the user profile details from the database and create the embedding
                    pass
                else:
                    print("Invalid type for similarity score, must be 'book' or 'user'.")
                    return
                
    def bookEmbedder(self, id, title, subtitle, description, subjects):
        """main method to create a vector embedding for a single book or user and store it in the database
        then calculate cosine similarity scores between the new embedding and all existing book/user embeddings in the database and store those similarity scores in the database as well"""

        self.createBookEmbedding(id, title, subtitle, description, subjects)
       
        newEmbedding = self.embeddingRepo.getEmbedding('book', id)
        if newEmbedding is not None:
            allEmbeddings = self.embeddingRepo.getAllEmbeddings('book')
            for otherID, otherEmbedding in allEmbeddings:
                if otherID != id:
                    similarityScore = self.calculateCosineSimilarity(newEmbedding, otherEmbedding)
                    self.addSimilarityScore('book', id, otherID, similarityScore)    
