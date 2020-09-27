from re import L
from forepy.dotenv import load_env
from forepy.procfile import load_procfile, loads_procfile, Procfile
from forepy.proc import Process
import click
import select
import sys
import signal
import time




class forepy:

    def __init__(self, dotenv_file_path=None, procfile_path=None):
        self.env = {}
        if dotenv_file_path:
            self.env = load_env(dotenv_file_path)

        self.procfile = Procfile(path=procfile_path)
        self.procfile.build_deps_graph()
        self._running_procs = {}
        self._done_procs = {}
        self._procs = {}

    def on_sigint(self, n, stack):
        print("got int")
        for p in self._running_procs.values():
            p.send_signal(signal.SIGINT)
        exit()

    def on_sigterm(self, n, stack):
        print("got term")

        for p in self._running_procs.values():
            p.terminate()
        exit()

    def on_sigstop(self, n, stack):
        print("got sigstop")

        for p in self._running_procs.values():
            p.send_signal(signal.SIGSTOP)
        exit()


    def register_sighandlers(self):
        signal.signal(signal.SIGTERM, self.on_sigterm)
        signal.signal(signal.SIGINT, self.on_sigint)
        # signal.signal(signal.SIGSTOP, self.on_sigstop)

    def prepare_procs(self):
        for proc_name, proc_info in self.procfile.processes_info.items():
            print(proc_name, proc_info)
            cmd = proc_info.get('cmd')
            use_shell = proc_info.get('use_shell', True)
            run_once  =  proc_info.get('run_once', False)
            cmd_check = ''
            tcp_ports = []
            udp_ports = []
            if "checks" in proc_info:
                cmd_check = proc_info["checks"].get('cmd', '')
                tcp_ports = proc_info["checks"].get('tcp_ports', [])
                udp_ports = proc_info["checks"].get('udp_ports', [])
            deps = proc_info.get('deps', [])
            if not cmd:
                raise ValueError(f"invalid proc ${proc_name} doesn't have cmd entry.")
            p = Process(cmd=cmd, use_shell=use_shell, env=self.env, run_once=run_once, cmd_check=cmd_check, tcp_ports=tcp_ports, udp_ports=udp_ports, deps=deps)
            print(f"adding {proc_name} with {p}")
            self._procs[proc_name] = p

        self.procfile.build_deps_graph()

    def run(self):
        self.register_sighandlers()
        for proc_name in self._procs:
            print(f"starting {proc_name}")
            self._run_proc(proc_name)

    def _run_proc(self, proc_name):
        proc = self._procs[proc_name]
        deps = proc.deps
        for d in deps:
            # dep_p = self._procs[d]
            self._run_proc(d)
        self._running_procs[proc_name] = proc.run()

    def all_done(self):
        return all(x.poll() is not None for x in self._running_procs.values())
    
    def process_chores(self):
        running_procs = self._running_procs.copy()
        print(f"running procs {running_procs}")
        for p_name, p in running_procs.items():
            # print(f"proc {p_name} poll: {p.poll()} , is running = {self._procs[p_name].is_running()}")
            if not self._procs[p_name].is_running():
                # it was finished
                if self._procs[p_name].run_once:
                    # print(p_name, " was supposed to run once so it's ok")
                    self._done_procs[p_name] = p
                    del self._running_procs[p_name]
                else:
                    print(f"***respawning {p_name}..")
                    print(self._procs[p_name])
                    self._running_procs[p_name] = self._procs[p_name].run()

    @property
    def readers(self):
        self.process_chores()

        stdoutreaders = [p.stdout for p in self._running_procs.values()]
        stderrreaders = [p.stderr for p in self._running_procs.values()]
        inputs = [*stdoutreaders, *stderrreaders]
        return inputs

    def start_watching(self):
        inputs = self.readers
        while inputs or not self.all_done():
            # print(self._running_procs)
            # print("all_done: ", self.all_done())
            # print([(x, x.closed, x.readable()) for x in inputs])
            inputs = [x for x in inputs if not x.closed]
            # print("now inputs are: ", inputs)
            # Wait for at least one of the sockets to be
            # ready for processing
            # print('waiting for the next event', file=sys.stderr)
            readable, _, _ = select.select(inputs, [], [])
            for r in readable:
                line = r.readline()
                if line.strip():
                    print(line)
            time.sleep(0.1)
            inputs = self.readers

@click.command()
@click.option('--procfile', type=click.Path(exists=True, readable=True), help="procfile path")
@click.option('--envfile', type=click.Path(exists=True, readable=True), help=".env file path")
def run(procfile, envfile):
    """Entrypoint for badass forepy."""
    print(procfile, envfile)
    thecmd = forepy(dotenv_file_path=envfile, procfile_path=procfile)
    thecmd.prepare_procs()
    print(thecmd)
    print(thecmd._procs)
    thecmd.run()
    thecmd.start_watching()

    print("hello")

if __name__ == '__main__':
    run()