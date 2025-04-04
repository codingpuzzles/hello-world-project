from io import BytesIO
from typing import List, Optional
from bson import ObjectId
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
import gridfs
from pydantic import BaseModel, Field, validator
import json
import os
import uuid
import logging

from auth import get_current_user
import db

app = FastAPI()


# Define the Book model
class CreateBook(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    gridfs_fileid : str


class BookView(CreateBook):
    id: str = Field(..., alias = '_id')
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
    


# API to create a book
@app.post("/books", response_model=BookView, status_code=201)
async def create_book(book_name: str = Form(...), author: str = Form(...),
                 description: Optional[str] = Form(None), 
                  file: UploadFile = File(...), user_details: dict = Depends(get_current_user)):
    try:

        mydb = db.connect()
        fs = gridfs.GridFS(mydb)
        # Read the file content
        file_content = await file.read()
    
        # Create a BytesIO object to simulate a file-like object
        file_like = BytesIO(file_content)
    
        # Store the PDF in GridFS
        file_id = fs.put(file_like, filename=file.filename, content_type="application/pdf")
        book = CreateBook(title=book_name, author=author, description=description, gridfs_fileid=str(file_id))
    
        insert_result = mydb.books.insert_one(book.model_dump())
        if insert_result.inserted_id:
            result = mydb.books.find_one({ "_id" : insert_result.inserted_id})
            return result
        else:
            raise HTTPException(status_code = 422)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="something went wrong")
    

#API to get books
@app.get("/books", response_model=List[BookView], status_code=200)
def get_books(user_details: dict = Depends(get_current_user)):
    try:
        mydb = db.connect()
        result = mydb.books.find({})
        all_docs = list(result)
        return all_docs
    except Exception:
        raise HTTPException(status_code=500, detail="something went wrong")


#API to get book by id
@app.get("/books/{book_id}", response_model= BookView, status_code=200)
def get_book_by_id(book_id: str, user_details = Depends(get_current_user)):
    
    mydb = db.connect()
    result = mydb.books.find_one({ "_id": ObjectId(book_id)})
    if result is None:
        raise HTTPException(status_code= 404)
    return result
    



@app.delete("/books/{book_id}")
def delete_book(book_id: str, user_details = Depends(get_current_user)):
    
    mydb = db.connect()
    result = mydb.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code= 404)
    return JSONResponse(None, status_code=204)
    
    





