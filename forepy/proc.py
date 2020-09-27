import subprocess
import socket

def is_port_listening(port, type_="tcp"):
    """check if the port is being used by any process

    Args:
        port (int): port number

    Returns:
        Bool: True if port is used else False
    """
    result = None
    if type_ == "tcp":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(("127.0.0.1", port))

    else:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            result = s.connect_ex(("127.0.0.1", port))

    return result == 0


class Process:
    def __init__(self, cmd, use_shell=False, env=None, run_once=False, cmd_check="", tcp_ports=None, udp_ports=None, deps=None ):
        self.cmd = cmd
        self.env = env or {}
        self.cmd_check = cmd_check
        self.run_once = run_once
        self.tcp_ports = tcp_ports or []
        self.udp_ports = udp_ports or []
        self.deps = deps or [] 
        self.use_shell = use_shell
        self.proc_object = None

    def is_running(self):
        if self.cmd_check:
            try:
                res = subprocess.check_call(self.cmd, shell=True)
            except subprocess.CalledProcessError:
                return False
            else:
                return True
        if self.tcp_ports:
            for p in self.tcp_ports:
                if not is_port_listening(p):
                    return False

        if self.udp_ports:
            for p in self.udp_ports:
                if not is_port_listening(p, "udp"):
                    return False
        return True


    def run(self):
        p = subprocess.Popen(self.cmd, shell=self.use_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.proc_object = p
        return p