import time
import sys
import os

# Fix Unicode encoding on Windows
os.environ["PYTHONIOENCODING"] = "utf-8"

from pyngrok import ngrok

def start():
    print("Starting ngrok tunnel on port 3003...", flush=True)
    try:
        public_url = ngrok.connect(3003).public_url
        print("")
        print("==================================================")
        print("LINK NGROK: " + public_url)
        print("==================================================")
        print("", flush=True)
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing ngrok tunnel")
    except Exception as e:
        print("Error starting ngrok: " + str(e))

if __name__ == "__main__":
    start()
