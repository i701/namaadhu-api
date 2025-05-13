# namaadhu-api
Namaadhu API in fastapi to return prayer times both in json and xml for a given date.


# Development
1. Clone the repository
2. make a virtual environment
```
uv venv
```
3. Activate the environment [check uv documentation](https://docs.astral.sh/uv/pip/environments/#using-a-virtual-environment)
4. Install the requirements
```
uv pip install -r requirements.txt
```
5. Run the dev server
```
fastapi dev main.py
```

# How to use this
There is only one endpoint which accepts a date in mm/dd/yyyy format. You can pass format=json to get a response in json. By default it will give xml.


```
/prayertimes/?date_input=04/02/2025
```