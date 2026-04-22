from library.libraryConnection import connectToLibrary

def testConnection():
    conn = connectToLibrary()
    cur = conn.cursor()
    
    cur.execute("SELECT 1;")
    print(cur.fetchone())
    
    cur.close()
    conn.close()

#if test is successful, it will print (1,) to the console. 
#if there is an error, it will raise an exception.
