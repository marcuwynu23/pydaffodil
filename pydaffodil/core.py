import os
import subprocess
import paramiko
from paramiko import SSHClient
from tqdm import tqdm
import ctypes
from colorama import init, Fore

# Initialize colorama for colored terminal output
init(autoreset=True)

class Daffodil:
    def __init__(self, remote_user, remote_host, remote_path=None, scp_ignore=".scpignore"):
        """
        Initialize the DaffodilCLI deployment framework.

        :param remote_user: The remote server username.
        :param remote_host: The remote server hostname or IP address.
        :param remote_path: The remote server path to deploy files (default is current directory).
        :param scp_ignore: Path to the scp ignore file.
        """
        self.remote_user = remote_user
        self.remote_host = remote_host
        self.ssh_client = SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(self.remote_host, username=self.remote_user)

        # Set remote_path to the current directory if not provided
        self.remote_path = remote_path if remote_path else self.get_remote_current_directory()

        self.scp_ignore = scp_ignore
        self.exclude_list = self.load_ignore_list()
        # print(dir(self.ssh_client))

    def run_command(self, command):
        """Run a shell command and print its output."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"{Fore.RED}deploy: Error: {stderr.decode('utf-8')}")
            raise Exception(stderr.decode('utf-8'))
        print(f"{Fore.GREEN}deploy: {stdout.decode('utf-8')}")

    def check_admin(self):
        """Check for admin privileges."""
        try:
            if os.name == 'nt':  # Check for Windows
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:  # Assume Unix-like system
                is_admin = (os.geteuid() == 0)
        except AttributeError:
            is_admin = False
        if not is_admin:
            print(f"{Fore.RED}deploy: You do not have Administrator rights to run this script! Please re-run as an Administrator.")
            exit()

    def transfer_files(self, local_path, destination_path=None):
        """
        Transfer files using command-line SCP with a progress bar.

        :param local_path: The local path from which files will be transferred.
        :param destination_path: The destination path on the remote server. Defaults to self.remote_path if not provided.
        """
        # Use destination_path if provided, otherwise fall back to remote_path
        remote_target_path = destination_path if destination_path else self.remote_path

        files_to_transfer = []
        for dirpath, dirnames, filenames in os.walk(local_path):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                if not any(exclude in file_path for exclude in self.exclude_list):
                    files_to_transfer.append(file_path)

        with tqdm(total=len(files_to_transfer), desc="Transferring Files", unit="file") as pbar:
            for file_path in files_to_transfer:
                print(f"{Fore.CYAN}deploy: Copying: {file_path}")
                # Use the remote_target_path for the SCP command
                scp_command = f"scp \"{file_path}\" {self.remote_user}@{self.remote_host}:{remote_target_path}"
                self.run_command(scp_command)
                pbar.update(1)


    def deploy(self, steps):
        """
        Execute deployment steps.

        :param steps: A list of deployment steps, where each step is a dictionary
                      with 'step' (description) and 'command' (lambda function).
        """
        self.check_admin()

        try:
            self.ssh_client.connect(self.remote_host, username=self.remote_user)
        except Exception as e:
            print(f"{Fore.RED}deploy: SSH connection failed - {e}")
            exit()

        for i, step in enumerate(steps, start=1):
            print(f"{Fore.YELLOW}deploy: Step {i}/{len(steps)}: {step['step']}")
            tqdm.write(f"{Fore.YELLOW}deploy: Executing: {step['step']}")
            try:
                step['command']()
            except Exception as e:
                print(f"{Fore.RED}deploy: Error in step: {step['step']} - {e}")
                break

        self.ssh_client.close()
        print(f"{Fore.GREEN}deploy: Deployment completed successfully.")

    def load_ignore_list(self):
        """Load ignore list from file. If the file doesn't exist, create it."""
        exclude_list = []
        if not os.path.exists(self.scp_ignore):
            # Create the .scpignore file with a default comment
            print(f"{Fore.MAGENTA}deploy: No .scpignore file found. Creating a default one.")
            with open(self.scp_ignore, 'w') as f:
                f.write("# Add file patterns to ignore during SCP transfer\n")
            print(f"{Fore.GREEN}deploy: Created {self.scp_ignore} file. You can now add file patterns to it.")

        # Read the ignore file if it exists
        with open(self.scp_ignore, 'r') as f:
            exclude_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        return exclude_list

    def get_remote_current_directory(self):
        """Retrieve the current working directory on the remote server."""
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command("pwd")
            current_directory = stdout.read().decode().strip()
            print(f"{Fore.GREEN}deploy: Remote current directory is {current_directory}")
            return current_directory
        except Exception as e:
            print(f"{Fore.RED}deploy: Failed to get remote current directory - {e}")
            exit()

    def ssh_command(self, command):
        """Execute an SSH command."""
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        for line in stdout:
            print(f"{Fore.GREEN}deploy: {line.strip()}")
        for line in stderr:
            print(f"{Fore.RED}deploy: Error: {line.strip()}")


    def make_directory(self, directory_name):
        """
        Create a directory inside the remote_path on the remote server.

        :param directory_name: The name of the directory to create inside the remote_path.
        """
        # Combine remote_path with directory_name to get the full path
        full_directory_path = f"{self.remote_path}/{directory_name}"  # Concatenating the paths

        try:
            # Execute the mkdir command on the remote server
            command = f"mkdir -p {full_directory_path}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                print(f"{Fore.GREEN}deploy: Created directory {full_directory_path} on the remote server.")
            else:
                print(f"{Fore.RED}deploy: Failed to create directory {full_directory_path}. Error: {stderr.read().decode()}")
        except Exception as e:
            print(f"{Fore.RED}deploy: Failed to create directory {full_directory_path} - {e}")
            exit()
