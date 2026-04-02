import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_root, "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from pydaffodil import Daffodil

cli = Daffodil(
    inventory="inventory.ini",
    group="webservers",
    remote_path="/root/production",
)

steps = [
    {"step": "Copy build/ to production", "command": lambda: cli.transfer_files("build", "/root/production")}
]

cli.deploy(steps)
