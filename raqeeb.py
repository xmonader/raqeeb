import logging
import os
import select
import signal
import sys
import time
from re import L

import click
import redis

from raqeeb.config import load_config
from raqeeb.dotenv import load_env
from raqeeb.proc import Process
from raqeeb.procfile import Procfile, load_procfile, loads_procfile
from raqeeb.sinks import StdoutSink, RedisSink, FilesystemSink, sink_from_info




class forepy:

    def __init__(self, dotenv_path=None, procfile_path=None, config_path=None):
        self.env = {}
        if dotenv_path:
            self.env = load_env(dotenv_path)

        self.procfile = Procfile(path=procfile_path)
        self.procfile.build_deps_graph()
        self._running_procs = {}
        self._done_procs = {}
        self._procs = {}

        self._config = {}
        if config_path:
            self.set_config(load_config(config_path))
        
        self.__sinks = {}

    def push_to_sink(self, sink_name, m):
        # print(self._sinks)
        print(f"pushing {m} to sink {sink_name}")
        self._sinks[sink_name].log(m)

    def set_config(self, config):
        self._config = config

    def _get_sinks_config(self):
        if not self._config:
            return {'stdout': {'type': 'stdout'}}
        else:
            return self._config['sinks']

    @property
    def _sinks(self):
        if not self.__sinks:
            sinks_config = self._get_sinks_config()
            
            for sink_name, sink_info in sinks_config.items():
                s = sink_from_info(sink_info)
                self.__sinks[sink_name] = s
        return self.__sinks

    

    
    def on_sigint(self, n, stack):
        print("got int")
        for p in self._running_procs.values():
            p.send_signal(signal.SIGINT)
        exit()

    def _terminate(self):
        for p in self._running_procs.values():
            p.terminate()
        exit()
    
    def on_sigterm(self, n, stack):
        print("got term")
        self._terminate()


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
            if "log" in proc_info:
                log_sinks = proc_info["log"]
            else:
                log_sinks = None
            if not cmd:
                raise ValueError(f"invalid proc ${proc_name} doesn't have cmd entry.")
            p = Process(cmd=cmd, use_shell=use_shell, env=self.env, run_once=run_once, cmd_check=cmd_check, tcp_ports=tcp_ports, udp_ports=udp_ports, deps=deps, log_sinks=log_sinks)
            print(f"adding {proc_name} with {p}")
            if p.is_running:
                self._procs[proc_name] = p
            else:
                print(f"process {proc_name} failed to start.")
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
        # print(f"running procs {running_procs}")
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
                    # print(self._procs[p_name])
                    self._running_procs[p_name] = self._procs[p_name].run()

    @property
    def readers(self):
        self.process_chores()

        inputs = []
        readers_to_procs = {}
        for p_name, popen in self._running_procs.items():
            inputs.append(popen.stdout)
            readers_to_procs[popen.stdout.fileno()] = self._procs[p_name]
            inputs.append(popen.stderr)
            readers_to_procs[popen.stderr.fileno()] = self._procs[p_name]
            

        return inputs, readers_to_procs

    def start_watching(self):
        inputs, readers_to_procs = self.readers

        while inputs or not self.all_done():
            # print(self._running_procs)
            # print("all_done: ", self.all_done())
            # print("inputs: ", inputs)
            # print("readers to procs: ", readers_to_procs)
            inputs = [x for x in inputs if not x.closed]
            # print("now inputs are: ", inputs)
            # Wait for at least one of the sockets to be
            # ready for processing
            # print('waiting for the next event', file=sys.stderr)
            readable, _, _ = select.select(inputs, [], [])
            for r in readable:
                line = r.readline()
                if line.strip():
                    sinks = readers_to_procs[r.fileno()].log_sinks
                    for sink_name in sinks:
                        self.push_to_sink(sink_name, line)
                    # print(line)
            time.sleep(0.01)
            inputs, readers_to_procs = self.readers


@click.command()
@click.option('--procfile', type=click.Path(exists=True, readable=True), help="procfile path")
@click.option('--envfile', type=click.Path(exists=True, readable=True), help=".env file path")
@click.option('--configfile', type=click.Path(exists=True, readable=True), help="config file path")
def run(procfile, envfile, configfile=None):
    """Entrypoint for badass raqeeb."""
    print(procfile, envfile)
    thecmd = forepy(dotenv_path=envfile, procfile_path=procfile, config_path=configfile)
    thecmd.prepare_procs()
    print(thecmd)
    # print(thecmd._procs)
    thecmd.run()
    thecmd.start_watching()


if __name__ == '__main__':
    run()
