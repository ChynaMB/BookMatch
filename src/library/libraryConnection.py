import psycopg2

def connectToLibrary():
    return psycopg2.connect(
        dbname="library",
        user="chynam-blye",  
        password="BlueBag",  
        host="localhost",
        port="5432"
    )