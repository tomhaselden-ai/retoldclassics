import json
import mysql.connector
from openai import OpenAI
import os
import time
import requests

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SECONDS = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "240"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))

# ---------------------------------
# DATABASE CONNECTIONS
# ---------------------------------

sources = [
    {"db":"aesop","author":"Aesop"},
    {"db":"grimm","author":"Brothers Grimm"},
    {"db":"andersen","author":"Hans Christian Andersen"},
    {"db":"bible","author":"The Children's Bible"}
]

TARGET_DB = {
    "host":"localhost",
    "user":"rtcwa",
    "password":"!Wdfez69",
    "database":"stories"
}

BASE_DB = {
    "host":"localhost",
    "user":"rtcwa",
    "password":"!Wdfez69"
}

AI_PROMPT = """
You are a children's literature story analyst and editor.

You will receive a classic story in JSON format containing a title and paragraphs.

Your job is to analyze the story and return structured metadata while rewriting the paragraphs in a modern storytelling voice.

IMPORTANT WRITING RULES

When rewriting paragraphs:

- Preserve the exact meaning, events, and intent of the original text.
- Do NOT add new information.
- Do NOT remove any events or details.
- Do NOT summarize.
- Rewrite each paragraph fully.
- Modernize vocabulary, sentence flow, and readability.
- Avoid archaic phrasing.
- Keep the tone narrative and natural for contemporary readers (modern 2020 storytelling voice).
- Maintain the same paragraph structure and order.

If a paragraph contains dialogue, keep the dialogue but modernize phrasing only.

OUTPUT REQUIREMENTS

Return STRICT JSON only.

Do NOT include explanations, commentary, or markdown.

All fields must be present even if empty.

TASKS

1 Rewrite each paragraph in a modern storytelling voice
2 Extract characters and descriptions
3 Extract locations
4 Identify character traits (honesty, courage, faith, etc)
5 Break the story into scenes
6 Break scenes into beats
7 Extract themes
8 Estimate age range
9 Estimate reading level
10 Extract the moral of the story
11 Create illustration prompts for major scenes
12 Create narration scripts suitable for audiobook narration

STRICT JSON STRUCTURE

{
 "paragraphs_modern":[
  {"index":0,"text":""}
 ],

 "characters":[
  {"name":"","description":""}
 ],

 "locations":[
  {"name":"","description":""}
 ],

 "traits":["honesty","courage"],

 "themes":["perseverance","justice"],

 "age_range":"6-10",

 "reading_level":"grade 3",

 "moral":"",

 "scenes":[
   {
     "scene_title":"",
     "summary":"",
     "beats":[
        {"beat":"","description":""}
     ]
   }
 ],

 "illustration_prompts":[
   {"scene":"","prompt":""}
 ],

 "narration":[
   {"paragraph_index":0,"script":""}
 ]
}

Return JSON only.
"""


# ---------------------------------
# LOAD STORY
# ---------------------------------

def load_story(db_name,story_id):

    conn = mysql.connector.connect(**BASE_DB,database=db_name)
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM stories WHERE story_id=%s",(story_id,))
    story = cur.fetchone()

    cur.execute("""
        SELECT paragraph_index,paragraph_text
        FROM paragraphs
        WHERE story_id=%s
        ORDER BY paragraph_index
    """,(story_id,))

    paragraphs = cur.fetchall()

    conn.close()

    return story,paragraphs

# ---------------------------------
# CALL AI
# ---------------------------------

def enrich_story(story,paragraphs):

    payload = {
        "title":story["title"],
        "paragraphs":paragraphs
    }

    messages = [
        {"role":"system","content":AI_PROMPT},
        {"role":"user","content":json.dumps(payload, ensure_ascii=True)}
    ]

    last_error = None

    for attempt in range(1, OPENAI_MAX_RETRIES + 1):
        try:
            if hasattr(client, "responses"):
                response = client.responses.create(
                    model=MODEL,
                    input=messages,
                )
                txt = response.output_text
            else:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": MODEL,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": str(AI_PROMPT)},
                            {"role": "user", "content": json.dumps(payload, ensure_ascii=True)}
                        ]
                    },
                    timeout=OPENAI_TIMEOUT_SECONDS
                )
                if not response.ok:
                    raise RuntimeError(
                        f"OpenAI chat completions failed ({response.status_code}): {response.text}"
                    )
                txt = response.json()["choices"][0]["message"]["content"]

            return json.loads(txt)
        except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout) as exc:
            last_error = exc
            print(f"timeout on '{story['title']}' attempt {attempt}/{OPENAI_MAX_RETRIES}")
        except Exception as exc:
            last_error = exc
            if attempt == OPENAI_MAX_RETRIES:
                break
            print(f"retrying '{story['title']}' after error on attempt {attempt}/{OPENAI_MAX_RETRIES}: {exc}")

        if attempt < OPENAI_MAX_RETRIES:
            time.sleep(attempt * 2)

    raise RuntimeError(
        f"Failed to enrich '{story['title']}' after {OPENAI_MAX_RETRIES} attempts: {last_error}"
    )

# ---------------------------------
# EXISTENCE CHECK
# ---------------------------------

def story_already_processed(author, title):

    conn = mysql.connector.connect(**TARGET_DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 1
        FROM stories
        WHERE source_author=%s AND title=%s
        LIMIT 1
        """,
        (author, title)
    )

    exists = cur.fetchone() is not None

    conn.close()

    return exists

# ---------------------------------
# SAVE RESULT
# ---------------------------------

def save_result(author,story_id,title,data):

    conn = mysql.connector.connect(**TARGET_DB)
    cur = conn.cursor()

    sql = """
    INSERT INTO stories
    (source_author,source_story_id,title,
    age_range,reading_level,moral,
    characters,locations,traits,themes,
    scenes,beats,paragraphs_modern,
    narration,illustration_prompts)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(sql,(
        author,
        story_id,
        title,
        data.get("age_range"),
        data.get("reading_level"),
        data.get("moral"),

        json.dumps(data.get("characters")),
        json.dumps(data.get("locations")),
        json.dumps(data.get("traits")),
        json.dumps(data.get("themes")),

        json.dumps(data.get("scenes")),
        json.dumps(data.get("beats")),
        json.dumps(data.get("paragraphs_modern")),
        json.dumps(data.get("narration")),
        json.dumps(data.get("illustration_prompts"))
    ))

    conn.commit()
    conn.close()

# ---------------------------------
# MAIN PIPELINE
# ---------------------------------

def run():

    for source in sources:

        db = source["db"]
        author = source["author"]

        conn = mysql.connector.connect(**BASE_DB,database=db)
        cur = conn.cursor()

        cur.execute("SELECT story_id,title FROM stories")

        stories = cur.fetchall()

        conn.close()

        for story_id,title in stories:

            if story_already_processed(author, title):
                print("skipped", title)
                continue

            story,paragraphs = load_story(db,story_id)

            try:
                result = enrich_story(story,paragraphs)
                save_result(author,story_id,title,result)
                print("processed",title)
            except Exception as exc:
                print("failed", title, exc)

if __name__ == "__main__":
    run()
