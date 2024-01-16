## Set up environment

You can install this repository by
```
pip install git+https://github.com/cancercentereu/python-client.git
```

## Example

```python
from ccai_client import API
import json

organization = input('Enter organization codename: ')

api = API(organization)

file_id = '<YOUR FILE ID>'
file = File.get(api, id=file_id)

print(file.name)
```

## How to use
Please take a look at the `examples` folder. The notebook [working-with-slides.ipynb](/examples/working-with-slides.ipynb) shows how to use the library to download histopathology data.