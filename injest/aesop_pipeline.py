import os
import re
import json
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import mysql.connector
from openai import OpenAI

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------

HTML_FILE = r"C:\Users\Administrator\story_universe_platform\injest\aesop_fables.html"
IMAGE_DIR = "images"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

IMAGE_BASE = "https://www.gutenberg.org/files/11339/11339-h/"

DB = {
    "host": "localhost",
    "user": "rtcwa",
    "password": "!Wdfez69",
    "database": "aesop"
}

client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------------------------------
# MYSQL
# ----------------------------------------------------

def db_connect():
    return mysql.connector.connect(**DB)

# ----------------------------------------------------
# EMBEDDINGS
# ----------------------------------------------------

def get_embedding(text):

    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return resp.data[0].embedding

# ----------------------------------------------------
# IMAGE DOWNLOAD
# ----------------------------------------------------

def download_image(url):

    os.makedirs(IMAGE_DIR, exist_ok=True)

    filename = url.split("/")[-1]
    path = os.path.join(IMAGE_DIR, filename)

    if not os.path.exists(path):

        r = requests.get(url)

        with open(path, "wb") as f:
            f.write(r.content)

    return path

# ----------------------------------------------------
# MORAL DETECTOR
# ----------------------------------------------------

def detect_moral(text):

    m = re.search(r"Moral[:\.]\s*(.*)", text, re.IGNORECASE)

    if m:
        return m.group(1).strip()

    return None

# ----------------------------------------------------
# HTML PARSER
# ----------------------------------------------------

def parse_html():

    with open(HTML_FILE, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    stories = []

    current = None
    p_index = 0
    in_story_section = False
    ignored_headings = {
        "AESOP'S FABLES",
        "INTRODUCTION",
        "CONTENTS",
        "LIST OF ILLUSTRATIONS",
        "IN COLOUR",
        "IN BLACK AND WHITE",
        "V. S. VERNON JONES",
        "G. K. CHESTERTON",
        "ARTHUR RACKHAM",
    }

    for el in soup.find_all(["h2", "h3", "p", "img"]):

        if el.name in {"h2", "h3"}:

            title = " ".join(el.get_text(" ", strip=True).split())

            if title == "AESOP'S FABLES":
                in_story_section = True
                continue

            if (
                in_story_section
                and title.isupper()
                and title not in ignored_headings
            ):

                if current:
                    stories.append(current)

                current = {
                    "title": title,
                    "paragraphs": [],
                    "images": [],
                    "moral": None
                }

                p_index = 0

        elif el.name == "p" and current:

            txt = el.get_text().strip()

            if txt:

                moral = detect_moral(txt)

                if moral:
                    current["moral"] = moral

                current["paragraphs"].append(txt)

                p_index += 1

        elif el.name == "img" and current:

            src = el.get("src")

            if src:

                if not src.startswith("http"):
                    src = IMAGE_BASE + src.replace("./","")

                current["images"].append({
                    "url": src,
                    "paragraph_index": p_index
                })

    if current:
        stories.append(current)

    return stories

# ----------------------------------------------------
# DATABASE INSERT
# ----------------------------------------------------

def insert_story(cursor, story):

    sql = """
    INSERT INTO stories (title, moral, source)
    VALUES (%s,%s,%s)
    """

    cursor.execute(sql, (
        story["title"],
        story["moral"],
        "Project Gutenberg"
    ))

    return cursor.lastrowid

# ----------------------------------------------------
# INSERT PARAGRAPHS
# ----------------------------------------------------

def insert_paragraph(cursor, story_id, idx, text):

    emb = get_embedding(text)

    sql = """
    INSERT INTO paragraphs
    (story_id, paragraph_index, paragraph_text, embedding)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        story_id,
        idx,
        text,
        json.dumps(emb)
    ))

# ----------------------------------------------------
# INSERT IMAGE
# ----------------------------------------------------

def insert_image(cursor, story_id, img):

    local_file = download_image(img["url"])

    sql = """
    INSERT INTO images
    (story_id, paragraph_index, image_file, image_url)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        story_id,
        img["paragraph_index"],
        local_file,
        img["url"]
    ))

# ----------------------------------------------------
# MAIN PIPELINE
# ----------------------------------------------------

def run_pipeline():

    stories = parse_html()

    print("Stories found:", len(stories))

    db = db_connect()
    cursor = db.cursor()

    for story in tqdm(stories):

        story_id = insert_story(cursor, story)

        for i, p in enumerate(story["paragraphs"]):

            insert_paragraph(cursor, story_id, i, p)

        for img in story["images"]:

            insert_image(cursor, story_id, img)

    db.commit()

    cursor.close()
    db.close()

    print("Pipeline complete")

# ----------------------------------------------------

if __name__ == "__main__":
    run_pipeline()
