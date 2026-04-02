import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_root, "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from pydaffodil import Daffodil

cli = Daffodil(remote_user="root", remote_host="203.161.53.228", remote_path="/root/production")

steps = [
    {"step": "Copy .env.test to production for testing .env if copied", "command": lambda: cli.transfer_files("build", "/root/production")}
]
cli.deploy(steps)
