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
url_to_data_map = {}  # Maps URLs to user_name and dp_url and aggregate_details
# Store active WebSocket connections
connections = set()
uid_to_socket_map = {}
url_to_uid_map = {}

class Input(BaseModel): #User's post
    url: str
    text: str
    imgs: List[str]

class Name(BaseModel):  #User's name
    url: str
    name: str
    dp: str

@asynccontextmanager
async def lifespan(app: FastAPI):
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
    print(url_to_uid_map)
    return url in url_to_uid_map

def add_socket_to_uid_map(session_id: str, websocket: WebSocket):
    """
    Add a WebSocket connection to the uid_to_socket_map with the session ID.
    This function is called when a new WebSocket connection is established.
    """
    global uid_to_socket_map
    if session_id not in uid_to_socket_map:
        uid_to_socket_map[session_id] = [websocket]
    else:
        if websocket not in uid_to_socket_map[session_id]:
            uid_to_socket_map[session_id].append(websocket)
        
def remove_socket_from_uid_map(session_id: str, websocket: WebSocket):
    """
    Remove a WebSocket connection from the uid_to_socket_map with the session ID.
    This function is called when a WebSocket connection is closed.
    """
    global uid_to_socket_map
    if session_id in uid_to_socket_map:
        if websocket in uid_to_socket_map[session_id]:
            uid_to_socket_map[session_id].remove(websocket)
        if not uid_to_socket_map[session_id]:  # Remove session ID if no sockets left
            del uid_to_socket_map[session_id]

def get_socket_by_session_id(session_id: str):
    """
    Get the WebSocket connection for a specific session ID.
    Returns None if no WebSocket is found for the session ID.
    """
    global uid_to_socket_map
    return uid_to_socket_map.get(session_id,[])    
     
            
async def subscribe_to_url(url: str, session_id: str):
    """
    Subscribe to a URL with a session ID.
    This function is called when a new profile is received.
    """
    global url_to_uid_map
    if url not in url_to_uid_map:
        url_to_uid_map[url] = [session_id]
    else:
        url_to_uid_map[url].append(session_id)
    print(url_to_uid_map)
    print(f"Subscribed session ID {session_id} to URL {url}")
    if data_exists(url):
        user_data = get_user_data(url)
        websockets = get_socket_by_session_id(session_id)
        for websocket in websockets:
            if websocket:
                try:
                    await websocket.send_text(json.dumps({"type": "user_name","url":url,"name":user_data.get("user_name"),"dp":user_data.get("dp_url")}))
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

def remove_websocket_from_subscriptions(websocket,session_id,from_url):
    """
    Remove a WebSocket connection from all subscriptions.
    This function is called when a WebSocket connection is closed.
    """
    global url_to_uid_map, uid_to_socket_map
    
    if from_url in url_to_uid_map:
        if session_id in url_to_uid_map[from_url]:
            url_to_uid_map[from_url].remove(session_id)
            if not url_to_uid_map[from_url]:
                del url_to_uid_map[from_url]
    
    remove_socket_from_uid_map(session_id, websocket)  # Remove WebSocket from uid_to_socket_map
    if not subscription_exixts(from_url):
        print(f"No subscriptions left for URL {from_url}. Resetting user data and clearing results.")
        send_data(msg_type="STOP SCROLL",msg_data=from_url)
        reset_user_data(from_url)  # Reset user data if no subscriptions left
        clear_result(from_url)  # Clear results if no subscriptions left
        reset_personality_aggregation(from_url)  # Reset personality aggregation if no subscriptions left
    print(url_to_uid_map)
    
def remove_all_subscriptions(session_id):
    global url_to_uid_map
    all_keys = list(url_to_uid_map.keys())
    for url in all_keys:
        if url in url_to_uid_map:
            if session_id in url_to_uid_map[url]:
                url_to_uid_map[url].remove(session_id)
            if not url_to_uid_map[url]:
                del url_to_uid_map[url]
            if not subscription_exixts(url):
                print(f"No subscriptions left for URL {url}. Resetting user data and clearing results.")
                send_data(msg_type="STOP SCROLL",msg_data=url)
                reset_user_data(url)  # Reset user data if no subscriptions left
                clear_result(url)  # Clear results if no subscriptions left
                reset_personality_aggregation(url)  # Reset personality aggregation if no subscriptions left
    print(url_to_uid_map)
    
from starlette.websockets import WebSocketState
import re

async def remove_disconnected_sockets():
    """
    Remove disconnected WebSocket connections from the uid_to_socket_map.
    This function should be scheduled periodically in an async context.
    """
    global uid_to_socket_map
    print("Removing disconnected sockets")
    sessions_to_remove = []
    for session_id, websockets in list(uid_to_socket_map.items()):
        connected_sockets = []
        for ws in websockets:
            if ws.client_state == WebSocketState.CONNECTED:
                connected_sockets.append(ws)
        uid_to_socket_map[session_id] = connected_sockets
        print(f"Session id: {session_id} Connected: {connected_sockets}")
        if not connected_sockets:
            sessions_to_remove.append(session_id)
    print("Remove: ",sessions_to_remove)
    for session_id in sessions_to_remove:
        if unsubscribe(session_id):
            del uid_to_socket_map[session_id]
            remove_all_subscriptions(session_id)

def unsubscribe(session_id):
    """
    Remove one instance of session_id from url_to_uid_map for any url.
    If no sessions left for that url after removal, return True; else False.
    """
    global url_to_uid_map
    for url in list(url_to_uid_map.keys()):
        if session_id in url_to_uid_map[url]:
            url_to_uid_map[url].remove(session_id)
            if not url_to_uid_map[url]:
                return True
    return False
    


def get_subscriptions(url):
    """
    Get all session IDs subscribed to a URL.
    """
    global url_to_uid_map
    return set(url_to_uid_map.get(url, []))

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
        
def normalize_facebook_url(url: str) -> str:
    """
    Normalize Facebook profile URLs to the form 'https://www.facebook.com/{username}'
    """
    # Remove query params/fragments
    url = url.split('?')[0].split('#')[0]
    # Match username part
    match = re.match(r'^https?://(www\.)?facebook\.com/([^/]+)$', url)
    if match:
        username = match.group(2)
        return f"https://www.facebook.com/{username}"
    # Handle 'facebook.com/username' without scheme
    match = re.match(r'^(www\.)?facebook\.com/([^/]+)$', url)
    if match:
        username = match.group(2)
        return f"https://www.facebook.com/{username}"
    # Handle 'https://facebook.com/username' (no www)
    match = re.match(r'^https?://facebook\.com/([^/]+)$', url)
    if match:
        username = match.group(1)
        return f"https://www.facebook.com/{username}"
    return url

def is_valid_facebook_url(url: str) -> bool:
    """
    Validate if the URL is a Facebook profile in the form 'https://www.facebook.com/{username}'
    (does not match homepage or URLs with trailing slash).
    """
    # Accept only URLs with username (no trailing slash, no subpages, not homepage)
    pattern = r'^https://www\.facebook\.com/([A-Za-z0-9.\-_]+)$'
    # Exclude homepage and URLs with trailing slash
    if url in ("https://www.facebook.com", "https://www.facebook.com/"):
        return False
    return re.match(pattern, url) is not None

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
            msg_data = message.get("data",None)
            if msg_type == 'Profile':
                link = msg_data  # Profile URL
                print("New Profile: ", link)

                # Normalize and validate the link
                link = normalize_facebook_url(link)
                if not is_valid_facebook_url(link):
                    await websocket.send_text(json.dumps({"type": "Bad_link", "url": link}))
                    continue
                session_id= message.get("session_id", None)  # Get session ID or create a new one
                if not subscription_exixts(link):
                    send_data(msg_type="PROFILE", msg_data=link)  # Send profile link to the server
                await subscribe_to_url(link, session_id)
                add_socket_to_uid_map(session_id, websocket) 
            
            if msg_type == "session_id":
                session_id = msg_data
                add_socket_to_uid_map(session_id, websocket) 
                
            elif msg_type == 'Stop_analysis':
                session_id = message.get("session_id", None)
                link=normalize_facebook_url(msg_data)
                if session_id:
                    remove_websocket_from_subscriptions(websocket,session_id,link)
                    
            elif msg_type == "Group_subscribe":
                urls = msg_data  # Expecting a list of URLs
                session_id = message.get("session_id", None)
                add_socket_to_uid_map(session_id, websocket)  # Add WebSocket to the uid_to_socket_map
                if isinstance(urls, list):
                    for url in urls:
                        url=normalize_facebook_url(url)
                        if not is_valid_facebook_url(url):
                            await websocket.send_text(json.dumps({"type": "Bad_link", "url": url}))
                            continue
                        
                        if not subscription_exixts(url):
                            send_data(msg_type="PROFILE", msg_data=url)
                        await subscribe_to_url(url, session_id)
            
    except WebSocketDisconnect:
        await remove_disconnected_sockets()  # Clean up disconnected sockets
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
    return response

@app.get("/favicon.ico")
async def favicon():
    icon_path = os.path.join(os.path.dirname(__file__), 'public', 'icon.png')
    return FileResponse(icon_path, media_type="image/png")


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
async def send_name(request: Request):
    try:
        raw_body = await request.body()
        try:
            body = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            print("Error decoding/parsing JSON:", e)
            return {"success": False, "error": "Invalid JSON", "raw_data": raw_body.decode("utf-8")}
        print("Name: ",body.get("name"))
        url = body.get("url")
        name = body.get("name")
        dp_url = body.get("dp")
        if not url or not name or not dp_url:
            return {"success": False, "error": "Missing required fields", "body": body}
        set_user_data(url, name, dp_url)  # Store user data for the URL
        session_ids = get_subscriptions(url)
        # Notify all websockets subscribed to this URL
        for session_id in session_ids:
            websockets = get_socket_by_session_id(session_id)
            for websocket in websockets:
                if websocket:
                    try:
                        await websocket.send_text(json.dumps({"type": "user_name", "name": name, "dp": dp_url, "url": url}))
                    except Exception as e:
                        print(f"Error sending WebSocket message: {e}")
        return {"success": True}
    except Exception as e:
        print("Exception in /send_name:", e)
        return {"success": False, "error": str(e)}

def analyze_and_process(body: dict):
    global Verify, vectorizer, url_to_result_map,url_to_uid_map
    
    url = body.get("url", "NONE")
    post_text = body["text"]
    img_links = body.get("imgs", [])
    if not subscription_exixts(url):
        print(f"URL {url} is not subscribed to. Skipping analysis.")
        print(url_to_uid_map)
        return "Not Subscribed"
    
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

    # print("----- New Post Received -----")
    # print("Post Text:")
    # print(post_text[:100])
    # if whole_image_text:
    #     print("Image OCR Text:")
    #     print(whole_image_text)
    # if expressions:
    #     print("Detected Expression(s):")
    #     for expr in expressions:
    #         print(expr)

    cognitive_score = get_cognitive_score(url)
    print(f"Current Cognitive Score: {cognitive_score:.2f}")
    update_user_data(url, f"{cognitive_score:.2f}")  # Update cognitive score in user data
    current_personality = update_personality_aggregation(combined_text, url, models, vectorizer)
    overall_result = get_aggregated_personality(url)
    print("Overall Personality Result:", overall_result)
    aggregates = get_aggregated_details(url)
    print("Current MBTI Prediction:", current_personality)
    print(f"Current Aggregation Details for: {url}")
    for dichotomy, data in aggregates.items():
        print(f" {dichotomy}:")
        for letter, stats in data.items():
            if isinstance(stats, dict):
                avg = stats['conf_sum'] / stats['count'] if stats['count'] > 0 else 0.0
                print(f"   {letter}: count = {stats['count']}, average confidence = {avg:.2f}")
        print("-" * 50)
    Result=get_result(url)
    if current_personality in Result:
        Result[current_personality] += 1
    else:
        Result[current_personality] = 1

    set_result(url, Result)
    session_ids = get_subscriptions(url)
    for session_id in session_ids:
        websockets = get_socket_by_session_id(session_id)
        for websocket in websockets:
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
