import os
import json
import yaml
import aiofiles
import urllib.parse
from slugify import slugify

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def slugify_url(url: str):
    return slugify(url.replace('/', '_').replace(':', ''))

async def load_json(path: str) -> dict:
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content)

async def save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        await f.write(json_str)

async def load_yaml(path: str) -> dict:
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        content = await f.read()
        return yaml.safe_load(content)

async def save_yaml(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    yaml_str = yaml.dump(data, allow_unicode=True)
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write(yaml_str)

def decode_double_encoding(encoded_str):
    decoded_str = encoded_str
    while True:
        prev_str = decoded_str
        decoded_str = urllib.parse.unquote(decoded_str)
        if prev_str == decoded_str:
            break
    return decoded_str
