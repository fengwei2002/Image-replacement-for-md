# replace_markdown_images_to_local_url

open markdown notes folder (**don't forget** to make a perfect backup before replacing).

usage: 

```sh
chmod +x run.sh
./run.sh
```

or 

```sh
echo "Installing required Python packages..."
pip3 install -r requirements.txt

echo "Running the Markdown image downloader..."
python3 replace.py "$@"
```
