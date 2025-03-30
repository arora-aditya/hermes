from langchain_community.document_loaders import PyPDFLoader
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.document import Document
from typing import List
from fastapi import HTTPException


class IngestRequest(BaseModel):
    document_ids: list[int] = Field(
        ..., description="List of document IDs to ingest", min_items=1
    )


class Ingest:
    def __init__(self):
        pass

    async def ingest_docs(self, document_ids: List[int], db: AsyncSession):
        all_docs = []

        try:
            # First verify all documents exist to fail early if any are missing
            for doc_id in document_ids:
                stmt = select(Document).where(Document.id == doc_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                if not document:
                    raise HTTPException(
                        status_code=404, detail=f"Document with id {doc_id} not found"
                    )

            # Process all documents
            for doc_id in document_ids:
                stmt = select(Document).where(Document.id == doc_id)
                result = await db.execute(stmt)
                document = result.scalar_one()
                # Load and process the PDF
                loader = PyPDFLoader(document.file_path)
                docs = loader.load()
                all_docs.extend(docs)

                # Update document status
                update_stmt = (
                    update(Document)
                    .where(Document.id == doc_id)
                    .values(is_ingested=True)
                )
                await db.execute(update_stmt)

            await db.commit()
            return all_docs

        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error processing documents: {str(e)}"
            )
