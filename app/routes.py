from flask import render_template, request, redirect, flash, url_for, jsonify, make_response
from PIL import Image
import os
import pandas as pd
from .utils import (allowed_file, rename_product_image, delete_product_image,
                    get_description, set_description, get_recipe, search_by_name, calculate_prices, calculate_graphs)
import pdfkit

def setup_routes(app, base_path):

    @app.route("/")
    def index():
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']

        df_calculation = calculate_prices()
        df_calculation.sort_values(by='Producto', inplace=True)
        products = df_calculation.to_dict(orient='records')

        return render_template('index.html', products=products, mode=mode)


    @app.route('/product/<product_name>')
    def product(product_name):
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']
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
            if product_name not in app.config['df_products'].columns:
                if 'product_image' in request.files:
                    product_image = request.files['product_image']
                    if product_image.filename != '':
                        if allowed_file(product_image.filename):
                            img = Image.open(product_image)
                            if product_image.filename.lower().endswith('.png'):
                                img = img.convert('RGB')

                            width, height = img.size
                            aspect_ratio = width / height
                            if aspect_ratio > 2:
                                new_width = height * 2
                                left = (width - new_width) / 2
                                img = img.crop((left, 0, left + new_width, height))
                            elif aspect_ratio < 2:
                                new_height = width / 2
                                top = (height - new_height) / 2
                                img = img.crop((0, top, width, top + new_height))

                            img = img.resize((500, 250), Image.LANCZOS)

                            filename = product_name + '.jpg'
                            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        else:
                            flash('Formato de imagen no válido. Use solamente: jpg, jpeg o png')
                            return redirect(url_for('index'))

                app.config['df_products'][product_name] = None
                app.config['df_products'].to_csv('data/recipes.csv')
                flash('Producto añadido exitosamente')
            else:
                flash('El producto ya existe')
        else:
            flash('Ingrese un nombre válido para el producto')

        return redirect(url_for('index'))


    @app.route('/delete_product/<product_name>', methods=['GET', 'POST'])
    def delete_product(product_name):
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']
        if request.method == 'POST':
            if product_name in app.config['df_products'].columns:
                delete_product_image(product_name, app.config['UPLOAD_FOLDER'])

                app.config['df_products'].drop(columns=[product_name], inplace=True)
                app.config['df_products'].to_csv('data/recipes.csv')
                flash(f'Producto "{product_name}" eliminado correctamente')
                return redirect(url_for('index'))
            else:
                flash(f'Error: El producto "{product_name}" no existe')
                return redirect(url_for('index'))

        return render_template('confirm_delete_product.html', product_name=product_name, mode=mode)


    @app.route('/update_product', methods=['POST'])
    def update_product():
        product_name = request.form['product_name']
        new_product_name = request.form['new_product_name']
        description = request.form['description']
        ingredients = request.form.getlist('ingredients[]')
        quantities = request.form.getlist('quantities[]')

        if new_product_name and new_product_name != product_name:
            if product_name in app.config['df_products'].columns:
                app.config['df_products'].rename(columns={product_name: new_product_name}, inplace=True)
                rename_product_image(product_name, new_product_name)
            else:
                flash(f'Error: El producto "{product_name}" no existe en la base de datos')

        new_recipe = {ingredient: float(quantity) for ingredient, quantity in zip(ingredients, quantities)}
        for ingredient, quantity in new_recipe.items():
            app.config['df_products'].at[ingredient, new_product_name] = quantity

        for ingredient in app.config['df_products'].index:
            if ingredient not in new_recipe:
                app.config['df_products'].at[ingredient, new_product_name] = None

        app.config['df_products'].to_csv('data/recipes.csv')
        
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

            width, height = img.size
            aspect_ratio = width / height
            if aspect_ratio > 2:
                new_width = height * 2
                left = (width - new_width) / 2
                img = img.crop((left, 0, left + new_width, height))
            elif aspect_ratio < 2:
                new_height = width / 2
                top = (height - new_height) / 2
                img = img.crop((0, top, width, top + new_height))

            img = img.resize((500, 250), Image.LANCZOS)

            filename = product_name + '.jpg'
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            new_image_url = url_for('static', filename=f'media/products/{filename}')
            return jsonify({'success': True, 'new_image_url': new_image_url})

        return jsonify({'success': False, 'message': 'Formato de archivo no permitido. Por favor, sube una imagen JPG o PNG.'})


    @app.route('/ingredients')
    def ingredients_form():
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']
        ingredients = app.config['df_ingredients'].to_dict(orient='records')
        return render_template('ingredients.html', ingredients=ingredients, mode=mode)


    @app.route('/update_prices', methods=['POST'])
    def update_prices():
        nombres = request.form.getlist('nombres[]')
        cantidades = request.form.getlist('cantidades[]')
        precios = request.form.getlist('precios[]')

        new_data = {
            'Nombre': nombres,
            'Cantidad': [float(cantidad) for cantidad in cantidades],
            'Precio': [float(precio) for precio in precios]
        }
        app.config['df_ingredients'] = pd.DataFrame(new_data)

        app.config['df_ingredients'].to_csv('data/ingredients.csv', index=False)
        flash('Precios actualizados')
        return redirect(url_for('ingredients_form'))


    @app.route('/expenses')
    def expenses_form():
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']
        df_expenses = pd.read_csv('data/expenses.csv')
        expenses = df_expenses.to_dict(orient='records')

        total = df_expenses['monto'].sum()

        return render_template('expenses.html', expenses=expenses, total=total, mode=mode)


    @app.route('/update_expenses', methods=['POST'])
    def update_expenses():
        tipos = request.form.getlist('tipos[]')
        montos = request.form.getlist('montos[]')

        new_data = {
            'expensa': tipos,
            'monto': [float(monto) for monto in montos]
        }
        app.config['df_expenses'] = pd.DataFrame(new_data)

        app.config['df_expenses'].to_csv('data/expenses.csv', index=False)
        flash('Expensas actualizadas')
        return redirect(url_for('expenses_form'))


    @app.route("/summary")
    def summary():
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']
        path = os.path.join(base_path, 'static', 'temp')
        print(path)
        calculate_graphs(path)
        return render_template('summary.html', mode=mode)


    @app.route('/menu')
    def menu():
        settings = pd.read_csv('data/settings.csv', index_col='setting')
        mode = settings.loc['mode', 'value']
        calculate_prices()
        menu = pd.read_csv('data/menu.csv')
        menu.fillna("", inplace=True)
        menu = menu.to_dict(orient='records')
        return render_template('menu.html', products=menu, mode=mode)


    @app.route('/export_pdf')
    def export_pdf():

        wkhtmltopdf_path = os.path.abspath('wkhtmltopdf/bin/wkhtmltopdf.exe')
        print(f'Using wkhtmltopdf executable at: {wkhtmltopdf_path}')
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

        menu = pd.read_csv('data/menu.csv')
        menu.fillna("", inplace=True)
        menu = menu.to_dict(orient='records')
        rendered = render_template('menu_pdf.html', products=menu)

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
