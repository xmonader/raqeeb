# forepy

your favorite [foreman](https://github.com/ddollar/foreman) implementation with extra goodies

## .env file

You can define env vars to be passed to all of your services

```
A=HII
DOMAIN=google.com
FAV_NUM=50
```

## Procfile

And you can define services in `Procfile`

```yaml
app1:
    cmd: ping -c 1 google.com 
    run_once: true
    checks:
        cmd: ps aux | grep google
    deps: 
        - redis
app2:
    cmd: ping -c 50 yahoo.com
    checks:
        cmd: ps aux | grep google

redis:
    cmd: redis-server --port 6010
    checks:
        cmd: redis-cli -p 6010 ping
        tcp_ports: [6010]
```

Here we define two services

- app1 service, that executes command `ping -c 1 google.com`, and run_once to not respawn it if it ever dies we say it depends on `redis` service, so redis needs to execute first. and it's check command is checking for google in `ps aux` output
- app2 service, executes `ping -c 50 yahoo.com` and when it's done it will respawn and it's check command is checking for yahoo in `ps aux` output
- redis service starts redis on port 6010 and its check is checking for port 6010 to be listening and also there's a `redis-cli -p 6010 ping` check command to validate if redis ok


```
starting app1
starting app2
b'PING yahoo.com (98.137.11.164) 56(84) bytes of data.\n'
b'PING google.com (216.58.198.78) 56(84) bytes of data.\n'
b'64 bytes from mrs09s08-in-f14.1e100.net (216.58.198.78): icmp_seq=1 ttl=116 time=155 ms\n'
b'64 bytes from media-router-fp73.prod.media.vip.gq1.yahoo.com (98.137.11.164): icmp_seq=1 ttl=49 time=248 ms\n'
b'64 bytes from media-router-fp73.prod.media.vip.gq1.yahoo.com (98.137.11.164): icmp_seq=2 ttl=49 time=265 ms\n'
***respawning app2..
b'PING yahoo.com (98.137.11.164) 56(84) bytes of data.\n'
^Cgot int
```

see the `**respawning app2`?



more advanced examples
```yaml
web: 
  cmd: node api.js 1000
  checks:
    - tcp_ports: [1000]
    - udp_port: []
    - cmd: nc 1000
  run_once: true
  deps:
     - redis

redis: 
  cmd: redis --port 15000
  checks:
    - tcp_ports: [15000]
    - cmd: nc -z 127.0.0.1 15000

  run_once: false
```

Here you can define your dependencies so `redis` service will have to execute before `web` service, and also has more advanced checks
- cmd_check: a command to execute to ensure the service is running (e.g pinging and endpoint or checking a file exists on the filesystem)
- tcp_port : checks if certain set of tcp ports been taken
- udp_port : checks if certain set of udp ports been taken



##  Sinks
when starting forepy you can define sinks in the  config.yaml file.

example 
```yaml
sinks:
  stdout:
      type: stdout
      name: thecmd

  redis:
      type: redis
      host: 127.0.0.1
      port: 6379
      name: thecmd
    
  filesystem:
      type: filesystem
      path: /tmp
      name: thecmd
```

Currently we support different kinds of sinks for

- stdout: just see the output in forepy console
- filesystem: logs in the filesystem  in $path/$name.log
- redis: logs in redis (requires redis info) (still in progress)

And to use logging sink for your service, all you need to do is use the log section for your service config, here's an example:

```yaml
app1:
    cmd: ping -c 1 google.com 
    run_once: true
    checks:
        cmd: ps aux | grep google
    deps: 
        - redis
    log:
        - stdout
app2:
    cmd: ping -c 4 yahoo.com
    checks:
        cmd: ps aux | grep google
    log:
        - stdout
        - redis

redis:
    cmd: redis-server --port 6010
    checks:
        cmd: redis-cli -p 6010 ping
        tcp_ports: [6010]
    log:
        - stdout

```

## todo
add more sinks, e.g redis, log stash, check python buffering