from fastapi import UploadFile, File, Depends
from pathlib import Path
from typing import List
from uuid import uuid4
from models.document import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class Upload:
    def __init__(self):
        self.UPLOAD_DIR = Path("uploads")
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    async def s3_upload(self, files: List[UploadFile] = File(...)):
        pass

    async def local_upload(self, db: AsyncSession, files: List[UploadFile] = File(...)):
        try:
            saved_files = []
            for file in files:
                # Create a safe filename
                file_path = self.UPLOAD_DIR / file.filename

                # Save the file
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)

                # Create database record
                doc = Document(
                    filename=file.filename,
                    file_path=str(file_path.absolute()),
                    is_ingested=False,
                )
                print(doc)
                db.add(doc)
                await db.commit()
                await db.refresh(doc)

                saved_files.append(
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "size": len(contents),
                        "content_type": file.content_type,
                        "is_ingested": doc.is_ingested,
                    }
                )

            return {"message": "Files uploaded successfully", "files": saved_files}
        except Exception as e:
            await db.rollback()
            return {"error": str(e), "status_code": 500}

    async def list_files(self, db: AsyncSession):
        try:
            query = select(Document)
            result = await db.execute(query)
            documents = result.scalars().all()

            return {
                "files": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "path": doc.file_path,
                        "is_ingested": doc.is_ingested,
                        "created_at": doc.created_at,
                        "updated_at": doc.updated_at,
                    }
                    for doc in documents
                ]
            }
        except Exception as e:
            return {"error": str(e), "status_code": 500}
