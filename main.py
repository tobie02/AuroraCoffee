from flask import Flask, render_template, request, redirect, flash, url_for, jsonify, make_response, session
from flaskwebgui import FlaskUI
import pandas as pd
import csv
from PIL import Image
import pdfkit
import os
import sys

from updater import check_for_updates
from calculation import calculate_prices, calculate_graphs

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(".")

wkhtmltopdf_path = os.path.abspath('wkhtmltopdf/bin/wkhtmltopdf.exe')
print(f'Using wkhtmltopdf executable at: {wkhtmltopdf_path}')

config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

UPLOAD_FOLDER = os.path.join(get_base_path(), 'static/media/products')

app = Flask(__name__, static_folder=os.path.join(get_base_path(), 'static'), template_folder=os.path.join(get_base_path(), 'templates'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ui = FlaskUI(app, idle_interval=None)

app.secret_key = 'Aurora Coffee'

df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
df_ingredients = pd.read_csv('data/ingredients.csv')
df_expenses = pd.read_csv('data/expenses.csv')
df_menu = pd.read_csv('data/menu.csv')
settings_df = pd.read_csv('data/settings.csv', index_col='setting')


ingredients = df_ingredients['Nombre'].to_list()

def get_description(product_name):
    description = df_menu.loc[df_menu['Producto'] == product_name, 'Descripcion'].values
    return description[0] if description else ""


def set_description(product_name, description):
    global df_menu

    if product_name in df_menu['Producto'].values:
        df_menu.loc[df_menu['Producto'] == product_name, 'Descripcion'] = description
    else:
        new_row = pd.DataFrame({'Producto': [product_name], 'Descripcion': [description]})
        df_menu = pd.concat([df_menu, new_row], ignore_index=True)
    df_menu.to_csv('data/menu.csv', index=False)


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
    global mode

    settings = pd.read_csv('data/settings.csv', index_col='setting')
    mode = settings.loc['mode', 'value']

    df_calculation = calculate_prices()
    products = df_calculation.to_dict(orient='records')

    return render_template('index.html', products=products, mode=mode)


@app.route('/product/<product_name>')
def product(product_name):
    global df_products, df_menu, mode
    df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
    df_menu = pd.read_csv('data/menu.csv')
    ingredients = get_recipe(product_name)
    description = get_description(product_name)
    
    df_calculation = calculate_prices()
    products = df_calculation.to_dict(orient='records')
    product = search_by_name(products, product_name)
    
    return render_template('product.html', product=product, ingredients=ingredients, description=description, mode=mode)


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
                        img = Image.open(product_image)
                        if product_image.filename.lower().endswith('.png'):
                            img = img.convert('RGB')

                        # Asegurarse de que la imagen tenga una relación de aspecto 2:1
                        width, height = img.size
                        aspect_ratio = width / height
                        if aspect_ratio > 2:
                            # Recortar el ancho
                            new_width = height * 2
                            left = (width - new_width) / 2
                            img = img.crop((left, 0, left + new_width, height))
                        elif aspect_ratio < 2:
                            # Recortar el alto
                            new_height = width / 2
                            top = (height - new_height) / 2
                            img = img.crop((0, top, width, top + new_height))

                        # Redimensionar la imagen a un tamaño específico si es necesario
                        img = img.resize((500, 250), Image.LANCZOS)  # Ajusta este tamaño según tus necesidades

                        # Crear un nombre de archivo seguro usando el nombre del producto y la extensión jpg
                        filename = product_name + '.jpg'
                        img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
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


@app.route('/delete_product/<product_name>', methods=['GET', 'POST'])
def delete_product(product_name):
    global df_products, mode

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
    return render_template('confirm_delete_product.html', product_name=product_name, mode=mode)


def delete_product_image(product_name):
    filename = product_name + '.jpg'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'Imagen del producto "{product_name}" eliminada correctamente')
    else:
        flash(f'La imagen del producto "{product_name}" no existe')


@app.route('/update_product', methods=['POST'])
def update_product():
    global df_products, df_menu
    product_name = request.form['product_name']
    new_product_name = request.form['new_product_name']
    description = request.form['description']
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

    # Guardar el DataFrame actualizado en el archivo CSV
    df_products.to_csv('data/recipes.csv')
    
    # Guardar la descripción en el archivo CSV
    set_description(new_product_name, description)

    flash(f'Producto "{new_product_name}" actualizado con éxito.')
    return redirect(url_for('product', product_name=new_product_name))


@app.route('/upload_product_image', methods=['POST'])
def upload_product_image():
    if 'product_image' not in request.files:
        return jsonify({'success': False, 'message': 'No se subió ningún archivo'})

    file = request.files['product_image']
    if file and allowed_file(file.filename):
        product_name = request.form['product_name']

        img = Image.open(file)
        if file.filename.lower().endswith('.png'):
            img = img.convert('RGB')

        # Asegurarse de que la imagen tenga una relación de aspecto 2:1
        width, height = img.size
        aspect_ratio = width / height
        if aspect_ratio > 2:
            # Recortar el ancho
            new_width = height * 2
            left = (width - new_width) / 2
            img = img.crop((left, 0, left + new_width, height))
        elif aspect_ratio < 2:
            # Recortar el alto
            new_height = width / 2
            top = (height - new_height) / 2
            img = img.crop((0, top, width, top + new_height))

        # Redimensionar la imagen a un tamaño específico si es necesario
        img = img.resize((500, 250), Image.LANCZOS)  # Ajusta este tamaño según tus necesidades

        filename = product_name + '.jpg'
        img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_image_url = url_for('static', filename=f'media/products/{filename}')
        return jsonify({'success': True, 'new_image_url': new_image_url})

    return jsonify({'success': False, 'message': 'Formato de archivo no permitido. Por favor, sube una imagen JPG o PNG.'})


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def rename_product_image(old_name, new_name):
    old_path = f'static/media/products/{old_name}.jpg'
    new_path = f'static/media/products/{new_name}.jpg'
    if os.path.exists(old_path):
        os.rename(old_path, new_path)


@app.route('/ingredients')
def ingredients_form():
    global mode

    ingredients = df_ingredients.to_dict(orient='records')
    return render_template('ingredients.html', ingredients=ingredients, mode=mode)


@app.route('/update_prices', methods=['POST'])
def update_prices():
    global df_ingredients

    nombres = request.form.getlist('nombres[]')
    cantidades = request.form.getlist('cantidades[]')
    precios = request.form.getlist('precios[]')

    # Crear un nuevo DataFrame para los ingredientes actualizados
    new_data = {
        'Nombre': nombres,
        'Cantidad': [float(cantidad) for cantidad in cantidades],
        'Precio': [float(precio) for precio in precios]
    }
    df_ingredients = pd.DataFrame(new_data)

    # Guardar el DataFrame actualizado en el archivo CSV
    df_ingredients.to_csv('data/ingredients.csv', index=False)
    flash('Precios y cantidades actualizados')
    return redirect(url_for('ingredients_form'))


@app.route('/expenses')
def expenses_form():
    global mode

    df_expenses = pd.read_csv('data/expenses.csv')
    expenses = df_expenses.to_dict(orient='records')

    total = df_expenses['monto'].sum()

    return render_template('expenses.html', expenses=expenses, total=total, mode=mode)


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
    global mode

    path = os.path.join(get_base_path(), 'static', 'temp')
    print(path)
    calculate_graphs(path)
    return render_template('summary.html', mode=mode)


def read_csv(file_path):
    products = []
    with open(file_path, newline='', encoding='latin1') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products.append(row)
    return products


@app.route('/menu')
def menu():
    global mode

    calculate_prices()
    products = read_csv('data/menu.csv')
    return render_template('menu.html', products=products, mode=mode)


@app.route('/export_pdf')
def export_pdf():
    products = read_csv('data/menu.csv')
    rendered = render_template('menu_pdf.html', products=products)

    pdf = pdfkit.from_string(rendered,
                            False,
                            configuration=config,
                            options={'no-stop-slow-scripts': '', 'enable-local-file-access': ''})

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=menu.pdf'
    return response


@app.route('/settings')
def settings():
    global mode
    settings = pd.read_csv('data/settings.csv', index_col='setting')
    mode = settings.loc['mode', 'value']
    ganancia = settings.loc['ganancia', 'value']
    iva = settings.loc['iva', 'value']
    ib = settings.loc['ib', 'value']
    return render_template('settings.html', ganancia=ganancia, iva=iva, ib=ib, mode=mode)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    ganancia = request.form['ganancia']
    iva = request.form['iva']
    ib = request.form['ib']

    settings = pd.read_csv('data/settings.csv', index_col='setting')
    settings.loc['ganancia', 'value'] = ganancia
    settings.loc['iva', 'value'] = iva
    settings.loc['ib', 'value'] = ib
    settings.to_csv('data/settings.csv')
    return redirect(url_for('settings'))

@app.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    settings = pd.read_csv('data/settings.csv', index_col='setting')
    current_mode = settings.loc['mode', 'value']
    new_mode = 'dark' if current_mode == 'light' else 'light'
    settings.loc['mode', 'value'] = new_mode
    settings.to_csv('data/settings.csv')
    return jsonify(success=True)


if __name__ == "__main__":
    check_for_updates()
    ui.run()

