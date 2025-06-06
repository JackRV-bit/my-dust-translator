import os
import requests
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

# The class name now includes the required path
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # --- Load your secret API keys from Vercel ---
            DUST_API_KEY = os.environ.get('DUST_API_KEY')
            DUST_WID = os.environ.get('DUST_WID')
            DUST_SID = os.environ.get('DUST_SID')
            DUST_API_URL = f"https://dust.tt/api/v1/w/{DUST_WID}/apps/{DUST_SID}/runs"

            # 1. Get the last message from the ElevenLabs request
            content_len = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_len))
            last_message = ""
            if body.get("messages"):
                last_message = body["messages"][-1].get("content", "")

            if not last_message:
                response_text = "Hello, who am I speaking with?"
            else:
                # 2. Call the dust.tt API to get the agent's response
                headers = {
                    "Authorization": f"Bearer {DUST_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "inputs": [{"question": last_message}],
                    "blocking": True
                }
                
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload)
                api_response.raise_for_status()
                
                response_data = api_response.json()
                agent_response_text = response_data['run']['results'][0][0]['value']['message']

            # 3. Send the response back in the OpenAI-compatible format
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_payload = {
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": agent_response_text
                    },
                    "finish_reason": "stop"
                }]
            }
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_payload = json.dumps({"error": str(e)})
            self.wfile.write(error_payload.encode('utf-8'))
        return

    # This handles the root path and is needed for Vercel to map the directory
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"API is running.")
