app1:
    cmd: ping -c 1 google.com 
    run_once: true
    checks:
        cmd: pgrep google.com
    deps: 
        - redis
app2:
    cmd: ping -c 50 yahoo.com
    checks:
        cmd: pgrep yahoo.com

redis:
    cmd: redis-server --port 6010
    checks:
        cmd: ./checkredis.sh
        tcp_ports: [6010]