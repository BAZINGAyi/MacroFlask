class BaseLogin(object):

    def __init__(self, host_ip, port, **kwargs):
        self.encoding = 'utf8'
        self.host_ip = host_ip
        self.login(host_ip, port, **kwargs)
        self.device = None
        self.logger = None if 'logger' not in kwargs else kwargs['logger']

    def login(self, host_ip, port, **kwargs):
        raise NotImplementedError('login method must be implement')

    def get_show_command_result(self, command_set):
        raise NotImplementedError('get_show_command_result method must be implement')

    def exit(self):
        self.device.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()
