from fastapi import UploadFile, File
from pathlib import Path
from typing import List


class Upload:
    def __init__(self):
        self.UPLOAD_DIR = Path("uploads")
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    async def s3_upload(self, files: List[UploadFile] = File(...)):
        pass

    async def local_upload(self, files: List[UploadFile] = File(...)):
        try:
            saved_files = []
            for file in files:
                # Create a safe filename
                file_path = self.UPLOAD_DIR / file.filename

                # Save the file
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)

                saved_files.append(
                    {
                        "filename": file.filename,
                        "size": len(contents),
                        "content_type": file.content_type,
                    }
                )

            return {"message": "Files uploaded successfully", "files": saved_files}
        except Exception as e:
            return {"error": str(e)}, 500

    def list_files(self):
        try:
            files = []
            for file_path in self.UPLOAD_DIR.glob("*"):
                if file_path.is_file():
                    files.append(
                        {
                            "filename": file_path.name,
                            "path": str(file_path.absolute()),
                            "size": file_path.stat().st_size,
                        }
                    )
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}, 500
