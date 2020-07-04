class FLVItem:
    def __init__(self, idx: int, url: str):
        self.idx = idx
        self.url = url

    def __str__(self):
        return "\n".join([f"idx={self.idx}",
                          f"url={self.url}"])
