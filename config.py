import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('postgresql://postgres:Ethio#2014@localhost/LearnT')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


