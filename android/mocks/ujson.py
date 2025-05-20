import sys

if "ujson" not in sys.modules:
    sys.modules["ujson"] = sys.modules["json"]