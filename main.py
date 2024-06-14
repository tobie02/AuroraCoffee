from flask import Flask, render_template, request, redirect, flash, url_for
from flaskwebgui import FlaskUI
import pandas as pd

from updater import check_for_updates
from calculation import calculation

app = Flask(__name__)
ui = FlaskUI(app, idle_interval=None)

app.secret_key = 'Aurora Cafe'

df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
df_ingredients = pd.read_csv('data/ingredients.csv')

ingredients = df_ingredients['Nombre'].to_list()


def get_recipe(product_name):
    product_data = df_products[product_name].dropna().to_dict()
    return product_data


def set_recipe(product_name, recipe):
    df_products.loc[product_name]


@app.route("/")
def index():
    '''
    Main Page.
    '''
    return render_template('index.html', products=df_products.columns.to_list())


@app.route('/product/<product_name>')
def product(product_name):
    global df_products
    df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
    ingredients = get_recipe(product_name)
    return render_template('product.html', product=product_name, ingredients=ingredients)


@app.route('/update_ingredients', methods=['POST'])
def update_ingredients():
    product_name = request.form['product_name']
    ingredients = request.form.getlist('ingredients[]')
    quantities = request.form.getlist('quantities[]')

    new_recipe = {ingredient: float(quantity) for ingredient, quantity in zip(ingredients, quantities)}

    for ingredient, quantity in new_recipe.items():
        df_products.at[ingredient, product_name] = quantity

    for ingredient in df_products.index:
        if ingredient not in new_recipe:
            df_products.at[ingredient, product_name] = None

    df_products.to_csv('data/recipes.csv')

    flash('Receta actualizada')
    return redirect(url_for('product', product_name=product_name))


@app.route('/ingredients')
def ingredients_form():
    ingredients = df_ingredients.to_dict(orient='records')
    return render_template('ingredients.html', ingredients=ingredients)

@app.route('/update_prices', methods=['POST'])
def update_prices():
    global df_ingredients

    nombres = request.form.getlist('nombres[]')
    precios = request.form.getlist('precios[]')
    unidades = request.form.getlist('unidades[]')

    # Crear un nuevo DataFrame para los ingredientes actualizados
    new_data = {
        'Nombre': nombres,
        'Precio': [float(precio) for precio in precios],
        'Unidad': unidades
    }
    df_ingredients = pd.DataFrame(new_data)

    # Guardar el DataFrame actualizado en el archivo CSV
    df_ingredients.to_csv('data/ingredients.csv', index=False)
    flash('Precios y unidades actualizados')
    return redirect(url_for('ingredients_form'))

@app.route("/summary")
def summary():
    '''
    Summary Page.
    '''
    df_calculation = calculation()
    products = df_calculation.to_dict(orient='records')
    return render_template('summary.html', products=products)

@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == "__main__":
    check_for_updates()
    ui.run()

