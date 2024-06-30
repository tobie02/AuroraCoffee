import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'Aurora Coffee')
    UPLOAD_FOLDER = os.path.join(os.path.abspath("."), 'static/media/products')
