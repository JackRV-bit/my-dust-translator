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

            # This will be built up as the agent streams its response
            agent_response_text = ""

            if last_message:
                headers = {
                    "Authorization": f"Bearer {DUST_API_KEY}",
                    "Content-Type": "application/json"
                }
                # --- FINAL OPTIMIZATION ---
                # We will now explicitly ask for a non-blocking stream.
                # This is the fastest way to get the first tokens back.
                payload = {
                    "message": {
                        "content": last_message,
                        "mentions": [{"configurationId": DUST_SID}],
                        "context": { "timezone": "Europe/London", "username": "Jack-Voice-Call", "origin": "api" }
                    },
                    "blocking": False, # Changed to False
                    "stream": True     # Explicitly request streaming
                }
                
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload, stream=True)
                api_response.raise_for_status()
                
                # Listen for the individual pieces of the agent's message as they are generated
                for line in api_response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').lstrip('data: ')
                        if not line_str or "[DONE]" in line_str:
                            continue
                        
                        try:
                            event_data = json.loads(line_str)
                            # The newest API version uses 'agent_message_chunk' for streaming text
                            if event_data.get('type') == 'agent_message_chunk':
                                agent_response_text += event_data.get('text', '')
                        except json.JSONDecodeError:
                            continue # Ignore lines that aren't valid JSON
            else:
                agent_response_text = "Connection test successful. AI Sales Director is ready."

            # If the process timed out before we got any text
            if not agent_response_text:
                agent_response_text = "I received the message, but my thought process was interrupted. Could you ask again?"

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
