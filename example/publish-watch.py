import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
_src = os.path.join(_root, "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from pydaffodil import Daffodil

cli = Daffodil(remote_user="root", remote_host="203.161.53.228", remote_path="/root/production")

steps = [
    {"step": "Copy build/ to production", "command": lambda: cli.transfer_files("build", "/root/production")}
]

# Watch local build output for changes (Ctrl+C to stop)
cli.watch(
    paths=[os.path.abspath("build")],
    debounce=2_000,
    interval=2_000,
).deploy(steps)

# Optional: also watch a git repo (uncomment and set repo_path)
# cli.watch(
#     paths=[os.path.abspath("build")],
#     repo_path=os.path.abspath(".."),
#     branches=["main"],
#     tags=True,
#     tag_pattern=r"^v\d+\.\d+\.\d+$",
#     events=["commit", "merge", "tag"],
#     debounce=2_000,
#     interval=5_000,
# ).deploy(steps)
