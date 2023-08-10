import json
import os
import re
import shutil
from collections import OrderedDict
from datetime import datetime

import frontmatter
import mistune


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content


def save_as_html_file(file_path, content):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def read_config(content_folder_path):
    config_path = os.path.join(content_folder_path, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            config_data = json.load(file)
        return config_data
    else:
        return []


def get_nav_struct(content_folder_path):
    folder_list = []
    file_list = []

    ignored_items = ["imgs", "index.md", "config.json"]

    for item in os.listdir(content_folder_path):
        if not item.startswith(".") and item not in ignored_items:
            item_path = os.path.join(content_folder_path, item)
            if os.path.isdir(item_path):
                folder_list.append(item_path)
            elif os.path.isfile(item_path):
                file_list.append(item_path)

    return folder_list, file_list


def read_base_html():
    current_script_path = os.path.abspath(__file__)
    base_html_file_path = os.path.join(
        os.path.dirname(current_script_path), "static", "base.html"
    )
    return read_file(base_html_file_path)


def customize_base_html(base_html, config, folder_list, file_list):
    if "lang" in config:
        base_html = base_html.replace("en-US", config["lang"])
    if "title" in config:
        base_html = base_html.replace(">My Flea Site<", ">" + config["title"] + "<")
    if "author" in config:
        base_html = base_html.replace(
            '<!-- <meta name="author" content=""> -->',
            '<meta name="author" content="{}">'.format(config["author"]),
        )
    if "footer" in config:
        base_html = base_html.replace("<!-- footer -->", config["footer"])
    if "nav" in config:
        base_html = base_html.replace(
            "<!-- nav -->", generate_custom_nav(config["nav"])
        )
    else:
        base_html = base_html.replace(
            "<!-- nav -->", generate_default_nav(folder_list, file_list)
        )
    return base_html


def generate_custom_nav(markdown_nav_list):
    nav_html = ""
    for markdown_link in markdown_nav_list:
        nav_html += parse_markdown_link(markdown_link)
    return nav_html


def parse_markdown_link(link):
    return mistune.html(link)[3:-5] + "\n"


def generate_default_nav(folder_list, file_list):
    folder_list.sort()
    file_list.sort()

    nav_html = '<a href="/">Home</a>\n'

    for folder in folder_list:
        folder_name = folder.split("/")[-1]
        url = "/" + folder_name
        title = folder_name
        nav_html += '<a href="{}">{}</a>\n'.format(url, title)

    for file in file_list:
        file_name = file.split("/")[-1]
        url = "/" + os.path.splitext(file_name)[0] + ".html"
        title = file_name.split(".")[0]
        metadata = read_metadata(file)
        if "title" in metadata:
            title = metadata["title"]
        nav_html += '<a href="{}">{}</a>\n'.format(url, title)

    return nav_html


def read_metadata(markdown_file_path):
    markdown_content = read_file(markdown_file_path)
    post = frontmatter.loads(markdown_content)
    return post.metadata


def parse_markdown_file(file_path, base_html):
    markdown_content = read_file(file_path)
    post = frontmatter.loads(markdown_content)

    parser = mistune.create_markdown(
        plugins=["strikethrough", "footnotes", "table", "task_lists"]
    )
    main_html = parser(post.content)

    html = base_html.replace("<!-- main -->", main_html)

    return html


# WARNING! This function will first REMOVE public_folder_path!
def generate_site(
    base_html, content_folder_path, public_folder_path, folder_list, file_list
):
    # generate public folder, copy style & imgs
    os.makedirs(public_folder_path)

    script_absolute_path = os.path.abspath(__file__)
    flea_absolute_path = os.path.dirname(script_absolute_path)

    shutil.copytree(
        os.path.join(flea_absolute_path, "static"),
        os.path.join(public_folder_path, "static"),
    )

    shutil.copytree(
        os.path.join(content_folder_path, "imgs"),
        os.path.join(public_folder_path, "imgs"),
    )

    # generate index.html
    save_as_html_file(
        os.path.join(public_folder_path, "index.html"),
        parse_markdown_file(os.path.join(content_folder_path, "index.md"), base_html),
    )

    # tag_dict
    tag_dict = {}

    # generate outter pages
    for file in file_list:
        file_name = file.split("/")[-1]
        html_path = os.path.join(
            public_folder_path, os.path.splitext(file_name)[0] + ".html"
        )
        html = generate_single_page(file, base_html)
        save_as_html_file(html_path, html)

        metadata = read_metadata(file)
        if "tags" in metadata:
            date = datetime(1970, 1, 1).date()
            if "date" in metadata:
                date = metadata["date"]
            title = os.path.splitext(file_name)[0]
            if "title" in metadata:
                title = metadata["title"]
            update_tag_dict(
                tag_dict,
                metadata["tags"],
                [date, title, "/" + html_path.split("/")[-1]],
            )

    # generate folders & inner pages
    for folder in folder_list:
        folder_name = folder.split("/")[-1]
        os.makedirs(os.path.join(public_folder_path, folder_name))

        title = folder_name
        config = read_config(content_folder_path)
        if "nav" in config:
            for item in config["nav"]:
                match = re.search(r"\[(.*?)\]\((.*?)\)", item)
                if match:
                    text = match.group(1)
                    link = match.group(2)

                    if link == "/" + folder_name:
                        title = text

        index_path = os.path.join(folder, "index.md")
        if os.path.exists(index_path):
            html = parse_markdown_file(index_path, base_html)
        else:
            html = base_html
        html = re.sub(r"<title>.*?</title>", "<title>{}</title>".format(title), html)

        page_list_html = generate_page_list(
            base_html, content_folder_path, public_folder_path, folder, tag_dict
        )
        html = html.replace("<!-- list -->", page_list_html)
        html = html.replace("<main>", "<main><h1>{}/</h1>".format(folder_name))

        save_as_html_file(
            os.path.join(public_folder_path, folder_name, "index.html"), html
        )

    # generate tag page
    tag_page_html = generate_tag_page(tag_dict, base_html)
    save_as_html_file(os.path.join(public_folder_path, "tags.html"), tag_page_html)

    # generate 404 page
    fof_html = base_html.replace("<main>", "<main><h1>404</h1>\n")
    if os.path.exists(os.path.join(content_folder_path, "404.md")):
        fof_html = parse_markdown_file(
            os.path.join(content_folder_path, "404.md"), base_html
        )
    save_as_html_file(os.path.join(public_folder_path, "404.html"), fof_html)


def generate_single_page(file_path, base_html):
    html = parse_markdown_file(file_path, base_html)

    metadata = read_metadata(file_path)
    if "date" in metadata:
        html = html.replace(
            "<main>",
            '<main><span class="date"><p>{}</p></span>'.format(metadata["date"]),
        )
    if "title" in metadata:
        html = re.sub(
            r"<title>.*?</title>",
            "<title>{}</title>".format(metadata["title"]),
            html,
        )
        html = html.replace("<main>", "<main><h1>{}</h1>".format(metadata["title"]))
    if "tags" in metadata:
        tags_html = '<p class="tags"></p>'
        for tag in metadata["tags"]:
            tags_html = tags_html.replace(
                "</p>", '<a href="/tags.html#{}"># {}</a></p>'.format(tag, tag)
            )
        html = html.replace("</main>", "<small>" + tags_html + "</small></main>")
    return html


def update_tag_dict(tag_dict, tags, page_info):
    for tag in tags:
        if tag not in tag_dict:
            page_info_list = [page_info]
            tag_dict[tag] = page_info_list
        else:
            tag_dict[tag].append(page_info)


def generate_page_list(
    base_html, content_folder_path, public_folder_path, folder_path, tag_dict
):
    file_list = []
    for item in os.listdir(folder_path):
        if not item.startswith(".") and item != "index.md":
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                file_list.append(item_path)

    page_info_list = []
    for file in file_list:
        metadata = read_metadata(file)
        date = datetime(1970, 1, 1).date()
        if "date" in metadata:
            date = metadata["date"]
        title = os.path.splitext(os.path.basename(file))[0]
        if "title" in metadata:
            title = metadata["title"]

        file_base_name = file.split("/")[-2] + "/" + file.split("/")[-1].split(".")[0]
        save_as_html_file(
            os.path.join(public_folder_path, file_base_name + ".html"),
            generate_single_page(
                os.path.join(content_folder_path, file_base_name + ".md"), base_html
            ),
        )
        url = "/" + file_base_name + ".html"

        if "tags" in metadata:
            update_tag_dict(tag_dict, metadata["tags"], [date, title, url])

        page_info_list.append([date, title, url])
    page_info_list = sorted(page_info_list, key=lambda item: item[0], reverse=True)

    page_info_list_html = ""
    for page_info in page_info_list:
        page_info_list_html += "<li>\n"
        page_info_list_html += '<span class="date">{}</span>\n'.format(page_info[0])
        page_info_list_html += '<a href="{}">{}</a>\n'.format(
            page_info[2], page_info[1]
        )
        page_info_list_html += "</li>\n"
    page_info_list_html = '<ul class="page-list">\n' + page_info_list_html + "</ul>"

    return page_info_list_html


def generate_tag_page(tag_dict, base_html):
    ordered_tag_dict = OrderedDict()
    for tag, page_info_list in tag_dict.items():
        ordered_tag_dict[tag] = sorted(
            page_info_list, key=lambda item: item[0], reverse=True
        )
    ordered_tag_dict = OrderedDict(
        sorted(ordered_tag_dict.items(), key=lambda item: item[1][0][0], reverse=True)
    )

    tag_list_html = ""
    for tag, page_info_list in ordered_tag_dict.items():
        single_tag_html = ""
        for page_info in page_info_list:
            single_tag_html += "<li>\n"
            single_tag_html += '<span class="date">{}</span>\n'.format(page_info[0])
            single_tag_html += '<a href="{}">{}</a>\n'.format(
                page_info[2], page_info[1]
            )
            single_tag_html += "</li>\n"
        single_tag_html = (
            '<li class="tag" id="{}">{}<ul class="page-list">\n'.format(tag, tag)
            + single_tag_html
            + "</ul></li>\n"
        )
        tag_list_html += single_tag_html
    tag_list_html = '<h1>Tags</h1>\n<ul class="tags">\n' + tag_list_html + "</ul>"

    tag_page_html = base_html.replace("<!-- main -->", tag_list_html)
    tag_page_html = re.sub(r"<title>.*?</title>", "<title>Tags</title>", tag_page_html)

    return tag_page_html


def main(content_folder_path, public_folder_path):
    config = read_config(content_folder_path)
    folder_list, file_list = get_nav_struct(content_folder_path)

    base_html = read_base_html()
    base_html = customize_base_html(base_html, config, folder_list, file_list)

    if os.path.exists(public_folder_path):
        shutil.rmtree(public_folder_path)

    # WARNING! This function will first REMOVE public_folder_path!
    generate_site(
        base_html, content_folder_path, public_folder_path, folder_list, file_list
    )


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) != 2:
        print("Usage: python path_to_flea.py content_folder_path")
        sys.exit(1)

    content_folder_path = sys.argv[1]

    flea_abs_path = os.path.dirname(os.path.abspath(__file__))

    main(content_folder_path, os.path.join(flea_abs_path, "flea-site"))
