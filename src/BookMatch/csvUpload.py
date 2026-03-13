import pandas as pd
from library import Library

class CSVparser:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.csvDataFrame = pd.read_csv(csv_path)
        self.library = Library()
        self.userID = self.library.add_user()

    def getStarRating(self, rating: int):
        """Return a list of ISBNs based on the 'my rating' column in the csvDataFrame
        the rating can only be one of 1,2,3,4,5"""
        if rating not in [1,2,3,4,5]:
            raise ValueError("Rating must be an integer between 1 and 5")
        
        filtered = self.csvDataFrame[self.csvDataFrame['My Rating'] == rating]
        isbns = filtered['ISBN']
        return isbns.tolist()

#tests      
parser = CSVparser("goodreads_library_export.csv")
df = parser.csvDataFrame
print(df.head())
print(df.columns)