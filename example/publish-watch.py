import importlib.util
import sys
import os


def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Usage
module = import_from_file("Daffodil", "../pydaffodil/__init__.py")

cli = module.Daffodil(remote_user="root", remote_host="203.161.53.228", remote_path="/root/production")

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
