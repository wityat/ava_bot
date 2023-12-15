import os
from importlib import import_module

from tg_bot import dp

for module in os.listdir(os.path.dirname(__file__)):
    if module in ("__init__.py", "states.py") or module[-3:] != ".py":
        continue
    dp.include_router(getattr(import_module(f".{module[:-3]}", __package__), "ui"))
