from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from langchain_community.document_loaders import PyMuPDFLoader
import os
import asyncio
import json
import zipfile
import uvicorn
from datetime import datetime
import subprocess
from pathlib import Path
import logging
from urllib.parse import quote
from pydantic import BaseModel
import shutil
import multiprocessing
import sys
import webbrowser

logging.basicConfig(level=logging.INFO)

BASE_JSON_DIR = Path.cwd()/ "manual/src/json"
FRONTEND = Path.cwd() / "static"
COPY_FOLDER = Path.cwd() / "copy"
BUILD_FOLDER = Path.cwd() / "build"


# 폴더 없을 시, 생성
COPY_FOLDER.mkdir(parents=True, exist_ok=True)
BUILD_FOLDER.mkdir(parents=True, exist_ok=True)

now = datetime.now().strftime('%y%m%d_%H%M%S')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers = ["Content-Disposition"]
)


def preprocess_text(text):
    text = text.replace('\n', ' ')
    sentences = text.split('.')
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    return ' '.join(sentences)


def create_json(filename: str, processed_data: List[dict]) -> List[dict]:
    json_data = {
        "filename": filename,
        "content": []
    }
    for data in processed_data:
        page_number = data["page_number"]
        content = data["content"]
        json_data["content"].append({
            "page": page_number,
            "text": content
        })
    return json_data


def save_json(data, file_path):
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class MenuItem(BaseModel):
    title: str
    page: int
    icon: Optional[str] = None
    submenu: Optional[List["MenuItem"]] = None

class DataItem(BaseModel):
    filename: str
    car: str
    menu: List[MenuItem]


# 순차 처리
lock = asyncio.Lock()

# serve fronted
# frontend = "./frontend/dist"
app.mount("/static", StaticFiles(directory="./static"), name="static")

async def run_build():
    script_path = "./build_copy.sh"
    print(f"Checking for script at: {script_path}")

    if os.path.isfile(script_path):
        try:
            # Run the script
            subprocess.run(['bash', script_path], check=True,shell=True)
            logging.info("Build script executed successfully!")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error executing build script: {e}")
            raise HTTPException(status_code=500, detail="Build script execution failed")
    else:
        logging.error(f"Script not found at: {script_path}")
        raise HTTPException(status_code=500, detail="Build script not found")


# zip build folder
def create_zip(zip_output_name):
    zip_file_path = Path.cwd() / zip_output_name
    if BUILD_FOLDER.is_dir():
        try:
            with zipfile.ZipFile(zip_file_path, "w") as build_zip:
                for root, _, files in os.walk(BUILD_FOLDER):
                    for file in files:
                        file_path = Path(root) / file
                        build_zip.write(file_path, file_path.relative_to(BUILD_FOLDER))
            logging.info(f"ZIP file created at: {zip_file_path}")
            return zip_file_path
        except Exception as e:
            logging.error(f"Error creating ZIP file: {e}")
            raise HTTPException(status_code=500, detail="Failed to create ZIP file")
    else:
        logging.error("Build folder does not exist.")
        raise HTTPException(status_code=500, detail="Build folder not found")


async def process_pdf(file: UploadFile) -> List[dict]:
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".PDF")):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    pdf_path = pdf_path = BASE_JSON_DIR / file.filename


    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    loader = PyMuPDFLoader(pdf_path)
    pages = loader.load()
    processed_data = []

    for page_num, page in enumerate(pages):
        processed_text = preprocess_text(page.page_content)
        processed_data.append({
            "page_number": page_num + 1,
            "content": processed_text
        })

    os.remove(pdf_path)
    return processed_data


# endpoint
@app.post("/upload")
async def upload_files(body: str = Form(...), files: List[UploadFile] = File(...)):
    async with lock:
        try:
            title_data = json.loads(body)
            data_dict = [DataItem(**item).model_dump() for item in title_data]
            car_name = data_dict[0]["car"] if data_dict else None
            zip_name = f"{car_name}_{now}.zip"
            total_json_file = os.path.join(BASE_JSON_DIR, "tableOfContents.json")
            save_json(data_dict, total_json_file)
            logging.info("Title JSON saved successfully")

            pdf_data = []
            for file in files:
                try:
                    # pdf 추출 될때까지 기다림
                    processed_data = await process_pdf(file)
                    json_data = create_json(filename=file.filename, processed_data=processed_data)
                    pdf_data.append(json_data)
                except asyncio.TimeoutError:
                    logging.error(f"Processing {file.filename} timed out.")
                    raise HTTPException(status_code=408, detail=f"Processing {file.filename} timed out.")
                except Exception as e:
                    logging.error(f"Error processing {file.filename}: {e}")
                    raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")

            total_pdf = os.path.join(BASE_JSON_DIR, "pdfText.json")
            save_json(pdf_data, total_pdf)
            logging.info("All PDF contents saved successfully")

            # await = 빌드 스크립트 실행될때까지 기다림
            await run_build()

            zip_file_path = create_zip(zip_name)
            encoded_zip_name = quote(zip_name)

            print(zip_name)

            # 빌드 후 json삭제
            # os.remove(total_json_file)
            # os.remove(total_pdf)
            # logging.info("JSON files deleted successfully")

            # 한글깨짐테스트
            response_headers = {
                    "Content-Disposition": f"attachment; filename={encoded_zip_name}"
                }

            return StreamingResponse(
                open(zip_file_path, "rb"),
                media_type="application/octet-stream",
                headers=response_headers
            )
        except json.JSONDecodeError:
            logging.error("Invalid JSON in request body.")
            raise HTTPException(status_code=400, detail="Invalid JSON format.")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")

if __name__ == "__main__":
    multiprocessing.freeze_support() # 윈도우
    uvicorn.run(app, host="localhost", port=8000)



