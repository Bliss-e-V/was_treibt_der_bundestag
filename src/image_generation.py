#!/usr/bin/env python

"""image_generation.py: Contains code to automatically generate images from
                        the information gathered from a scraped PDFs.
                        Note that `imagemagick` is needed here! """

import textwrap
from datetime import datetime
import locale
from pathlib import Path
from hashlib import sha256
import pyphen  # for hyphenation
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

locale.setlocale(locale.LC_TIME, "de_DE")
hyphenator = pyphen.Pyphen(lang="de_DE")


def german_hyphenation(word):
    return hyphenator.inserted(word)


def draw_text_with_line_breaks(
    img, text, x, y, y_offset, font_size, max_width_offset, color
):
    if text == "":
        return img
    # Save actual 'in-word' hyphens, which should not used for breaking, for
    #  later
    text = text.replace("-", "~")

    max_lines = 7
    max_width = 35 + max_width_offset

    # Find correct hyphenation for line breaks
    words = text.split(" ")
    hyphenated_words = [german_hyphenation(word) for word in words]
    hyphenated_words = " ".join(hyphenated_words)
    # Split text into lines based on max width and max lines
    lines = textwrap.wrap(hyphenated_words, width=max_width, break_on_hyphens=True)
    if len(lines) >= max_lines:
        lines = lines[:max_lines]  # Limit to max lines
        lines.append("[...]")
    # Remove hyphens again if not at the end of line
    lines = [line[:-1].replace("-", "") + line[-1:] for line in lines]

    # Create Drawing context
    with Drawing() as draw:
        draw.font = "res/tt_bells.otf"
        draw.font_size = font_size
        draw.fill_color = Color(color)
        # Draw each line
        if y_offset is True:
            y_offset = int(-90 * len(lines) / 2)
        else:
            y_offset = False
        for line in lines:
            # Make sure to convert initial hyphens to acutal ones again
            draw.text(x, y + y_offset, line.replace("~", "-"))
            y_offset += font_size + 10  # Adjust based on font size

        # Execute drawing
        draw(img)

    return img


def generate_images(link, d):
    """
    Transforms the given structured data into (potentially) multiple images.
    """
    # Set up temp folder to store images
    rand_folder_title = sha256(link.encode("utf-8")).hexdigest()
    path = Path(f".temp/{rand_folder_title}")
    path.mkdir(parents=True)

    files = []

    # Check date and if it's older than 10 days, skip this file
    if (
        datetime.now() - datetime.strptime(str(d["Sitzungsdatum"]), "%d. %B %Y")
    ).days > 10:
        return files

    wahlperiode = str(d["Wahlperiode"]) + ". Wahlperiode"
    sitzung = str(d["Sitzungsnummer"]) + ". Sitzung"
    ort_datum = "Berlin, " + str(d["Sitzungsdatum"])
    ausschuss = str(d["Ausschuss"])

    for index, item in enumerate(d["Tagesordnungspunkte"]):
        number = "TAGESORDNUNGSPUNKT  " + str(item["Nummer"])
        title = str(item["Titel"])
        # Minor manual cleaning of unwanted things in title
        idx = max(
            [
                title.find("BT-Drucksache"),
                title.find("Ausschussdrucksache"),
                title.find("Bundestagsdrucksacke"),
            ]
        )
        if idx != -1:
            title = title[:idx]

        num_fractions = len(item["Fraktion"])
        color = "black"
        if num_fractions > 1:
            fractions = [str(fraction) for fraction in item["Fraktion"]]
            template = "default"
        elif num_fractions == 1:
            fractions = str(item["Fraktion"][0])
            if "CDU" in fractions:
                template = "cdu"
                color = "white"
            elif "Grünen" in fractions:
                template = "gruene"
            elif "Bundesregierung" in fractions:
                template = "bundesregierung"
            elif "Nicht zutreffend" in fractions:
                template = "default"
                # We want to ignore any "Anträge" that are not specific to one
                #  or more parties; hence, we continue here
                continue
            else:
                template = fractions
        else:
            template = "default"

        template = f"res/templates/{template.lower()}.png"
        # Probably rather .svg if posted on our own website

        # Define draw tasks
        draw_fractions = "Antrag"
        if num_fractions > 1:
            if num_fractions > 3:
                fractions = fractions[:3] + ["..."]
            draw_fractions += " der " + ", ".join(fractions)
        elif num_fractions == 1 and fractions != "Nicht zutreffend":
            draw_fractions += " der " + fractions
        # fmt: off
        draws = {
            "text":             [draw_fractions, title, number, ausschuss, wahlperiode, sitzung, ort_datum],
            "x":                [200,            42,    200,    200,       20,          200,     350],
            "y":                [170,            650,   170,    198,       1069,        1069,    1069],
            "y_offset":         [True,           True,  False,  False,     False,       False,   False],
            "font_size":        [37,             62,    22,     18,        18,          18,      18],
            "max_width_offset": [10,              -1,     0,    35,        0,           0,       0],
            "color":            ["white",        color, color,  color,     color,       color,   color],
        }
        # fmt: on

        # Open correct template
        with Image(filename=template) as img:
            for i in range(len(draws["text"])):
                img = draw_text_with_line_breaks(
                    img,
                    draws["text"][i],
                    draws["x"][i],
                    draws["y"][i],
                    draws["y_offset"][i],
                    draws["font_size"][i],
                    draws["max_width_offset"][i],
                    draws["color"][i],
                )

            # Scale up image for better quality -> didn't help!
            # img.resize(2160, 2160)

            # Save image
            filename = path / f"{index}.jpg"
            # Probably rather .svg if posted on our own website
            img.save(filename=filename)
            files.append(filename)

    return files


def main():
    """Tests"""
    import json

    pth = Path(".temp")
    for child in pth.iterdir():
        if not child.is_dir():
            child.unlink()
            continue
        for childchild in child.iterdir():
            childchild.unlink()
        child.rmdir()
    pth.rmdir()
    generate_images("test", json.load(open("tests/pdf_content.json", "r")))


if __name__ == "__main__":
    main()
