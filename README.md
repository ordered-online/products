# ordered online products service

This django based micro service provides an API to obtain products from locations.

## Technology Stack

- Python 3
- Django

## Quickstart

```
$ python3 -m pip install -r requirements.txt
```

Run the server in development mode.

```
$ cd codes
$ python3 manage.py migrate
$ python3 manage.py runserver 127.0.0.1:8002
```

Note that verification based endpoints need the `locations` and the `verification` service to run.

## Admin panel

The admin panel is accessible to a superuser via `/products/admin/`
