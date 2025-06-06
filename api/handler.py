import os
import requests
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # --- Load your secret API keys from Vercel ---
            DUST_API_KEY = os.environ.get('DUST_API_KEY')
            DUST_WID = os.environ.get('DUST_WID')
            DUST_SID = os.environ.get('DUST_SID')
            DUST_API_URL = f"https://dust.tt/api/v1/w/{DUST_WID}/apps/{DUST_SID}/runs"

            # 1. Get the transcript from the ElevenLabs request
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len)
            
            # ElevenLabs sends form-encoded data, so we parse it
            parsed_data = parse_qs(post_body.decode('utf-8'))
            
            # The transcript is in a list, get the first item
            last_transcript = parsed_data.get('user_message', [''])[0]

            if not last_transcript:
                # If there's no message, send a default greeting
                response_text = "Hello, who am I speaking with?"
            else:
                # 2. Call the dust.tt API to get the agent's response
                headers = {
                    "Authorization": f"Bearer {DUST_API_KEY}",
                    "Content-Type": "application/json"
                }
                # Simplified payload - dust.tt uses the agent's saved config
                payload = {
                    "inputs": [{"question": last_transcript}],
                    "blocking": True # Wait for the full response
                }
                
                api_response = requests.post(DUST_API_URL, headers=headers, json=payload)
                api_response.raise_for_status() # Check for API errors
                
                response_data = api_response.json()
                # Extract the final message from the agent's output
                agent_response_text = response_data['run']['results'][0][0]['value']['message']

            # 3. Send the response text back to ElevenLabs
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # ElevenLabs expects a JSON object with a "text" key
            response_payload = json.dumps({"text": agent_response_text})
            self.wfile.write(response_payload.encode('utf-8'))

        except Exception as e:
            # If anything goes wrong, send an error message
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_payload = json.dumps({"text": f"I encountered an error. The error is {str(e)}"})
            self.wfile.write(error_payload.encode('utf-8'))
        return
