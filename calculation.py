import pandas as pd
import matplotlib.pyplot as plt

def calculate_prices():
    recetas_df = pd.read_csv('data/recipes.csv', index_col=0)
    precios_df = pd.read_csv('data/ingredients.csv')

    precios_df['Nombre'] = precios_df['Nombre'].str.lower()
    recetas_df.index = recetas_df.index.str.lower()

    unidad_to_factor = {
        'kilogramo': 1000,
        'litro': 1000,
        'unidad': 1  # unidad se mantiene igual
    }

    def calcular_costo(row):
        costo_total = 0
        for ingrediente, cantidad in row.items():
            if pd.notna(cantidad) and ingrediente in precios_dict:
                precio = precios_dict[ingrediente]['Precio']
                unidad = precios_dict[ingrediente]['Unidad']
                factor = unidad_to_factor.get(unidad, 1)  # obtener el factor de conversión
                costo_total += cantidad * precio / factor  # ajustar la cantidad según la unidad
        return costo_total

    precios_dict = precios_df.set_index('Nombre').to_dict(orient='index')

    costo_recetas = recetas_df.apply(calcular_costo, axis=0)

    df = pd.DataFrame(costo_recetas.items(), columns=['Producto', 'Precio crudo'])

    df['Precio final'] = df['Precio crudo'] * 1.3

    df['Precio crudo'] = round(df['Precio crudo'], 2)
    df['Precio final'] = round(df['Precio final'], 2)


    df.to_csv('data/calculation.csv', index=False)

    return df

def calculate_graphs():
    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    sales = [150, 200, 180, 220, 300, 250, 210, 240, 270, 290, 310, 330]

    plt.figure(figsize=(10, 6))
    plt.bar(months, sales, color='skyblue')
    plt.xlabel('Mes')
    plt.ylabel('Ventas')
    plt.title('Ventas por Mes')
    plt.xticks(rotation=45)

    path = 'static/temp/ventas.png'
    plt.savefig(path)
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

    path = 'static/temp/ventas_gastos.png'
    plt.savefig(path)
    plt.close()

def search_by_name(productos, nombre_producto):
    for producto in productos:
        if producto['Producto'] == nombre_producto:
            return producto
    return None    


if __name__ == '__main__':

    df_calculation = calculate_prices()
    products = df_calculation.to_dict(orient='records')
    print(search_by_name(products, "Cappuccino"))
