from fastapi import FastAPI, File, UploadFile, HTTPException, Request
import asyncio
from contextlib import asynccontextmanager
import requests
import dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from app_manager import AppManager
from database import (
    create_database,
    create_tables,
    insert_file,
    create_session,
    save_question_answer,
    get_file_by_id,
    delete_file_by_id,
    get_all_file_info,
    delete_session_by_id,
    get_all_sessions,
    get_all_question_answer,
)

dotenv.load_dotenv()

llm_config = {
    "model_name": "models/gemini-2.0-flash-lite-preview-02-05",
    "api_key": os.environ.get("GOOGLE_API_KEY"),
    "base_url": os.environ.get("GOOGLE_BASE_URL"),
}

embedding_config = {
    "model_name": "jinaai/jina-embeddings-v2-small-en",  # FastEmbedEmbeddings
    "max_length": 1000,
    "batch_size": 64,
}

reranker_config = {
    "model_name": "jinaai/jina-reranker-v1-tiny-en"
}  # FastEmbed TextCrossEncoder

app_manager = AppManager()

from fastapi import FastAPI
import asyncio


class RequestCancelledMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        queue = asyncio.Queue()
        
        async def message_poller():
            try:
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        handler_task.cancel()
                        return
                    await queue.put(message)
            except asyncio.CancelledError:
                print("Message poller task cancelled")
        handler_task = asyncio.create_task(self.app(scope, queue.get, send))
        poller_task = asyncio.create_task(message_poller())

        try:
            return await handler_task
        except asyncio.CancelledError:
            print("Cancelling request due to disconnect")
        except Exception as e:
            print(e)
            print(f"Exception in request handler: {e}")
        finally:
            poller_task.cancel()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_database()
    create_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    RequestCancelledMiddleware,
)

# Đường dẫn đến thư mục lưu trữ file
UPLOAD_DIR = "uploads"


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    try:
        file_location = f"uploads/{file.filename}"  # Lưu file vào folder "uploads"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        insert_file(file.filename)
        return {"detail": f"File '{file.filename}' uploaded successfully!"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


class DownloadRequest(BaseModel):
    url: str


@app.post("/download/")
async def download_pdf(request: DownloadRequest):
    """
    Download a PDF file from a given URL and save it to the "uploads" folder.

    Args:
        request: The request containing the URL of the PDF file to download.

    Returns:
        A JSON response containing a success message, or an error message if the file
        cannot be downloaded or saved successfully.
    """

    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    try:
        url = request.url
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type")
        if "pdf" not in content_type.lower():
            raise HTTPException(status_code=400, detail="The file is not a PDF.")
        filename = os.path.basename(url)
        if not filename.endswith(".pdf"):
            filename = filename + ".pdf"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as file:
            file.write(response.content)
        insert_file(filename)
        return {"detail": f"File '{filename}' downloaded successfully!"}

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred when downloading the PDF: {str(e)}",
        )


@app.delete("/delete/{file_id}")
async def delete_file(file_id: int):
    """
    Delete a file both from the server and the database using its file ID.

    Args:
        file_id (int): The ID of the file to be deleted.

    Returns:
        dict: A JSON response with a success message if the file is deleted.

    Raises:
        HTTPException: If the file is not found in the database or on the server.
    """
    filename = get_file_by_id(file_id)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if file_id:
        delete_file_by_id(file_id)
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"detail": f"File '{filename}' deleted successfully!"}
    else:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")


@app.get("/")
async def get_files_info():
    """
    Retrieve all file information from the database.

    Returns:
        list: A list of dictionaries. Each dictionary contains the file_id, source, and created_at of a file.
    """
    data = get_all_file_info()
    return data


@app.post("/initialize/{file_id}")
async def initialize(file_id: int):
    """
    Initialize the application with the given file ID.

    This endpoint activates the application associated with the provided file ID using
    the specified configurations for the language model, embedding, and reranker.

    Args:
        file_id (int): The ID of the file to initialize the application with.

    Returns:
        dict: A JSON response containing a success message if the application is
        initialized successfully.
    """
    await app_manager.active_app(
        file_id=file_id,
        llm_config=llm_config,
        embedding_config=embedding_config,
        reranker_config=reranker_config,
    )
    return {"detail": f"App with file_id '{file_id}' initialized successfully!"}


class QuestionRequest(BaseModel):
    question: str
    session_id: str


@app.post("/question/{file_id}")
async def ask_question(
    request: Request, file_id: int, question_request: QuestionRequest
):
    try:
        if app_manager.current_app and app_manager.current_app["file_id"] == file_id:
            result = None
            try: 
                result = await app_manager.current_app["app"].ainvoke(
                    {
                        "question": question_request.question,
                        "max_retries": 1,
                        "max_generations": 2,
                    }
                )
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    raise HTTPException(
                        status_code=429,
                        detail="You have reached the rate limit. Please try again later or change LLM API.",
                    )
                raise e
            await asyncio.to_thread(
                save_question_answer,
                question_request.session_id,
                question_request.question,
                result["final_answer"],
            )
            return {"detail": "success", "answer": result["final_answer"]}
        else:
            raise HTTPException(
                status_code=404,
                detail="App is not initialized! Please initialize app first!",
            )
    except asyncio.CancelledError:
        print("Request was cancelled")
        raise 
    except Exception as e:
        raise e


@app.post("/new_session/{file_id}")
async def new_session(file_id: int):
    """
    Create a new session for a given file ID.

    This endpoint creates a new session for a given file ID and returns a JSON
    response containing the session ID.

    Args:
        file_id (int): The ID of the file to create a new session for.

    Returns:
        dict: A JSON response containing the session ID if the session is created
            successfully.

    Raises:
        HTTPException: If there is an error while creating the session.
    """

    try:
        session_id = create_session(file_id)
        return {
            "detail": f"Session '{session_id}' created successfully!",
            "session_id": session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete_session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session by its session ID.

    This endpoint deletes a session by its session ID and returns a JSON response
    containing a success message if the session is deleted successfully.

    Args:
        session_id (str): The session ID of the session to delete.

    Returns:
        dict: A JSON response containing a success message if the session is
            deleted successfully.

    Raises:
        HTTPException: If there is an error while deleting the session.
    """
    try:
        delete_session_by_id(session_id)
        return {"detail": f"Session '{session_id}' deleted successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_all_sessions/{file_id}")
async def get_sessions(file_id: int):
    """
    Retrieve all session information for a given file ID.

    This endpoint retrieves all session information associated with the provided
    file ID from the database and returns it in a JSON response.

    Args:
        file_id (int): The ID of the file to retrieve session information for.

    Returns:
        dict: A JSON response containing a success message and a list of session
        information if the retrieval is successful.

    Raises:
        HTTPException: If there is an error while retrieving the session information.
    """
    try:
        session_data = get_all_sessions(file_id)
        return {"detail": "success", "session_data": session_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_all_question_answer/{session_id}")
async def get_question_answer(session_id: str):
    """
    Retrieve all question and answer information for a given session ID.

    This endpoint fetches all question and answer pairs associated with the
    specified session ID from the database and returns them in a JSON response.

    Args:
        session_id (str): The ID of the session to retrieve question and answer
            information for.

    Returns:
        dict: A JSON response containing a success message and a list of question
        and answer pairs if the retrieval is successful.

    Raises:
        HTTPException: If there is an error while retrieving the question and
        answer information.
    """
    try:
        data = get_all_question_answer(session_id)
        return {"detail": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
