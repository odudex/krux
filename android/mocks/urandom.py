import sys

if "urandom" not in sys.modules:
    sys.modules["urandom"] = sys.modules["random"]