from flask import Flask
from flaskwebgui import FlaskUI
import os
import sys
import pandas as pd
import pdfkit

from app.routes import setup_routes
from app.updater import check_for_updates

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(".")

def create_app():
    app = Flask(__name__, static_folder=os.path.join(get_base_path(), 'static'), template_folder=os.path.join(get_base_path(), 'templates'))
    
    app.secret_key = 'Aurora Coffee'
    app.config['UPLOAD_FOLDER'] = os.path.join(get_base_path(), 'static/media/products')
    
    # Cargar datos
    app.config['df_products'] = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
    app.config['df_ingredients'] = pd.read_csv('data/ingredients.csv')
    app.config['df_expenses'] = pd.read_csv('data/expenses.csv')
    app.config['df_menu'] = pd.read_csv('data/menu.csv')
    app.config['settings_df'] = pd.read_csv('data/settings.csv', index_col='setting')
    
    setup_routes(app, get_base_path())
    
    return app

def main():
    check_for_updates()
    app = create_app()
    ui = FlaskUI(app, idle_interval=None)
    ui.run()

if __name__ == "__main__":
    main()
