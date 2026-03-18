import argparse
from html import unescape
from html.parser import HTMLParser
import logging
import os
import re
from pathlib import Path
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection


LOGGER = logging.getLogger("bible_pipeline")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_HTML_FILE = BASE_DIR / "biblestories.html"

DB_HOST = os.getenv("BIBLE_DB_HOST", "localhost")
DB_USER = os.getenv("BIBLE_DB_USER", "rtcwa")
DB_PASSWORD = os.getenv("BIBLE_DB_PASSWORD", "!Wdfez69")
DB_NAME = os.getenv("BIBLE_DB_NAME", "bible")

OLD_TESTAMENT = "Old Testament"
NEW_TESTAMENT = "New Testament"
START_TITLE = "THE STORY OF CREATION"
END_HEADING = "SCRIBNER ILLUSTRATED CLASSICS FOR YOUNGER READERS"
TEXT_CONTAINER_CLASSES = {"poem", "poem2", "blockquot"}
FIGURE_CONTAINER_CLASSES = {"figleft", "figright", "figcenter"}


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse The Children's Bible HTML and load a dedicated Bible database."
    )
    parser.add_argument(
        "--html-file",
        default=str(DEFAULT_HTML_FILE),
        help="Path to the Project Gutenberg Bible HTML file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the source file and report counts without writing to MySQL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of parsed stories to load.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def db_root_connect() -> MySQLConnection:
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def db_connect() -> MySQLConnection:
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def ensure_database() -> None:
    LOGGER.info("ensuring database %s exists", DB_NAME)
    conn = db_root_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
        )
    finally:
        cursor.close()
        conn.close()

    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stories (
                story_id INT NOT NULL AUTO_INCREMENT,
                story_order INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                testament VARCHAR(32) NOT NULL,
                source VARCHAR(100) NOT NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (story_id),
                UNIQUE KEY unique_story_order (story_order)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS paragraphs (
                paragraph_id INT NOT NULL AUTO_INCREMENT,
                story_id INT NOT NULL,
                paragraph_index INT NOT NULL,
                paragraph_text LONGTEXT NOT NULL,
                PRIMARY KEY (paragraph_id),
                UNIQUE KEY unique_story_paragraph (story_id, paragraph_index),
                CONSTRAINT paragraphs_story_fk
                    FOREIGN KEY (story_id) REFERENCES stories (story_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                image_id INT NOT NULL AUTO_INCREMENT,
                story_id INT NOT NULL,
                image_index INT NOT NULL,
                image_src TEXT NOT NULL,
                image_alt TEXT,
                caption TEXT,
                PRIMARY KEY (image_id),
                UNIQUE KEY unique_story_image (story_id, image_index),
                CONSTRAINT images_story_fk
                    FOREIGN KEY (story_id) REFERENCES stories (story_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def normalize_heading_text(text: str) -> str:
    compact = " ".join(unescape(text).replace("\xa0", " ").split())
    return compact.strip()


def clean_text_block(text: str, multiline: bool = False) -> str:
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"\[[^\]]+\]", "", text)
    if multiline:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines).strip()
    return re.sub(r"\s+", " ", text).strip()


class BibleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stories: list[dict[str, Any]] = []
        self.current_story: dict[str, Any] | None = None
        self.current_testament = OLD_TESTAMENT
        self.story_order = 0
        self.started = False
        self.stopped = False

        self.heading_tag: str | None = None
        self.heading_buffer: list[str] = []

        self.text_block: dict[str, Any] | None = None

        self.ignore_depth = 0
        self.ignore_tags: list[str] = []
        self.skip_section_depth = 0

        self.figure_stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        class_names = set(attr_map.get("class", "").split())

        if tag == "section" and "pg-boilerplate" in class_names:
            self.skip_section_depth += 1
            return

        if self.skip_section_depth > 0:
            return

        if tag == "pre":
            self.skip_section_depth += 1
            return

        if tag in {"span", "a"} and self._is_page_marker(tag, attr_map, class_names):
            self.ignore_depth += 1
            self.ignore_tags.append(tag)
            return

        if tag in {"h2", "h3"}:
            self.heading_tag = tag
            self.heading_buffer = []
            return

        if self.stopped:
            return

        if self._is_figure_container(tag, class_names):
            self.figure_stack.append(
                {
                    "div_depth": 1,
                    "image_index": None,
                    "caption_active": False,
                    "caption_buffer": [],
                    "italic_active": False,
                    "italic_buffer": [],
                }
            )
            return

        if self.figure_stack and tag == "div":
            self.figure_stack[-1]["div_depth"] += 1

        if not self.started or self.current_story is None:
            return

        if tag == "img":
            src = attr_map.get("src", "").strip()
            if not src:
                return

            image_index = len(self.current_story["images"])
            self.current_story["images"].append(
                {
                    "image_src": src,
                    "image_alt": normalize_heading_text(attr_map.get("alt", "")) or None,
                    "caption": None,
                }
            )
            if self.figure_stack:
                self.figure_stack[-1]["image_index"] = image_index
            return

        if tag == "p":
            self.text_block = {"multiline": False, "buffer": []}
            return

        if tag == "div" and class_names.intersection(TEXT_CONTAINER_CLASSES):
            self.text_block = {"multiline": True, "buffer": []}
            return

        if tag == "span" and "caption" in class_names and self.figure_stack:
            self.figure_stack[-1]["caption_active"] = True
            return

        if tag == "i" and self.figure_stack:
            self.figure_stack[-1]["italic_active"] = True
            return

        if tag == "br":
            self._append_line_break()

    def handle_endtag(self, tag: str) -> None:
        if self.skip_section_depth > 0:
            if tag in {"section", "pre"}:
                self.skip_section_depth -= 1
            return

        if self.ignore_tags and tag == self.ignore_tags[-1]:
            self.ignore_tags.pop()
            self.ignore_depth -= 1
            return

        if tag in {"h2", "h3"} and self.heading_tag == tag:
            heading = normalize_heading_text("".join(self.heading_buffer)).upper()
            self.heading_tag = None
            self.heading_buffer = []
            self._handle_heading(tag, heading)
            return

        if self.stopped:
            return

        if self.figure_stack and tag == "span" and self.figure_stack[-1]["caption_active"]:
            self.figure_stack[-1]["caption_active"] = False
            return

        if self.figure_stack and tag == "i" and self.figure_stack[-1]["italic_active"]:
            self.figure_stack[-1]["italic_active"] = False
            return

        if tag == "p" and self.text_block is not None and not self.text_block["multiline"]:
            self._finalize_text_block()
            return

        if tag == "div":
            if self.text_block is not None and self.text_block["multiline"]:
                self._finalize_text_block()
                return

            if self.figure_stack:
                self.figure_stack[-1]["div_depth"] -= 1
                if self.figure_stack[-1]["div_depth"] == 0:
                    self._finalize_figure()
            return

    def handle_data(self, data: str) -> None:
        if self.skip_section_depth > 0 or self.ignore_depth > 0:
            return

        if self.heading_tag is not None:
            self.heading_buffer.append(data)
            return

        if self.stopped:
            return

        if self.figure_stack:
            figure = self.figure_stack[-1]
            if figure["caption_active"]:
                figure["caption_buffer"].append(data)
                return
            if figure["italic_active"]:
                figure["italic_buffer"].append(data)
                return

        if self.text_block is not None:
            self.text_block["buffer"].append(data)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")

    def close(self) -> None:
        super().close()
        if self.current_story is not None and self.current_story["paragraphs"]:
            self.stories.append(self.current_story)

    def _append_line_break(self) -> None:
        if self.text_block is not None and self.text_block["multiline"]:
            self.text_block["buffer"].append("\n")
        if self.figure_stack:
            figure = self.figure_stack[-1]
            if figure["caption_active"]:
                figure["caption_buffer"].append("\n")
            elif figure["italic_active"]:
                figure["italic_buffer"].append("\n")

    def _handle_heading(self, tag: str, heading: str) -> None:
        if tag == "h2":
            if heading == "THE NEW TESTAMENT":
                self.current_testament = NEW_TESTAMENT
            elif heading == END_HEADING:
                self.stopped = True
            return

        if heading == START_TITLE:
            self.started = True

        if not self.started or self.stopped:
            return

        if self.current_story is not None and self.current_story["paragraphs"]:
            self.stories.append(self.current_story)

        self.story_order += 1
        self.current_story = {
            "story_order": self.story_order,
            "title": heading.title(),
            "testament": self.current_testament,
            "source": "The Children's Bible",
            "paragraphs": [],
            "images": [],
        }

    def _finalize_text_block(self) -> None:
        if self.current_story is None or self.text_block is None:
            self.text_block = None
            return

        text = clean_text_block(
            "".join(self.text_block["buffer"]),
            multiline=self.text_block["multiline"],
        )
        if text:
            self.current_story["paragraphs"].append(text)
        self.text_block = None

    def _finalize_figure(self) -> None:
        figure = self.figure_stack.pop()
        if self.current_story is None:
            return

        image_index = figure["image_index"]
        if image_index is None:
            return

        caption = clean_text_block("".join(figure["caption_buffer"]), multiline=True)
        if not caption:
            caption = clean_text_block("".join(figure["italic_buffer"]), multiline=True)

        if caption:
            self.current_story["images"][image_index]["caption"] = caption

    @staticmethod
    def _is_figure_container(tag: str, class_names: set[str]) -> bool:
        return tag == "div" and bool(class_names.intersection(FIGURE_CONTAINER_CLASSES))

    @staticmethod
    def _is_page_marker(tag: str, attrs: dict[str, str], class_names: set[str]) -> bool:
        if tag == "span" and "pagenum" in class_names:
            return True
        if tag == "a" and attrs.get("id", "").startswith("Page_"):
            return True
        return False


def parse_html(html_file: Path) -> list[dict[str, Any]]:
    parser = BibleHTMLParser()
    with html_file.open("r", encoding="utf-8") as handle:
        parser.feed(handle.read())
    parser.close()
    return parser.stories


def upsert_story(cursor, story: dict[str, Any]) -> int:
    cursor.execute(
        """
        SELECT story_id
        FROM stories
        WHERE story_order = %s
        """,
        (story["story_order"],),
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            """
            INSERT INTO stories (story_order, title, testament, source)
            VALUES (%s, %s, %s, %s)
            """,
            (
                story["story_order"],
                story["title"],
                story["testament"],
                story["source"],
            ),
        )
        return int(cursor.lastrowid)

    story_id = int(row[0])
    cursor.execute(
        """
        UPDATE stories
        SET title = %s,
            testament = %s,
            source = %s
        WHERE story_id = %s
        """,
        (
            story["title"],
            story["testament"],
            story["source"],
            story_id,
        ),
    )
    return story_id


def replace_story_paragraphs(cursor, story_id: int, paragraphs: list[str]) -> None:
    cursor.execute("DELETE FROM paragraphs WHERE story_id = %s", (story_id,))
    for index, paragraph_text in enumerate(paragraphs):
        cursor.execute(
            """
            INSERT INTO paragraphs (story_id, paragraph_index, paragraph_text)
            VALUES (%s, %s, %s)
            """,
            (story_id, index, paragraph_text),
        )


def replace_story_images(cursor, story_id: int, images: list[dict[str, Any]]) -> None:
    cursor.execute("DELETE FROM images WHERE story_id = %s", (story_id,))
    for index, image in enumerate(images):
        cursor.execute(
            """
            INSERT INTO images (story_id, image_index, image_src, image_alt, caption)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                story_id,
                index,
                image["image_src"],
                image["image_alt"],
                image["caption"],
            ),
        )


def load_database(stories: list[dict[str, Any]]) -> None:
    ensure_database()

    conn = db_connect()
    cursor = conn.cursor()
    try:
        for story in stories:
            story_id = upsert_story(cursor, story)
            replace_story_paragraphs(cursor, story_id, story["paragraphs"])
            replace_story_images(cursor, story_id, story["images"])
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def summarize(stories: list[dict[str, Any]]) -> None:
    old_count = sum(1 for story in stories if story["testament"] == OLD_TESTAMENT)
    new_count = sum(1 for story in stories if story["testament"] == NEW_TESTAMENT)
    image_count = sum(len(story["images"]) for story in stories)
    paragraph_count = sum(len(story["paragraphs"]) for story in stories)

    LOGGER.info("stories parsed: %s", len(stories))
    LOGGER.info("old testament stories: %s", old_count)
    LOGGER.info("new testament stories: %s", new_count)
    LOGGER.info("paragraph blocks parsed: %s", paragraph_count)
    LOGGER.info("images linked: %s", image_count)

    if stories:
        LOGGER.info("first story: %s", stories[0]["title"])
        LOGGER.info("last story: %s", stories[-1]["title"])


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)

    html_file = Path(args.html_file).resolve()
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")

    stories = parse_html(html_file)
    if args.limit is not None:
        stories = stories[: args.limit]

    summarize(stories)

    if args.dry_run:
        LOGGER.info("dry run complete; no database changes were made")
        return

    load_database(stories)
    LOGGER.info("bible database load complete")


if __name__ == "__main__":
    main()
