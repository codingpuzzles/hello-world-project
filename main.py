from io import BytesIO
import io
from typing import List, Optional
from bson import ObjectId
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
import gridfs
from pydantic import BaseModel, Field, validator
import logging

from pymongo import ASCENDING
from pypdf import PdfReader, PdfWriter

from auth import get_current_user
import db

app = FastAPI()


# Define the Book model
class CreateBook(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    no_of_pages: int
    
# Define the page metadata model
class Page(BaseModel):
    book_id: str
    page_no: int
    gridfs_pageid: str


class BookView(CreateBook):
    id: str = Field(..., alias = '_id')
    @validator('id', pre=True)
    def convert_objectid_to_str(cls, value):
        if isinstance(value, ObjectId):
            return str(value)
        return value
    

#API to get book by id with actual book data itself with pages
@app.get("/books/{book_id}/pages", response_model= Page, status_code= 200)
async def get_pages(book_id: str, start: int = Query(0, ge=0), end: int = Query(0, ge=0), user_details : dict = Depends(get_current_user)):
        if start > end:
            end = start

        mydb = db.connect()
        fs = gridfs.GridFS(mydb)
        oid = ObjectId(book_id)
        result = mydb.pages.find({
            "book_id": oid,
            "page_no": {"$gte": start, "$lte": end}}
            )
        result = result.sort("page_no", ASCENDING)
    
        if not result:
            raise HTTPException(status_code=404, detail="Pages not found")
        writer = PdfWriter()
        for page in result:
            file_data = fs.get(page["gridfs_pageid"]).read()
            reader = PdfReader(BytesIO(file_data))
            writer.add_page(reader.pages[0])

        output = BytesIO()
        writer.write(output)
        output.seek(0)

        return StreamingResponse(output, media_type="application/pdf", headers={
            "Content-Disposition": f"inline; filename=book_{book_id}_pages_{start}_to_{end}.pdf"
        }
        )
    



# API to create a book
@app.post("/books", response_model=BookView, status_code=201)
async def create_book(book_name: str = Form(...), author: str = Form(...),
                 description: Optional[str] = Form(None), 
                  file: UploadFile = File(...), user_details: dict = Depends(get_current_user)):
    

        mydb = db.connect()
        fs = gridfs.GridFS(mydb)
        # Read the file content
        file_content = await file.read()
    
        # Create a BytesIO object to simulate a file-like object
        file_like = PdfReader(BytesIO(file_content))
        total_pages = len(file_like.pages)

        book = CreateBook(title=book_name, author=author, description=description, no_of_pages=total_pages)
    
        insert_result = mydb.books.insert_one(book.model_dump())
        new_book_id = str(insert_result.inserted_id)
    
        # Store the PDF in GridFS
        for i, page  in enumerate(file_like.pages):
            writer = PdfWriter()
            writer.add_page(page)
             
            buffer = BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            
            new_gridfs_pageid = fs.put(buffer.read(), filename=f"{new_book_id}-{i}.pdf", content_type="application/pdf")
            new_page = Page(book_id=new_book_id, page_no=i, gridfs_pageid=str(new_gridfs_pageid))
            inserted_page = mydb.pages.insert_one(new_page.model_dump())
            


        if new_book_id:
            result = mydb.books.find_one({ "_id" : ObjectId(new_book_id)})
            return result
        else:
            raise HTTPException(status_code = 422)


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
    
    





