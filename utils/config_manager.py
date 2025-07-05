### utils/config_manager.py ###
from helpers import load_yaml

class ConfigManager:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.config = None

    async def load_config(self):
        try:
            self.config = await load_yaml(self.config_file_path)
        except Exception as e:
            print(f"Gagal memuat konfigurasi: {e}")

    def get_config(self):
        return self.config

    def get_global_config(self):
        return self.config.get('global_config', {})

    def get_http_request_config(self):
        return self.config.get('http-request_config', {})

    def get_domain_check_config(self):
        return self.config.get('domain-check_config', {})

    def get_crawler_config(self):
        return self.config.get('crawler_config', {})

    def get_executor_config(self):
        return self.config.get('executor_config', {})
