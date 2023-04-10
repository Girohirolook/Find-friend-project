from data.database import create_db, Session
from data.__all_models import *

def create_database():
    create_db()
