from flask import Flask, render_template, request, redirect, flash, url_for
from flaskwebgui import FlaskUI
from werkzeug.utils import secure_filename
import pandas as pd
from PIL import Image
import os
import sys

from updater import check_for_updates
from calculation import calculate_prices, calculate_graphs

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(".")

UPLOAD_FOLDER = os.path.join(get_base_path(), 'static/media/products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, static_folder=os.path.join(get_base_path(), 'static'), template_folder=os.path.join(get_base_path(), 'templates'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


@app.route('/add_product', methods=['POST'])
def add_product():
    product_name = request.form['product_name'].strip()
    if product_name:
        if product_name not in df_products.columns:
            # Guardar la imagen del producto si se proporcionó
            if 'product_image' in request.files:
                product_image = request.files['product_image']
                if product_image.filename != '':
                    if allowed_file(product_image.filename):
                        # Convertir PNG a JPG si es necesario
                        if product_image.filename.lower().endswith('.png'):
                            img = Image.open(product_image)
                            rgb_img = img.convert('RGB')
                            product_image = rgb_img

                        # Crear un nombre de archivo seguro usando el nombre del producto y la extensión jpg
                        filename = secure_filename(product_name + '.jpg')
                        product_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    else:
                        flash('Formato de imagen no válido. Use solamente: jpg, jpeg')
                        return redirect(url_for('index'))

            df_products[product_name] = None
            df_products.to_csv('data/recipes.csv')
            flash('Producto añadido exitosamente')
        else:
            flash('El producto ya existe')
    else:
        flash('Ingrese un nombre válido para el producto')

    return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/delete_product/<product_name>', methods=['GET', 'POST'])
def delete_product(product_name):
    global df_products

    if request.method == 'POST':
        # Eliminar el producto del DataFrame y guardar el CSV actualizado
        if product_name in df_products.columns:
            # Eliminar la imagen asociada al producto
            delete_product_image(product_name)

            df_products.drop(columns=[product_name], inplace=True)
            df_products.to_csv('data/recipes.csv')
            flash(f'Producto "{product_name}" eliminado correctamente')
            return redirect(url_for('index'))
        else:
            flash(f'Error: El producto "{product_name}" no existe')
            return redirect(url_for('index'))

    # Si es un GET, mostrar confirmación de eliminación
    return render_template('confirm_delete_product.html', product_name=product_name)

def delete_product_image(product_name):
    filename = secure_filename(product_name + '.jpg')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'Imagen del producto "{product_name}" eliminada correctamente')
    else:
        flash(f'La imagen del producto "{product_name}" no existe')


@app.route('/update_product', methods=['POST'])
def update_product():
    global df_products
    product_name = request.form['product_name']
    new_product_name = request.form['new_product_name']
    ingredients = request.form.getlist('ingredients[]')
    quantities = request.form.getlist('quantities[]')

    # Actualizar el nombre del producto en el DataFrame si ha cambiado
    if new_product_name and new_product_name != product_name:
        if product_name in df_products.columns:
            df_products.rename(columns={product_name: new_product_name}, inplace=True)
            # También renombrar la imagen si existe
            rename_product_image(product_name, new_product_name)
        else:
            flash(f'Error: El producto "{product_name}" no existe en la base de datos')

    # Actualizar las cantidades de ingredientes en el DataFrame
    new_recipe = {ingredient: float(quantity) for ingredient, quantity in zip(ingredients, quantities)}
    for ingredient, quantity in new_recipe.items():
        df_products.at[ingredient, new_product_name] = quantity

    # Establecer como None las cantidades para los ingredientes no presentes
    for ingredient in df_products.index:
        if ingredient not in new_recipe:
            df_products.at[ingredient, new_product_name] = None

    # Guardar el DataFrame actualizado de vuelta al archivo CSV
    df_products.to_csv('data/recipes.csv')

    flash('Producto actualizado exitosamente')
    return redirect(url_for('product', product_name=new_product_name))

def rename_product_image(old_product_name, new_product_name):
    old_filename = secure_filename(old_product_name + '.jpg')
    new_filename = secure_filename(new_product_name + '.jpg')

    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

    if os.path.exists(old_filepath):
        os.rename(old_filepath, new_filepath)
        flash(f'Imagen del producto "{old_product_name}" renombrada a "{new_product_name}" correctamente')
    else:
        flash(f'La imagen del producto "{old_product_name}" no existe')


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
    path = os.path.join(get_base_path(), 'static', 'temp')
    print(path)
    calculate_graphs(path)
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

