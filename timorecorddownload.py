import json
import logging
import os
import os.path
import shutil
import urllib.request

from flvitem import FLVItem
from recorditem import RecordItem
from timoconfig import TimoConfig


class TimoRecordDownload:
    def __init__(self):
        self.cfg = TimoConfig("/etc/timo/timo.conf")

        self.logger = logging.getLogger("TimoRecordDownload")
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        handler = logging.FileHandler("/var/log/timo.log")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def get_request_from_url(self, url: str) -> urllib.request.Request:
        req = urllib.request.Request(url)
        for k in self.cfg.headers:
            req.add_header(k, self.cfg.headers[k])
        return req

    def run(self):
        self.logger.info("get info from %s", self.cfg.record_list_url)
        request = self.get_request_from_url(self.cfg.record_list_url)
        content = ""
        with urllib.request.urlopen(request) as f:
            content = f.read().decode('utf-8')
        content = json.loads(content)
        if "data" in content and "count" in content["data"] and content["data"]["count"] > 0:
            content = content["data"]["list"][0]
            recordItem = RecordItem(
                content["rid"], content["start_timestamp"])
        else:
            self.logger.warn("get record item fail")
            return
        self.logger.info("get record item %s", recordItem)

        flv_list_url = self.cfg.flv_list_url.replace("++++", recordItem.rid)
        self.logger.info("get info from %s", flv_list_url)
        request = self.get_request_from_url(flv_list_url)
        with urllib.request.urlopen(request) as f:
            content = f.read().decode('utf-8')
        content = json.loads(content)
        flv_items = []
        if "data" in content and "list" in content["data"]:
            for index in range(len(content["data"]["list"])):
                flv_items.append(
                    FLVItem(index + 1, content["data"]["list"][index]["url"]))
        else:
            self.logger.warn("get flv list fail")
            return
        self.logger.info("get %d flv items", len(flv_items))

        if not os.path.exists(self.cfg.local_library):
            os.makedirs(self.cfg.local_library)
            self.logger.info("create folders %s", self.cfg.local_library)

        save_dir = os.path.join(self.cfg.local_library, recordItem.time_str)
        if os.path.exists(save_dir):
            self.logger.warn("%s exists", save_dir)
            return
        self.logger.info("create folders %s", save_dir)
        os.makedirs(save_dir)

        for item in flv_items:
            local_flv_path = os.path.join(save_dir, str(item.idx) + ".flv")
            request = self.get_request_from_url(item.url)
            self.logger.info("start to get #%d flv %s",
                             item.idx, local_flv_path)
            with urllib.request.urlopen(request) as ffrom, open(local_flv_path, mode="bw") as fto:
                chunk = ffrom.read(16*1024)
                while chunk:
                    fto.write(chunk)
                    chunk = ffrom.read(16*1024)
        self.logger.info("DONE!")
