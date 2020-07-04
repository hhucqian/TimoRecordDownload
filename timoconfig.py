import configparser


class TimoConfig:
    def __init__(self, file: str):
        self.configfilepath = file
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

    def __str__(self):
        return "\t".join([f"record_list_url={self.record_list_url}",
                          f"flv_list_url={self.flv_list_url}",
                          f"local_library={self.local_library}",
                          f"header_count={self.header_count}"])
