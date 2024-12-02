# Markdown Image URL Localizer

A tool to download remote images and replace their URLs with local paths in Markdown files.

## 📝 Description

This tool helps you convert Markdown files by:
- Downloading remote images to your local directory
- Replacing remote image URLs with local file paths
- Preserving your original Markdown content structure

> ⚠️ **Important**: Always create a backup of your Markdown files before running this tool!

## 🚀 Installation

1. Clone this repository:

```bash
git clone [repository-url]
cd markdown-image-localizer
```

2. Install dependencies:

```bash
pip3 install -r requirements.txt
```

## 💻 Usage

```bash
python3 replace.py <folder_path>
```

Where:
- `folder_path`: Path to the folder containing Markdown files to process

Example:

```bash
python3 replace.py ./my_markdown_files
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
