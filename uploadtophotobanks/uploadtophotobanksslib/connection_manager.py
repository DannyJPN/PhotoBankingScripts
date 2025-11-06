
"""
Connection manager for various photobank FTP/SFTP servers.
"""
import ftplib
import logging
import ssl
import time
from typing import Optional, Dict, Any
import paramiko
from paramiko import SSHClient, AutoAddPolicy

from uploadtophotobanksslib.constants import (
    PHOTOBANK_CONFIGS,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY
)


class PhotobankConnection:
    """Base class for photobank connections."""

    def __init__(self, photobank: str, credentials: Dict[str, str]):
        self.photobank = photobank
        self.credentials = credentials
        self.config = PHOTOBANK_CONFIGS.get(photobank)
        self.connection = None

        if not self.config:
            raise ValueError(f"Unsupported photobank: {photobank}")

    def connect(self) -> bool:
        """Connect to the photobank server."""
        raise NotImplementedError

    def disconnect(self) -> None:
        """Disconnect from the photobank server."""
        raise NotImplementedError

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to the server."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Check if connection is active."""
        raise NotImplementedError


class FTPConnection(PhotobankConnection):
    """FTP connection handler for photobanks."""

    def __init__(self, photobank: str, credentials: Dict[str, str]):
        super().__init__(photobank, credentials)
        self.ftp = None

    def connect(self, file_path: Optional[str] = None) -> bool:
        """Connect to FTP server."""
        try:
            protocol = self.config["protocol"]
            host = self._get_host(file_path)
            port = self.config["port"]

            logging.info(f"Connecting to {self.photobank} via {protocol.upper()} at {host}:{port}")

            if protocol == "ftps":
                # Explicit FTPS (like Shutterstock)
                self.ftp = ftplib.FTP_TLS()
                self.ftp.set_debuglevel(0)
                # Longer timeout for slow servers
                self.ftp.connect(host, port, timeout=600)  # 10 minutes

                # Login first, then switch to encrypted data connection
                self.ftp.login(self.credentials["username"], self.credentials["password"])
                self.ftp.prot_p()  # Switch to encrypted data connection

                logging.info(f"Successfully connected to {self.photobank} via FTPS")
            else:
                # Plain FTP
                self.ftp = ftplib.FTP()
                self.ftp.set_debuglevel(0)
                # Longer timeout for slow servers
                self.ftp.connect(host, port, timeout=600)  # 10 minutes
                self.ftp.login(self.credentials["username"], self.credentials["password"])

                logging.info(f"Successfully connected to {self.photobank} via FTP")

            # Configure for slow servers
            if hasattr(self.ftp, 'sock') and self.ftp.sock:
                # Set socket options for keep-alive and longer timeouts
                import socket
                self.ftp.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                self.ftp.sock.settimeout(600)  # 10 minutes for data operations

            # Set passive mode (required for most photobanks)
            if self.config.get("passive", True):
                self.ftp.set_pasv(True)
                logging.debug("Set passive mode")

            return True

        except Exception as e:
            logging.error(f"Failed to connect to {self.photobank}: {e}")
            if self.ftp:
                try:
                    self.ftp.quit()
                except:
                    pass
                self.ftp = None
            return False

    def _get_host(self, file_path: Optional[str] = None) -> str:
        """Get the appropriate host for the connection."""
        if "hosts" in self.config:
            # 123RF has multiple hosts based on content type
            content_type = self._detect_content_type(file_path) if file_path else "photos"
            return self.config["hosts"].get(content_type, list(self.config["hosts"].values())[0])
        else:
            return self.config["host"]

    def _detect_content_type(self, file_path: str) -> str:
        """Detect content type based on file extension."""
        if not file_path:
            return "photos"

        file_ext = file_path.lower().split('.')[-1]

        # Video files
        if file_ext in ['mp4', 'mov', 'avi', 'wmv', 'mkv', 'flv', 'webm']:
            return "video"

        # Audio files
        elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma']:
            return "audio"

        # Default to photos for images and other formats
        else:
            return "photos"

    def disconnect(self) -> None:
        """Disconnect from FTP server."""
        if self.ftp:
            try:
                self.ftp.quit()
                logging.debug(f"Disconnected from {self.photobank}")
            except:
                logging.debug(f"Force closed connection to {self.photobank}")
            finally:
                self.ftp = None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via FTP with robustness for slow servers."""
        if not self.is_connected():
            logging.error("Not connected to FTP server")
            return False

        import os
        file_size = os.path.getsize(local_path)
        logging.info(f"Uploading {local_path} to {remote_path} ({file_size:,} bytes)")

        # Progress callback for slow uploads
        bytes_transferred = 0
        def progress_callback(block):
            nonlocal bytes_transferred
            bytes_transferred += len(block)
            if bytes_transferred % (1024 * 1024) == 0:  # Log every 1MB
                progress = (bytes_transferred / file_size) * 100 if file_size > 0 else 0
                logging.debug(f"Upload progress: {progress:.1f}% ({bytes_transferred:,} / {file_size:,} bytes)")

        max_retries = 3
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                # Verify connection before upload
                if not self.is_connected():
                    logging.warning(f"Connection lost, attempting to reconnect (attempt {attempt + 1})")
                    if not self.connect():
                        continue

                # Set longer timeout for data operations
                if hasattr(self.ftp, 'sock') and self.ftp.sock:
                    self.ftp.sock.settimeout(1200)  # 20 minutes for very slow uploads

                logging.info(f"Starting upload attempt {attempt + 1}/{max_retries}")
                bytes_transferred = 0

                with open(local_path, 'rb') as f:
                    # Use callback for progress tracking on slow uploads
                    if file_size > 10 * 1024 * 1024:  # Files > 10MB get progress tracking
                        self.ftp.storbinary(f'STOR {remote_path}', f, callback=progress_callback)
                    else:
                        self.ftp.storbinary(f'STOR {remote_path}', f)

                logging.info(f"Successfully uploaded {local_path}")
                return True

            except Exception as e:
                logging.warning(f"Upload attempt {attempt + 1} failed for {local_path}: {e}")

                if attempt < max_retries - 1:
                    logging.info(f"Retrying upload in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logging.error(f"Failed to upload {local_path} after {max_retries} attempts: {e}")
                    return False

        return False

    def change_directory(self, directory: str) -> bool:
        """Change to specified directory."""
        if not self.is_connected():
            return False

        try:
            self.ftp.cwd(directory)
            logging.debug(f"Changed to directory: {directory}")
            return True
        except Exception as e:
            logging.error(f"Failed to change directory to {directory}: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if FTP connection is active."""
        if not self.ftp:
            return False

        try:
            self.ftp.voidcmd("NOOP")
            return True
        except:
            return False


class SFTPConnection(PhotobankConnection):
    """SFTP connection handler for photobanks like Adobe Stock."""

    def __init__(self, photobank: str, credentials: Dict[str, str]):
        super().__init__(photobank, credentials)
        self.ssh_client = None
        self.sftp_client = None

    def connect(self) -> bool:
        """Connect to SFTP server."""
        try:
            host = self.config["host"]
            port = self.config["port"]

            logging.info(f"Connecting to {self.photobank} via SFTP at {host}:{port}")

            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

            self.ssh_client.connect(
                hostname=host,
                port=port,
                username=self.credentials["username"],
                password=self.credentials["password"],
                timeout=DEFAULT_TIMEOUT
            )

            self.sftp_client = self.ssh_client.open_sftp()

            logging.info(f"Successfully connected to {self.photobank} via SFTP")
            return True

        except Exception as e:
            logging.error(f"Failed to connect to {self.photobank} via SFTP: {e}")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Disconnect from SFTP server."""
        if self.sftp_client:
            try:
                self.sftp_client.close()
            except:
                pass
            self.sftp_client = None

        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
            self.ssh_client = None

        logging.debug(f"Disconnected from {self.photobank}")

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file via SFTP."""
        if not self.is_connected():
            logging.error("Not connected to SFTP server")
            return False

        try:
            logging.info(f"Uploading {local_path} to {remote_path}")

            self.sftp_client.put(local_path, remote_path)

            logging.info(f"Successfully uploaded {local_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to upload {local_path}: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if SFTP connection is active."""
        try:
            if self.sftp_client and self.ssh_client:
                # Try a simple operation to test connection
                self.sftp_client.listdir('.')
                return True
        except:
            pass
        return False


class RF123Connection(FTPConnection):
    """Specialized connection for 123RF with dynamic server switching."""

    def __init__(self, photobank: str, credentials: Dict[str, str]):
        super().__init__(photobank, credentials)
        self.current_host = None
        self.current_content_type = None

    def connect_for_file(self, file_path: str) -> bool:
        """Connect to appropriate 123RF server based on file type."""
        content_type = self._detect_content_type(file_path)
        required_host = self.config["hosts"][content_type]

        # If already connected to the right server, use existing connection
        if self.current_host == required_host and self.is_connected():
            logging.debug(f"Using existing connection to {content_type} server: {required_host}")
            return True

        # Disconnect from current server if connected to wrong one
        if self.is_connected():
            logging.info(f"Switching from {self.current_content_type} to {content_type} server")
            self.disconnect()

        # Connect to the correct server
        self.current_content_type = content_type
        self.current_host = required_host

        if self.connect(file_path):
            logging.info(f"Connected to 123RF {content_type} server: {required_host}")
            return True

        return False

    def upload_file_with_switch(self, local_path: str, remote_path: str) -> bool:
        """Upload file, switching servers if necessary."""
        if not self.connect_for_file(local_path):
            logging.error(f"Failed to connect to appropriate 123RF server for {local_path}")
            return False

        return self.upload_file(local_path, remote_path)


class ConnectionManager:
    """Manager for photobank connections with retry logic."""

    def __init__(self):
        self.connections: Dict[str, PhotobankConnection] = {}

    def get_connection(self, photobank: str, credentials: Dict[str, str]) -> Optional[PhotobankConnection]:
        """Get or create a connection for the specified photobank."""

        if photobank in self.connections and self.connections[photobank].is_connected():
            return self.connections[photobank]

        config = PHOTOBANK_CONFIGS.get(photobank)
        if not config:
            logging.error(f"Unsupported photobank: {photobank}")
            return None

        protocol = config["protocol"]

        # Create appropriate connection type
        if photobank == "123RF":
            # Special handling for 123RF with multiple servers
            connection = RF123Connection(photobank, credentials)
        elif protocol in ["ftp", "ftps"]:
            connection = FTPConnection(photobank, credentials)
        elif protocol == "sftp":
            connection = SFTPConnection(photobank, credentials)
        else:
            logging.error(f"Unsupported protocol: {protocol}")
            return None

        # Attempt connection with retry logic
        for attempt in range(DEFAULT_RETRY_COUNT):
            if connection.connect():
                self.connections[photobank] = connection
                return connection

            if attempt < DEFAULT_RETRY_COUNT - 1:
                logging.warning(f"Connection attempt {attempt + 1} failed, retrying in {DEFAULT_RETRY_DELAY} seconds...")
                time.sleep(DEFAULT_RETRY_DELAY)

        logging.error(f"Failed to connect to {photobank} after {DEFAULT_RETRY_COUNT} attempts")
        return None

    def disconnect_all(self) -> None:
        """Disconnect all active connections."""
        for photobank, connection in self.connections.items():
            try:
                connection.disconnect()
                logging.info(f"Disconnected from {photobank}")
            except Exception as e:
                logging.error(f"Error disconnecting from {photobank}: {e}")

        self.connections.clear()

    def disconnect(self, photobank: str) -> None:
        """Disconnect from specific photobank."""
        if photobank in self.connections:
            try:
                self.connections[photobank].disconnect()
                del self.connections[photobank]
                logging.info(f"Disconnected from {photobank}")
            except Exception as e:
                logging.error(f"Error disconnecting from {photobank}: {e}")