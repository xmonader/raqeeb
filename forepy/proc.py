import subprocess
import socket
import psutil

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
    # print(f"checking port {port} result was {result}")
    return result == 0


class Process:
    def __init__(self, cmd, use_shell=False, env=None, run_once=False, cmd_check="", tcp_ports=None, udp_ports=None, deps=None, log_sinks=None ):
        self.cmd = cmd
        self.env = env or {}
        self.cmd_check = cmd_check
        self.run_once = run_once
        self.tcp_ports = tcp_ports or []
        self.udp_ports = udp_ports or []
        self.deps = deps or [] 
        self.use_shell = use_shell
        self.proc_object = None
        self.log_sinks = log_sinks or []

    def __str__(self):
        return f"Proc {self.cmd}, {self.cmd_check}, {self.tcp_ports}, {self.udp_ports}, {self.deps}"

    def is_running(self):
        # DON'T RESTORE PSUTIL
        print("checking pid: ", self.proc_object.pid)
        # if not psutil.pid_exists(self.proc_object.pid):
        #     return False
        # print(self)
        # print(f"checking command is running")
        if self.cmd_check:
            # print(f"checking by command {self.cmd_check}")
            try:
                res = subprocess.check_call(self.cmd, shell=True)
            except subprocess.CalledProcessError:
                # print("not runnning..., cmd_check")
                return False
            else:
                # print("running...")
                return True
        if self.tcp_ports:
            for p in self.tcp_ports:
                # print("checking against tcp port ",p )
                if not is_port_listening(p):
                    # print("port reason")
                    return False

        if self.udp_ports:
            for p in self.udp_ports:
                # print("checking against udp port ", p)
                if not is_port_listening(p, "udp"):
                    # print("port reason")
                    return False
        # print(f"{self.cmd} is running.... correctly after checks")
        return True

    def run(self):
        p = subprocess.Popen(self.cmd, shell=self.use_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.proc_object = p
        return p