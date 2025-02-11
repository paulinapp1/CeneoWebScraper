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
from flask import send_from_directory


from flask_babel import _
@app.route('/set_language/<language>')
def set_language(language):
    session['language'] = language
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/test')
def test():
    return _('Strona Główna') 
    
@app.route('/extract', methods=['POST','GET'])
@app.route('/extract', methods=['POST', 'GET'])
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

                # Save opinions in the static folder
                opinions_path = os.path.join('app/static/opinions', f"{product_id}.json")
                utils.save_json(all_opinions, opinions_path)

                # Prepare product stats
                stats = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "opinions_count": len(all_opinions),
                    "average_stars": pd.DataFrame(all_opinions)["stars"].apply(lambda s: float(s.split("/")[0].replace(",", ".")) if isinstance(s, str) else s).mean(),
                    "stars_distribution": pd.DataFrame(all_opinions)["stars"].apply(lambda s: float(s.split("/")[0].replace(",", ".")) if isinstance(s, str) else s).value_counts().to_dict(),
                    "recommendations_distribution": pd.DataFrame(all_opinions)["recommendation"].value_counts().to_dict(),
                }

                # Save product stats in the static folder
                product_stats_path = os.path.join('app/static/products', f"{product_id}.json")
                utils.save_json(stats, product_stats_path)

                # Generate charts and save them in static folder
                stars_chart_path, recommendations_chart_path = utils.create_charts(all_opinions, product_id)

                return render_template("product.html", 
                                       product_id=product_id, 
                                       product_name=product_name, 
                                       stars_chart=stars_chart_path,
                                       recommendations_chart=recommendations_chart_path)

            return render_template("extract.html", error="Podany produkt nie ma żadnych opinii")
        
        return render_template("extract.html", error="Podany produkt nie istnieje")
    
    return render_template("extract.html")


@app.route('/products')
def products():
    if not os.path.isdir("app/static/opinions"):
        os.makedirs("app/static/opinions", exist_ok=True)
        return render_template('error.html')
    products_list=[filename.split(".")[0] for filename in os.listdir("app/static/opinions")]
    products = []
    for product_id in products_list:
        try:
            with open(f"app/static/products/{product_id}.json","r", encoding="UTF-8") as jf:
                products.append(json.load(jf))
        except FileNotFoundError:
            continue
    
    for filename in os.listdir('app/static/products'):
        if filename.endswith('.json'):
            file_path = os.path.join('app/static/products', filename)
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

