# Flask API Server

## Quick Start in `Docker`
> Start the app in Docker

```bash
$ docker build -t queds_api
$ docker run -it queds_api
```

The API server will start using the PORT `5000`

## Development

> **Step #1** - Create a virtual environment using python3

```bash
$ mkvirtualenv -p /usr/bin/python3.7 queds_api
$ workon queds_api
```

> **Step #2** - Install dependencies

```bash
$ pip install -r requirements.txt
```

> **Step #3** - Start the server at `localhost:5000`

Check configuration parameters in `../config/` folder.

> **Step #4** - Start the server at `localhost:5000`

```bash
$ WEB_SETTINGS=config/local.py python app.py
```

> **Step #5** - Check Swagger Dashboard at http://localhost:5000/api/

## Testing

Using pytest:
```
pytest tests.py
```

Or unittests
```
BACKEND_SETTINGS=config.local python -m unittest
```

## Pycharm debug
Disable `Gevent compatible` in Debugger settings