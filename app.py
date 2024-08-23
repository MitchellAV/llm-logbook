from markdownify import MarkdownConverter
from bs4 import BeautifulSoup
import os

data_dir = "./data"
output_dir = "./output"


def md(
    soup: BeautifulSoup,
    options: MarkdownConverter.Options | None = MarkdownConverter.DefaultOptions,
) -> str:
    markdown_converter = MarkdownConverter(options=options)
    markdown_data = markdown_converter.convert_soup(soup)
    return markdown_data


def modify_markdownify_options() -> MarkdownConverter.Options:
    options = MarkdownConverter.DefaultOptions

    # Modify the markdownify options
    return options


def modify_html(soup: BeautifulSoup) -> BeautifulSoup:
    # Modify the html content
    return soup


def convert_html_to_md(filename: str) -> str:
    # Read the html content from a file
    with open(f"{data_dir}/{filename}.html", "r") as fp:
        soup = BeautifulSoup(fp, "html.parser")

    # Modify the html content
    soup = modify_html(soup)

    # Convert the data to markdown
    markdownify_options = modify_markdownify_options()
    markdown_data = md(soup, markdownify_options)

    # Save the markdown to a file
    with open(f"{output_dir}/{filename}.md", "w") as fp:
        fp.write(markdown_data)


def main():
    list_of_files = os.listdir(data_dir)
    for filename in list_of_files:
        if filename.endswith(".html"):
            convert_html_to_md(filename)


if __name__ == "__main__":
    main()
