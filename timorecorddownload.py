import json
import os
import os.path
import shutil
import platform
import urllib.request
import sqlite3
import datetime

from timoconfig import TimoConfig
from timorecorddb import TimoRecordDB


class RecordItem:
    def __init__(self, json_item):
        self.origin_json = json_item
        self.rid = json_item["rid"]
        self.title = json_item["title"]
        self.start_timestamp = json_item["start_timestamp"]
        self.time_str = datetime.datetime.fromtimestamp(self.start_timestamp).strftime("%Y%m%d")

    @property
    def json_str(self):
        return json.dumps(self.origin_json, ensure_ascii=False, indent=2)

    def __str__(self):
        return "  ".join([f"rid={self.rid}", f"start_timestamp={self.start_timestamp}", f"time_str={self.time_str}"])

class FLVItem:
    def __init__(self, idx: int, url: str):
        self.idx = idx
        self.url = url

    def __str__(self):
        return "  ".join([f"idx={self.idx}", f"url={self.url}"])


class TimoRecordDownload:
    def __init__(self):
        self.cfg = TimoConfig()
        self.logger = self.cfg.logger
        self.init_library_path()
        self.db = TimoRecordDB(os.path.join(self.cfg.local_library, "data.db"))

    def init_library_path(self):
        if not os.path.exists(self.cfg.local_library):
            os.makedirs(self.cfg.local_library)
            self.logger.info("create folders %s", self.cfg.local_library)

    def get_request_from_url(self, url):
        req = urllib.request.Request(url)
        for k in self.cfg.headers:
            req.add_header(k, self.cfg.headers[k])
        return req

    def get_content_str_from_request(self, request):
        content = ""
        with urllib.request.urlopen(request) as f:
            content = f.read().decode('utf-8')
        return content

    def get_record_list(self):
        res = []
        request = self.get_request_from_url(self.cfg.record_list_url)
        response_str = self.get_content_str_from_request(request)
        response_json = json.loads(response_str)
        if "data" in response_json and "count" in response_json["data"] and response_json["data"]["count"] > 0:
            for content in response_json["data"]["list"]:
                recordItem = RecordItem(content)
                res.append(recordItem)
        return res

    def get_flv_list(self, rid):
        res = []
        flv_list_url = self.cfg.flv_list_url.replace("++++", rid)
        request = self.get_request_from_url(flv_list_url)
        response_str = self.get_content_str_from_request(request)
        response_json = json.loads(response_str)
        if "data" in response_json and "list" in response_json["data"]:
            for index in range(len(response_json["data"]["list"])):
                res.append(FLVItem(index + 1, response_json["data"]["list"][index]["url"]))
        return res

    def create_save_dir(self, item):
        save_dir_index = 1
        save_dir = os.path.join(self.cfg.local_library, item.time_str)
        while os.path.exists(save_dir):
                save_dir = os.path.join(self.cfg.local_library, item.time_str + "_" + str(save_dir_index))
                save_dir_index += 1
        self.logger.info("create folder %s", save_dir)
        os.makedirs(save_dir)
        return save_dir

    def download_flv_items(self, flv_items, save_dir):
        for item in flv_items:
            local_flv_path = os.path.join(save_dir, str(item.idx) + ".flv")
            self.logger.info("start to get #%d flv %s", item.idx, local_flv_path)
            request = self.get_request_from_url(item.url)
            with urllib.request.urlopen(request) as ffrom, open(local_flv_path, mode="bw") as fto:
                chunk = ffrom.read(16*1024)
                while chunk:
                    fto.write(chunk)
                    chunk = ffrom.read(16*1024)

    def run(self):
        record_items = self.get_record_list()
        self.logger.info("get %d record items", len(record_items))
        for item in record_items:
            if self.db.isDownloaded(item.rid):
                self.logger.info(f"skip one record rid={item.rid} title={item.title}")
                continue
            flv_items = self.get_flv_list(item.rid)
            self.logger.info("get %d flv items", len(flv_items))
            save_dir = self.create_save_dir(item)
            with open(os.path.join(save_dir, "info.json"), "wt", encoding="utf-8") as f:
                f.write(item.json_str)
            self.logger.info("start to download flv files")
            self.download_flv_items(flv_items, save_dir)
            self.db.markDownload(item.rid)
        self.logger.info("DONE!")
