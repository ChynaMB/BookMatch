import requests
import json
from sentence_transformers import SentenceTransformer

#hashed out all hardcover API code for now since - seems a little unreliable and requires an API key. 
#Can add back in later if we want to use it as a source for ratings and embeddings.
class Book:
    def __init__(self, work, ISBN, title, author, subjects, library):
        self.work = work
        self.ISBN = ISBN
        self.title = title
        self.author = author
        self.subjects = subjects
        self.library = library
        self.description = self.getDescription()
        self.averageRating = self.updateRating()[0]
        self.ratingCount = self.updateRating()[1]
        self.bookVectorEmbedding = self.createBookVectorEmbedding()
        #self.bookStringEmbedding = json.dumps(self.bookVectorEmbedding.tolist()) #convert numpy array to list, then to string for database storage
        
        self.bookData_id = self.library.addBookData(self.work, self.title, self.author, self.averageRating, self.subjects, self.bookVectorEmbedding)

        self.openLibraryURL = "https://openlibrary.org"
        self.googleBooksURL = "https://www.googleapis.com/books/v1/volumes"
        self.hardcoverURL = "https://api.hardcover.io/v1/books"

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def updateRating(self) -> tuple:
        """using ISBN, fetch average rating and rating count from open library API, google books API, 
        and hardcover API. Use the average of the ratings from the three sources as the final 
        rating for the book. If a source does not have a rating for the book, ignore that 
        source in the average calculation."""
        ratings = []
        # Open Library API
        url = f"{self.openLibraryURL}{self.work}.json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "average_rating" in data and "ratings_count" in data:
                ratings.append((data["average_rating"], data["ratings_count"]))

        # Google Books API
        url = f"{self.googleBooksURL}?q=isbn:{self.ISBN}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                volume_info = data["items"][0]["volumeInfo"]
                if "averageRating" in volume_info and "ratingsCount" in volume_info:
                    ratings.append((volume_info["averageRating"], volume_info["ratingsCount"]))

        # # Hardcover API
        # headers = {"Authorization": "Bearer YOUR_HARDCOVER_API_KEY"}
        # params = {"isbn": self.ISBN}
        # response = requests.get(self.hardcoverURL, headers=headers, params=params)
        # if response.status_code == 200:
        #     data = response.json()
        #     if "average_rating" in data and "ratings_count" in data:
        #         ratings.append((data["average_rating"], data["ratings_count"]))

        if ratings:
            average_rating = sum(rating[0] for rating in ratings) / len(ratings)
            rating_count = sum(rating[1] for rating in ratings)
            return average_rating, rating_count
        else:
            return None, None

    def getDescription(self):
        """using ISBN, fetch description from google books API. 
        If google books does not have a description for the book, fetch from open library API."""
        # Google Books API
        url = f"{self.googleBooksURL}?q=isbn:{self.ISBN}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                volume_info = data["items"][0]["volumeInfo"]
                if "description" in volume_info:
                    return volume_info["description"]

        # Open Library API
        url = f"{self.openLibraryURL}{self.work}.json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "description" in data:
                if isinstance(data["description"], dict) and "value" in data["description"]:
                    return data["description"]["value"]
                elif isinstance(data["description"], str):
                    return data["description"]

        return None

    def createBookVectorEmbedding(self):
        """using the three open source APIs, fetch data on the book and create a vector embedding"""
        textForEmbedding = f"""
        Title: {self.title}
        Author: {self.author}
        Subjects: {', '.join(self.subjects)}
        Description: {self.description}
        """
        return self.model.encode(textForEmbedding)