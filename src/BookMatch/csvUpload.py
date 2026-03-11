import pandas as pd
from library import Library

class CSVparser:
    def __init__(self, username: str, email: str, csv_path: str):
        self.csv_path = csv_path
        self.csvDataFrame = pd.read_csv(csv_path)
        self.library = Library()
        self.CSV_ID = self.library.add_user(username, email)
    
#tests      
parser = CSVparser("abc", "xyz", "goodreads_library_export.csv")
df = parser.csvDataFrame
print(df.head())
print(df.columns)