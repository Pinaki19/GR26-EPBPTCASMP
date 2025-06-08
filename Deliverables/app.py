import os
import tempfile
import time
from selenium import webdriver
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  
import time
from selenium.common.exceptions import NoAlertPresentException
import socket
import json
import socket
import threading
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.service import Service 
from selenium.webdriver.edge.options import Options as EdgeOptions 
from webdriver_manager.microsoft import EdgeChromiumDriverManager 


# File to store the path of the driver (so it only installs once)
driver_path_file = 'driver_path.pkl'
EMAIL="atryeedhar23@gmail.com"
PASSWORD="hello25"

STOP=False
driver=None
Logged_in=False
FB_HOMEPAGE=r'https://www.facebook.com/'
Scroll_thread=None

def dismiss_alert_if_present(driver):
    try:
        alert = driver.switch_to.alert  # Switch to alert if present
        alert.dismiss()  # Dismiss the alert
    except NoAlertPresentException:
        pass
    
def setup_edge_with_extension():
   
    edge_options = EdgeOptions() # Changed to EdgeOptions
    prefs = {
        "profile.default_content_setting_values.notifications": 2
    }
    edge_options.add_experimental_option("prefs", prefs)
    
    # Enable extensions and disable file access checks (Chromium-based)
    edge_options.add_argument('--enable-extensions')
    edge_options.add_argument('--disable-extensions-file-access-check')
    
    # Performance/rendering related arguments (Chromium-based)
    edge_options.add_argument('--disable-features=VizDisplayCompositor')
    edge_options.add_argument('--disable-background-timer-throttling')
    edge_options.add_argument('--disable-renderer-backgrounding')
    edge_options.add_argument('--disable-backgrounding-occluded-windows')
    edge_options.add_argument('--force-device-scale-factor=1')
    
    # Automation hiding (Chromium-based)
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    edge_options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')
    
    edge_options.add_argument('--headless=new')
    edge_options.add_argument('--window-size=1920,1080')

    # Extension directory (path remains the same)
    # Use your absolute path directly or resolve dynamically if needed
    current_dir = os.path.dirname(os.path.abspath(__file__))
    extension_directory = os.path.abspath(os.path.join(current_dir, "extension"))
    
    if not os.path.exists(extension_directory):
        raise Exception(f"Extension directory not found: {extension_directory}")

    print(f"Loading extension from: {extension_directory}")
    # Load unpacked extension (same argument as Chrome due to Chromium base)
    edge_options.add_argument(f'--load-extension={extension_directory}')

    return edge_options


def set_up_driver():
    # Create a unique temporary Edge profile for this instance
    temp_profile = tempfile.TemporaryDirectory()
    edge_options = setup_edge_with_extension() # Changed to setup_edge_with_extension
    
    # Override user-data-dir with the temp profile
    edge_options.add_argument(f'--user-data-dir={temp_profile.name}')

    driver_path = get_driver_path()
    driver = webdriver.Edge(service=Service(driver_path), options=edge_options) # Changed to webdriver.Edge
 
    try:
        login(driver) # This call will likely fail if driver is already quit.
        print("Logged in with temporary profile (after browser closed, if login is not using a live driver).")
    except Exception as e:
        print(f"Error during login: {e}")
    return driver, temp_profile


def get_driver_path():
    # Always install a new driver version, ignoring cached value
    # Check if the cached driver path exists and is valid
    if os.path.exists(driver_path_file):
        try:
            with open(driver_path_file, 'rb') as file:
                driver_path = pickle.load(file)
                if os.path.exists(driver_path):  # Make sure the path is valid
                    print(f"Using cached Edge driver: {driver_path}")
                    return driver_path
        except (pickle.UnpicklingError, EOFError, FileNotFoundError):
            print("Cached driver path file is corrupted or empty. Installing new driver.")
            # Fall through to install new driver if file is invalid

    # If no saved driver, or if it's invalid, install it using EdgeChromiumDriverManager and save the path
    print("Installing new Edge driver...")
    driver_path = EdgeChromiumDriverManager().install() # Changed to EdgeChromiumDriverManager
    with open(driver_path_file, 'wb') as file:
        pickle.dump(driver_path, file)
    print(f"New Edge driver installed and cached: {driver_path}")
    return driver_path


def page_has_loaded(driver):
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'


def human_like_typing(element, text):
    """Types text into an input field with human-like delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.2, 0.4))  # Random delay per character

def login(driver):
    global EMAIL,PASSWORD
    email= EMAIL
    driver.get(FB_HOMEPAGE)
    password= PASSWORD
    c = 0
    while c < 120:
        c += 1
        if page_has_loaded(driver):
            break
        time.sleep(0.5)
    
    time.sleep(random.uniform(1, 3))  # Random wait before interacting
    
    email_input = driver.find_element(By.NAME, "email")
    pass_input = driver.find_element(By.NAME, "pass")
    login_button = driver.find_element(By.NAME, "login")  # Updated for button click
    
    # Scroll into view
    driver.execute_script("arguments[0].scrollIntoView();", email_input)
    time.sleep(random.uniform(0.5, 1.5))
    
    # Click on email field first before typing
    ActionChains(driver).move_to_element(email_input).click().perform()
    human_like_typing(email_input, email)
    time.sleep(random.uniform(0.7, 1.5))  # Short pause between field entries
    # Click on password field before typing
    ActionChains(driver).move_to_element(pass_input).click().perform()
    human_like_typing(pass_input, password)
    time.sleep(random.uniform(0.5, 2))  # Short pause before submission
    # Click login button instead of pressing Enter
    ActionChains(driver).move_to_element(login_button).click().perform()

    time.sleep(random.uniform(3, 5))  # Allow time for login process


def scroll_profile(profile_link):
    driver, temp_profile = set_up_driver()
    try:
        print("Scrolling profile:", profile_link)
        driver.get(profile_link)
        script = """
        Object.defineProperty(document, 'hidden', {value: false});
        Object.defineProperty(document, 'visibilityState', {value: 'visible'});
        setInterval(() => {document.dispatchEvent(new Event('visibilitychange'));}, 2000);
        """
        driver.execute_script(script)
        # Time to wait for the page to load completely
        time.sleep(3)
        SCROLL_PAUSE_TIME = 1

        # Get scroll height
        last_height=0
        while last_height==0:
            dismiss_alert_if_present(driver)
            last_height = driver.execute_script("return document.body.scrollHeight")
        height=min(100,last_height)
        lim=500
        cur=0
        same_height_count=0
        while cur<lim and not STOP and height<20000:
            cur+=1
            dismiss_alert_if_present(driver)
            # Scroll down to bottom
            print(f"window.scrollTo(0, {height});")
            driver.execute_script(f"window.scrollTo(0, {height});")
            # dummy user interaction to force render
            driver.execute_script("window.dispatchEvent(new Event('scroll'));")
            driver.execute_script("document.body.style.zoom='1.05'")  # Small zoom to force re-render
            driver.execute_script("document.body.style.zoom='1.0'")  # Reset
            height=min(height+400,last_height)

            time.sleep(SCROLL_PAUSE_TIME)
            # Calculate new scroll height and compare with last scroll height
            last_height = driver.execute_script("return document.body.scrollHeight")
            if(height==last_height):
                same_height_count+=1
                if same_height_count>5:
                    print("Reached end of profile or no new content loaded.")
                    break
            else:
                same_height_count=0
    except Exception as e:
        print(f"Error while scrolling profile {profile_link}: {e}")
    finally:
        print("Exiting driver..")
        driver.quit()
        temp_profile.cleanup()  # Deletes the temporary profile directory


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

from __init__ import set_dir
set_dir()

url_to_thread_map={}

def start_server(host='127.0.0.1', port=65431):
    """
    Starts a server that listens for incoming connections and receives data.

    :param host: IP address to bind the server to (default is localhost).
    :param port: Port to bind the server to.
    
    """
    global Logged_in,driver,STOP,Scroll_thread
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server listening on {host}:{port}...")
        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024)  # Receive up to 1024 bytes
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))  # Parse JSON
                print(f"Received Type: {message['type']}, Data: {message['data']}")
                if message['type'] == "FINAL STOP":
                    print("Stop message received. Shutting down the server.")
                    conn.sendall(b"Server stopping.")  # Send acknowledgment
                    driver.quit()
                    break
                elif message['type']=="PROFILE":
                    STOP=False
                    link=message['data']
                    print("New profile: ",link)
                    Scroll_thread=StoppableThread(target=scroll_profile,args=(link,))
                    url_to_thread_map[link]=Scroll_thread
                    url_to_thread_map[link].start()
                    
                elif message['type']=="STOP SCROLL":
                    STOP=True
                    print("STOP resquested...")
                    thread=url_to_thread_map.get(message['data'])
                    if thread and thread.is_alive():
                        print("Stopping scroll thread for:", message['data'])
                        thread.stop()
                else:
                    pass
                
if __name__=='__main__':
    start_server()