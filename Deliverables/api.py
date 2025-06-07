'''
Make sure to run this server on port 8090 or
change the url path on the background.js script
'''
from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Query,Response,Cookie,Query, BackgroundTasks,Request
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
from fastapi.responses import RedirectResponse
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
url_to_result_map = {}  # Maps URLs to results
Verify =False       #Was used to validate results, not used for now
url_to_data_map = {}  # Maps URLs to user_name and dp_url and aggregate_details

class Input(BaseModel): #User's post
    url: str
    text: str
    imgs: List[str]

class Name(BaseModel):  #User's name
    url: str
    name: str
    dp:str
    
class Profiles(BaseModel):   #web service sends list of profiles
    url:List[str]


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

def set_user_data(url: str, user_name: str, dp_url: str):
    """
    Set user data for a specific URL.
    This function is called when the user name and profile picture URL are received.
    """
    global url_to_data_map
    if url not in url_to_data_map:
        url_to_data_map[url] = {"user_name": user_name, "dp_url": dp_url,"cognitive_score": "0.00"}
        
def get_user_data(url: str):
    """
    Get user data for a specific URL.
    Returns a dictionary with user_name and dp_url.
    """
    global url_to_data_map
    return url_to_data_map.get(url, {"user_name": "", "dp_url": ""})

def update_user_data(url: str, cognitive_score: str):
    """
    Update user data for a specific URL with cognitive score.
    This function is called when the cognitive score is updated.
    """
    if not subscription_exixts(url):
        return
    global url_to_data_map
    if url in url_to_data_map:
        url_to_data_map[url]["cognitive_score"] = cognitive_score
    else:
        url_to_data_map[url] = {"user_name": "", "dp_url": "", "cognitive_score": cognitive_score}

def reset_user_data(url: str):
    """
    Reset user data for a specific URL.
    This function is called when the analysis is stopped.
    """
    global url_to_data_map
    if url in url_to_data_map:
        del url_to_data_map[url]

def data_exists(url: str):
    """
    Check if user data exists for a specific URL.
    Returns True if user data exists, otherwise False.
    """
    global url_to_data_map
    return url in url_to_data_map and bool(url_to_data_map[url])

def subscription_exixts(url):
    """
    Check if a URL is already subscribed to by any session.
    """
    global url_to_uid_map
    return url in url_to_uid_map and bool(url_to_uid_map[url])

async def subscribe_to_url(url: str, session_id: str):
    """
    Subscribe to a URL with a session ID.
    This function is called when a new profile is received.
    """
    if url not in url_to_uid_map:
        url_to_uid_map[url] = [session_id]
    else:
        if session_id not in url_to_uid_map[url]:
            url_to_uid_map[url].append(session_id)
    print(f"Subscribed session ID {session_id} to URL {url}")
    if data_exists(url):
        user_data = get_user_data(url)
        if session_id in uid_to_socket_map:
            websocket = uid_to_socket_map.get(session_id,None)
        if websocket:
            try:
                await websocket.send_text(json.dumps({"type": "user_name", "name":user_data.get("user_name"),"dp":user_data.get("dp_url")}))
                if result_exists(url):
                    result = get_result(url)
                    aggregates = get_aggregated_details(url)
                    cognitive_score = user_data.get("cognitive_score", "0.00")
                    await websocket.send_text(json.dumps({
                        "type": "update",
                        "url": url,
                        "cog_score": cognitive_score,
                        "result": result,
                        "aggregate": aggregates
                    }))
            except Exception as e:
                print(f"Error sending WebSocket message: {e}")      
        
def unsubscribe_from_url(session_id: str,url=None) -> bool:    # returns wheather all sessions are unsubscribed or not
    """
    Unsubscribe from a URL with a session ID.
    This function is called when the analysis is stopped.
    """
    if not url:
        print('Trying to unsubscribe from all URLs for session ID:', session_id)
        print(url_to_uid_map)
        # If no URL is provided, unsubscribe from all URLs for this session ID
        for url in list(url_to_uid_map.keys()):
            if session_id in url_to_uid_map[url]:
                url_to_uid_map[url].remove(session_id)
                if not url_to_uid_map[url]:  # Remove URL if no sessions are left
                    del url_to_uid_map[url]
                    clear_result(url)
                    reset_user_data(url)  # Reset user data for this URL
                    reset_personality_aggregation(url)
                    send_data(msg_type='STOP SCROLL',msg_data=url)
            return False
    else:
        if url in url_to_uid_map and session_id in url_to_uid_map[url]:
            url_to_uid_map[url].remove(session_id)
            if not url_to_uid_map[url]:  # Remove URL if no sessions are left
                del url_to_uid_map[url]
                clear_result(url)  # Clear results for this URL
                reset_user_data(url)  # Reset user data for this URL
                return True  # All sessions unsubscribed
        else:
            print(f"Session ID {session_id} not found for URL {url}. No action taken.")
            
        return False  # Not all sessions unsubscribed
            
def get_subscriptions(url):
    """
    Get all session IDs subscribed to a URL.
    """
    global url_to_uid_map
    return url_to_uid_map.get(url, [])

def get_result(url):
    """
    Get the result for a specific URL.
    """
    global url_to_result_map
    return url_to_result_map.get(url, {})
def result_exists(url):
    """
    Check if results exist for a specific URL.
    Returns True if results exist, otherwise False.
    """
    global url_to_result_map
    return url in url_to_result_map and bool(url_to_result_map[url])

def set_result(url, result):
    """
    Set the result for a specific URL.
    """
    if not subscription_exixts(url):
        return
    global url_to_result_map
    if url not in url_to_result_map:
        url_to_result_map[url] = {}
    url_to_result_map[url].update(result)

def clear_result(url):
    """
    Clear the result for a specific URL.
    """
    global url_to_result_map
    if url in url_to_result_map:
        del url_to_result_map[url]
        
        

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket endpoint for real-time communication with frontend """
    await websocket.accept()
    global url_to_result_map, uid_to_socket_map
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")
            msg_data = message.get("data")
            if msg_type == 'Profile':
                link = msg_data  # Profile URL
                print("New Profile: ", link)
                session_id= message.get("session_id", None)  # Get session ID or create a new one
                if not subscription_exixts(link):
                    send_data(msg_type="PROFILE", msg_data=link)  # Send profile link to the server
                await subscribe_to_url(link, session_id)
            if msg_type == "session_id":
                session_id = msg_data
                uid_to_socket_map[session_id] = websocket  # Map session ID to WebSocket
                
            elif msg_type == 'Stop_analysis':
                if unsubscribe_from_url( message.get("session_id", None),msg_data):
                    reset_personality_aggregation(msg_data)
                    send_data(msg_type='STOP SCROLL',msg_data=msg_data)

    except WebSocketDisconnect:
        # Remove the disconnected WebSocket from the mapping
        for uid, ws in list(uid_to_socket_map.items()):
            if ws == websocket:
                unsubscribe_from_url(uid)  # Unsubscribe from all URLs for this session ID
                del uid_to_socket_map[uid]
        print("WebSocket Disconnected")
        
        
@app.get("/")
async def serve_main(session_id: str = Cookie(default=None)):
    main_file_path = os.path.join(os.path.dirname(__file__), 'public', 'html', 'index.html')
    response = FileResponse(main_file_path, media_type="text/html")
    
    if session_id is None:
        new_session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=new_session_id, httponly=False, samesite="lax")
        print(f"New session ID set: {new_session_id}")
    else:
        print(f"Existing session ID: {session_id}")
        unsubscribe_from_url(session_id)  # Unsubscribe from all URLs for this session ID
    return response


@app.get("/analyze_candidates")
async def analyze_candidates(
    request: Request,
    count: int = Query(..., title="Number of URLs")
):
    """
    Serves the candidate analysis page and provides the list of URLs as query parameters.
    """
    # Extract all url{index} parameters from the query string
    urls = []
    for i in range(count):
        url_key = f"url{i}"
        url_val = request.query_params.get(url_key)
        if url_val:
            urls.append(url_val)
    print("Analyzing candidates for URLs:", urls)
    file_path = os.path.join(os.path.dirname(__file__), 'public', 'html', 'results.html')
    response = FileResponse(file_path, media_type="text/html")
    return response
    
@app.get("/analyze_individual")
async def analyze_individual(url: str = Query(..., title="Profile URL"),session_id: str = Cookie(default=None)):
    """
    Analyzes a single profile URL and returns the results.
    This endpoint is called when the user clicks on a single profile URL.
    """
    file_path = os.path.join(os.path.dirname(__file__), 'public', 'html', 'main.html')
    # Append the url as a query parameter to the response
    response = FileResponse(file_path, media_type="text/html")
    return response
    

@app.post("/send_name")
async def get_user_name(body: Name):
    """
    Receives and processes the user's name.
    """
    name = body.name
    session_ids = get_subscriptions(body.url)
    #name = " ".join(name.split(" ")[:2])
    url = body.url
    print("User:", name, "Url:", url)
    dp_url=body.dp
    set_user_data(url, name, dp_url)  # Store user data for the URL
    # Check if any WebSocket connection exists for this URL
    for session_id in session_ids:
        websocket = uid_to_socket_map.get(session_id,None)
        if websocket:
            try:
                await websocket.send_text(json.dumps({"type": "user_name", "name":name,"dp":dp_url}))
            except Exception as e:
                print(f"Error sending WebSocket message: {e}")

    return {"success": True}

def analyze_and_process(body: dict):
    global Verify, vectorizer, url_to_result_map
    
    url = body.get("url", "NONE")
    post_text = body["text"]
    img_links = body.get("imgs", [])
    if not subscription_exixts(url):
        print(f"URL {url} is not subscribed to. Skipping analysis.")
        return "Not Subscribed"
    session_ids = get_subscriptions(url)
    Result=get_result(url)
    
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

    cognitive_score = get_cognitive_score(url)
    print(f"Current Cognitive Score: {cognitive_score:.2f}")
    update_user_data(url, f"{cognitive_score:.2f}")  # Update cognitive score in user data
    current_personality = update_personality_aggregation(combined_text, url, models, vectorizer)
    overall_result = get_aggregated_personality(url)
    print("Overall Personality Result:", overall_result)
    aggregates = get_aggregated_details(url)
    print("Current MBTI Prediction:", current_personality)
    # print("Current Aggregation Details:")
    # for dichotomy, data in aggregates.items():
    #     print(f" {dichotomy}:")
    #     for letter, stats in data.items():
    #         if isinstance(stats, dict):
    #             avg = stats['conf_sum'] / stats['count'] if stats['count'] > 0 else 0.0
    #             print(f"   {letter}: count = {stats['count']}, average confidence = {avg:.2f}")
    #     print("-" * 50)

    if current_personality in Result:
        Result[current_personality] += 1
    else:
        Result[current_personality] = 1

    set_result(url, Result)
   
    for session_id in session_ids:
        websocket = uid_to_socket_map.get(session_id,None)
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
