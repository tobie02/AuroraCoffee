import pandas as pd
import numpy as np

products = {
    "Cafe Chico": {'Cafe': 100, 'Azucar': 50},
    "Cappuccino": {'Cafe': 100, 'Azucar': 100, 'Cacao': 50, 'Leche': 50},
    "Medialuna": {'Harina': 300, 'Huevos': 2, 'Azucar': 100, 'Almibar': 100},
    "Cookies": {},
    "Lemon Pie": {'Harina': 800, 'Limon': 2, 'Azucar': 300, 'Huevos': 5, 'Leche': 200},
    "La Marquese": {},
    "Cheesecake": {},
}

df = pd.DataFrame(products)

df.to_csv('data/products.csv')