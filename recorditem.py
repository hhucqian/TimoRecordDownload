from datetime import datetime


class RecordItem:
    def __init__(self, rid: str, start_timestamp: int):
        self.rid = rid
        self.start_timestamp = start_timestamp
        self.time_str = datetime.fromtimestamp(
            self.start_timestamp).strftime("%Y%m%d")

    def __str__(self):
        return "    ".join([f"rid={self.rid}",
                            f"start_timestamp={self.start_timestamp}",
                            f"time_str={self.time_str}"])


if __name__ == "__main__":
    item = RecordItem("R1tx411c7mE", 1592571904)
    print(item)
