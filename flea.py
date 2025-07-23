import argparse
import datetime
import json
import os
import re
import shutil
from collections import OrderedDict

import frontmatter
import mistune


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content


def save_as_html_file(file_path, content):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def is_folder_empty_or_not_exists(folder_path):
    if not os.path.exists(folder_path):
        return True
    if os.path.isdir(folder_path):
        return not any(os.scandir(folder_path))
    return False


def read_config(src_folder_path):
    config_path = os.path.join(src_folder_path, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            config = json.load(file)
        return config
    else:
        return {}


def get_folder_struct(folder_path, ignore_404=False):
    folder_list, file_list = [], []
    ignored_items = ["config.json", "index.md", "static", "imgs"]
    if ignore_404:
        ignored_items.append("404.md")

    for item in os.listdir(folder_path):
        if item not in ignored_items:
            item_path = os.path.join(folder_path, item)

            if os.path.isdir(item_path):
                folder_list.append(item)
            if os.path.isfile(item_path) and item.endswith(".md"):
                file_list.append(item)

    return sorted(folder_list), sorted(file_list)


def generate_base_html(src_folder_path, config, folder_list, file_list):
    base_html = "<!DOCTYPE html>\n"
    base_html += f'<html lang="{config.get("lang", "en-US")}">\n'
    base_html += "<head>\n"
    base_html += '<meta charset="utf-8" />\n'
    base_html += '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'  # fmt: skip
    base_html += "<!-- flea-description -->\n"
    base_html += f'<meta name="author" content="{config.get("author","anonymous")}">\n'
    base_html += generate_favicon_html(config)
    base_html += generate_style_html(config)
    base_html += f'<title>{config.get("title","My Flea Site")}</title>\n'
    base_html += generate_script_html(config)
    base_html += "</head>\n"
    base_html += "<body>\n"
    base_html += "<header>\n"
    base_html += f'<h2>{config.get("title","My Flea Site")}</h2>\n'
    base_html += generate_nav_html(src_folder_path, config, folder_list, file_list)
    base_html += "</header>\n"
    base_html += "<main><!-- flea-main --><!-- flea-list --><!-- flea-tags --></main>\n"
    base_html += f'<footer>{config["footer"]}</footer>' if "footer" in config else ""
    base_html += "</body>"
    base_html += "</html>"

    return base_html


def generate_favicon_html(config):
    favicon_html = ""

    disable_default_favicon = config.get("disable_default_favicon", False)
    if not disable_default_favicon:
        for size in [16, 32, 96]:
            favicon_html += f'<link rel="icon" type="image/png" href="/static/flea-favicon-{size}.png" sizes="{size}x{size}" />\n'

    favicons = config.get("favicons", [])
    for favicon in favicons:
        if favicon.startswith('<link rel="icon"'):
            favicon_html += favicon + "\n"

    return favicon_html


def generate_style_html(config):
    style_html = ""

    disable_default_style = config.get("disable_default_style", False)
    if not disable_default_style:
        style_html += '<link rel="stylesheet" type="text/css" href="/static/flea-style.css" />\n'  # fmt: skip

    styles = config.get("styles", [])
    for style in styles:
        if style.startswith('<link rel="stylesheet"'):
            style_html += style + "\n"
        else:
            style_html += f'<link rel="stylesheet" type="text/css" href="{style}" />\n'

    return style_html


def generate_script_html(config):
    script_html = ""

    scripts = config.get("scripts", [])
    for script in scripts:
        if script.startswith("<script"):
            script_html += script + "\n"
        else:
            script_html += f'<script src="{script}"></script>\n'

    return script_html


def generate_nav_html(src_folder_path, config, folder_list, file_list):
    nav_html = ""

    nav = config.get("nav", [])
    if nav:
        for item in nav:
            nav_html += mistune.html(item)[3:-5] + "\n"
    else:
        nav_html += '<a href="/">Home</a>\n'

        for folder in folder_list:
            folder_name = folder

            url = "/" + folder_name
            title = folder_name
            nav_html += f'<a href="{url}">{title}</a>\n'

        for file in file_list:
            file_name = os.path.splitext(file)[0]
            file_path = os.path.join(src_folder_path, file)
            metadata = frontmatter.loads(read_file(file_path)).metadata

            url = "/" + file_name + ".html"
            title = metadata.get("title", file_name)
            nav_html += f'<a href="{url}">{title}</a>\n'

    return nav_html


def init_dst_folder(src_folder_path, dst_folder_path, config):
    if os.path.exists(dst_folder_path):
        shutil.rmtree(dst_folder_path)
    os.mkdir(dst_folder_path)

    flea_abs_path = os.path.abspath(os.path.dirname(__file__))

    src_static_path = os.path.join(src_folder_path, "static")
    dst_static_path = os.path.join(dst_folder_path, "static")

    src_imgs_path = os.path.join(src_folder_path, "imgs")
    dst_imgs_path = os.path.join(dst_folder_path, "imgs")

    if not is_folder_empty_or_not_exists(src_static_path):
        shutil.copytree(src_static_path, dst_static_path)

    if not os.path.exists(dst_static_path):
        os.mkdir(dst_static_path)

    disable_default_favicon = config.get("disable_default_favicon", False)
    if not disable_default_favicon:
        for size in [16, 32, 96]:
            shutil.copy2(
                os.path.join(flea_abs_path, f"static/flea-favicon-{size}.png"),
                dst_static_path,
            )

    disable_default_style = config.get("disable_default_style", False)
    if not disable_default_style:
        shutil.copy2(
            os.path.join(flea_abs_path, "static/flea-style.css"), dst_static_path
        )

    if not is_folder_empty_or_not_exists(src_imgs_path):
        shutil.copytree(src_imgs_path, dst_imgs_path)


def generate_site(src_folder_path, dst_folder_path, config, base_html, folder_list, file_list):  # fmt: skip
    parser = get_parser()
    tags_info = {}

    generate_index_page(src_folder_path, dst_folder_path, base_html, parser)
    generate_404_page(src_folder_path, dst_folder_path, base_html, parser)
    generate_outer_pages(src_folder_path, dst_folder_path, base_html, parser, file_list, tags_info)  # fmt: skip
    generate_inner_pages(src_folder_path, dst_folder_path, config, base_html, parser, folder_list, tags_info)  # fmt: skip
    generate_tags_page(dst_folder_path, base_html, tags_info)


def generate_index_page(src_folder_path, dst_folder_path, base_html, parser):
    index_file_path = os.path.join(src_folder_path, "index.md")
    index_html_path = os.path.join(dst_folder_path, "index.html")

    index_page = parse_md_file(base_html, index_file_path, parser, ignore_metadata=True)

    save_as_html_file(index_html_path, index_page)


def generate_404_page(src_folder_path, dst_folder_path, base_html, parser):
    _404_file_path = os.path.join(src_folder_path, "404.md")
    _404_html_path = os.path.join(dst_folder_path, "404.html")

    _404_base_html = re.sub(r"<title>.*?</title>", "<title>404</title>", base_html)
    _404_base_html = _404_base_html.replace("<main>", "<main><h1>404</h1>")

    _404_page = _404_base_html
    if os.path.exists(_404_file_path):
        _404_page = parse_md_file(_404_base_html, _404_file_path, parser, ignore_metadata=True)  # fmt: skip

    save_as_html_file(_404_html_path, _404_page)


def generate_outer_pages(src_folder_path, dst_folder_path, base_html, parser, file_list, tags_info):  # fmt: skip
    for file in file_list:
        file_path = os.path.join(src_folder_path, file)
        file_name = os.path.splitext(file)[0]
        url = "/" + file_name + ".html"
        html_path = os.path.join(dst_folder_path, file_name + ".html")

        page, tags, date, title = parse_md_file(base_html, file_path, parser)

        save_as_html_file(html_path, page)
        update_tags_info(tags_info, tags, [date, title if title else file_name, url])


def generate_inner_pages(src_folder_path, dst_folder_path, config, base_html, parser, folder_list, tags_info):  # fmt: skip
    custom_nav = config.get("nav", [])

    for folder in folder_list:
        src_subfolder_path = os.path.join(src_folder_path, folder)
        dst_subfolder_path = os.path.join(dst_folder_path, folder)
        os.mkdir(dst_subfolder_path)

        folder_name = os.path.basename(folder)
        title = folder_name
        if custom_nav:
            for item in custom_nav:
                match = re.search(r"\[(.*?)\]\((.*?)\)", item)
                if match:
                    custom_title, custom_url = match.group(1), match.group(2)
                    title = custom_title if custom_url == "/" + folder_name else title

        inner_index_page = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", base_html)  # fmt: skip
        inner_index_page = inner_index_page.replace("<main>", f"<main><h1>{folder_name}/</h1>")  # fmt: skip

        inner_index_file_path = os.path.join(src_subfolder_path, "index.md")
        if os.path.exists(inner_index_file_path):
            inner_index_page = parse_md_file(inner_index_page, inner_index_file_path, parser, ignore_metadata=True)  # fmt: skip

        _, inner_file_list = get_folder_struct(src_subfolder_path)
        inner_page_info_list = []
        for file in inner_file_list:
            file_path = os.path.join(src_subfolder_path, file)
            file_name = os.path.splitext(file)[0]
            url = "/" + folder_name + "/" + file_name + ".html"
            html_path = os.path.join(dst_subfolder_path, file_name + ".html")

            page, tags, date, title = parse_md_file(base_html, file_path, parser)

            save_as_html_file(html_path, page)
            update_tags_info(tags_info, tags, [date, title if title else folder_name + "/" + file_name, url])  # fmt: skip
            inner_page_info_list.append([date, title if title else file_name, url])  # fmt: skip
        inner_page_info_list.sort(key=lambda item: item[0], reverse=True)

        inner_page_list_html = '<ul class="page-list">\n'
        for page_info in inner_page_info_list:
            inner_page_list_html += "<li>\n"
            inner_page_list_html += f'<span class="date">{page_info[0].date()}</span>\n'
            inner_page_list_html += f'<a href="{page_info[2]}">{page_info[1]}</a>\n'
            inner_page_list_html += "</li>\n"
        inner_page_list_html += "</ul>"

        inner_index_page = inner_index_page.replace('<!-- flea-list -->', inner_page_list_html)  # fmt: skip

        save_as_html_file(os.path.join(dst_subfolder_path, "index.html"), inner_index_page)  # fmt: skip


def generate_tags_page(dst_folder_path, base_html, tags_info):
    tags_html_path = os.path.join(dst_folder_path, "tags.html")

    ordered_tags_info = OrderedDict()
    for tag, page_info_list in tags_info.items():
        ordered_tags_info[tag] = sorted(
            page_info_list, key=lambda item: item[0], reverse=True
        )
    ordered_tags_info = OrderedDict(
        sorted(ordered_tags_info.items(), key=lambda item: item[1][0][0], reverse=True)
    )

    tag_list_html = ""
    for tag, page_info_list in ordered_tags_info.items():
        single_tag_html = ""
        for page_info in page_info_list:
            single_tag_html += "<li>\n"
            single_tag_html += f'<span class="date">{page_info[0].date()}</span>\n'
            single_tag_html += f'<a href="{page_info[2]}">{page_info[1]}</a>\n'
            single_tag_html += "</li>\n"
        single_tag_html = (
            f'<li class="tag" id="{tag}">{tag}<ul class="page-list">\n'
            + single_tag_html
            + "</ul></li>\n"
        )
        tag_list_html += single_tag_html
    tag_list_html = '<h1>Tags</h1>\n<ul class="tags">\n' + tag_list_html + "</ul>"

    tags_page = re.sub(r"<title>.*?</title>", "<title>Tags</title>", base_html)
    tags_page = tags_page.replace("<!-- flea-list -->", tag_list_html)

    save_as_html_file(tags_html_path, tags_page)


def get_parser():
    class CustomRenderer(mistune.HTMLRenderer):
        def image(self, alt, url, title=None):
            if not alt:
                alt = title
            img_html = f'<img src="{url}" alt="{alt}" />'
            if title:
                if title.endswith(", fit"):
                    img_html = f'<img class="fit" src="{url}" alt="{alt}" />'
                    title = title[: -len(", fit")]

                if title.endswith(", pano"):
                    img_html = f'<img class="pano" src="{url}" alt="{alt}" />'
                    title = title[: -len(", pano")]

                if title.endswith(", pair"):
                    img_html = f'<img class="pair_h" src="{url}" alt="{alt}" />'
                    title = title[: -len(", pair")]

                if title.endswith(", pair_h"):
                    img_html = f'<img class="pair_h" src="{url}" alt="{alt}" />'
                    title = title[: -len(", pair_h")]

                if title.endswith(", pair_v"):
                    img_html = f'<img class="pair_v" src="{url}" alt="{alt}" />'
                    title = title[: -len(", pair_v")]

                img_html += f'<span class="image-title">{title}</span>'
            return img_html

    plugins = [
        "strikethrough",
        "footnotes",
        "table",
        "task_lists",
        "mark",
        "superscript",
        "subscript",
    ]

    parser = mistune.create_markdown(renderer=CustomRenderer(), plugins=plugins)

    return parser


def parse_md_file(base_html, file_path, parser, ignore_metadata=False):
    post = frontmatter.loads(read_file(file_path))
    metadata, content = post.metadata, post.content

    html = base_html.replace("<!-- flea-main -->", merge_image_pairs(parser(content)))

    if not ignore_metadata:
        tags = metadata.get("tags", [])
        if tags:
            tags_html = '<small><p class="tags">\n'
            for tag in tags:
                tags_html += f'<a href="/tags.html#{tag}"># {tag}</a>\n'
            tags_html += "</p></small>"

            html = html.replace("<!-- flea-tags -->", tags_html)

        date = metadata.get("date", datetime.datetime(1970, 1, 1))
        if isinstance(date, datetime.date):
            date = datetime.datetime.combine(date, datetime.time())
        if date != datetime.datetime(1970, 1, 1):
            html = html.replace("<main>", f'<main><span class="date"><p>{date.date()}</p></span>')  # fmt: skip

        title = metadata.get("title", "")
        if title:
            html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html)
            html = html.replace("<main>", f"<main><h1>{title}</h1>")

        return html, tags, date, title

    return html


def merge_image_pairs(content_html):
    pattern = re.compile(
        r'<p><img class="pair_h" src="([^"]+)" alt="([^"]*)" />'
        r'<span class="image-title">((?:[^<]|<br>)*)</span></p>\s*'
        r'<p><img class="pair_h" src="([^"]+)" alt="([^"]*)" />'
        r'<span class="image-title">((?:[^<]|<br>)*)</span></p>'
        r"|"
        r'<p><img class="pair_v" src="([^"]+)" alt="([^"]*)" />'
        r'<span class="image-title">((?:[^<]|<br>)*)</span></p>\s*'
        r'<p><img class="pair_v" src="([^"]+)" alt="([^"]*)" />'
        r'<span class="image-title">((?:[^<]|<br>)*)</span></p>'
    )

    def repl(match):
        if match.group(1):  # pair_h matched
            src1, alt1, title1 = match.group(1), match.group(2), match.group(3)
            src2, alt2, title2 = match.group(4), match.group(5), match.group(6)
            div_class = "pair_h"
        else:  # pair_v matched
            src1, alt1, title1 = match.group(7), match.group(8), match.group(9)
            src2, alt2, title2 = match.group(10), match.group(11), match.group(12)
            div_class = "pair_v"

        alt = alt2 or alt1
        title = title2 or title1
        return (
            f"<p>"
            f'<div class="{div_class}">'
            f'<img class="pair" src="{src1}" alt="{alt}" />'
            f'<img class="pair" src="{src2}" alt="{alt}" />'
            f"</div>"
            f'<span class="image-title">{title}</span>'
            f"</p>"
        )

    return re.sub(pattern, repl, content_html)


def update_tags_info(tags_info, tags, page_info):
    for tag in tags:
        if tag not in tags_info:
            page_info_list = [page_info]
            tags_info[tag] = page_info_list
        else:
            tags_info[tag].append(page_info)


def flea(src_folder_path, dst_folder_path):
    config = read_config(src_folder_path)
    folder_list, file_list = get_folder_struct(src_folder_path, ignore_404=True)
    base_html = generate_base_html(src_folder_path, config, folder_list, file_list)
    init_dst_folder(src_folder_path, dst_folder_path, config)
    generate_site(src_folder_path, dst_folder_path, config, base_html, folder_list, file_list)  # fmt: skip


def main():
    parser = argparse.ArgumentParser(
        description="Generate a static website from Markdown files.", add_help=False
    )

    parser.add_argument(
        "-h", "--help", action="store_true", help="Show help message and exit."
    )
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "content"),
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "flea-site"),
    )

    args = parser.parse_args()

    if args.help:
        custom_help_message = "Flea - Generate a Static Website from Markdown Files\n\n"  # fmt: skip
        custom_help_message += "Usage:\n"
        custom_help_message += "  python flea.py [-h] [-s SOURCE] [-d DESTINATION]\n\n"
        custom_help_message += "Options:\n"
        custom_help_message += "  -h, --help         Show this help message and exit.\n"
        custom_help_message += "  -s, --source  SOURCE\n"  # fmt: skip
        custom_help_message += "                     Path to the source folder containing Markdown files.\n"  # fmt: skip
        custom_help_message += "  -d, --destination DESTINATION\n"  # fmt: skip
        custom_help_message += "                     Path to the destination folder as the root of the\n"  # fmt: skip
        custom_help_message += "                     generated site.\n"
        custom_help_message += "                     \033[91mWARNING: The destination folder will be REMOVED before\n"  # fmt: skip
        custom_help_message += "                     generating the site.\033[0m"  # fmt: skip

        print(custom_help_message)
    else:
        src_folder_path = args.source
        dst_folder_path = args.destination

        flea(src_folder_path, dst_folder_path)


if __name__ == "__main__":
    main()
