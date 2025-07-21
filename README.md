![flea icon by icons8](/static/flea-favicon-96.png)

# Flea: Static Website Generator

Flea is a Python script designed to simplify the process of generating static websites from Markdown files. It automates the conversion of Markdown content into HTML pages, providing customizable options for styling, navigation, and more.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Usage](#usage)
- [Markdown](#markdowns)
- [Content Folder Structure](#content-folder-structure)
- [Configuration](#configuration)
- [License](#license)

## Introduction

Flea is a static website generator that aims to streamline the process of creating static websites from Markdown content. It offers a lightweight solution for building websites without the need for complex frameworks or setups.

## Features

- **Easy Website Generation:** Flea simplifies turning content into a website with a single command.
- **Customization:** Customize website details like title, author, icons, navigation bar, and more.
- **External Styles and Scripts:** Easily add external CSS and JavaScript to enhance your site.

## Getting Started

### Installation

1. Clone this repository:

   ```sh
   git clone https://github.com/undr22/flea.git
   ```

### Usage

1. Navigate to the repository's root directory.

   ```sh
   cd flea
   ```

2. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Run the following command to generate the static website:

   ```sh
   python flea.py -s SOURCE -d DESTINATION
   ```

   Replace `SOURCE` with the path to your source folder containing Markdown files and `DESTINATION` with the path to the destination folder for the generated site.

   _NOTE: The destination folder will be REMOVED before generating the site._

   For more information and options, use:

   ```sh
   python flea.py -h
   ```

## Markdowns

Flea accepts all common Markdown syntax, and additionally includes: strikethrough, footnotes, tables, task lists, mark, superscript, subscript, and more.

Flea also supports extended syntax for images using the `title` field to apply special display styles. **Only one special tag is allowed per image**. The following suffixes are recognized at the end of the `title`:

* `, fit`: limits the image’s **display height** to avoid taking up too much space on the page.
* `, pano`: allows the image to **extend beyond the page width**, if possible.
* `, pair` / `, pair_h`: displays two consecutive images as a **horizontal pair**.
* `, pair_v`: displays two consecutive images as a **vertical pair**.

To enable a paired layout, **two images must appear consecutively and both must have matching `pair`-type suffixes** in their titles.

Example:

```
![Image 1](url1 "First image, pair")
![Image 2](url2 "Second image, pair")
```

In paired mode:

* Only **two** images are allowed per group.
* The **second image’s `alt` and `title`** will be used for display; if missing, it falls back to the first.

Standalone images will render normally, with their `title` shown below the image:

```html
<img class="fit" src="..." alt="..." /><span class="image-title">title</span>
```

At the beginning of a Markdown file, you can use YAML front matter to include metadata: `title`, `date`, and `tags`. These are parsed and styled distinctly in the output page. Example:

```
---
title: the Flea Manual
date: 2023-08-10
tags: [flea, doc, animal]
---
```

If you write multiple articles in one day and want them to sort precisely, you can append a timestamp:

```
---
date: 2023-08-10 12:00:00
---
```

*Note: All `index.md` files and the `404.md` in the root of the content folder do not support metadata.*

## Content Folder Structure

Flea expects a specific folder structure for your website content like this：

```
.
├── index.md              - Required
├── config.json           - Optional, custom configuration file
├── imgs                  - Optional, used to store images, must be named exactly "imgs"
│   └── flea.jpg
├── static                - Optional, used for static files, must be named exactly "static"
│   └── code-style.css
│   └── my_script.js
├── blog                  - Outer directory, included in the navigation bar
│   ├── my-back-itches.md
│   └── go-see-a-doctor.md
├── about.md              - Outer file, included in the navigation bar (excluding 404.md)
└── 404.md                - Used for generating the 404 page
```

Nested folders aren't permitted within the content directory. To put it simply, you can only add one additional layer of folders within the content folder. Pages of inner folders are displayed as directories, showcasing the pages rendered from their internal Markdown files.

Nonetheless, you have the option to include an index.md within an inner folder. This allows you to provide details about the folder. Unlike other files, this index.md won't be visible in the directory list. Instead, its content is directly read and displayed before the directory listing.

## Configuration

Flea offers customization through a `config.json` file located in the source folder. This JSON file lets you define specific website details, such as the title, author, styles, and navigation bar.

Here are the available options:

- **lang**: Language code, defaults to "en-US".
- **title**: Website title, defaults to "My Flea Site".
- **author**: Author's name, defaults to "anonymous".
- **nav**: Accept an array of markdown-style links. By default, the nav bar is based on the file structure.
- **footer**: Accept HTML codes, will be enclosed in `<footer></footer>` tag.
- **disable_default_favicon**: Set true to disable the default favicon (the tiny flea icon), defaults to false.
- **favicons**: Accept tags start with `<link rel="icon"`, it's recommended to provide icons of at least 16x16 and 32x32 sizes.
- **disable_default_style**: Set true to disable the default stylesheet, defaults to false.
- **styles**: Accept an array of paths to local or online stylesheet files, or HTML tags start with `<link rel="stylesheet"`.
- **scripts**: Accept an array of paths to local or online script files, or HTML tags start with `<script`.

A possible example:

```json
{
  "title": "Ken's blog",
  "author": "Ken",
  "footer": "This is Ken's footer.",
  "nav": [
    "[Home](/)",
    "[🖊️ Blogs](/blog)",
    "[⌨️ Codes](/code)",
    "[📷 Photos](/photo)",
    "[🧮 Math](/math)",
    "[About](/about-me.html)"
  ],
  "disable_default_styles": true,
  "styles": ["/static/my-style.css"],
  "scripts": [
    "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML",
    "<script type=\"text/x-mathjax-config\">MathJax.Hub.Config({tex2jax: {inlineMath: [['$', '$']], displayMath: [['$$', '$$']], processEscapes: true}});</script>"
  ]
}
```

## License

Flea is open-source software released under the [MIT License](https://opensource.org/licenses/MIT).

---

[Flea](https://icons8.com/icon/F2ynpEa6aUZd/fleaFlea) icon by [Icons8](https://icons8.com)
