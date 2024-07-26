import re
import time
from base64 import decodebytes

import paramiko


class ParamikoLoginUtils(object):
    wait_login_timeout = 5
    # device upgrade need more times
    wait_exec_command_timeout = 300
    __bufsize = 65536

    def __enter__(self):
        return self

    def __init__(self, ip, port, username, password, **kwargs):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(ip, port, username, password,
                         timeout=self.wait_login_timeout,
                         look_for_keys=False, allow_agent=False,
                         disabled_algorithms=dict(pubkeys=['rsa-sha2-256', 'rsa-sha2-512'])
                         )
        self.__end_character = ""

    # realtime query info for dealing upgrade process
    def execute_command_and_get_response(self, command):
        stdin, stdout, stderr = self.ssh.exec_command(
            command, get_pty=True, timeout=self.wait_exec_command_timeout)
        while not stdout.channel.exit_status_ready():
            line_content = stdout.readline()
            print(line_content)
            if stdout.channel.exit_status_ready():
                the_rest_content = stdout.readlines()
                print(the_rest_content)
                break

    def execute_command_quickly(self, command, timeout=None):
        timeout = self.wait_login_timeout if not timeout else timeout
        stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
        return stdout.readlines()
    
    def get_invoke_shell(self):
        channel = self.ssh.invoke_shell()
        # decide what is the end character
        channel.send(b"\n")
        time.sleep(2)
        data = channel.recv(self.__bufsize).decode("utf8")
        for sysmbol in ["#", "<", ">"]:
            end_character = re.search('\s+([\S]+{})\s+'.format(sysmbol), data)
            if end_character:
                self.__end_character = end_character.group(1).strip()
                break
        if self.__end_character == "":
            raise Exception("Find end character failed, please add time out with this method, and query more details by handle.")
        return channel

    def pull_result_in_shell(self, channel, target_character=None, timeout=1, sleep_time=1):
        start_time = time.time()
        status, message = False, ""
        total_result = ""

        if not target_character:
            target_character = self.__end_character

        while True:
            if channel.recv_ready():
                data = channel.recv(self.__bufsize).decode("utf8")
                total_result += data
                # print(total_result)
                if total_result.find(target_character) != -1:
                    status = True
                    break

            if channel.exit_status_ready():
                print('exit ....')
                break

            now_time = time.time()
            if (now_time - start_time) < timeout:
                time.sleep(sleep_time)
            else:
                message = "Timeout executing this command... context info {}".format(total_result)
                print('time out ....')
                break

        if channel.recv_ready():
            data = channel.recv(self.__bufsize)
            total_result += data
            if total_result.find(target_character) != -1:
                status = True

        return status, message, total_result

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.ssh.close()
