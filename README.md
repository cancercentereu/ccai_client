## Set up environment

You can install this repository by
```
pip install git+https://github.com/cancercentereu/ccai_client.git
```

## Example

```python
from ccai_client import API, File

organization = input('Enter organization codename: ')

api = API(organization)

file_id = '<YOUR FILE ID>'
file = File.get(api, id=file_id)

print(file.name)
```

## How to use
Please take a look at the `notebooks` folder. The notebook [working_with_slides.ipynb](/notebooks/working_with_slides.ipynb) shows how to use the library to download histopathology data.
