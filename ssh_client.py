import paramiko
import socket
import re
import logging
from typing import List, Tuple, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSHClient:
    def __init__(self, host: str, username: str, key_path: str, passphrase: Optional[str] = None):
        self.host = host
        self.username = username
        self.key_path = key_path
        self.passphrase = passphrase
        self.client = None
        self.connected = False

    def connect(self) -> bool:
        """Establish SSH connection to the server."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.passphrase:
                key = paramiko.RSAKey.from_private_key_file(self.key_path, password=self.passphrase)
                self.client.connect(self.host, username=self.username, pkey=key, timeout=10)
            else:
                self.client.connect(self.host, username=self.username, key_filename=self.key_path, timeout=10)
            
            self.connected = True
            logger.info(f"Successfully connected to {self.host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.host}: {str(e)}")
            self.connected = False
            raise

    def disconnect(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info(f"Disconnected from {self.host}")

    def validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        return all(0 <= int(part) <= 255 for part in ip.split('.'))

    def execute_command(self, command: str, get_pty: bool = False) -> Tuple[str, str]:
        """Execute a command and return stdout and stderr."""
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to SSH server")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=get_pty, timeout=30)
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {str(e)}")
            raise

class CommandRunner:
    def __init__(self, ssh_client: SSHClient):
        self.ssh_client = ssh_client

    def run_command_sequence(self, client_ip: str, commands: List[str]) -> Tuple[List[str], str]:
        """Run a sequence of commands on the client through the proxy."""
        if not self.ssh_client.validate_ip(client_ip):
            raise ValueError(f"Invalid IP address: {client_ip}")

        # Start logclient
        logclient_channel = self._start_logclient(client_ip)

        # Connect to client and run commands
        outputs = []
        try:
            shell, client_ssh = self._connect_to_client(client_ip)
            
            for cmd in commands:
                output = self._run_client_command(shell, cmd)
                outputs.append(output)

            self._finish_client_session(shell, client_ssh)
        except Exception as e:
            logger.error(f"Error during command execution: {str(e)}")
            raise
        
        self.kill_logclient_for_ip(client_ip)

        # Get logclient output
        logclient_output = self._get_logclient_output(logclient_channel)
        
        return outputs, logclient_output

    def _start_logclient(self, client_ip: str):
        """Start logclient for the given client IP."""
        cmd = f"logclient {client_ip}"
        _, stdout, _ = self.ssh_client.client.exec_command(cmd, get_pty=True)
        return stdout

    def _connect_to_client(self, client_ip: str) -> Tuple[paramiko.Channel, paramiko.SSHClient]:
        """Establish connection to the client through proxy."""
        client_ssh = paramiko.SSHClient()
        client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client_ssh.connect(
                self.ssh_client.host,
                username=self.ssh_client.username,
                key_filename=self.ssh_client.key_path,
                passphrase=self.ssh_client.passphrase
            )
            
            shell = client_ssh.invoke_shell()
            time.sleep(1)
            
            # Connect to client
            shell.send(f"ssh -o StrictHostKeyChecking=no root@{client_ip}\n")
            time.sleep(1)
            
            # Handle authentication
            self._handle_authentication(shell)
            
            return shell, client_ssh
        except Exception as e:
            logger.error(f"Failed to connect to client {client_ip}: {str(e)}")
            raise

    def _handle_authentication(self, shell: paramiko.Channel):
        """Handle SSH authentication prompts."""
        output = ""
        timeout = time.time() + 10
        
        while time.time() < timeout:
            if shell.recv_ready():
                chunk = shell.recv(1024).decode()
                output += chunk
                
                if "yes/no" in output:
                    shell.send("yes\n")
                    time.sleep(1)
                elif "password:" in output.lower():
                    shell.send("kreatv\n")
                    time.sleep(1)
                    break
            
            time.sleep(0.1)

    def _run_client_command(self, shell: paramiko.Channel, command: str) -> str:
        """Execute command on client and return output."""
        shell.send(command + "\n")
        time.sleep(2)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(1024).decode()
        
        return output

    def _finish_client_session(self, shell: paramiko.Channel, client_ssh: paramiko.SSHClient):
        """Clean up client session."""
        shell.send("exit\n")
        kill_cmd = f"ps -aux | grep 'logclient {client_ip}' | grep -v grep | awk '{{print $2}}' | xargs -r kill -9"
        stdin, stdout, stderr = self.ssh_proxy.exec_command(kill_cmd)
        out = stdout.read().decode()
        err = stderr.read().decode()
        time.sleep(1)
        client_ssh.close()

    def _get_logclient_output(self, channel) -> str:
        """Collect and return logclient output."""
        try:
            channel.channel.send("\x03")  # Ctrl-C
            time.sleep(1)
            channel.channel.send("exit\n")
            time.sleep(1)
            
            output = ""
            timeout = time.time() + 5
            while time.time() < timeout:
                if channel.channel.recv_ready():
                    output += channel.channel.recv(1024).decode()
                else:
                    time.sleep(0.1)
            
            channel.channel.close()
            return output
        except Exception as e:
            logger.error(f"Error collecting logclient output: {str(e)}")
            return ""
        
        def kill_logclient_for_ip(self, client_ip: str) -> Tuple[str, str]:
            """
            Kill the logclient process on the proxy that was started for the specified client IP.
            Returns a tuple of (stdout, stderr) from the kill command.
            """
            # Build the kill command.
            # Note: Adjust to include 'sudo' if necessary and ensure your user can run it without a password.
            kill_cmd = f'ps -aux | grep "logclient {client_ip}" | grep -v grep | awk \'{{print $2}}\' | xargs -r kill -9'
            stdin, stdout, stderr = self.ssh_client.client.exec_command(kill_cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            logger.info(f"kill_logclient_for_ip output: {repr(out)}")
            logger.info(f"kill_logclient_for_ip error: {repr(err)}")
            return out, err
