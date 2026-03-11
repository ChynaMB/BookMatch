import pandas as pd
from Library import Library

class CSVparser:
    def __init__(self, csv_path: str):
        self.CSV_ID = Library.generateCSV_ID()
        self.csv_path = csv_path
        self.csvDataFrame = pd.read_csv(csv_path)

    def fetch

    

    
#tests      
parser = CSVParser("goodreads_library_export.csv")
df = parser.csvDataFrame
print(df.head())
print(df.columns)