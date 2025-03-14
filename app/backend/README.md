# Backend processor
Process all the petitions received via Redis queue

## Requirements
Redis

## Quick Start in `Docker`
> Start the app in Docker

```bash
$ docker build -t queds_backend
$ docker run -it queds_backend
```

## Development

> **Step #1** - Create a virtual environment using python3
```bash
$ mkvirtualenv -p /usr/bin/python3.7 queds_backend
$ workon queds_backend
```

> **Step #2** - Install dependencies
```bash
$ pip install -r requirements.txt
```

> **Step #3** - Install redis
```bash
$  docker run --name some-redis -d redis
```

> **Step #4** - Start the worker. Will listen to redis queues
```
BACKEND_SETTINGS=config.local python worker.py
```

## Test message using client

```
BACKEND_SETTINGS=config.local python client.py
```
