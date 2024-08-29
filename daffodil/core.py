 import os
import subprocess
import paramiko
from paramiko import SSHClient
from tqdm import tqdm
import ctypes
from colorama import init, Fore

# Initialize colorama for colored terminal output
init(autoreset=True)

class DaffodilCLI:
    def __init__(self, remote_user, remote_host, remote_path, scp_ignore=".scpignore"):
        """
        Initialize the DaffodilCLI deployment framework.

        :param remote_user: The remote server username.
        :param remote_host: The remote server hostname or IP address.
        :param remote_path: The remote server path to deploy files.
        :param scp_ignore: Path to the scp ignore file.
        """
        self.remote_user = remote_user
        self.remote_host = remote_host
        self.remote_path = remote_path
        self.scp_ignore = scp_ignore
        self.exclude_list = self.load_ignore_list()
        self.ssh_client = SSHClient()
        self.ssh_client.load_system_host_keys()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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

    def transfer_files(self, local_path):
        """Transfer files using command-line SCP with a progress bar."""
        files_to_transfer = []
        for dirpath, dirnames, filenames in os.walk(local_path):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                if not any(exclude in file_path for exclude in self.exclude_list):
                    files_to_transfer.append(file_path)

        with tqdm(total=len(files_to_transfer), desc="Transferring Files", unit="file") as pbar:
            for file_path in files_to_transfer:
                print(f"{Fore.CYAN}deploy: Copying: {file_path}")
                scp_command = f"scp \"{file_path}\" {self.remote_user}@{self.remote_host}:{self.remote_path}"
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
        """Load ignore list from file."""
        exclude_list = []
        if os.path.exists(self.scp_ignore):
            with open(self.scp_ignore, 'r') as f:
                exclude_list = [line.strip() for line in f if line.strip()]
        else:
            print(f"{Fore.MAGENTA}deploy: No .scpignore file found. Proceeding without exclusions.")
        return exclude_list

    def ssh_command(self, command):
        """Execute an SSH command."""
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        for line in stdout:
            print(f"{Fore.GREEN}deploy: {line.strip()}")
        for line in stderr:
            print(f"{Fore.RED}deploy: Error: {line.strip()}")
