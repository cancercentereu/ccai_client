from ccai_client import API, File
from ccai_client.file_classes import PathologySlideNode

api = API("https://api.cancercenter.ai", "patho")

images = File.get(api, id="7807ee72-7440-4e22-87b8-7e237ad5d79a")
for item in images.children():
    if isinstance(item, PathologySlideNode):
        item.download_original(path="data/" + item.name)
