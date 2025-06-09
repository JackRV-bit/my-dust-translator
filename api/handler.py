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
            
            DUST_API_URL = f"https://dust.tt/api/v1/w/{DUST_WID}/assistant/conversations"

            # 1. Get the last message from the ElevenLabs request
            content_len = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_len))
            last_message = body.get("messages", [{}])[-1].get("content", "")

            agent_response_text = "No response generated."

            if last_message:
                # 2. Call the dust.tt API
                headers = {
                    "Authorization": f"Bearer {DUST_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "message": {
                        "content": last_message,
                        "mentions": [{"configurationId": DUST_SID}],
                        "context": {
                            "timezone": "Europe/London",
                            "username": "Jack-Voice-Call",
                            "origin": "api"
                        }
                    },
                    "blocking": True 
                }
                
                # Make the request with streaming enabled
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload, stream=True)
                api_response.raise_for_status()
                
                # --- FINAL CORRECTED LOGIC: Read the event stream ---
                # Iterate through each line of the response to find the agent's message.
                for line in api_response.iter_lines():
                    if line:
                        # The stream sends lines like "data: { ... }", we need to clean that up
                        line_str = line.decode('utf-8').lstrip('data: ')
                        if line_str and '"type":"agent_message"' in line_str:
                            try:
                                # Parse the line as JSON and extract the content
                                event_data = json.loads(line_str)
                                agent_response_text = event_data.get('message', {}).get('content', '')
                                break # Stop after finding the first agent message
                            except json.JSONDecodeError:
                                continue # Ignore lines that aren't valid JSON
            else:
                agent_response_text = "Connection test successful. AI Sales Director is ready."

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
            print(f"An exception occurred: {str(e)}")
            error_payload = json.dumps({"error": f"Error interacting with Dust API: {str(e)}"})
            self.wfile.write(error_payload.encode('utf-8'))
        return
