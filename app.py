from typing import Any, NotRequired, TypedDict, cast
from markdownify import MarkdownConverter, _todict
from bs4 import BeautifulSoup, ResultSet, Tag, PageElement
import os
import urllib.parse

data_dir = "./data"
output_dir = "./output"


def md(
    soup: BeautifulSoup,
    options: dict[str, Any] | None = _todict(MarkdownConverter.DefaultOptions),
) -> str:
    markdown_converter = MarkdownConverter(options=options)
    markdown_data = markdown_converter.convert_soup(soup)
    return markdown_data


def modify_markdownify_options():
    options = _todict(MarkdownConverter.DefaultOptions)

    # Modify the markdownify options
    return options


class HeaderMetadata(TypedDict):
    header_author: NotRequired[str]
    header_category: NotRequired[str]
    header_date: NotRequired[str]
    header_hist: NotRequired[str]
    header_severity: NotRequired[str]
    header_table: NotRequired[str]
    header_time: NotRequired[str]
    header_title: NotRequired[str]


def extract_header(header_rows: ResultSet[BeautifulSoup]):
    # Extract the header from the html content
    header_metadata_list: list[HeaderMetadata] = []

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
        header_metadata: HeaderMetadata = {}
        for class_name in header_class_list:
            header_cell = header_row.find("td", class_=class_name)
            if header_cell:
                header_metadata[class_name] = header_cell.text.strip()
        header_metadata_list.append(header_metadata)

    return header_metadata_list


class ImageMetadata(TypedDict):
    src: NotRequired[str | list[str] | None]
    alt: NotRequired[str | list[str] | None]
    href: NotRequired[str | list[str] | None]
    target: NotRequired[str | list[str] | None]


class ContentMetadata(TypedDict):
    content_image: NotRequired[ImageMetadata]
    content_table: NotRequired[str]
    content_text: NotRequired[str]


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
                        image_metadata: ImageMetadata = {}
                        image_tag = cast(Tag, content_cell.find("img"))
                        image_metadata["src"] = image_tag.get("src", "")
                        image_metadata["alt"] = image_tag.get("alt", "")
                        image_link_tag = cast(Tag, content_cell.find("a"))
                        image_metadata["href"] = image_link_tag.get("href", "")
                        image_metadata["target"] = image_link_tag.get("target", "")
                        content_metadata[class_name] = image_metadata
                else:
                    content_metadata[class_name] = content_cell.text.strip()
        content_metadata_list.append(content_metadata)

    return content_metadata_list


class EntryMetadata(TypedDict):
    header: list[HeaderMetadata]
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


def create_markdown_from_entry_metadata(entry_metadata: list[EntryMetadata]) -> str:
    return ""


def convert_html_to_md(filename: str):
    # Read the html content from a file
    with open(f"{data_dir}/{filename}.html", "r") as fp:
        soup = BeautifulSoup(fp, "html.parser")

    # Extract all the unique classes
    extract_all_unique_classes(soup)

    # Modify the html content
    entry_metadata_list = extract_entries(soup)

    # Convert the data to markdown

    markdown_data = create_markdown_from_entry_metadata(entry_metadata_list)
    # markdownify_options = modify_markdownify_options()
    # markdown_data = md(soup, markdownify_options)

    # Save the markdown to a file
    with open(f"{output_dir}/{filename}.md", "w") as fp:
        fp.write(markdown_data)


def main():

    # file_references = "file-names.csv"
    # file_metadata = []
    # with open(file_references, "r") as fp:
    #     for line in fp:
    #         line = urllib.parse.unquote(line)
    #         line = line.strip().split("?")[-1]
    #         params = line.split("&")
    #         file = params[0].split("=")[-1]
    #         xsl = params[1].split("=")[-1]
    #         picture = params[2].split("=")[-1]

    #         data = {"file": file, "xsl": xsl, "picture": picture}
    #         file_metadata.append(data)

    # with open("file-metadata.csv", "w") as fp:
    #     for data in file_metadata:
    #         fp.write(f"{data['file']},{data['xsl']},{data['picture']}\n")

    list_of_files = os.listdir(data_dir)
    for filename in list_of_files:
        if filename.endswith(".html"):
            filename = filename.split(".html")[0]
            convert_html_to_md(filename)


if __name__ == "__main__":
    main()
