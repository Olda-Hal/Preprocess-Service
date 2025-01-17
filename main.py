from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
import binascii
import tarfile
import os
import merger

app = FastAPI()


class ExecuteRequest(BaseModel):
    test_tar: str
    exec_tar: str
    test_file_path: str
    exec_file_path: str
    timeout: int
    language: str

@app.post("/execute")
async def execute(request: ExecuteRequest):
    test_tar_binary = binascii.unhexlify(request.test_tar)
    exec_tar_binary = binascii.unhexlify(request.exec_tar)

    with open("test_tar_temp.tar.gz", "wb") as test_tar_file:
        test_tar_file.write(test_tar_binary)
    
    with open("exec_tar_temp.tar.gz", "wb") as exec_tar_file:
        exec_tar_file.write(exec_tar_binary)

    os.makedirs("extracted_files", exist_ok=True)

    with tarfile.open("test_tar_temp.tar.gz", "r:gz") as test_tar:
        test_tar.extractall(path="extracted_files")
    
    with tarfile.open("exec_tar_temp.tar.gz", "r:gz") as exec_tar:
        exec_tar.extractall(path="extracted_files")

    os.remove("test_tar_temp.tar.gz")
    os.remove("exec_tar_temp.tar.gz")
    test_file_new_path = os.path.join("extracted_files", request.test_file_path)
    exec_file_new_path = os.path.join("extracted_files", request.exec_file_path)
    
    merger.merge(test_file_new_path, exec_file_new_path, request.language)
    
    output_tar_path = "output.tar.gz"
    with tarfile.open(output_tar_path, "w:gz") as tar:
        tar.add("extracted_files", arcname=os.path.basename("extracted_files"))

    with open(output_tar_path, "rb") as output_tar_file:
        output_tar_binary = output_tar_file.read()

    output_tar_hex = binascii.hexlify(output_tar_binary).decode()

    os.remove(output_tar_path)
    return {"output_tar": output_tar_hex}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)