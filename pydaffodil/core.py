import os
import subprocess
import paramiko
from paramiko import SSHClient, RSAKey, ECDSAKey, Ed25519Key
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
        """Load an SSH private key. Supports RSA, ECDSA, and Ed25519 key types."""
        try:
            return RSAKey.from_private_key_file(key_path, password=password)
        except paramiko.PasswordRequiredException:
            raise
        except paramiko.SSHException:
            try:
                return ECDSAKey.from_private_key_file(key_path, password=password)
            except paramiko.SSHException:
                try:
                    return Ed25519Key.from_private_key_file(key_path, password=password)
                except paramiko.SSHException:
                    raise paramiko.SSHException(f"Unsupported or invalid SSH key format at {key_path}. Supported formats: RSA, ECDSA, Ed25519")
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

    def _detect_local_archive_tools(self):
        """Detect available archive tools on the local system, ordered by efficiency."""
        tools = {
            'pigz': None,      # Parallel gzip (fastest for compression)
            '7z': None,        # 7-Zip (excellent compression)
            'tar': None,       # Standard tar
            'gzip': None,      # Standard gzip
            'zip': None,       # Standard zip
        }
        
        for tool in tools.keys():
            tool_path = shutil.which(tool)
            if tool_path:
                tools[tool] = tool_path
        
        return tools

    def _select_best_archive_format(self):
        """Select the best archive format and tool based on platform and available tools."""
        system = platform.system().lower()
        tools = self._detect_local_archive_tools()
        
        # Priority order: fastest/most efficient first
        if system == 'windows':
            if tools['7z']:
                return 'zip', '7z', tools['7z']  # Use 7z tool but create zip format
            elif tools['zip']:
                return 'zip', 'zip', tools['zip']
            else:
                return 'zip', 'shutil', None
        else:
            # POSIX systems (Linux, macOS, etc.)
            if tools['pigz'] and tools['tar']:
                return 'gztar', 'pigz+tar', {'pigz': tools['pigz'], 'tar': tools['tar']}
            elif tools['7z']:
                return 'zip', '7z', tools['7z']  # Use 7z tool but create zip format for compatibility
            elif tools['tar'] and tools['gzip']:
                return 'gztar', 'tar+gzip', {'tar': tools['tar'], 'gzip': tools['gzip']}
            elif tools['tar']:
                return 'gztar', 'tar', tools['tar']
            elif tools['zip']:
                return 'zip', 'zip', tools['zip']
            else:
                return 'gztar', 'shutil', None

    def _create_archive_optimized(self, archive_path, local_path, format_type, tool_type, tool_info):
        """Create archive using the most efficient available method."""
        if tool_type == 'shutil':
            archive_full_path = shutil.make_archive(archive_path, format_type, local_path)
            return archive_full_path
        
        archive_ext = '.zip' if format_type == 'zip' else '.tar.gz'
        archive_full_path = f"{archive_path}{archive_ext}"
        
        # Normalize paths for cross-platform compatibility
        local_path_abs = os.path.abspath(local_path)
        archive_full_path_abs = os.path.abspath(archive_full_path)
        
        try:
            if tool_type == 'pigz+tar':
                # Use pigz for parallel compression with tar
                pigz_path = tool_info['pigz']
                tar_path = tool_info['tar']
                base_name = os.path.basename(local_path_abs)
                parent_dir = os.path.dirname(local_path_abs)
                
                if os.name == 'nt':  # Windows
                    cmd = f'cd /d "{parent_dir}" && "{tar_path}" -cf - "{base_name}" | "{pigz_path}" -9 > "{archive_full_path_abs}"'
                else:  # POSIX
                    cmd = f'cd "{parent_dir}" && {tar_path} -cf - "{base_name}" | {pigz_path} -9 > "{archive_full_path_abs}"'
                
                subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return archive_full_path_abs
                
            elif tool_type == 'tar+gzip':
                # Use tar with gzip
                tar_path = tool_info['tar']
                base_name = os.path.basename(local_path_abs)
                parent_dir = os.path.dirname(local_path_abs)
                
                if os.name == 'nt':  # Windows
                    cmd = f'cd /d "{parent_dir}" && "{tar_path}" -czf "{archive_full_path_abs}" "{base_name}"'
                else:  # POSIX
                    cmd = f'cd "{parent_dir}" && {tar_path} -czf "{archive_full_path_abs}" "{base_name}"'
                
                subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return archive_full_path_abs
                
            elif tool_type == 'tar':
                # Use tar only (will create .tar, then we compress)
                tar_path = tool_info
                base_name = os.path.basename(local_path_abs)
                parent_dir = os.path.dirname(local_path_abs)
                tar_file = f"{archive_path}.tar"
                tar_file_abs = os.path.abspath(tar_file)
                
                if os.name == 'nt':  # Windows
                    cmd = f'cd /d "{parent_dir}" && "{tar_path}" -cf "{tar_file_abs}" "{base_name}"'
                else:  # POSIX
                    cmd = f'cd "{parent_dir}" && {tar_path} -cf "{tar_file_abs}" "{base_name}"'
                
                subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                
                # Compress with gzip
                if os.name == 'nt':
                    gzip_cmd = f'gzip -9 "{tar_file_abs}"'
                else:
                    gzip_cmd = f'gzip -9 "{tar_file_abs}"'
                subprocess.run(gzip_cmd, shell=True, capture_output=True, text=True, check=True)
                return archive_full_path_abs
                
            elif tool_type == '7z':
                # Use 7-Zip - supports both zip and tar.gz formats
                sevenz_path = tool_info
                if format_type == 'zip':
                    cmd = f'"{sevenz_path}" a -tzip -mx=9 "{archive_full_path_abs}" "{local_path_abs}"'
                    subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                    return archive_full_path_abs
                else:
                    # For tar.gz, create tar first then compress
                    tar_file = f"{archive_path}.tar"
                    tar_file_abs = os.path.abspath(tar_file)
                    cmd1 = f'"{sevenz_path}" a -ttar -mx=0 "{tar_file_abs}" "{local_path_abs}"'
                    subprocess.run(cmd1, shell=True, capture_output=True, text=True, check=True)
                    cmd2 = f'"{sevenz_path}" a -tgzip -mx=9 "{archive_full_path_abs}" "{tar_file_abs}"'
                    subprocess.run(cmd2, shell=True, capture_output=True, text=True, check=True)
                    # Clean up intermediate tar file
                    try:
                        os.remove(tar_file_abs)
                    except:
                        pass
                    return archive_full_path_abs
                
            elif tool_type == 'zip':
                # Use native zip command
                zip_path = tool_info
                if os.name == 'nt':  # Windows
                    cmd = f'"{zip_path}" -r -9 "{archive_full_path_abs}" "{local_path_abs}"'
                else:  # POSIX
                    cmd = f'{zip_path} -r -9 "{archive_full_path_abs}" "{local_path_abs}"'
                
                subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
                return archive_full_path_abs
                
        except subprocess.CalledProcessError as e:
            print(f"{Fore.YELLOW}deploy: Native tool failed, falling back to shutil: {e.stderr if e.stderr else 'Unknown error'}")
            return shutil.make_archive(archive_path, format_type, local_path)
        except Exception as e:
            print(f"{Fore.YELLOW}deploy: Error with native tool, falling back to shutil: {e}")
            return shutil.make_archive(archive_path, format_type, local_path)
        
        # Final fallback
        return shutil.make_archive(archive_path, format_type, local_path)

    def _detect_remote_extraction_tools(self):
        """Detect available extraction tools on the remote server."""
        tools = {}
        
        # Detect remote OS
        stdin, stdout, stderr = self.ssh_client.exec_command("uname -s 2>/dev/null || echo 'unknown'")
        remote_os = stdout.read().decode().strip().lower()
        
        if 'windows' in remote_os or remote_os == '':
            # Windows - check for PowerShell and 7-Zip
            stdin, stdout, stderr = self.ssh_client.exec_command("powershell -Command 'Get-Command Expand-Archive -ErrorAction SilentlyContinue' 2>/dev/null")
            if stdout.read().decode().strip():
                tools['powershell'] = True
            
            stdin, stdout, stderr = self.ssh_client.exec_command("where 7z 2>/dev/null || which 7z 2>/dev/null")
            if stdout.read().decode().strip():
                tools['7z'] = True
        else:
            # POSIX systems
            check_commands = {
                'tar': 'which tar',
                'unzip': 'which unzip',
                'pigz': 'which pigz',
                '7z': 'which 7z',
                'gzip': 'which gzip',
            }
            
            for tool, cmd in check_commands.items():
                stdin, stdout, stderr = self.ssh_client.exec_command(f"{cmd} 2>/dev/null")
                if stdout.read().decode().strip():
                    tools[tool] = True
        
        return tools, remote_os

    def _get_remote_extraction_command(self, remote_archive_path, remote_target_path, archive_format, remote_tools, remote_os):
        """Get the optimal extraction command for the remote server. Extracts contents directly to destination."""
        # Escape paths for shell safety
        escaped_archive = remote_archive_path.replace("'", "'\"'\"'").replace(" ", "\\ ")
        escaped_target = remote_target_path.replace("'", "'\"'\"'").replace(" ", "\\ ")
        
        # Create temp extraction directory (use unescaped path for temp, then escape it)
        temp_extract_raw = f"{remote_target_path}_pydaffodil_temp"
        temp_extract = temp_extract_raw.replace("'", "'\"'\"'").replace(" ", "\\ ")
        
        if archive_format == 'zip':
            if remote_os and 'windows' in remote_os:
                # Windows extraction
                if 'powershell' in remote_tools:
                    return (
                        f"powershell -Command \""
                        f"$tempDir = '{temp_extract}'; "
                        f"New-Item -ItemType Directory -Force -Path $tempDir | Out-Null; "
                        f"Expand-Archive -Path '{escaped_archive}' -DestinationPath $tempDir -Force; "
                        f"$subDir = Get-ChildItem $tempDir -Directory | Select-Object -First 1; "
                        f"if ($subDir) {{ Move-Item -Path $subDir\\* -Destination '{escaped_target}' -Force; Remove-Item $tempDir -Recurse -Force }} "
                        f"else {{ Move-Item -Path $tempDir\\* -Destination '{escaped_target}' -Force; Remove-Item $tempDir -Recurse -Force }}; "
                        f"Remove-Item '{escaped_archive}' -Force\""
                    )
                elif '7z' in remote_tools:
                    return (
                        f"mkdir \"{temp_extract}\" 2>nul && "
                        f"7z x \"{escaped_archive}\" -o\"{temp_extract}\" -y && "
                        f"for /d %%d in (\"{temp_extract}\\*\") do (xcopy /E /Y \"%%d\\*\" \"{escaped_target}\\\" && rmdir /S /Q \"%%d\") && "
                        f"xcopy /E /Y \"{temp_extract}\\*\" \"{escaped_target}\" 2>nul && "
                        f"rmdir /S /Q \"{temp_extract}\" && "
                        f"del /f \"{escaped_archive}\""
                    )
                else:
                    return self._get_python_extraction_command(escaped_archive, escaped_target, 'zip', temp_extract)
            else:
                # POSIX extraction
                if 'unzip' in remote_tools:
                    return (
                        f"mkdir -p '{temp_extract}' '{escaped_target}' && "
                        f"unzip -o '{escaped_archive}' -d '{temp_extract}' && "
                        f"subdir=$(find '{temp_extract}' -mindepth 1 -maxdepth 1 -type d | head -1); "
                        f"if [ -n \"$subdir\" ]; then "
                        f"  mv \"$subdir\"/* '{escaped_target}'/ 2>/dev/null || true; "
                        f"  rmdir \"$subdir\" 2>/dev/null || true; "
                        f"else "
                        f"  mv '{temp_extract}'/* '{escaped_target}'/ 2>/dev/null || true; "
                        f"fi && "
                        f"rmdir '{temp_extract}' 2>/dev/null || true && "
                        f"rm -f '{escaped_archive}'"
                    )
                elif '7z' in remote_tools:
                    return (
                        f"mkdir -p '{temp_extract}' '{escaped_target}' && "
                        f"7z x '{escaped_archive}' -o'{temp_extract}' -y && "
                        f"subdir=$(find '{temp_extract}' -mindepth 1 -maxdepth 1 -type d | head -1); "
                        f"if [ -n \"$subdir\" ]; then "
                        f"  mv \"$subdir\"/* '{escaped_target}'/ 2>/dev/null || true; "
                        f"  rmdir \"$subdir\" 2>/dev/null || true; "
                        f"else "
                        f"  mv '{temp_extract}'/* '{escaped_target}'/ 2>/dev/null || true; "
                        f"fi && "
                        f"rmdir '{temp_extract}' 2>/dev/null || true && "
                        f"rm -f '{escaped_archive}'"
                    )
                else:
                    return self._get_python_extraction_command(escaped_archive, escaped_target, 'zip', temp_extract)
        
        else:  # gztar format
            if remote_os and 'windows' in remote_os:
                # Windows - use Python or 7z
                if '7z' in remote_tools:
                    return (
                        f"mkdir \"{temp_extract}\" 2>nul && "
                        f"7z x \"{escaped_archive}\" -o\"{temp_extract}\" -y && "
                        f"for /d %%d in (\"{temp_extract}\\*\") do (xcopy /E /Y \"%%d\\*\" \"{escaped_target}\\\" && rmdir /S /Q \"%%d\") && "
                        f"xcopy /E /Y \"{temp_extract}\\*\" \"{escaped_target}\" 2>nul && "
                        f"rmdir /S /Q \"{temp_extract}\" && "
                        f"del /f \"{escaped_archive}\""
                    )
                else:
                    return self._get_python_extraction_command(escaped_archive, escaped_target, 'gztar', temp_extract)
            else:
                # POSIX extraction - use --strip-components=1 to extract contents directly
                if 'pigz' in remote_tools and 'tar' in remote_tools:
                    return (
                        f"mkdir -p '{escaped_target}' && "
                        f"pigz -dc '{escaped_archive}' | tar -xf - -C '{escaped_target}' --strip-components=1 && "
                        f"rm -f '{escaped_archive}'"
                    )
                elif 'tar' in remote_tools and 'gzip' in remote_tools:
                    return (
                        f"mkdir -p '{escaped_target}' && "
                        f"tar -xzf '{escaped_archive}' -C '{escaped_target}' --strip-components=1 && "
                        f"rm -f '{escaped_archive}'"
                    )
                elif 'tar' in remote_tools:
                    return (
                        f"mkdir -p '{escaped_target}' && "
                        f"tar -xzf '{escaped_archive}' -C '{escaped_target}' --strip-components=1 && "
                        f"rm -f '{escaped_archive}'"
                    )
                elif '7z' in remote_tools:
                    return (
                        f"mkdir -p '{temp_extract}' '{escaped_target}' && "
                        f"7z x '{escaped_archive}' -o'{temp_extract}' -y && "
                        f"subdir=$(find '{temp_extract}' -mindepth 1 -maxdepth 1 -type d | head -1); "
                        f"if [ -n \"$subdir\" ]; then "
                        f"  mv \"$subdir\"/* '{escaped_target}'/ 2>/dev/null || true; "
                        f"  rmdir \"$subdir\" 2>/dev/null || true; "
                        f"else "
                        f"  mv '{temp_extract}'/* '{escaped_target}'/ 2>/dev/null || true; "
                        f"fi && "
                        f"rmdir '{temp_extract}' 2>/dev/null || true && "
                        f"rm -f '{escaped_archive}'"
                    )
                else:
                    return self._get_python_extraction_command(escaped_archive, escaped_target, 'gztar', temp_extract)

    def _get_python_extraction_command(self, escaped_archive, escaped_target, format_type, temp_extract):
        """Get Python-based extraction command as final fallback. Extracts contents directly to destination."""
        python_cmd = "python3"
        check_python = "which python3 2>/dev/null || which python 2>/dev/null"
        stdin, stdout, stderr = self.ssh_client.exec_command(check_python)
        python_available = stdout.read().decode().strip()
        
        if python_available:
            python_cmd = python_available.split('\n')[0]
        
        return (
            f"{python_cmd} -c "
            f"\"import shutil, os, sys; "
            f"try: "
            f"  temp_dir = '{temp_extract}'; "
            f"  target_dir = '{escaped_target}'; "
            f"  os.makedirs(temp_dir, exist_ok=True); "
            f"  os.makedirs(target_dir, exist_ok=True); "
            f"  shutil.unpack_archive('{escaped_archive}', temp_dir, '{format_type}'); "
            f"  subdirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]; "
            f"  if subdirs: "
            f"    source_dir = os.path.join(temp_dir, subdirs[0]); "
            f"    for item in os.listdir(source_dir): "
            f"      src = os.path.join(source_dir, item); "
            f"      dst = os.path.join(target_dir, item); "
            f"      if os.path.exists(dst): "
            f"        if os.path.isdir(dst): "
            f"          shutil.rmtree(dst); "
            f"        else: "
            f"          os.remove(dst); "
            f"      shutil.move(src, dst); "
            f"    os.rmdir(source_dir); "
            f"  else: "
            f"    for item in os.listdir(temp_dir): "
            f"      src = os.path.join(temp_dir, item); "
            f"      dst = os.path.join(target_dir, item); "
            f"      if os.path.exists(dst): "
            f"        if os.path.isdir(dst): "
            f"          shutil.rmtree(dst); "
            f"        else: "
            f"          os.remove(dst); "
            f"      shutil.move(src, dst); "
            f"  shutil.rmtree(temp_dir); "
            f"  os.remove('{escaped_archive}'); "
            f"  sys.exit(0); "
            f"except Exception as e: "
            f"  print(f'Error: {{e}}', file=sys.stderr); "
            f"  sys.exit(1)\""
        )

    def transfer_files(self, local_path, destination_path=None):
        """
        Transfer files and directories recursively by creating an optimized archive, transferring it,
        and unarchiving on the remote server. Cross-platform compatible (Windows, macOS, Linux).
        Automatically selects the fastest available compression tools.

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
            # Step 1: Select optimal archive format and create archive
            print(f"{Fore.YELLOW}deploy: Analyzing available tools and creating optimized archive from {local_path}...")
            format_type, tool_type, tool_info = self._select_best_archive_format()
            
            if tool_type != 'shutil':
                print(f"{Fore.CYAN}deploy: Using {tool_type} for archive creation (faster than default)")
            
            with tqdm(desc="Creating archive", unit="file") as pbar:
                archive_full_path = self._create_archive_optimized(
                    archive_path, local_path, format_type, tool_type, tool_info
                )
                pbar.update(1)
            
            archive_size = os.path.getsize(archive_full_path) / (1024 * 1024)  # Size in MB
            print(f"{Fore.GREEN}deploy: Archive created: {os.path.basename(archive_full_path)} ({archive_size:.2f} MB)")

            # Step 2: Transfer the archive
            print(f"{Fore.YELLOW}deploy: Transferring archive to remote server...")
            remote_archive_path = f"{remote_target_path}/{os.path.basename(archive_full_path)}"
            
            with tqdm(desc="Transferring archive", unit="file") as pbar:
                scp_command = f"scp -p {archive_full_path} {self.remote_user}@{self.remote_host}:{remote_archive_path}"
                self.run_command(scp_command)
                pbar.update(1)
            
            print(f"{Fore.GREEN}deploy: Archive transferred successfully")

            # Step 3: Detect remote tools and extract archive
            print(f"{Fore.YELLOW}deploy: Detecting remote extraction tools...")
            remote_tools, remote_os = self._detect_remote_extraction_tools()
            
            if remote_tools:
                tool_list = ', '.join(remote_tools.keys())
                print(f"{Fore.CYAN}deploy: Remote tools detected: {tool_list}")
            
            print(f"{Fore.YELLOW}deploy: Extracting archive on remote server...")
            extract_command = self._get_remote_extraction_command(
                remote_archive_path, remote_target_path, format_type, remote_tools, remote_os
            )
            
            stdin, stdout, stderr = self.ssh_client.exec_command(extract_command)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print(f"{Fore.GREEN}deploy: Archive extracted successfully on remote server")
            else:
                error_msg = stderr.read().decode()
                stdout_msg = stdout.read().decode()
                if not error_msg:
                    error_msg = stdout_msg
                if not error_msg:
                    error_msg = "Unknown error during extraction"
                print(f"{Fore.RED}deploy: Failed to extract archive on remote server: {error_msg}")
                raise Exception(f"Failed to extract archive: {error_msg}")

        except FileNotFoundError:
            raise
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

