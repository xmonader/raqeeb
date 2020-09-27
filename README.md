# forepy

your favorite foreman implementation with extra goodies

## .env file

You can define env vars to be passed to all of your services

```
A=HII
DOMAIN=google.com
FAV_NUM=50
```

## Procfile

And you can define services in `Procfile`

```
app1:
    cmd: ping -c 1 google.com 
    use_shell: true
    run_once: true
    
app2:
    cmd: ping -c 2 yahoo.com
    use_shell: true    
```

Here we define two services

- app1 service, that executes command `ping -c 1 google.com`, use_shell for shell syntax, and run_once to not respawn it if it ever dies
- app2 service, executes `ping -c 2 yahoo.com` and when it's done it will respawn



more advanced examples
```
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


## todo
add more sinks, e.g redis, log stash, check python buffering