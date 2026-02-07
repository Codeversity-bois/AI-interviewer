import websocket
import json
import base64
import threading
import time
from typing import Callable, Optional

class GeminiLiveSession:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None
        self.is_connected = False
        self.message_handler = None
        self.setup_complete = False
        
    def connect(self, on_message: Optional[Callable] = None):
        """Connect to Gemini Live API WebSocket"""
        # websocket_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={self.api_key}"
        websocket_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=AIzaSyDSGabNEnUZjxH-my3jY9qiDkB-C8hlkEU"
        self.message_handler = on_message
        
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            websocket_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        # Start WebSocket in separate thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection
        while not self.is_connected:
            time.sleep(0.1)
            
    def send_setup(self, resume_context: str = ""):
        """Send initial configuration with interview context"""
        setup_message = {
            "setup": {
                "model": "models/gemini-2.5-flash",
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                    "responseModalities": ["TEXT", "AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": "Puck"
                            }
                        }
                    }
                },
                "systemInstruction": {
                    "parts": [{
                        "text": f"""You are an AI interviewer for zentervyu. Conduct professional interviews based on the candidate's resume. 
                        
                        Resume context: {resume_context}
                        
                        Guidelines:
                        - Ask relevant questions about their experience and skills
                        - Be conversational and professional
                        - Follow up on interesting points
                        - Keep questions focused and clear
                        - Transition smoothly between topics"""
                    }]
                }
            }
        }
        
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(setup_message))
            
    def send_audio(self, audio_data: bytes):
        """Send real-time audio to API"""
        # Convert audio to base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "realtimeInput": {
                "mediaChunks": [{
                    "mimeType": "audio/pcm;rate=16000",
                    "data": audio_b64
                }]
            }
        }
        
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(message))
            
    def send_text(self, text: str):
        """Send text message to API"""
        message = {
            "clientContent": {
                "turns": [{
                    "role": "user",
                    "parts": [{
                        "text": text
                    }]
                }],
                "turnComplete": True
            }
        }
        
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(message))
            
    def send_realtime_text(self, text: str):
        """Send real-time text input"""
        message = {
            "realtimeInput": {
                "mediaChunks": [{
                    "mimeType": "text/plain",
                    "data": base64.b64encode(text.encode()).decode()
                }]
            }
        }
        
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(message))
    
    def interrupt_model(self):
        """Interrupt the model if it's currently speaking"""
        message = {
            "clientContent": {
                "turns": [],
                "turnComplete": False
            }
        }
        
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(message))
    
    def _on_open(self, ws):
        """Called when WebSocket connection opens"""
        print("Connected to Gemini Live API")
        self.is_connected = True
        
    def _on_message(self, ws, message):
        """Handle incoming messages from Gemini API"""
        try:
            data = json.loads(message)
            
            # Check if setup is complete
            if "setupComplete" in data:
                self.setup_complete = True
                print("Setup complete - ready for conversation")
                
            # Handle server content (AI responses)
            if "serverContent" in data:
                server_content = data["serverContent"]
                
                # Text response
                if "modelTurn" in server_content:
                    model_turn = server_content["modelTurn"]
                    if "parts" in model_turn:
                        for part in model_turn["parts"]:
                            if "text" in part:
                                text_response = part["text"]
                                if self.message_handler:
                                    self.message_handler("text", text_response)
                
                # Audio response
                if "audio" in server_content:
                    audio_data = server_content["audio"]
                    if self.message_handler:
                        self.message_handler("audio", audio_data)
                
                # Turn complete
                if server_content.get("turnComplete", False):
                    if self.message_handler:
                        self.message_handler("turn_complete", True)
            
            # Handle tool calls (if any)
            if "toolCall" in data:
                tool_call = data["toolCall"]
                if self.message_handler:
                    self.message_handler("tool_call", tool_call)
                    
        except json.JSONDecodeError as e:
            print(f"Error parsing message: {e}")
            
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print("WebSocket connection closed")
        self.is_connected = False
        
    def close(self):
        """Close the WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.is_connected = False


trying = GeminiLiveSession("AIzaSyDSGabNEnUZjxH-my3jY9qiDkB-C8hlkEU")
trying.connect()
trying.send_setup(resume_context="Highly proficient in python, c++, java")
