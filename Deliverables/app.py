import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # Import Keys class for special keys like Enter
import time
from selenium.common.exceptions import NoAlertPresentException
import socket
import json
import socket
import threading
import random
from selenium.webdriver.common.action_chains import ActionChains

# File to store the path of the driver (so it only installs once)
driver_path_file = 'driver_path.pkl'
EMAIL="8334999569"
PASSWORD="myfbaccount2024"

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
def setup_chrome_with_extension():
    global driver, EMAIL, PASSWORD, Logged_in

    chrome_options = webdriver.ChromeOptions()

    prefs = {
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--enable-extensions')
    chrome_options.add_argument('--disable-extensions-file-access-check')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--force-device-scale-factor=1')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--window-size=1920,1080')

    # Extension directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    extension_directory = os.path.abspath(os.path.join(current_dir, "extension"))
    print(f"Loading extension from: {extension_directory}")
    chrome_options.add_argument(f'--load-extension={extension_directory}')

    # Persistent Chrome profile
    user_data_dir = os.path.abspath("chrome_profile")
    chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

    return chrome_options


def set_up_driver():
    global driver, FB_HOMEPAGE, Logged_in

    user_data_dir = os.path.abspath("chrome_profile")
    first_time = not os.path.exists(user_data_dir)

    chrome_options = setup_chrome_with_extension()
    driver_path = get_driver_path()

    driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    driver.get(FB_HOMEPAGE)

    # If first-time, perform login
    if first_time:
        try:
            login()  
            print("Logged in and Chrome profile created.")
            Logged_in = True
        except Exception as e:
            print(f"Error during login: {e}")
    else:
        print("Using existing Chrome profile.")
        Logged_in = True


def get_driver_path():
    # Always install a new driver version, ignoring cached value
    if os.path.exists(driver_path_file):
        with open(driver_path_file, 'rb') as file:
            driver_path = pickle.load(file)
            if os.path.exists(driver_path):  # Make sure the path is valid
                return driver_path
    # If no saved driver, install it using ChromeDriverManager and save the path
    driver_path = ChromeDriverManager().install()
    with open(driver_path_file, 'wb') as file:
        pickle.dump(driver_path, file)
    return driver_path

def page_has_loaded(driver):
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'


def human_like_typing(element, text):
    """Types text into an input field with human-like delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.2, 0.4))  # Random delay per character

def login():
    global driver,EMAIL,PASSWORD,Logged_in
    email= EMAIL
    password= PASSWORD
    if Logged_in:
        return
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


        

# Function to scroll through a user profile
def scroll_profile(profile_link):
    global STOP,driver
    # Get or install the Chrome driver path
    # Open the profile link
    driver.execute_script("window.open('');") 
    # Switch to the new window and open new URL 
    driver.switch_to.window(driver.window_handles[1]) 
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
    while cur<lim and not STOP:
        cur+=1
        dismiss_alert_if_present(driver)
        # Scroll down to bottom
        print(f"window.scrollTo(0, {height});")
        driver.execute_script(f"window.scrollTo(0, {height});")
        # dummy user interaction to force render
        driver.execute_script("window.dispatchEvent(new Event('scroll'));")
        driver.execute_script("document.body.style.zoom='1.01'")  # Small zoom to force re-render
        driver.execute_script("document.body.style.zoom='1.0'")  # Reset
        height=min(height+400,last_height)
        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        last_height = new_height
    driver.close()
    driver.switch_to.window(driver.window_handles[0]) 



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

#--------------------------For verification dont touch -------------------------------------
#-------------------------------------------------------------------------------------------
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
                    #scroll_profile(link)
                    Scroll_thread=StoppableThread(target=scroll_profile,args=(link,))
                    Scroll_thread.start()
                elif message['type']=="STOP SCROLL":
                    STOP=True
                    print("STOP resquested...")
                    Scroll_thread.stop()
                elif message['type']=='LOGIN':
                    if Logged_in:
                        return
                    set_up_driver()
                else:
                    pass
                
if __name__=='__main__':
    start_server()