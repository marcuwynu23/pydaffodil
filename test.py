from pydaffodil import Daffodil
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

remote_user = os.getenv("REMOTE_USER", "user")
remote_host = os.getenv("REMOTE_HOST", "user@example.com")
remote_path = os.getenv("REMOTE_PATH", "/home/user/")

cli = Daffodil(remote_user=remote_user, remote_host=remote_host, remote_path=remote_path)

steps = [
    # {"step": "Build the project", "command": lambda: cli.run_command("npm run build")},
    {"step": "Stop backend process on remote server", "command": lambda: cli.make_directory("test")},
    {"step": "Transfer files to remote server", "command": lambda: cli.transfer_files(local_path="dist", destination_path="/root/test")},
    # {"step": "Restart backend process on remote server", "command": lambda: cli.ssh_command("sudo forever restartall")}
]

cli.deploy(steps)
