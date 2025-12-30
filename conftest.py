# Instruct pytest to ignore legacy test modules that have conflicting basenames
collect_ignore = [
    "user-service/tests/test_smoke.py",
    "orders-service/tests/test_smoke.py",
]
