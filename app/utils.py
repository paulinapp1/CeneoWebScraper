
import requests 
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
import os
import io
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.io as pio
def extract(ancestor,selector=None, attribute=None, return_list=False):
    if selector:
        if return_list:
            if attribute:
                return [tag[attribute].strip() for tag in ancestor.select(selector)]
            return [tag.text.strip() for tag in ancestor.select(selector)]
        if attribute:
            try:
                return  ancestor.select_one(selector)[attribute].strip()
            except TypeError:
               return None
        try:
            return  ancestor.select_one(selector).text.strip()
        except AttributeError:
            return None
    if attribute:
        return ancestor[attribute].strip()
    return ancestor.select_one(selector).text.strip()

selectors = {
    "opinion_id": (None, "data-entry-id"),
    "author": ("span.user-post__author-name",),
    "recommendation": ("span.user-post__author-recomendation",),
    "stars": ("span.user-post__score-count",),
    "content": ("div.user-post__text",),
    "pros": ("div.review-feature__title--positives ~ div.review-feature__item", None, True),
    "cons": ("div.review-feature__title--negatives ~ div.review-feature__item", None, True),
    "helpful": ("button.vote-yes > span",),
    "unhelpful": ("button.vote-no > span",),
    "publish_date": ("span.user-post__published > time:nth-child(1)", "datetime"),
    "purchase_date": ("span.user-post__published > time:nth-child(2)", "datetime"),
}

def create_charts(all_opinions, product_id):
    opinions_df = pd.DataFrame(all_opinions)
    opinions_df['stars'] = opinions_df['stars'].apply(lambda s: float(s.split("/")[0].replace(",", ".")) if isinstance(s, str) else s)
    opinions_df['stars'] = pd.to_numeric(opinions_df['stars'], errors='coerce')
    opinions_df = opinions_df.dropna(subset=['stars']) 
    stars_distribution = opinions_df['stars'].value_counts().reindex(list(range(0, 6)), fill_value=0)
    df = pd.DataFrame(stars_distribution).reset_index()
    df.columns = ['Stars', 'Count']
                
    fig = px.bar(df, x='Stars', y='Count', labels={'Stars': 'Liczba gwiazdek', 'Count': 'Liczba opinii'})
    fig.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=[0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
        ticktext=[str(i) for i in [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]]
    ))
    stars_chart = pio.to_html(fig, full_html=False)

    recommendations_distribution = opinions_df['recommendation'].value_counts(dropna=False).reindex(
            ["Polecam", "Brak rekomendacji", "Nie polecam"], fill_value=0
    )
                
    fig2 = px.pie(recommendations_distribution, names=recommendations_distribution.index, values=recommendations_distribution.values)
    recommendations_chart = pio.to_html(fig2, full_html=False)

    charts_dir = f"app/static/charts/{product_id}"
    os.makedirs(charts_dir, exist_ok=True)
    
    # Save the charts as HTML files
    with open(f"{charts_dir}/stars_chart.html", "w", encoding="utf-8") as f:
         f.write(stars_chart)

    with open(f"{charts_dir}/recommendations_chart.html", "w", encoding="utf-8") as f:
        f.write(recommendations_chart)

    return f"/charts/{product_id}/stars_chart.html", f"/charts/{product_id}/recommendations_chart.html"

    

def save_json(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="UTF-8") as jf:
        json.dump(data, jf, indent=4, ensure_ascii=False)           

