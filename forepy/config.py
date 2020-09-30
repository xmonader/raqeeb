import yaml

def loads_config(s):
    conf = yaml.load(s)
    return conf

def load_config(path):
    with open(path) as f:
        return loads_config(f.read())