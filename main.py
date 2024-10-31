from typing import Optional, List
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


import json

from starlette.responses import StreamingResponse

app = FastAPI()


# CORS 설정
origins = [
    "http://localhost:5173",  # 허용할 출처를 추가하세요
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Pydantic 모델 정의
class MenuItem(BaseModel):
    title: str
    page: int
    icon: Optional[str] = None
    submenu: Optional[List["MenuItem"]] = None

class DataItem(BaseModel):
    filename: str
    car: str
    menu: List[MenuItem]

@app.post("/json-body")
async def receive_and_save_data(body: str = Form(...) , files: List[UploadFile] = File(...)):
    data = json.loads(body)

    # Pydantic 모델로 변환해 검증 (필요 시)
    data_items = [DataItem(**item) for item in data]

    # Python dict로 변환하여 파일 저장
    data_dict = [item.dict() for item in data_items]
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(data_dict, file, ensure_ascii=False, indent=4)

    # 파일 저장 (필요할 경우)
    for uploaded_file in files:
        with open(uploaded_file.filename, 'wb') as file:
            file.write(await uploaded_file.read())

    file_path="data.zip"

    def file_iterator():
        with open(file_path, "rb") as file:
            yield from file  # 파일을 청크 단위로 읽어 전송

    return StreamingResponse(
        file_iterator(),
        media_type="application/octet-stream",  # blob을 위한 MIME 타입
        headers={"Content-Disposition": "attachment; filename=data.zip"})  # 다운로드 파일명 설정

    # # 저장 확인 응답
    # return JSONResponse(content={"status": "success", "message": "Data received and saved successfully"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)