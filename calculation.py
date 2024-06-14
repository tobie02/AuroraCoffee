import pandas as pd

def calculation():
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

    df.to_csv('data/calculation.csv', index=False)

    return df

if __name__ == '__main__':
    calculation()
