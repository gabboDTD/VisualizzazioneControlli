# config_manager.py
import os
import yaml
from yaml.loader import SafeLoader

CONFIG_PATH_KEY = 'CONFIG_PATH'

class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.getenv(CONFIG_PATH_KEY, 'config.yaml')
        self.config_path = config_path
        self.config = self.load_config()

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
