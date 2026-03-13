from library import Library
import requests

class Book:
    def __init__(self, work, ISBN, subjects):
        self.work = work
        self.ISBN = ISBN
        self.title = None
        self.subjects = subjects
        self.averageRating = self.updateRating()[0]
        self.ratingCount = self.updateRating()[1]
        self.embedding = self.createEmbedding()
        self.saveToLibrary()
        self.bookData_id = self.getBookData_idFromLibrary()

        self.openLibraryURL = "https://openlibrary.org"
        self.googleBooksURL = "https://www.googleapis.com/books/v1/volumes"
        self.hardcoverURL = "https://api.hardcover.io/v1/books"

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
        params = {"q": f"isbn:{self.ISBN}"}
        response = requests.get(self.googleBooksURL, params=params)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                volume_info = data["items"][0]["volumeInfo"]
                if "averageRating" in volume_info and "ratingsCount" in volume_info:
                    ratings.append((volume_info["averageRating"], volume_info["ratingsCount"]))

        # Hardcover API
        headers = {"Authorization": "Bearer YOUR_HARDCOVER_API_KEY"}
        params = {"isbn": self.ISBN}
        response = requests.get(self.hardcoverURL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if "average_rating" in data and "ratings_count" in data:
                ratings.append((data["average_rating"], data["ratings_count"]))

        if ratings:
            average_rating = sum(r[0] for r in ratings) / len(ratings)
            rating_count = sum(r[1] for r in ratings)
            return average_rating, rating_count
        else:
            return None, None

    def createEmbedding(self):
        pass

    def getBookData_idFromLibrary(self):
        pass

    def saveToLibrary(self):
        pass