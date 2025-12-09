import os
import subprocess
import paramiko
from paramiko import SSHClient, RSAKey, DSSKey, ECDSAKey, Ed25519Key
from tqdm import tqdm
from colorama import init, Fore
import shutil
import tempfile
import platform

# Initialize colorama for colored terminal output
init(autoreset=True)

class Daffodil:
    def __init__(self, remote_user, remote_host, remote_path=None, port=22, ssh_key_path=None, ssh_key_pass=None, scp_ignore=".scpignore"):
        """
        Initialize the DaffodilCLI deployment framework.

        :param remote_user: The remote server username.
        :param remote_host: The remote server hostname or IP address.
        :param remote_path: The remote server path to deploy files (default is current directory).
        :param port: The SSH port to connect to (default is 22).
        :param ssh_key_path: Path to the SSH private key file (optional).
        :param ssh_key_pass: Passphrase for the SSH private key (optional, required if key is password-protected).
        :param scp_ignore: Path to the scp ignore file.
        """
        self.remote_user = remote_user
        self.remote_host = remote_host
        self.port = port
        self.ssh_client = SSHClient()
        self.ssh_key_path = self._set_default_ssh_key_path(ssh_key_path)
        self.ssh_key_pass = ssh_key_pass
        self._connect_ssh()

        # Set remote_path to the current directory if not provided
        self.remote_path = remote_path if remote_path else self.get_remote_current_directory()

        self.scp_ignore = scp_ignore
        self.exclude_list = self.load_ignore_list()

    def _set_default_ssh_key_path(self, provided_path):
        """Set the default SSH key path if none is provided."""
        if provided_path:
            return provided_path

        default_paths = [
             os.path.expanduser("~/.ssh/id_rsa"),
            os.path.expanduser("~/.ssh/id_ed25519"),
            os.path.expanduser("~/.ssh/id_ecdsa"),
            os.path.expanduser("~/.ssh/id_dsa"),
        ]

        for path in default_paths:
            if os.path.exists(path):
                print(f"{Fore.YELLOW}deploy: Using default SSH key path: {path}")
                return path

        return None


    def _connect_ssh(self):
        """Establish the SSH connection using either password or SSH key."""
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.ssh_key_path:
                try:
                    if self.ssh_key_pass:
                        key = self._load_ssh_key(self.ssh_key_path, self.ssh_key_pass)
                    else:
                        key = self._load_ssh_key(self.ssh_key_path)
                    self.ssh_client.connect(self.remote_host, port=self.port, username=self.remote_user, pkey=key)
                    print(f"{Fore.GREEN}deploy: Connected to {self.remote_host} using SSH key.")
                except paramiko.PasswordRequiredException:
                    print(f"{Fore.RED}deploy: SSH key requires a passphrase. Please provide 'ssh_key_pass'.")
                    exit(1)
                except paramiko.SSHException as e:
                    print(f"{Fore.RED}deploy: Error connecting with SSH key: {e}")
                    exit(1)
                except FileNotFoundError:
                    print(f"{Fore.RED}deploy: SSH key file not found at {self.ssh_key_path}")
                    exit(1)
            else:
                # Prompt for password if no key is provided (less secure, but supported)
                password = input(f"Enter password for {self.remote_user}@{self.remote_host}: ")
                self.ssh_client.connect(self.remote_host, port=self.port, username=self.remote_user, password=password)
                print(f"{Fore.GREEN}deploy: Connected to {self.remote_host} using password.")
        except paramiko.AuthenticationException:
            print(f"{Fore.RED}deploy: Authentication failed for {self.remote_user}@{self.remote_host}. Check your credentials.")
            exit(1)
        except paramiko.SSHException as e:
            print(f"{Fore.RED}deploy: Could not establish SSH connection to {self.remote_host}: {e}")
            exit(1)
        except Exception as e:
            print(f"{Fore.RED}deploy: An error occurred during SSH connection: {e}")
            exit(1)

    def _load_ssh_key(self, key_path, password=None):
        """Load an SSH private key."""
        try:
            return RSAKey.from_private_key_file(key_path, password=password)
        except paramiko.PasswordRequiredException:
            raise
        except paramiko.SSHException:
            try:
                return DSSKey.from_private_key_file(key_path, password=password)
            except paramiko.SSHException:
                try:
                    return ECDSAKey.from_private_key_file(key_path, password=password)
                except paramiko.SSHException:
                    try:
                        return Ed25519Key.from_private_key_file(key_path, password=password)
                    except paramiko.SSHException:
                        raise paramiko.SSHException(f"Unsupported or invalid SSH key format at {key_path}")
        except FileNotFoundError:
            raise

    def run_command(self, command):
        """Run a shell command and print its output."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"{Fore.RED}deploy: Error: {stderr.decode('utf-8')}")
            raise Exception(stderr.decode('utf-8'))
        print(f"{Fore.GREEN}deploy: {stdout.decode('utf-8')}")

    def check_scp_installed(self):
        """Check if SCP is installed on the system."""
        scp_path = shutil.which('scp')
        if not scp_path:
            print(f"{Fore.RED}deploy: SCP is not installed on this system.")
            # Suggest installation methods based on the operating system
            if os.name == 'posix':  # Linux or macOS
                print(f"{Fore.YELLOW}deploy: On Linux, you can install SCP with: sudo apt-get install openssh-client")
                print(f"{Fore.YELLOW}deploy: On macOS, SCP is usually pre-installed. If not, install OpenSSH: brew install openssh")
            elif os.name == 'nt':  # Windows
                print(f"{Fore.YELLOW}deploy: On Windows, you can install SCP by enabling OpenSSH Client via Windows Features.")
            exit()

    def transfer_files(self, local_path, destination_path=None):
        """
        Transfer files and directories recursively by creating an archive, transferring it,
        and unarchiving on the remote server. Cross-platform compatible (Windows, macOS, Linux).

        :param local_path: The local path from which files will be transferred.
        :param destination_path: The destination path on the remote server. Defaults to self.remote_path if not provided.
        """
        # Check if SCP is installed
        self.check_scp_installed()

        # Use destination_path if provided, otherwise fall back to remote_path
        remote_target_path = destination_path if destination_path else self.remote_path

        # Validate local path exists
        if not os.path.exists(local_path):
            print(f"{Fore.RED}deploy: Local path does not exist: {local_path}")
            raise FileNotFoundError(f"Local path does not exist: {local_path}")

        # Create a temporary directory for the archive
        temp_dir = tempfile.gettempdir()
        archive_name = f"pydaffodil_transfer_{os.path.basename(os.path.abspath(local_path))}"
        archive_path = os.path.join(temp_dir, archive_name)
        archive_full_path = None

        try:
            # Step 1: Create archive using shutil (cross-platform)
            print(f"{Fore.YELLOW}deploy: Creating archive from {local_path}...")
            with tqdm(desc="Creating archive", unit="file") as pbar:
                # Determine archive format based on platform
                # Use 'zip' for maximum cross-platform compatibility
                archive_format = 'zip'
                archive_full_path = shutil.make_archive(archive_path, archive_format, local_path)
                pbar.update(1)
            
            print(f"{Fore.GREEN}deploy: Archive created: {archive_full_path}")

            # Step 2: Transfer the archive
            print(f"{Fore.YELLOW}deploy: Transferring archive to remote server...")
            remote_archive_path = f"{remote_target_path}/{os.path.basename(archive_full_path)}"
            
            with tqdm(desc="Transferring archive", unit="file") as pbar:
                scp_command = f"scp -p {archive_full_path} {self.remote_user}@{self.remote_host}:{remote_archive_path}"
                self.run_command(scp_command)
                pbar.update(1)
            
            print(f"{Fore.GREEN}deploy: Archive transferred successfully")

            # Step 3: Unarchive on remote server (cross-platform)
            print(f"{Fore.YELLOW}deploy: Extracting archive on remote server...")
            
            # Try to detect remote OS and use appropriate extraction command
            # Use Python's shutil for maximum cross-platform compatibility
            # This works on Windows, macOS, and Linux
            python_cmd = "python3"
            # Try python3 first, fallback to python
            check_python3 = "which python3 || which python"
            stdin_check, stdout_check, stderr_check = self.ssh_client.exec_command(check_python3)
            python_available = stdout_check.read().decode().strip()
            
            if python_available:
                python_cmd = python_available.split('\n')[0]  # Get first available Python
            
            # Escape paths for shell command
            escaped_archive = remote_archive_path.replace("'", "'\"'\"'")
            escaped_target = remote_target_path.replace("'", "'\"'\"'")
            
            # Use Python's shutil for cross-platform extraction
            extract_command = (
                f"{python_cmd} -c "
                f"\"import shutil, os, sys; "
                f"try: "
                f"  shutil.unpack_archive('{escaped_archive}', '{escaped_target}', 'zip'); "
                f"  os.remove('{escaped_archive}'); "
                f"  sys.exit(0); "
                f"except Exception as e: "
                f"  print(f'Error: {{e}}', file=sys.stderr); "
                f"  sys.exit(1)\""
            )
            
            # Alternative: try unzip command first (faster on Linux/macOS)
            stdin_uname, stdout_uname, stderr_uname = self.ssh_client.exec_command("uname -s 2>/dev/null || echo 'unknown'")
            remote_os = stdout_uname.read().decode().strip().lower()
            
            if remote_os and remote_os != 'unknown' and 'windows' not in remote_os:
                # Try unzip command first (faster)
                check_unzip = "which unzip"
                stdin_check, stdout_check, stderr_check = self.ssh_client.exec_command(check_unzip)
                unzip_available = stdout_check.read().decode().strip()
                
                if unzip_available:
                    # Use unzip command (faster for Linux/macOS)
                    extract_command = f"cd {remote_target_path} && unzip -o {remote_archive_path} && rm -f {remote_archive_path}"
            
            stdin, stdout, stderr = self.ssh_client.exec_command(extract_command)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print(f"{Fore.GREEN}deploy: Archive extracted successfully on remote server")
            else:
                error_msg = stderr.read().decode()
                stdout_msg = stdout.read().decode()
                if not error_msg:
                    error_msg = stdout_msg
                print(f"{Fore.RED}deploy: Failed to extract archive on remote server: {error_msg}")
                raise Exception(f"Failed to extract archive: {error_msg}")

        except Exception as e:
            print(f"{Fore.RED}deploy: Error during file transfer: {e}")
            raise
        finally:
            # Step 4: Clean up local archive
            if archive_full_path and os.path.exists(archive_full_path):
                try:
                    os.remove(archive_full_path)
                    print(f"{Fore.GREEN}deploy: Local archive cleaned up")
                except Exception as e:
                    print(f"{Fore.YELLOW}deploy: Warning: Could not remove local archive: {e}")

    def deploy(self, steps):
        """
        Execute deployment steps.

        :param steps: A list of deployment steps, where each step is a dictionary
                      with 'step' (description) and 'command' (lambda function).
        """
        for i, step in enumerate(steps, start=1):
            print(f"{Fore.YELLOW}deploy: Step {i}/{len(steps)}: {step['step']}")
            tqdm.write(f"{Fore.YELLOW}deploy: Executing: {step['step']}")
            try:
                step['command']()
            except Exception as e:
                print(f"{Fore.RED}deploy: Error in step: {step['step']} - {e}")
                break

        transport = self.ssh_client.get_transport()
        if transport and transport.is_active():
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

