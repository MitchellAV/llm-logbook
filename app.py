from typing import Any, NotRequired, TypedDict, cast
from bs4 import BeautifulSoup, ResultSet, Tag, PageElement
import os
import subprocess
import json

data_dir = "./data"
output_dir = "./output"


class FileMetadata(TypedDict):
    title: str
    date: str


class HeaderMetadata(TypedDict, total=False):
    header_author: str
    header_category: str
    header_date: str
    header_hist: str
    header_severity: str
    header_table: str
    header_time: str
    header_title: str


class ImageMetadata(TypedDict, total=False):
    src: str | list[str] | None
    alt: str | list[str] | None
    href: str | list[str] | None
    target: str | list[str] | None


class ContentMetadata(TypedDict, total=False):
    content_image: ImageMetadata
    content_table: str
    content_text: str


# def md(
#     soup: BeautifulSoup,
#     options: dict[str, Any] | None = _todict(MarkdownConverter.DefaultOptions),
# ) -> str:
#     markdown_converter = MarkdownConverter(options=options)
#     markdown_data = markdown_converter.convert_soup(soup)
#     return markdown_data


# def modify_markdownify_options():
#     options = _todict(MarkdownConverter.DefaultOptions)

#     # Modify the markdownify options
#     return options


def extract_header(header_rows: ResultSet[BeautifulSoup]):
    # Extract the header from the html content
    header_metadata: HeaderMetadata = {}

    header_class_list = [
        "header_author",
        "header_category",
        "header_date",
        "header_hist",
        "header_severity",
        "header_table",
        "header_time",
        "header_title",
    ]
    for header_row in header_rows:
        for class_name in header_class_list:
            header_cell = header_row.find("td", class_=class_name)
            if header_cell:
                text = format_content(header_cell.text)
                if class_name == "header_title":
                    if text == "from: unknown":
                        text = "No title"
                header_metadata[class_name] = text
        break

    return header_metadata


def format_content(content: str) -> str:
    content = content.strip()
    content = content.replace("\n", " ")
    content = content.replace("\r", " ")
    content = content.replace("\t", " ")
    # remove extra spaces within the content
    content = " ".join(content.split())
    return content


def extract_content(content_rows: ResultSet[BeautifulSoup]):
    # Extract the content from the html content
    content_metadata_list: list[ContentMetadata] = []

    content_class_list = ["content_image", "content_table", "content_text"]
    for content_row in content_rows:
        content_metadata: ContentMetadata = {}
        for class_name in content_class_list:
            content_cell = content_row.find("td", class_=class_name)
            if content_cell:
                if class_name == "content_image":
                    if type(content_cell) == Tag:
                        image_metadata: ImageMetadata = ImageMetadata()
                        image_tag = cast(Tag, content_cell.find("img"))
                        image_metadata["src"] = image_tag.get("src", "")
                        image_metadata["alt"] = image_tag.get("alt", "")
                        image_link_tag = cast(Tag, content_cell.find("a"))
                        image_metadata["href"] = image_link_tag.get("href", "")
                        image_metadata["target"] = image_link_tag.get("target", "")
                        content_metadata[class_name] = image_metadata
                else:
                    content_metadata[class_name] = format_content(content_cell.text)
        content_metadata_list.append(content_metadata)

    return content_metadata_list


class EntryMetadata(TypedDict):
    header: HeaderMetadata
    content: list[ContentMetadata]


def extract_entries(soup: BeautifulSoup):

    # Modify the html content

    header_tables: ResultSet[BeautifulSoup] = soup.find_all(
        "table", class_="header_table"
    )
    content_tables: ResultSet[BeautifulSoup] = soup.find_all(
        "table", class_="content_table"
    )

    if len(header_tables) != len(content_tables):
        raise ValueError("The number of header tables and content tables are not equal")

    metadata_list: list[EntryMetadata] = []

    for header_table, content_table in zip(header_tables, content_tables):
        header_rows: ResultSet[BeautifulSoup] = header_table.find_all("tr")
        content_rows: ResultSet[BeautifulSoup] = content_table.find_all("tr")

        header_metadata = extract_header(header_rows)
        content_metadata = extract_content(content_rows)

        entry_metadata: EntryMetadata = {
            "header": header_metadata,
            "content": content_metadata,
        }

        metadata_list.append(entry_metadata)

    return metadata_list


def extract_all_unique_classes(soup: BeautifulSoup):
    all_elements_w_classes = soup.find_all(class_=True)
    all_classes = set()

    for element in all_elements_w_classes:
        classes = element["class"]
        all_classes.update(classes)

    all_classes = sorted(all_classes)

    with open("classes.txt", "w") as fp:
        for class_name in sorted(all_classes):
            fp.write(f"{class_name}\n")


def index_generator():
    number = 1
    index_char = f"{number}."
    while True:
        yield index_char
        number += 1
        index_char = f"{number}."


def markdown_list(content: list[str], list_type: str) -> str:
    if list_type not in ["ul", "ol"]:
        raise ValueError("Invalid list type")

    list_str = ""
    list_char = ""
    generator = index_generator()

    for item in content:
        if list_type == "ol":
            list_char = next(generator)
        elif list_type == "ul":
            list_char = "-"
        list_str += f"{list_char} {item}\n"
    return list_str


def markdown_element(
    element_type: str,
    content: str | list[str] | ImageMetadata | dict | None,
) -> str:

    DEFAULT_IMG_ALT_TEXT = "Image for the entry"

    if content == None or content == "":
        if element_type == "hr":
            return "---\n\n"
        elif element_type == "br":
            return "\n"
        else:
            return ""
    elif type(content) == list:
        if element_type == "ul":
            return markdown_list(content, "ul")
        elif element_type == "ol":
            return markdown_list(content, "ol")
        else:
            raise ValueError(f"({element_type}) is an invalid element type")
    elif type(content) == str:
        if element_type == "p":
            return f"{content}\n\n"
        elif element_type == "h1":
            return f"# {content}\n\n"
        elif element_type == "h2":
            return f"## {content}\n\n"
        elif element_type == "h3":
            return f"### {content}\n\n"
        elif element_type == "h4":
            return f"#### {content}\n\n"
        elif element_type == "h5":
            return f"##### {content}\n\n"
        elif element_type == "h6":
            return f"###### {content}\n\n"
        elif element_type == "blockquote":
            return f"> {content}\n"
        elif element_type == "code":
            return f"`{content}`"
        elif element_type == "pre":
            return f"```\n{content}\n```\n"
        elif element_type == "div":
            return f"{content}\n"
        elif element_type == "span":
            return f"{content}\n"
        else:
            raise ValueError(f"({element_type}) is an invalid element type")
    elif type(content) == dict:
        if element_type == "img":
            alt_text = content.get("alt", DEFAULT_IMG_ALT_TEXT)
            if alt_text == "":
                alt_text = DEFAULT_IMG_ALT_TEXT

            return f"![{alt_text}]({content.get('src')})\n\n"
        if element_type == "a":
            return f"[{content.get('target')}]({content.get('href')})\n\n"

        raise ValueError(f"({element_type}) is an invalid element type")
    else:
        raise ValueError(f"({type(content)}) is an invalid content type")

    # elif element_type == "table":
    #     return markdown_table(element)


def markdown_entry_template(entry_metadata: EntryMetadata) -> str:
    header_metadata = entry_metadata["header"]
    content_metadata = entry_metadata["content"]
    markdown = ""

    header_string = f'{header_metadata.get("header_author", "")} - {header_metadata.get("header_date", "")} {header_metadata.get("header_time", "")} : {header_metadata.get("header_title", "")}'

    markdown += markdown_element("h3", header_string)

    markdown += markdown_element("p", header_metadata.get("header_category", ""))
    markdown += markdown_element("p", header_metadata.get("header_severity", ""))
    markdown += markdown_element("p", header_metadata.get("header_hist", ""))

    for content in content_metadata:
        markdown += markdown_element("p", content.get("content_text", ""))
        markdown += markdown_element("p", content.get("content_table", ""))
        markdown += markdown_element("img", content.get("content_image", None))
        markdown += markdown_element("a", content.get("content_image", None))

    markdown += markdown_element("hr", None)

    return markdown


def markdown_info_template(metadata: FileMetadata) -> str:
    markdown = ""

    header_string = f'{metadata.get("title", "")} - {metadata.get("date", "")}'

    markdown += markdown_element("h1", f"{header_string}")
    markdown += markdown_element("h2", "Logbook Entries")
    markdown += markdown_element("hr", None)

    return markdown


def create_markdown(metadata: FileMetadata, entry_metadata: list[EntryMetadata]) -> str:

    markdown = ""

    markdown += markdown_info_template(metadata)

    for entry in entry_metadata:
        markdown += markdown_entry_template(entry)

    return markdown


def extract_metadata(entry_metadata_list: list[EntryMetadata]) -> FileMetadata:
    metadata: FileMetadata = {
        "title": "",
        "date": "",
    }

    title = "LCLS E-log Logbook"
    date = ""

    first_entry_header = entry_metadata_list[-1]["header"]
    date = first_entry_header.get("header_date", date)

    metadata["title"] = title
    metadata["date"] = date

    return metadata


def convert_html_to_md(filename: str):
    # Read the html content from a file
    with open(f"{data_dir}/{filename}.html", "r") as fp:
        soup = BeautifulSoup(fp, "html.parser")

    # Extract all the unique classes
    extract_all_unique_classes(soup)

    # Modify the html content
    entry_metadata_list = extract_entries(soup)

    metadata = extract_metadata(entry_metadata_list)

    # Save as json
    with open(f"{output_dir}/{filename}.json", "w") as fp:
        fp.write(json.dumps(entry_metadata_list, indent=4))

    # Convert the data to markdown

    markdown_data = create_markdown(metadata, entry_metadata_list)
    # markdownify_options = modify_markdownify_options()
    # markdown_data = md(soup, markdownify_options)

    # Save the markdown to a file
    with open(f"{output_dir}/{filename}.md", "w") as fp:
        fp.write(markdown_data)

    # Format the markdown file
    try:
        subprocess.run(["mdformat", f"{output_dir}/{filename}.md"])
    except Exception as e:
        raise e


def main():

    list_of_files = os.listdir(data_dir)
    for filename in list_of_files:
        if filename.endswith(".html"):
            filename = filename.split(".html")[0]
            convert_html_to_md(filename)


if __name__ == "__main__":
    main()
