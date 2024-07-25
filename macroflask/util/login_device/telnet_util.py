import telnetlib
import time

from macroflask.util.login_device.base_login_util import BaseLogin


class TelnetLogin(BaseLogin):

    def attempt_login(self, kwargs: dict) -> bool:
        """
        Attempts to log in by sending username and password, and verifying the expected responses.

        Args:
            kwargs (dict): Dictionary containing 'username', 'username_expect', 'password', 'password_expect', and 'expect'.

        Returns:
            bool: True if login attempt is successful, False otherwise.
        """
        if not self.diff_expected_result_with_actual_result(kwargs['username_expect']):
            if self.logger:
                self.logger.error('{} Username expect failed.'.format(self.host_ip))
            return False

        self.send_command(kwargs['username'])
        if not self.diff_expected_result_with_actual_result(kwargs['password_expect']):
            if self.logger:
                self.logger.error('{} Password expect failed.'.format(self.host_ip))
            return False

        self.send_command(kwargs['password'])
        if not self.diff_expected_result_with_actual_result(kwargs['expect']):
            if self.logger:
                self.logger.error('{} Expect failed.'.format(self.host_ip))
            return False

        return True

    def login(self, host_ip: str, port: int, **kwargs) -> str:
        """
        Attempts to log in to the Telnet server at the given IP and port.

        Args:
            host_ip (str): The IP address of the Telnet server.
            port (int): The port number of the Telnet server.
            kwargs (dict): Additional keyword arguments for login (e.g., 'username', 'username_expect', 'password', 'password_expect', 'expect').

        Returns:
            str: "Login successful" if login is successful.

        Raises:
            Exception: If login fails after 3 attempts.
        """
        self.host_ip = host_ip
        self.device = telnetlib.Telnet(host=host_ip, port=port)
        for attempt in range(3):
            if self.attempt_login(kwargs):
                return "Login successful"
            else:
                time.sleep(1)  # Optional: Delay before retrying
        raise Exception("Login failed after 3 attempts")

    def diff_expected_result_with_actual_result(self, expected_str: str, timeout: int = 2) -> bool:
        """
        Compares the expected response with the actual response from the Telnet server.

        Args:
            expected_str (str): The expected response string.
            timeout (int, optional): Timeout for waiting for the response. Defaults to 2 seconds.

        Returns:
            bool: True if the expected string is found in the actual response, False otherwise.
        """
        result = self.device.read_until(bytes(expected_str, encoding=self.encoding), timeout)
        return expected_str in result.decode(self.encoding)

    def send_command(self, command: str) -> None:
        """
        Sends a command to the Telnet server.

        Args:
            command (str): The command to send.
        """
        self.device.write(bytes(command, encoding=self.encoding) + b'\n')

    def send_command_and_get_response(self, command: str, timeout: int = 3) -> str:
        """
        Sends a command to the Telnet server and returns the response.

        Args:
            command (str): The command to send.
            timeout (int, optional): Timeout for waiting for the response. Defaults to 3 seconds.

        Returns:
            str: The response from the server.
        """
        self.device.write(bytes(command, encoding=self.encoding) + b'\n')
        time.sleep(timeout)
        return self.device.read_very_eager().decode(self.encoding)

    def send_command_and_get_response_efficiency(self, expected_str: str, timeout: int = 10) -> str:
        """
        Sends a command to the Telnet server and waits for an expected response efficiently.

        Args:
            expected_str (str): The expected response string.
            timeout (int, optional): Timeout for waiting for the response. Defaults to 10 seconds.

        Returns:
            str: The response from the server.
        """
        return self.device.read_until(bytes(expected_str, encoding=self.encoding), timeout).decode(self.encoding)

    def get_show_command_result(self, command_set: list) -> dict:
        """
        Executes a set of show commands and returns their results.

        Args:
            command_set (list): List of dictionaries containing command keys and their corresponding commands.

        Returns:
            dict: Dictionary containing the commands and their results.

        Raises:
            Exception: If setting terminal length to 0 fails.
        """
        self.send_command('terminal length 0')
        if not self.diff_expected_result_with_actual_result('>', timeout=1):
            raise Exception('Setting terminal length to 0 failed')

        return_command_dict = {}
        for command_dict in command_set:
            for key, value in command_dict.items():
                self.send_command(value)
                result = self.send_command_and_get_response_efficiency('>')
                return_command_dict[key] = result
        return return_command_dict

    def exit(self) -> None:
        """
        Closes the Telnet connection.
        """
        if self.device:
            self.device.close()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Ensures the Telnet connection is closed when exiting the context.

        Args:
            exc_type (type): The exception type.
            exc_val (Exception): The exception value.
            exc_tb (traceback): The traceback object.
        """
        self.exit()


if __name__ == '__main__':
    ccc = TelnetLogin(
        host_ip='10.124.x.x', port=23, password_expect='Password', username='root', password='xxx',
        username_expect='Username', expect='>')

    print(ccc.get_show_command_result(
        [{"aaa":"sh ip sla configuration | i Entry number: | Tag:|Target address/Source address:|Target port/Source port:|Type Of Service parameter:|Number of packets:"}]))

