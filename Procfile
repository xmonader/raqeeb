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