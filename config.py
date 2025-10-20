import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('VITE_SUPABASE_ANON_KEY')
