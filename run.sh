#!/bin/bash

# 检查并安装依赖
echo "Installing required Python packages..."
pip3 install -r requirements.txt

# 运行 Python 脚本
echo "Running the Markdown image downloader..."
python3 replace.py "$@"