We use the `pytest` framework to test our small tests. 

You should install [redis](http://redis.io) first and start the service on `redis://localhost:6379`.

#### Prerequisition

1. Run the following command in your command line:

```
pip install -U pytest
pip install -U redis
```
2. Check that you have installed the correct version

```
pytest --version
```

#### Testing

run the following command in the `tiny_bot/tests` folder
```
$ pytest
======================= test session starts =======================
......
......
......
======================= 9 passed in 3.28 seconds =======================
```
