import re
import yaml
from .depsresolver import DepsResolver

def loads_procfile(s):
    apps = yaml.load(s)
    print(apps)
    return apps

def load_procfile(path):
    with open(path) as f:
        return loads_procfile(f.read())

class Procfile:
    def __init__(self, content=None, path=None):
        if path is not None:
            with open(path) as f:
                content = f.read()
        self._content = content
        self._loaded_content = {}
        self._depsresolver = None
        self._tasks_deps = {}

    @property
    def processes_info(self):
        return self._loaded_content

    @property
    def processes_deps_graph(self):
        return self._tasks_deps

    def load_procs(self):
        self._loaded_content = loads_procfile(self._content)
        return self._loaded_content

    def build_deps_graph(self):
        if not self._loaded_content:
            self.load_procs()
        self._depsresolver = DepsResolver()
        for proc_name in self._loaded_content:
            proc_data = self._loaded_content[proc_name]
            proc_deps = []
            if "deps" in proc_data:
                proc_deps = proc_data["deps"]
            self._depsresolver.add_task(proc_name, proc_deps)
        for proc_name in self._loaded_content:
            deps = self._depsresolver.resolve_deps(proc_name)
            deps.remove(proc_name)
            self._tasks_deps[proc_name] = deps
        return self._tasks_deps        



if __name__ == '__main__':
    # TODO
    """
    # sinks:
    #     - one:
    #         type: redis
    #         port: ...
    #     - two: 
    #         type: elastic
    #         port: ....

    """
    s = """


web: 
  cmd: node api.js 1000
  checks:
    tcp_ports: [1000]
    udp_port: []
    cmd: nc 1000
  run_once: true
  deps:
     - redis

redis: 
  cmd: redis --port 15000
  checks:
    tcp_ports: [15000]
    cmd: nc -z 127.0.0.1 15000

  run_once: false

"""

    loads_procfile(s)
    p = Procfile(s)
    print(p.build_deps_graph())


