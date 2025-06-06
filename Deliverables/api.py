'''
Make sure to run this server on port 8090 or
change the url path on the background.js script
'''
from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Query,Response,Cookie,Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio
import uuid
from pathlib import Path
import os
import json
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import socket
from contextlib import asynccontextmanager
from utils.DBN_ANN import ANN, DBN, RBM, train_ann_model, train_dbn_model
from utils.cognitive import predict_jobs
from utils.predictor import (
    load_models, 
    update_personality_aggregation, 
    get_aggregated_personality, 
    reset_personality_aggregation,
    get_aggregated_details,
    get_cognitive_score
)
from image_analysis import download_and_process_image

from __init__ import set_dir


set_dir()

executor = ThreadPoolExecutor(max_workers=20)
Result=dict()
Verify =False       #Was used to validate results, not used for now
User_name="none"

class Input(BaseModel): #User's post
    url: str
    text: str
    imgs: List[str]

class Name(BaseModel):  #User's name
    url: str
    name: str
    dp:str
    
class Profile(BaseModel):   #web service sends a new profile link
    url:str



@asynccontextmanager
async def lifespan(app: FastAPI):
    global Verify
    Verify = False #True if input("Verify results?(Y/N): ") == 'Y' else False
    await set_up()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/public", StaticFiles(directory="public"), name="public")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Store active WebSocket connections
connections = set()
uid_to_socket_map = {}
url_to_uid_map = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket endpoint for real-time communication with frontend """
    await websocket.accept()
    global Result, User_name, uid_to_socket_map
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            msg_data = message.get("data")

            if msg_type == 'Profile':
                User_name = "none"
                Result.clear()
                link = msg_data  # Profile URL
                print("New Profile: ", link)
                session_id= message.get("session_id", None)  # Get session ID or create a new one
                # Store WebSocket connection associated with the profile URL
                url_to_uid_map[link] = session_id
                reset_personality_aggregation()  # Reset aggregation for a new session
                send_data(msg_type="PROFILE", msg_data=link)  # Send profile link to the server
            if msg_type == "session_id":
                session_id = msg_data
                print("Session ID received via WS message:", session_id)
                uid_to_socket_map[session_id] = websocket  # Map session ID to WebSocket
                
            elif msg_type == 'Stop_analysis':
                Result.clear()
                reset_personality_aggregation()
                User_name = "none"
                send_data(msg_type='STOP SCROLL')

    except WebSocketDisconnect:
        # Remove the disconnected WebSocket from the mapping
        for url, ws in list(uid_to_socket_map.items()):
            if ws == websocket:
                del uid_to_socket_map[url]
                break
        print("WebSocket Disconnected")
        
@app.get("/")
async def serve_main(session_id: str = Cookie(default=None)):
    main_file_path = os.path.join(os.path.dirname(__file__), 'public', 'html', 'main.html')
    response = FileResponse(main_file_path, media_type="text/html")
    
    if session_id is None:
        new_session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=new_session_id, httponly=False, samesite="lax")
        print(f"New session ID set: {new_session_id}")
    else:
        print(f"Existing session ID: {session_id}")
    
    return response

@app.post("/send_name")
async def get_user_name(body: Name):
    """
    Receives and processes the user's name.
    """
    global User_name
    name = body.name
    session_id = url_to_uid_map.get(body.url, None)  # Get session ID from URL mapping
    #name = " ".join(name.split(" ")[:2])
    url = body.url
    print("User:", name, "Url:", url)
    User_name=name
    dp_url=body.dp
    # Check if a WebSocket connection exists for this URL
    websocket = uid_to_socket_map.get(session_id)
    if websocket:
        try:
            await websocket.send_text(json.dumps({"type": "user_name", "name":User_name,"dp":dp_url}))
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")

    return {"success": True}

def analyze_and_process(body: dict):
    global Verify, vectorizer, Result

    url = body.get("url", "NONE")
    post_text = body["text"]
    img_links = body.get("imgs", [])
    session_id = url_to_uid_map.get(url, None)

    whole_image_text = ""
    expressions = []
    for img_url in img_links:
        result = download_and_process_image(img_url)
        extracted_text = result.get("ocr_text", "")
        if extracted_text:
            whole_image_text += extracted_text + ". "
        if result.get("expression"):
            expressions.append(result.get("expression"))

    combined_text = whole_image_text + post_text

    print("----- New Post Received -----")
    print("Post Text:")
    print(post_text[:100])
    if whole_image_text:
        print("Image OCR Text:")
        print(whole_image_text)
    if expressions:
        print("Detected Expression(s):")
        for expr in expressions:
            print(expr)

    cognitive_score = get_cognitive_score()
    print(f"Current Cognitive Score: {cognitive_score:.2f}")

    current_personality = update_personality_aggregation(combined_text, url, models, vectorizer)
    overall_result = get_aggregated_personality()

    aggregates = get_aggregated_details()
    print("Current MBTI Prediction:", current_personality)
    print("Current Aggregation Details:")
    for dichotomy, data in aggregates.items():
        print(f" {dichotomy}:")
        for letter, stats in data.items():
            if isinstance(stats, dict):
                avg = stats['conf_sum'] / stats['count'] if stats['count'] > 0 else 0.0
                print(f"   {letter}: count = {stats['count']}, average confidence = {avg:.2f}")
        print("-" * 50)

    if current_personality in Result:
        Result[current_personality] += 1
    else:
        Result[current_personality] = 1

    websocket = uid_to_socket_map.get(session_id)
    if websocket:
        try:
            asyncio.run(websocket.send_text(json.dumps({
                "type": "update",
                "url": url,
                "cog_score": f"{cognitive_score:.2f}",
                "result": Result,
                "aggregate": aggregates
            })))
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")

    return current_personality

@app.post("/api")
async def analyze_personality(body: Input):
    loop = asyncio.get_event_loop()
    current_personality = await loop.run_in_executor(executor, analyze_and_process, body.dict())
    return {"data": current_personality}


@app.get('/job_result')
async def get_mbti_details(
    mbti_type: str = Query(None, title="MBTI Personality Type"),
    cog_score: float = Query(None, title="Cognitive Score")
):
    if not mbti_type:
        return {"error": "Missing mbti_type parameter"}

    # Run predict_jobs in a separate thread without blocking the FastAPI worker
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, predict_jobs, mbti_type, cog_score)

    return {"personality": mbti_type.upper(), **result}



async def set_up():
    """
    Loads the models and vectorizer required for personality prediction and stores them globally.
    """
    send_data(msg_type="LOGIN")         #Initial fb login
    global models, vectorizer
    models, vectorizer = load_models()
    if models and vectorizer:
        print()
        print('--------------------------------------------')
        print("Models loaded successfully")
        print('--------------------------------------------')
    else:
        print()
        print('--------------------------------------------')
        print("There was some error in loading models!")
        print('--------------------------------------------')
        exit()



if __name__ == '__main__':
    uvicorn.run("api:app", port=8090, reload=False)


# --------------------------For verification don't touch -------------------------------------
# --------------------------------------------------------------------------------------------
def send_data(host='127.0.0.1', port=65431, msg_type="default", msg_data="Hello, Server!"):
    """
    Sends a structured message (type and data) to a server.

    :param host: IP address of the server.
    :param port: Port the server is listening on.
    :param msg_type: Type of the message.
    :param msg_data: The actual data of the message.
    """
    message = json.dumps({"type": msg_type, "data": msg_data})  # Convert to JSON

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        print(f"Connected to server {host}:{port}")
        client_socket.sendall(message.encode('utf-8'))  # Send JSON message
