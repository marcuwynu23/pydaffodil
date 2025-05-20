from pydaffodil import Daffodil

cli = Daffodil(remote_user="root", remote_host="147.92.62.112", remote_path="/root/")

steps = [
    # {"step": "Build the project", "command": lambda: cli.run_command("npm run build")},
    {"step": "Stop backend process on remote server", "command": lambda: cli.make_directory("test")},
    {"step": "Transfer files to remote server", "command": lambda: cli.transfer_files(local_path="dist",destination_path="/root/test")},
    # {"step": "Restart backend process on remote server", "command": lambda: cli.ssh_command("sudo forever restartall")}
]

cli.deploy(steps)

