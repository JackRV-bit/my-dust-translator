import os
import requests
import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # --- Load your secret API keys from Vercel ---
            DUST_API_KEY = os.environ.get('DUST_API_KEY')
            DUST_WID = os.environ.get('DUST_WID')
            DUST_SID = os.environ.get('DUST_SID')

            # --- DEBUGGING: Print the variables to the Vercel Logs ---
            # This will show us exactly what values the script is using.
            print("--- STARTING DEBUG LOG ---")
            print(f"Workspace ID from Vercel: {DUST_WID}")
            print(f"Agent ID from Vercel: {DUST_SID}")
            # We only print a small part of the key for security.
            if DUST_API_KEY:
                print(f"API Key from Vercel (is present): True, starts with: {DUST_API_KEY[:8]}...")
            else:
                print("API Key from Vercel (is present): False")
            print("--- END DEBUG LOG ---")
            # -----------------------------------------------------------
            
            DUST_API_URL = f"https://eu.dust.tt/api/v1/w/{DUST_WID}/assistant/conversations"

            content_len = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_len))
            last_message = body.get("messages", [{}])[-1].get("content", "")

            if not last_message:
                response_text = "Connection test successful."
            else:
                headers = {
                    "Authorization": f"Bearer {DUST_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "title": "Live Voice Call",
                    "visibility": "unlisted",
                    "message": { "content": last_message, "mentions": [{"configurationId": DUST_SID}] },
                    "blocking": True 
                }
                
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload)
                api_response.raise_for_status()
                
                response_data = api_response.json()
                agent_message_block = response_data['conversation']['content'][-1]
                agent_response_text = agent_message_block[0]['value']['content']

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_payload = { "choices": [{"index": 0, "message": { "role": "assistant", "content": agent_response_text }, "finish_reason": "stop" }] }
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # Also print the exception to the log for more detail
            print(f"An exception occurred: {str(e)}")
            error_payload = json.dumps({"error": f"Error interacting with Dust API: {str(e)}"})
            self.wfile.write(error_payload.encode('utf-8'))
        return
