import logging
import os

HAS_REDIS = False
try:
    import redis
except ImportError:
    print("[-] redis not available")
else:
    HAS_REDIS = True


class Sink:
    def log(self, m):
        pass

class StdoutSink(Sink):
    def __init__(self, sinfo):
        self.sinfo = sinfo
        self._name = sinfo['name']
        self.logger = logging.getLogger(self._name)
        self.logger.setLevel(logging.DEBUG)

    def log(self, m):
        self.logger.debug(m)

class FilesystemSink(Sink):
    def __init__(self, sinfo):
        self.sinfo = sinfo
        self._name = sinfo['name']
        self._path = sinfo.get('path', "")
        fh = logging.FileHandler(os.path.join(self._path, f"{self._name}.log"))
        fh.setLevel(logging.DEBUG)
        self.logger = logging.getLogger(self._name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)


    def log(self, m):
        self.logger.debug(m)


class RedisSink(Sink):
    def __init__(self, sinfo):
        self.sinfo = sinfo
        self._name = sinfo['name']
        self.r = redis.Redis(host=sinfo['host'], port=sinfo['port'])

    def log(self, m):
        self.r.rpush(self._name, m)
        

def sink_from_info(sinfo):
    if sinfo['type'] == "stdout":
        return StdoutSink(sinfo)
    elif sinfo['type'] == 'filesystem':
        return FilesystemSink(sinfo)
    elif sinfo['type'] == 'redis':
        return RedisSink(sinfo)
