from typing import List
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import json
import os
import uuid

from auth import get_current_user
import db

app = FastAPI()


# Define the Book model
class CreateBook(BaseModel):
    title: str
    author: str
    description: str


class BookView(CreateBook):
    id: str = Field(..., alias = '_id')
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
    


# API to create a book
@app.post("/books", response_model=BookView, status_code=201)
def create_book(book: CreateBook, user_details: dict = Depends(get_current_user)):
    try:

        mydb = db.connect()
        insert_result = mydb.books.insert_one(book.model_dump())
        if insert_result.inserted_id:
            result = mydb.books.find_one({ "_id" : insert_result.inserted_id})
            return result
        else:
            raise HTTPException(status_code = 422)
    except Exception:
        raise HTTPException(status_code=500, detail="something went wrong")
    

#API to get books
@app.get("/books", response_model=List[BookView])
def get_books():
    try:
        mydb = db.connect()
        result = mydb.books.find({})
        all_docs = list(result)
        return all_docs
    except Exception:
        raise HTTPException(status_code=500, detail="something went wrong")


#API to get
@app.get("/books/{book_id}", response_model= BookView)
def get_book_by_id(book_id: str):
    try:
        mydb = db.connect()
        result = mydb.books.find_one({ "_id": ObjectId(book_id)})
        if result is None:
            raise HTTPException(status_code= 404)
        return result
    except Exception as e:
        raise HTTPException(status_code = 500 )
    

@app.delete("/books/{book_id}")
def delete_book(book_id: str):
    
    mydb = db.connect()
    result = mydb.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code= 404)
    return JSONResponse(None, status_code=204)
    
    





