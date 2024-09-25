"""scarper_function.py: Contains code to crawl new Ausschuss data, save it to
                        a db and trigger the post generation."""

import functions_framework
import firebase_admin
from firebase_admin import firestore
import requests
from bs4 import BeautifulSoup

import os
from pathlib import Path
from dotenv import load_dotenv

dotenv_path = Path(".env")
load_dotenv(dotenv_path=dotenv_path)

app = firebase_admin.initialize_app()
backend_url = os.getenv("BACKEND_URL")


def strip_cell_text(cell):
    return cell.get_text(strip=True, separator=", ")


def add_soup_to_db(soup, db):
    for row in soup.find_all("tr")[1:]:
        date_td = row.find("td", attrs={"data-th": "Veröffentlichung"})
        theme_td = row.find("td", attrs={"data-th": "Thema"})
        document_td = row.find("td", attrs={"data-th": "Dokument"})

        date = strip_cell_text(date_td)
        topic = strip_cell_text(theme_td)
        document_name = strip_cell_text(document_td)
        try:
            doc_suffix = document_td.a["href"]
        except:
            continue

        link = "https://www.bundestag.de" + doc_suffix

        doc_ref = db.collection("tagesordnungspunkte").document(
            doc_suffix.replace("/", "_")
        )

        if doc_ref.get().exists:
            continue
            # raise ValueError(f"Document {doc_suffix} already exists in the database")

        doc_ref.set(
            {
                "publicized": date,
                "topic": topic,
                "document_name": document_name,
                "document_link": link,
            }
        )

        # Form data with the key 'pdf_url' and its value
        form_data = {"pdf_url": link}

        # Making the POST request
        requests.post(backend_url, data=form_data)


@functions_framework.http
def scrape(request):
    base_url = "https://www.bundestag.de/ajax/filterlist/de/ausschuesse/868608-868608"
    offset = 0
    db = firestore.client()

    request_url = f"{base_url}?offset={offset}"
    response = requests.get(request_url)
    while response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # try:
        add_soup_to_db(soup, db)
        # except ValueError as e:
        #     break
        offset += 10
        request_url = f"{base_url}?offset={offset}"
        response = requests.get(request_url)

    return "Sucess"
