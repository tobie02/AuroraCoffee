import os
import pandas as pd
import numpy as np
from math import ceil
import matplotlib.pyplot as plt
import csv

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def rename_product_image(old_name, new_name):
    old_path = f'static/media/products/{old_name}.jpg'
    new_path = f'static/media/products/{new_name}.jpg'
    if os.path.exists(old_path):
        os.rename(old_path, new_path)

def delete_product_image(product_name, upload_folder):
    filename = product_name + '.jpg'
    filepath = os.path.join(upload_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

def get_description(product_name):
    df_menu = pd.read_csv('data/menu.csv')
    df_menu.fillna("", inplace=True)
    description = df_menu.loc[df_menu['Producto'] == product_name, 'Descripcion'].values
    return description[0]

def set_description(product_name, description):
    df_menu = pd.read_csv('data/menu.csv')
    if product_name in df_menu['Producto'].values:
        df_menu.loc[df_menu['Producto'] == product_name, 'Descripcion'] = description
    else:
        new_row = pd.DataFrame({'Producto': [product_name], 'Descripcion': [description]})
        df_menu = pd.concat([df_menu, new_row], ignore_index=True)
    df_menu.to_csv('data/menu.csv', index=False)

def get_recipe(product_name):
    df_products = pd.read_csv('data/recipes.csv', index_col='Unnamed: 0')
    product_data = df_products[product_name].dropna().to_dict()
    return product_data

def search_by_name(products, name):
    for product in products:
        if product['Producto'] == name:
            return product
    return None

def read_csv(file_path):
    products = []
    with open(file_path, newline='', encoding='latin1') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products.append(row)
    return products

def calculate_prices():
    recetas_df = pd.read_csv('data/recipes.csv', index_col=0)
    precios_df = pd.read_csv('data/ingredients.csv')
    settings = pd.read_csv('data/settings.csv', index_col='setting')


    precios_df['Nombre'] = precios_df['Nombre'].str.lower()
    recetas_df.index = recetas_df.index.str.lower()

    def calcular_costo(row):
        costo_total = 0
        for ingrediente, cantidad in row.items():
            if pd.notna(cantidad) and ingrediente in precios_dict:
                precio = precios_dict[ingrediente]['Precio']
                cantidad_compra = precios_dict[ingrediente]['Cantidad']
                costo_total += cantidad * precio / cantidad_compra  # ajustar la cantidad según la unidad
        return costo_total

    precios_dict = precios_df.set_index('Nombre').to_dict(orient='index')

    costo_recetas = recetas_df.apply(calcular_costo, axis=0)

    df = pd.DataFrame(costo_recetas.items(), columns=['Producto', 'Precio crudo'])

    ganancia = int(settings.loc['ganancia', 'value'])
    ganancia = (ganancia / 100) + 1
    iva = int(settings.loc['iva', 'value'])
    iva = (iva / 100) + 1
    ib = int(settings.loc['ib', 'value'])
    ib = (ib / 100) + 1


    df['Precio final'] = df['Precio crudo'] * ganancia
    df['Precio final'] = df['Precio final'] * iva
    df['Precio final'] = df['Precio final'] * ib

    df['Precio final'] = df['Precio final'].apply(lambda x: ceil(x / 100) * 100)

    df['Precio crudo'] = round(df['Precio crudo'], 2)

    menu_df = pd.read_csv('data/menu.csv')

    products = df['Producto'].to_list()

    menu_df = menu_df[menu_df['Producto'].isin(products)]

    productos_faltantes = [producto for producto in products if producto not in menu_df['Producto'].values]

    nuevas_filas = []
    for producto in productos_faltantes:
        nuevas_filas.append({'Producto': producto, 'Descripcion': '', 'Precio crudo': None, 'Precio final': None})
    nuevas_filas = pd.DataFrame(nuevas_filas)
    menu_df = pd.concat([menu_df, nuevas_filas], ignore_index=True)
    

    for index, row in menu_df.iterrows():
        producto = row['Producto']
        if producto in df['Producto'].values:
            menu_df.loc[index, 'Precio crudo'] = df.loc[df['Producto'] == producto, 'Precio crudo'].values[0]
            menu_df.loc[index, 'Precio final'] = df.loc[df['Producto'] == producto, 'Precio final'].values[0]

    menu_df['Precio final'] = menu_df['Precio final'].astype(int)

    menu_df.to_csv('data/menu.csv', index=False)

    return menu_df

def calculate_graphs(path):
    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    sales = [150, 200, 180, 220, 300, 250, 210, 240, 270, 290, 310, 330]

    plt.figure(figsize=(10, 6))
    plt.bar(months, sales, color='skyblue')
    plt.xlabel('Mes')
    plt.ylabel('Ventas')
    plt.title('Ventas por Mes')
    plt.xticks(rotation=45)

    plt.savefig(f'{path}/ventas.png')
    plt.close()

    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    expenses = [300, 300, 320, 330, 340, 330, 330, 340, 310, 300, 290, 320]
    profits = [250, 240, 260, 270, 300, 340, 370, 380, 420, 430, 440, 460]

    plt.figure(figsize=(10, 6))
    plt.plot(months, expenses, label='Gastos', color='red')
    plt.plot(months, profits, label='Ganancias', color='green')
    plt.xlabel('Mes')
    plt.ylabel('Cantidad')
    plt.title('Gastos y Ganancias')
    plt.legend()    
    plt.xticks(rotation=45)

    plt.savefig(f'{path}/ventas_gastos.png')
    plt.close()

def search_by_name(productos, nombre_producto):
    for producto in productos:
        if producto['Producto'] == nombre_producto:
            return producto
    return None    
