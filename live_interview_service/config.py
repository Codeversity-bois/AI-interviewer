"""Configuration for the live interview microservice."""

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="interview_manager/.env")
load_dotenv()  # root .env for Astra/Mongo

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
EVAL_MODEL = "gemini-2.5-flash"
VOICE_NAME = "Puck"

# AstraDB
ASTRA_DB_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")
ASTRA_DB_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT", "")
CANDIDATE_COLLECTION = "candidate_profiles"

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB_NAME", "zenith_interviews")

# Interview
MAX_INTERVIEW_DURATION_MINS = 30
