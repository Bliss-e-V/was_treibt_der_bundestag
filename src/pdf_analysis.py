#!/usr/bin/env python

"""pdf_analysis.py: Contains code to analyse and extract information from a
                    pdf file."""

from io import BytesIO
import json
import requests
from pathlib import Path
import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI

dotenv_path = Path(".env")
load_dotenv(dotenv_path=dotenv_path)
client = OpenAI()


def extract_text(url):
    """
    Extracts the text from a PDF file using the pypdf library.
    :param path: Path to the PDF file
    :return: List of strings, each string representing the text of one page
    """

    # file_reader = pypdf.PdfReader(path)
    # raw_text = [
    #     page.extract_text(extraction_mode="layout", layout_mode_space_vertically=False)
    #     for page in file_reader.pages
    #     if page.extract_text()
    # ]

    req = requests.get(url)

    pages = []
    # Declaring bold text as such using pdfplumber
    with pdfplumber.open(BytesIO(req.content)) as plumb:
        for page in plumb.pages:
            text = ""
            in_bold = False
            for obj in page.chars:
                if "bold" in obj["fontname"].lower():
                    if not in_bold:
                        text += "<b>"
                        in_bold = True
                    text += obj["text"]
                else:
                    if in_bold:
                        text += "</b>"
                        in_bold = False
                    text += obj["text"]
                # if obj['doctop'] > obj['top']:  # Check if a new line should start
                #     text += "\n"  # Add a newline character for line breaks
            if in_bold:
                text += "</b>"
            pages.append(text)

    return pages


def extract_metadata(text):
    """
    Extracts the metadata Ergänzungsmitteilung, Wahlperiode, Sitzungsnummer,
    Mitteilungsdatum, Sitzungsdatum, and Ausschuss from the text.
    :param text: Text of the PDF file
    :return: Dictionary containing the extracted metadata
    """

    response = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "Gegeben dem folgenden Text, extrahiere Wahlperiode, "
                "Sitzungsnummer, Mitteilungsdatum, Sitzungsdatum "
                "sowie den Auschuss (ignoriere Unterausschüsse). Finde außerdem "
                "heraus, ob es sich um eine Ergänzungsmitteilung handelt, oder "
                "nicht. Wenn nicht alles klar und eindeutig herauszufinden ist, "
                'gebe als gesamten Output lediglich "{}" zurück. Ansonsten '
                "verwende für die Ausgabe folgendes JSON format: "
                '{"Ergänzungsmitteilung": false, "Wahlperiode": 20, '
                '"Sitzungsnummer": 50, "Mitteilungsdatum": "12. Februar 2024", '
                '"Sitzungsdatum": "15. Februar 2024", '
                '"Ausschuss": "Ausschuss für Kultur und Medien"}',
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    data = response.choices[0].message.content
    try:
        json_data = json.loads(data, strict=False)
    except Exception as exc:
        raise ValueError(
            "Could not parse data which is supposed to be in JSON format "
            f"-- urgh, GPT, LISTEN TO ME! The data looks like this:\n{data}"
        ) from exc
    return json_data


def extract_meeting_topics(text):
    """
    Extracts the meeting 'Tageordnungspunkte' from the text.
    :param text: Text of the PDF file
    :return: Dictionary containing the extracted meeting topics
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Gegeben dem folgenden Text, extrahiere die Themen"
                'aller Tagesordnungspunkte (beginnen mit "Tagesordnungspunkt"). '
                "Die Themen sind jeweils dickgedruckt (d.h. davor ein <b> und "
                "am Ende ein </b>)). Ignoriere Tagesordnungspunkte komplett, "
                'falls es sich um eine sogenannte "SAMMELLISTE" handelt '
                "oder sie aufgeteilt sind in mehrere Unterpunkte (a), b), ... "
                "oder 1), 2), ...); ignoriere in diesem Fall alle darauffolgenden "
                "Tagesordnungspunkte. Ignoriere außerdem Tagesordnungspunkte, "
                'welche lediglich "Verschiedenes" oder "Allgemeine Bekanntmachungen" '
                'enthalten, welche nicht explizit von einem "Antrag" oder einem '
                '"Gesetzentwurf" sprechen (sondern z.B. von einem "Fachgespräch" '
                'oder einer "Unterrichtung") und solche, welche nicht einen '
                "klaren, unmissverständlichen und nicht zu langen Titel (weniger "
                "als 30 Wörter) haben. Die Reihenfolge der Tagesordnungpunkte ist im "
                "gegebenen Text bereits geordnet; falls Nummern diese Ordnung "
                "missachten, ignorieren diese Nummern und liste sie nicht in "
                'deiner Ausgabe. Ignorieren außerdem den "BT-Drucksache 20/10385" '
                'oder "Bundestagsdrucksache 20/9700 Nr. 14" Kram. '
                "Erfasse die Nummer des Tagesordnungspunkts, den Titel, sowie die "
                "einbringende Fraktion. Die zulässigen Fraktion sind ausnahmslos "
                '"Bündnis 90/Die Grünen", "CDU/CSU", "AfD", "Linke", "SPD", '
                '"FDP", "Bundesregierung", oder "Nicht zutreffend". Diesen '
                'werden im Text durch "Antrag der ... und der Fraktion der ..." '
                "gelistet, klar gekennzeichnet und sind nicht personenabhängig "
                "(tauchen also nicht in eckigen oder runden Klammern hinter "
                'Personen auf; erst recht nicht unter "Berichterstatter/in:"). '
                "Verwende für die Ausgabe folgendes JSON Format: "
                '[{"Nummer": 1, "Titel": '
                '"Aktivitäten der Bundesregierung zur Förderung '
                "jüdischen Lebens und zur Bekämpfung des Antisemitismus "
                'im Kulturbereich", "Fraktion": '
                '["Bundesregierung"]}, ...]',
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    data = response.choices[0].message.content
    try:
        json_data = json.loads(data, strict=False)
    except Exception as exc:
        raise ValueError(
            "Could not parse data which is supposed to be in JSON format "
            f"-- urgh, GPT, LISTEN TO ME! The data looks like this:\n{data}"
        ) from exc
    return json_data


def analyze_pdf(path):
    """
    Analyzes a PDF file and extracts the metadata, meeting topics, and text.
    :param path: Path to the PDF file
    :return: Dictionary containing the extracted metadata, meeting topics, and text
    """
    # Extract text from PDF
    pages = extract_text(path)

    if "Wahlperiode" not in pages[0][:100]:
        return {}
    # Retrieve metadata and meeting topics from the first page of the pdf
    metadata = extract_metadata(pages[0])

    if metadata == {}:
        return metadata
    # Now add the Tagesordnungspunkte to the dictionary
    metadata["Tagesordnungspunkte"] = extract_meeting_topics(
        " ".join([page for page in pages if "Wahlperiode" in page])
    )

    return metadata
