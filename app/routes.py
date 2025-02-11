from app import app
from flask import render_template, request, redirect, url_for, send_file, session
import requests 
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from . import utils
import json
import os
import io
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio


from flask_babel import _
@app.route('/')
def index():
    lang = request.args.get('lang')
    if lang:
        session['lang'] = lang
    return render_template("index.html")

@app.route('/test')
def test():
    return _('Strona Główna')  # Should return the translated string

@app.route('/extract', methods=['POST','GET'])
def extract():
    if request.method == "POST":
        product_id = request.form.get('product_id')
        url = f"https://www.ceneo.pl/{product_id}"
        response = requests.get(url)
        
        if response.status_code == requests.codes['ok']:
            page_dom = BeautifulSoup(response.text, "html.parser")
            opinions_count = utils.extract(page_dom, "a.product-review__link > span")
            
            if opinions_count:
                product_name = utils.extract(page_dom, "h1.product-top__product-info__name")
                all_opinions = []
                
                while url:
                    response = requests.get(url)
                    page_dom = BeautifulSoup(response.text, "html.parser")
                    opinions = page_dom.select("div .js_product-review")
                    
                    for opinion in opinions:
                        single_opinion = {
                            key: utils.extract(opinion, *value)
                            for key, value in utils.selectors.items()
                        }
                        all_opinions.append(single_opinion)
                    
                    try:
                        url = "https://www.ceneo.pl/" + page_dom.select_one("a.pagination__next")["href"].strip()
                    except TypeError:
                        url = None
                
         
                opinions_dir = "app/opinions"
                if not os.path.exists(opinions_dir):
                    os.makedirs(opinions_dir)

           
                with open(f"{opinions_dir}/{product_id}.json", "w", encoding="UTF-8") as jf:
                    json.dump(all_opinions, jf, indent=4, ensure_ascii=False)


                stats = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "opinions_count": len(all_opinions),
                    "average_stars": pd.DataFrame(all_opinions)["stars"].apply(lambda s: float(s.split("/")[0].replace(",", ".")) if isinstance(s, str) else s).mean(),
                    "stars_distribution": pd.DataFrame(all_opinions)["stars"].apply(lambda s: float(s.split("/")[0].replace(",", ".")) if isinstance(s, str) else s).value_counts().to_dict(),
                    "recommendations_distribution": pd.DataFrame(all_opinions)["recommendation"].value_counts().to_dict(),
                }

                products_dir = "app/products"
                if not os.path.exists(products_dir):
                    os.makedirs(products_dir)
                
                with open(f"{products_dir}/{product_id}.json", "w", encoding="UTF-8") as jf:
                    json.dump(stats, jf, indent=4, ensure_ascii=False)

    
                opinions_df = pd.DataFrame(all_opinions)
                opinions_df['stars'] = opinions_df['stars'].apply(lambda s: float(s.split("/")[0].replace(",", ".")) if isinstance(s, str) else s)
                opinions_df['stars'] = pd.to_numeric(opinions_df['stars'], errors='coerce')  # Zamiana na NaN w przypadku błędnych danych
                opinions_df = opinions_df.dropna(subset=['stars']) 
                stars_distribution = opinions_df['stars'].value_counts().reindex(list(range(0, 6)), fill_value=0)
                df = pd.DataFrame(stars_distribution).reset_index()
                df.columns = ['Stars', 'Count']
                
                fig = px.bar(df, x='Stars', y='Count', labels={'Stars': 'Liczba gwiazdek', 'Count': 'Liczba opinii'})
                html_div = pio.to_html(fig, full_html=False)

                recommendations_distribution = opinions_df['recommendation'].value_counts(dropna=False).reindex(
                    ["Polecam", "Brak rekomendacji", "Nie polecam"], fill_value=0
                )
                
                fig2 = px.pie(recommendations_distribution, names=recommendations_distribution.index, values=recommendations_distribution.values)
                html_div2 = pio.to_html(fig2, full_html=False)

                return render_template("product.html", 
                                       product_id=product_id, 
                                       product_name=product_name, 
                                       stars_chart=html_div,
                                       recommendations_chart=html_div2)
            
            return render_template("extract.html", error="Podany produkt nie ma żadnych opinii")
        
        return render_template("extract.html", error="Podany produkt nie istnieje")
    
    return render_template("extract.html")

@app.route('/products')
def products():
    if not os.path.isdir("app/opinions"):
        os.makedirs("app/opinions", exist_ok=True)
        return render_template('error.html')
    products_list=[filename.split(".")[0] for filename in os.listdir("app/opinions")]
    products = []
    for product_id in products_list:
        try:
            with open(f"app/products/{product_id}.json","r", encoding="UTF-8") as jf:
                products.append(json.load(jf))
        except FileNotFoundError:
            continue
    
    for filename in os.listdir('app/products'):
        if filename.endswith('.json'):
            file_path = os.path.join('app/products', filename)
            with open(file_path, 'r') as jf:
                file_data = json.load(jf)
                products.append(file_data)
    return render_template('products.html', products=products)

@app.route('/product/<product_id>')
def product(product_id):
    return render_template("product.html",product_id=product_id)
@app.route('/product/download_json/<product_id>')
def download_json(product_id):
    return send_file(f"opinions/{product_id}.json","text/json", as_attachment=True)
@app.route('/product/download_csv/<product_id>')
def download_csv(product_id):
    opinions= pd.read_json(f"app/opinions/{product_id}.json")
    opinions.stars=opinions.stars.apply(lambda s: "'"+s)
    buffer= io.BytesIO(opinions.to_csv(sep=";", decimal=",", index=False).encode())
    return send_file(buffer,"text/csv", as_attachment=True, download_name=f"{product_id}.csv")
@app.route('/product/download_xlsx/<product_id>')
def download_xlsx(product_id):
    pass


@app.route('/name/<name>')
def name(name):
    return f"Hello, {name}!"

