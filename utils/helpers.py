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

def decode_double_encoding(url: str) -> str:
    decoded_path = url
    while True:
        prev_str = decoded_path
        decoded_path = urllib.parse.unquote(decoded_path)
        if prev_str == decoded_path:
            break
    return decoded_path

def without_param_fragment(url: str):
    parsed_url = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
    
def without_fragment(url: str):
    parsed_url = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.query, parsed_url.params, ''))
    