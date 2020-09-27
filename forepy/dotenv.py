import re

KV_RE = re.compile("([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(.+)")
def loads(s):
    ms = KV_RE.findall(s)
    
    print(dict(ms))
    return dict(ms)

def load(path):
    with open(path) as f:
        return loads(f.read())


if __name__ == '__main__':

    s = """
A = 5
AAA = 6
A_B = 7
$$ = 11
"""

    loads(s)