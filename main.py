#!/usr/bin/env python

"""main.py: Combines the PDF analysis, image generation and Instagram posting
            mechanisms.
            To test this locally, do `flask --app main run` and then POST
            a link to a PDF via Postman, for example. """

from flask import Flask, request

import os

from pathlib import Path
from dotenv import load_dotenv
from instagrapi import Client

# from src.app import summarize_text
from src.image_generation import generate_images
from src.instagram_posting import post_carousel
from src.pdf_analysis import analyze_pdf

dotenv_path = Path(".env")
load_dotenv(dotenv_path=dotenv_path)
instagram_username = os.getenv("INSTAGRAM_USERNAME")
instagram_password = os.getenv("INSTAGRAM_PASSWORD")

URL = "https://www.bundestag.de/ausschuesse"

app = Flask(__name__)


@app.route("/", methods=["POST"])
def index():
    link = request.form["pdf_url"]

    client = Client()
    client.login(username=instagram_username, password=instagram_password)

    pdf_content = analyze_pdf(link)

    if not pdf_content:
        return ("", 500)

    file_paths = generate_images(link, pdf_content)
    if not file_paths:
        return ("", 500)

    caption = "" if not pdf_content["Ergänzungsmitteilung"] else "[Ergänzung] "
    caption += f"[{pdf_content['Ausschuss']}] "
    caption += f"[{pdf_content['Sitzungsnummer']}. Sitzung am {pdf_content['Sitzungsdatum']}] "
    caption += f"[{pdf_content['Wahlperiode']}. Wahlperiode]"
    # TODO: Count tagesordnungen per party?
    # TODO: Shorten it automaticcaly? (Instagram maximal caption length: 2,200 characters)

    # Do post on instagram
    post_carousel(
        client=client,
        image_paths=file_paths,
        caption=caption,
    )
    # Funny idea: Let LLM "spice up" the caption haha (but stick to the infrmation)
    # Could do "slang days": monday: like a doctor tuesday: like a comupter nerd, blabla

    # Logout from the Instagrapi client
    client.logout()

    return ("", 200)
