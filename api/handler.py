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
            
            # FINAL CORRECTION: Using the main dust.tt server address as per support's instruction
            DUST_API_URL = f"https://dust.tt/api/v1/w/{DUST_WID}/assistant/conversations"

            # 1. Get the last message from the ElevenLabs request
            content_len = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_len))
            last_message = ""
            if body.get("messages"):
                last_message = body["messages"][-1].get("content", "")

            if not last_message:
                response_text = "Connection test successful. AI Sales Director is ready."
            else:
                # 2. Call the dust.tt "Assistant" API
                headers = {
                    "Authorization": f"Bearer {DUST_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "title": "Live Voice Call",
                    "visibility": "unlisted",
                    "message": {
                        "content": last_message,
                        "mentions": [{"configurationId": DUST_SID}] 
                    },
                    "blocking": True 
                }
                
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload)
                api_response.raise_for_status()
                
                response_data = api_response.json()
                agent_message_block = response_data['conversation']['content'][-1]
                agent_response_text = agent_message_block[0]['value']['content']

            # 3. Send the complete response back to ElevenLabs
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_payload = { "choices": [{"index": 0, "message": { "role": "assistant", "content": agent_response_text }, "finish_reason": "stop" }] }
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_payload = json.dumps({"error": f"Error interacting with Dust API: {str(e)}"})
            self.wfile.write(error_payload.encode('utf-8'))
        return
