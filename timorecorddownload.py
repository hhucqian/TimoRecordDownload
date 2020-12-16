import json
import os
import os.path
import shutil
import platform
import urllib.request
import sqlite3

from flvitem import FLVItem
from recorditem import RecordItem
from timoconfig import TimoConfig
from timorecorddb import TimoRecordDB


class TimoRecordDownload:
    def __init__(self):
        self.cfg = TimoConfig()
        self.logger = self.cfg.logger
        self.db = TimoRecordDB(os.path.join(self.cfg.local_library, "data.db"))

    def get_request_from_url(self, url: str) -> urllib.request.Request:
        req = urllib.request.Request(url)
        for k in self.cfg.headers:
            req.add_header(k, self.cfg.headers[k])
        return req

    def run(self):
        self.logger.info("get info from %s", self.cfg.record_list_url)
        request = self.get_request_from_url(self.cfg.record_list_url)
        content_raw = ""
        with urllib.request.urlopen(request) as f:
            content = json.loads(f.read().decode('utf-8'))
        if "data" in content and "count" in content["data"] and content["data"]["count"] > 0:
            for content in content["data"]["list"]:
                content_raw = json.dumps(content, indent=2, ensure_ascii=False)
                recordItem = RecordItem(
                    content["rid"], content["start_timestamp"])
                self.logger.info("get record item %s", recordItem)

                if self.db.isDownloaded(recordItem.rid):
                    self.logger.info("skip one record")
                    continue

                self.db.markDownload(recordItem.rid)

                flv_list_url = self.cfg.flv_list_url.replace(
                    "++++", recordItem.rid)

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
                    self.logger.info("create folders %s",
                                     self.cfg.local_library)
                    if hasattr(os, "chown"):
                        os.chown(self.cfg.local_library,
                                 self.cfg.uid, self.cfg.gid)

                save_dir = os.path.join(
                    self.cfg.local_library, recordItem.time_str)
                dir_index = 1
                while os.path.exists(save_dir):
                    save_dir = os.path.join(
                        self.cfg.local_library, recordItem.time_str + "_" + str(dir_index))
                    dir_index += 1
                self.logger.info("create folders %s", save_dir)
                os.makedirs(save_dir)
                if hasattr(os, "chown"):
                    os.chown(save_dir, self.cfg.uid, self.cfg.gid)

                with open(os.path.join(save_dir, "info.json"), "wt", encoding="utf-8") as f:
                    f.write(content_raw)

                for item in flv_items:
                    local_flv_path = os.path.join(
                        save_dir, str(item.idx) + ".flv")
                    self.logger.info("start to get #%d flv %s",
                                     item.idx, local_flv_path)
                    request = self.get_request_from_url(item.url)
                    with urllib.request.urlopen(request) as ffrom, open(local_flv_path, mode="bw") as fto:
                        chunk = ffrom.read(16*1024)
                        while chunk:
                            fto.write(chunk)
                            chunk = ffrom.read(16*1024)
                    if hasattr(os, "chown"):
                        os.chown(local_flv_path, self.cfg.uid, self.cfg.gid)

                self.logger.info("DONE!")
        else:
            self.logger.warn("get record item fail")
