# FastAPI 파일 + 바디 데이터 처리 및 정적 파일 서빙 테스트

## 📌 개요
이 프로젝트는 FastAPI를 이용하여 다음 기능을 테스트합니다.

1. **파일과 바디 데이터를 함께 받는 API**
2. **정적 파일 서빙 테스트**

## 🛠 환경 설정
### 1️⃣ FastAPI 설치
다음 명령어를 실행하여 FastAPI와 Uvicorn을 설치합니다.
```bash
pip install fastapi uvicorn
```

## 📂 파일 + 바디 데이터 함께 받기
FastAPI에서 `File`과 `Form`을 사용하여 파일과 바디 데이터를 동시에 받는 API를 구현할 수 있습니다.

### 🔹 코드 예제
```python
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Form(...)
):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "description": description
    }
```

### 🔹 테스트 방법
1. **FastAPI 서버 실행**
    ```bash
    uvicorn main:app --reload
    ```
2. **Swagger UI에서 테스트**
    - 브라우저에서 `http://127.0.0.1:8000/docs`로 접속
    - `/upload/` 엔드포인트에서 파일과 설명을 업로드
3. **cURL을 이용한 테스트**
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/upload/' \
      -H 'accept: application/json' \
      -H 'Content-Type: multipart/form-data' \
      -F 'file=@test.txt' \
      -F 'description=테스트 파일입니다.'
    ```

## 📂 정적 파일 서빙 테스트
FastAPI를 이용하여 `static` 폴더 안의 정적 파일을 서빙할 수 있습니다.

### 🔹 코드 예제
```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

### 🔹 정적 파일 제공 테스트
1. `static` 폴더를 만들고 `example.txt` 파일을 추가합니다.
    ```
    ├── main.py
    ├── static/
    │   ├── example.txt
    ```
2. **FastAPI 서버 실행**
    ```bash
    uvicorn main:app --reload
    ```
3. **브라우저에서 정적 파일 접근**
    - `http://127.0.0.1:8000/static/example.txt`

## 🚀 마무리
이 프로젝트에서는 **파일과 바디 데이터를 함께 받는 API**와 **정적 파일 서빙 기능**을 FastAPI로 테스트하는 방법을 다루었습니다. 추가적인 기능이 필요하면 FastAPI 문서를 참고하세요!

🔗 [FastAPI 공식 문서](https://fastapi.tiangolo.com/)

