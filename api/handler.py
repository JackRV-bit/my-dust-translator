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
            last_message = ""
            if body.get("messages"):
                last_message = body["messages"][-1].get("content", "")

            # This is a temporary response for the debugging step
            agent_response_text = "Debugging... Check Vercel Logs."
            
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
                
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload)
                api_response.raise_for_status()
                
                response_data = api_response.json()

                # --- NEW DEBUGGING STEP ---
                # This will print the full, detailed response from Dust.tt into the Vercel logs
                print("--- START DUST.TT API RESPONSE ---")
                print(json.dumps(response_data, indent=2))
                print("--- END DUST.TT API RESPONSE ---")
                # -----------------------------

                # This old logic will now be skipped, but the log will tell us what the new logic should be.
                # We will fix the parsing in the next step.
                agent_message_block = response_data['conversation']['content'][-1]
                # Check if the message is from the agent
                if agent_message_block[0]['type'] == 'agent_message':
                    agent_response_text = agent_message_block[0]['content']
                else: # Fallback for now
                    agent_response_text = "Response received, but format is unexpected."


            # 3. Send the response back to ElevenLabs
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
