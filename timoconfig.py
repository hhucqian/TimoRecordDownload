import configparser
import logging
import os


class TimoConfig:
    def __init__(self):
        self.configfilepath = "/etc/timo/timo.conf"
        self.log_file_path = "/var/log/timo/timo.log"
        self.config = configparser.ConfigParser()
        self.config.read(self.configfilepath)
        self.record_list_url = self.config.get("bilibili", "record_list_url")
        self.flv_list_url = self.config.get("bilibili", "flv_list_url")
        self.header_count = self.config.getint("bilibili", "header_count")
        self.headers = {}
        for i in range(self.header_count):
            kv = self.config.get("bilibili", f"header_{i+1}")
            kv = kv.split(":", maxsplit=1)
            self.headers[kv[0]] = kv[1].strip()

        self.local_library = self.config.get("local", "library")

        self._logger = logging.getLogger("TimoRecordDownload")
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        handler = logging.FileHandler(self.log_file_path, encoding="utf-8")
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)

    @property
    def logger(self):
        return self._logger
