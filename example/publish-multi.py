import importlib.util
import sys


def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Usage
module = import_from_file("Daffodil", "../pydaffodil/__init__.py")

cli = module.Daffodil(
    inventory="inventory.ini",
    group="webservers",
    remote_path="/root/production",
)

steps = [
    {"step": "Copy build/ to production", "command": lambda: cli.transfer_files("build", "/root/production")}
]

cli.deploy(steps)
