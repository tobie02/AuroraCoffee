from flask import Flask, render_template, request, redirect, flash, url_for
from flaskwebgui import FlaskUI
import pandas as pd

from updater import check_for_updates
from calculation import calculate_prices, calculate_graphs

app = Flask(__name__)
ui = FlaskUI(app, idle_interval=None)

app.secret_key = 'Aurora Cafe'

df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
df_ingredients = pd.read_csv('data/ingredients.csv')
df_expenses = pd.read_csv('data/expenses.csv')

ingredients = df_ingredients['Nombre'].to_list()


def get_recipe(product_name):
    product_data = df_products[product_name].dropna().to_dict()
    return product_data


def set_recipe(product_name, recipe):
    df_products.loc[product_name]


def search_by_name(products, name):
    for product in products:
        if product['Producto'] == name:
            return product
    return None    


@app.route("/")
def index():
    '''
    Main Page.
    '''
    df_calculation = calculate_prices()
    products = df_calculation.to_dict(orient='records')

    return render_template('index.html', products=products)


@app.route('/product/<product_name>')
def product(product_name):
    global df_products
    df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
    ingredients = get_recipe(product_name)
    
    df_calculation = calculate_prices()
    products = df_calculation.to_dict(orient='records')
    product = search_by_name(products, product_name)
    
    return render_template('product.html', product=product, ingredients=ingredients)


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


@app.route('/expenses')
def expenses_form():

    df_expenses = pd.read_csv('data/expenses.csv')
    expenses = df_expenses.to_dict(orient='records')

    total = df_expenses['monto'].sum()

    return render_template('expenses.html', expenses=expenses, total=total)


@app.route('/update_expenses', methods=['POST'])
def update_expenses():
    global df_expenses

    tipos = request.form.getlist('tipos[]')
    montos = request.form.getlist('montos[]')

    # Crear un nuevo DataFrame para las expensas actualizadas
    new_data = {
        'expensa': tipos,
        'monto': [float(monto) for monto in montos]
    }
    df_expenses = pd.DataFrame(new_data)

    # Guardar el DataFrame actualizado en el archivo CSV
    df_expenses.to_csv('data/expenses.csv', index=False)
    flash('Expensas actualizadas')
    return redirect(url_for('expenses_form'))


@app.route("/summary")
def summary():
    '''
    Summary Page.
    '''
    calculate_graphs()
    return render_template('summary.html')


@app.route('/settings')
def settings():
    '''
    Settings page.
    '''
    return render_template('settings.html')


if __name__ == "__main__":
    check_for_updates()
    ui.run()

