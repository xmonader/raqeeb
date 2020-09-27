from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Callable
from enum import Enum


class NodeColor(Enum):
    White = 0
    Gray = 1
    Black = 2


def has_cycle_dfs(
    graph: Dict[str, List[str]],
    node: str,
    colors: Dict[str, NodeColor],
    has_cycle: List[bool],
    parent_map: Dict[str, str],
):
    if has_cycle[0]:
        return
    colors[node] = NodeColor.Gray

    for dep in graph[node]:
        parent_map[dep] = node
        if colors[dep] == NodeColor.Gray:
            has_cycle[0] = True
            parent_map["__CYCLESTART__"] = dep
            return
        if colors[dep] == NodeColor.White:
            has_cycle_dfs(graph, dep, colors, has_cycle, parent_map)
        colors[node] = NodeColor.Black


def graph_has_cycle(graph: Dict[str, List[str]]) -> Tuple[bool, Dict[str, str]]:
    colors: Dict[str, NodeColor] = {}
    for node in graph:
        colors[node] = NodeColor.White

    parent_map: Dict[str, str] = {}
    has_cycle = [False]
    for node in graph:
        parent_map[node] = "null"
        if colors[node] == NodeColor.White:
            has_cycle_dfs(graph, node, colors, has_cycle, parent_map)
        if has_cycle[0]:
            return (True, parent_map)
    return (False, parent_map)


@dataclass
class Task:
    name: str
    requires: List[str]
    action: Callable


@dataclass
class DepsResolver:
    tasksgraph: Dict[str, List[str]] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(self, task_name: str, deps: List[str], action: str=""):
        thetask = Task(task_name, deps, action)
        self.tasksgraph[task_name] = deps
        self.tasks[task_name] = thetask

    def resolve_deps(self, task_name: str):
        has_cycle, parent_map = graph_has_cycle(self.tasksgraph)
        if has_cycle:
            print(f"cycle found: {parent_map}")
            return
        deps = []
        seen = []

        self._run_task_helper(task_name, deps, seen)

        return deps

    def run_task(self, task_name: str):
        has_cycle, parent_map = graph_has_cycle(self.tasksgraph)
        if has_cycle:
            print(f"cycle found: {parent_map}")
            return
        deps = []
        seen = []

        self._run_task_helper(task_name, deps, seen)
        for tsk in deps:
            t = self.tasks[tsk]
            if callable(t.action):
                t.action()
            elif isinstance(t.action, str):
                print("executing ", t.action)

    def _run_task_helper(self, task_name: str, deps: List[str], seen: List[str]):
        if task_name in seen:
            print(f"[+]resolved {task_name} before. no need to repeat action.")
        tsk = self.tasks[task_name]
        seen.append(task_name)
        if tsk.requires:
            for subtask in self.tasksgraph[tsk.name]:
                self._run_task_helper(subtask, deps, seen)
        deps.append(task_name)


if __name__ == "__main__":

    def with_cycle():
        deps_resolver = DepsResolver()
        deps_resolver.add_task("publish", ["build-release"], "print publish")
        deps_resolver.add_task("build-release", ["nim-installed"], "print exec command to build release mode")
        deps_resolver.add_task("nim-installed", ["curl-installed"], "print curl LINK | bash")
        deps_resolver.add_task("curl-installed", ["publish", "apt-installed"], "apt-get install curl")
        deps_resolver.add_task("apt-installed", [], "code to install apt...")
        deps_resolver.run_task("publish")

    def without_cycle():
        deps_resolver = DepsResolver()
        deps_resolver.add_task("publish", ["build-release"], "print publish")
        deps_resolver.add_task("build-release", ["nim-installed"], "print exec command to build release mode")
        deps_resolver.add_task("nim-installed", ["curl-installed"], "print curl LINK | bash")
        deps_resolver.add_task("curl-installed", ["apt-installed"], "apt-get install curl")
        deps_resolver.add_task("apt-installed", [], "code to install apt...")
        deps_resolver.run_task("publish")

    print("without cycle: ")
    without_cycle()

    print("with cycle")
    with_cycle()