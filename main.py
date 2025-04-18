from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os, json
from typing import Optional
from app.utils.openai_client import get_openai_response
from app.utils.file_handler import save_upload_file_temporarily
from app.utils.functions import *

app = FastAPI(title="IITM Assignment API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory if it exists
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    print("Warning: 'static' directory not found. Static files will not be served.")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "answer": None})

@app.post("/submit", response_class=HTMLResponse)
async def handle_form(
    request: Request,
    question: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    try:
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)

        answer = await get_openai_response(question, temp_file_path)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "answer": answer,
            "question": question
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "answer": f"Error: {str(e)}",
            "question": question
        })

@app.post("/api/")
async def process_question(
    question: str = Form(...), file: Optional[UploadFile] = File(None)
):
    try:
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)
        answer = await get_openai_response(question, temp_file_path)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/{function_name}")
async def debug_function(
    function_name: str,
    file: Optional[UploadFile] = File(None),
    params: str = Form("{}"),
):
    try:
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)
        parameters = json.loads(params)
        if temp_file_path:
            parameters["file_path"] = temp_file_path
        if function_name == "analyze_sales_with_phonetic_clustering":
            result = await analyze_sales_with_phonetic_clustering(**parameters)
            return {"result": result}
        elif function_name == "calculate_prettier_sha256":
            if temp_file_path:
                result = await calculate_prettier_sha256(temp_file_path)
                return {"result": result}
            else:
                return {"error": "No file provided for calculate_prettier_sha256"}
        else:
            return {"error": f"Function {function_name} not supported for direct testing"}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

if __name__ == "__main__":
    import uvicorn
    # Use port 8008 by default (or override with the PORT environment variable)
    port = int(os.environ.get("PORT", 8008))
    uvicorn.run(app, host="0.0.0.0", port=port)