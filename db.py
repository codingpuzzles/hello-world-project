from pymongo import MongoClient
from pymongo.database import Database

def connect() -> Database:
    client = MongoClient("mongodb://user:pass@localhost:27017/")

    # Access a database
    booksdb = client['mybooksappdb']
    return booksdb

         