from app import app
from flask import render_template, request, redirect, url_for, send_file
import requests 
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from . import utils
import json
import os
import io
import matplotlib.pyplot as plt
import base64



@app.route('/')
def index():
    return render_template("index.html")


@app.route('/extract', methods=['POST','GET'])
def extract():
    if request.method=="POST":
        product_id = request.form.get('product_id')
        url = f"https://www.ceneo.pl/{product_id}"
        response = requests.get(url)
        
        if response.status_code == requests.codes['ok']:
            page_dom = BeautifulSoup(response.text, "html.parser")
            opinions_count = utils.extract(page_dom, "a.product-review__link > span")
            
            if opinions_count:
                product_name = utils.extract(page_dom, "h1.product-top__product-info__name")
                all_opinions = []
                
                while(url):
                    response = requests.get(url)
                    page_dom = BeautifulSoup(response.text, "html.parser")
                    opinions = page_dom.select("div.js_product-review")
                    
                    for opinion in opinions:
                        single_opinion = {
                            key: utils.extract(opinion, *value)
                            for key, value in utils.selectors.items()
                        }
                        all_opinions.append(single_opinion)
                    
                    try:
                        url = "https://www.ceneo.pl/"+page_dom.select_one("a.pagination__next")["href"].strip()
                    except TypeError: 
                        url = None

                opinions = pd.DataFrame.from_dict(all_opinions)
                opinions.stars = opinions.stars.apply(lambda s: s.split("/")[0].replace(",", ".") if s else "0").astype(float)
                opinions.recommendation = opinions.recommendation.apply(lambda r: "Brak rekomendacji" if r is None else r)

                stars_distribution = opinions.stars.value_counts().reindex(list(np.arange(0, 5.5, 0.5)), fill_value=0)
                fig1, ax1 = plt.subplots()
                stars_distribution.plot.bar(color="lightpink", ax=ax1)
                ax1.set_title("Histogram częstości gwiazdek w opiniach")
                ax1.set_xlabel("Liczba gwiazdek")
                ax1.set_ylabel("Liczba opinii")
                ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)

     
                img1 = io.BytesIO()
                fig1.savefig(img1, format='png')
                img1.seek(0)
                stars_img = base64.b64encode(img1.getvalue()).decode('utf8')

                recommendations_distribution = opinions.recommendation.value_counts(dropna=False).reindex(
                    ["Polecam", "Brak rekomendacji", "Nie polecam"], fill_value=0
                )
                fig2, ax2 = plt.subplots()
                recommendations_distribution.plot.pie(colors=["lightgreen", "powderblue", "lightpink"], label="", autopct="%1.1f%%", ax=ax2)
                ax2.set_title("Udział rekomendacji w opiniach")

                img2 = io.BytesIO()
                fig2.savefig(img2, format='png')
                img2.seek(0)
                recommendations_img = base64.b64encode(img2.getvalue()).decode('utf8')

           
                return render_template("product.html", 
                                       product_id=product_id, 
                                       product_name=product_name, 
                                       stars_img=stars_img,
                                       recommendations_img=recommendations_img)
            
            return render_template("extract.html", error="Podany produkt nie ma żadnych opinii")
        
        return render_template("extract.html", error="Podany produkt nie istnieje")    

    return render_template("extract.html")

@app.route('/products')
def products():
    #products_list=[filename.split(".")[0] for filename in os.listdir("app/opinions")]
    #products=[]
    #for product_id in products_list:
        #with open(f"app/products/{product_id}.json","r", encoding="UTF-8") as jf:
           # products.append(json.load(jf))
    products = []
    for filename in os.listdir('app/products'):
        if filename.endswith('.json'):
            file_path = os.path.join('app/products', filename)
            with open(file_path, 'r') as jf:
                file_data = json.load(jf)
                products.append(file_data)
    return render_template('products.html', products=products)
@app.route('/about')
def about():
    return render_template("about.html")
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

