import pytube
import requests
from PIL import Image
from io import BytesIO


class YoutubeVid:
    def __init__(self, vid):
        self.author = vid.author
        self.date = vid.publish_date
        self.rating = vid.rating
        self.length = vid.length
        self.views = vid.views
        self.title = vid.title
        self.thumb = self.vid_thumb(vid)
        self.streams = vid.streams.filter(progressive=True).desc()

        self.vid_thumb(vid)

    def _convertToPng(self, img):
        with BytesIO() as f:
            img.save(f, format="PNG")
            return f.getvalue()

    def vid_thumb(self, vid):
        url = vid.thumbnail_url
        img = Image.open(requests.get(url, stream=True).raw).resize((384, 216))
        thumbnail = self._convertToPng(img)
        return thumbnail
