import time
from netmiko import ConnectHandler
from macroflask.util.login_device.base_login_util import BaseLogin


class NetmikoLogin(BaseLogin):
    """
    Class for handling network device login and executing commands using Netmiko.
    """

    def login(self, host_ip, port, **kwargs):
        """
        Establish a connection to the network device.

        Args:
            host_ip (str): The IP address of the host.
            port (int): The port number for the connection.
            kwargs (dict): Additional arguments such as 'username', 'password', and 'device_type'.
        """
        connection_params = {
            'fast_cli': False,
            'host': host_ip,
            'port': port,
            'username': kwargs['username'],
            'password': kwargs['password'],
            'device_type': kwargs['device_type']
        }
        self.device = ConnectHandler(**connection_params)
        if 'secret' in kwargs:
            self.device.enable()

    def send_command_and_get_response(self, command, timeout=None):
        """
        Send a command to the device and get the response.

        Args:
            command (str): The command to send.
            timeout (int, optional): The timeout for the command. Defaults to None.

        Returns:
            str: The response from the device.
        """
        extra_params = {'read_timeout': timeout} if timeout else {}
        return self.device.send_command(command, **extra_params)

    def exit(self):
        """
        Disconnect from the device.
        """
        self.device.disconnect()

    def config_command_set(self, command_set):
        """
        Send a set of configuration commands to the device.

        Args:
            command_set (list): A list of configuration commands.

        Returns:
            str: The response from the device after sending the configuration commands.
        """
        self.device.enable()
        return self.device.send_config_set(command_set)

    def get_show_command_result(self, command_set):
        """
        Execute a set of show commands and return their results.

        Args:
            command_set (list of dict): A list of dictionaries with command labels and commands.

        Returns:
            dict: A dictionary with command labels as keys and command outputs as values.
        """
        return_command_dict = {}
        for command_dict in command_set:
            for key, cmd in command_dict.items():
                cmd_result = self.send_command_and_get_response(cmd)
                return_command_dict[key] = cmd_result
        return return_command_dict

    def show_command_response(self, cmd, delay_factor=1):
        """
        Execute a command and print its response with a delay.

        Args:
            cmd (str): The command to send.
            delay_factor (int, optional): The delay factor between reading the response. Defaults to 1.
        """
        self.device.write_channel(cmd)
        end_character_list = ["", None]
        end_count_flag = 0
        while True:
            time.sleep(delay_factor)
            result_data = self.device.read_channel()
            if result_data in end_character_list:
                if end_count_flag == 3:
                    break
                end_count_flag += 1
            print(result_data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ensure the device is disconnected when exiting the context.

        Args:
            exc_type (type): The exception type.
            exc_val (Exception): The exception instance.
            exc_tb (traceback): The traceback object.
        """
        self.exit()


if __name__ == '__main__':
    cisco = {
        'device_type': 'cisco_ios',
        'host_ip': 'xxx',
        'username': 'xx',
        'password': 'xxxx',
        'secret': 'xxxx',
        'fast_cli': False,
        'port': 22
    }
    device = NetmikoLogin(**cisco)
    command = "sh ip sla enh col | i Entry number:|Aggregation start time|Target Address:|Type of operation:|RTT Values|RTTAvg:|PacketLossSD|Jitter Values|MinOfPositivesSD:|MinOfNegativesSD:|MinOfPositivesDS:|MinOfNegativesDS:|Jitter Avg:|One Way|OWMinSD|OWMinDS|OWAvgSD"
    command = "sh ip sla enh col | i Entry number:|Aggregation start time|Target Address:|RTT Values|RTTAvg:|PacketLossSD|Jitter Values|MinOfPositivesSD:|MinOfNegativesSD:|MinOfPositivesDS:|MinOfNegativesDS:|Jitter Avg:|One Way|OWMinSD|OWMinDS|OWAvgSD"
    command = "sh ip sla enh col | i Entry number:|Aggregation start time|Target Address:|RTT Values|RTTAvg:|PacketLossSD|Jitter Values|MinOfPositivesSD:|MinOfNegativesSD:|MinOfPositivesDS:|MinOfNegativesDS:|Jitter Avg:|One Way|OWMinSD|OWMinDS|OWAvgSD"

    command_list = [
        {
            "udp_result": "sh ip sla enh col | i Entry number:|Aggregation start time|Target Address:|RTT Values|RTTAvg:|PacketLossSD|Jitter Values|MinOfPositivesSD:|MinOfNegativesSD:|MinOfPositivesDS:|MinOfNegativesDS:|Jitter Avg:|One Way|OWMinSD|OWMinDS|OWAvgSD"},
        {
            "tcp_icmp_result": "show ip sla history full | i Entry number:|Sample time:|RTT|Response return code:"},
        {
            "http_result": "show ip sla statistics details | i IPSLA operation id:|Latest RTT:|Latest operation start|Latest operation return code|Latest TCP Connection RTT|Latest HTTP Status"}
    ]
    result = device.get_show_command_result(command_list)
    device.exit()
    print(result)