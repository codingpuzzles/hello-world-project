from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import json
import os
import uuid

app = FastAPI()

BOOKS_FILE = "books.json"

def generate_id():
    unique_id = uuid.uuid4()
    return str(unique_id)

class Book(BaseModel):
    id: str 
    title: str
    author: str

# Define the Book model
class CreateBook(BaseModel):
    id: str = Field(default_factory=generate_id)
    title: str
    author: str
    description: str

# Load existing books from file (if any)
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []


# Save books to file
def save_books(books):
    with open(BOOKS_FILE, "w") as file:
        json.dump(books, file, indent=4)


# API to create a book
@app.post("/books")
def create_book(book: CreateBook):
    books = load_books()
    books.append(book.model_dump())

    save_books(books)
    return book


# API to get all books
@app.get("/books")
def get_books():
    books = load_books()
    return books

@app.get("/books/{id}")
def get_a_book(id: str):
    books = load_books()
    for book in books:
        if book['id'] == id:
            return book
        else:
            raise HTTPException(status_code=404, detail="book not found")
            
@app.delete(path="/books/{id}")
def delete_a_book(id: str):
    books = load_books()
    found_a_book = False
    for i, book in enumerate(books):
        if book['id'] == id:
            found_a_book = True
            del books[i]
            save_books(books)
    if found_a_book == False:
        raise HTTPException(status_code=404, detail="Book not found")
        