# config_manager.py
import os
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv

CONFIG_PATH_KEY = 'CONFIG_PATH'
API_URL_KEY = 'API_URL'

class ConfigManager:
    def __init__(self, config_path=None):
        # Load environment variables from .env file
        load_dotenv()        
        if config_path is None:
            config_path = os.getenv(CONFIG_PATH_KEY, 'config.yaml')
        self.config_path = config_path
        self.config = self.load_config()

        # Load environment variables into the config if they exist
        self.config['api_url'] = os.getenv(API_URL_KEY, self.config.get('api_url', None))

    def load_config(self):
        """
        Load the configuration from a YAML file.

        Returns:
            dict: The loaded configuration.
        """
        with open(self.config_path, 'r', encoding='utf-8') as file:
            return yaml.load(file, Loader=SafeLoader)

    def save_config(self):
        """
        Save the current configuration to a YAML file.

        Returns:
            None
        """
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config, file, default_flow_style=False)
