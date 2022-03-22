from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.cli import CLI
import time

## 3 Switch 3 Sub Domain

class CutomTopo(Topo):
    def build(self, host_Per_Subdomain = 2 ):
        ## switch
        s1 = self.addSwitch("s1", cls=OVSKernelSwitch, protocols="OpenFlow13", dpid="0000000000000001")
        s2 = self.addSwitch("s2", cls=OVSKernelSwitch, protocols="OpenFlow13", dpid="0000000000000002")
        s3 = self.addSwitch("s3", cls=OVSKernelSwitch, protocols="OpenFlow13", dpid="0000000000000003")
        # switch Link
        self.addLink(s2, s1)
        self.addLink(s3, s2)
        ## host
        host_number = 1
        self.domain1 = []
        self.domain2 = []
        self.domain3 = []
        for i in range(10, 10 + host_Per_Subdomain):
            host = self.addHost("h{}".format(host_number), ip="172.16.20.{}/24".format(i))
            self.domain1.append(host)
            self.addLink(host, s1)
            host_number = host_number + 1
        for i in range(10, 10 + host_Per_Subdomain):
            host = self.addHost("h{}".format(host_number), ip="172.16.10.{}/24".format(i))
            self.domain2.append(host)
            self.addLink(host, s2)
            host_number = host_number + 1
        for i in range(10, 10 + host_Per_Subdomain):
            host = self.addHost("h{}".format(host_number), ip="192.168.30.{}/24".format(i))
            self.domain3.append(host)
            self.addLink(host, s3)
            host_number = host_number + 1
         
if __name__ == "__main__":
    host_Per_Subdomain = 2
    """ Net Setup 
       1. Create Master Controller as Router Controller
       2. Create Three Slave Monitor Which monitor the Switch Flow State.
    """
    topo = CutomTopo(host_Per_Subdomain=host_Per_Subdomain)
    c0 = RemoteController("c0")
    c1 = RemoteController("c1", port=6553)
    c2 = RemoteController("c1", port=6453)
    c3 = RemoteController("c1", port=6353)
    net = Mininet(topo= topo, controller=[c0, c1, c2, c3])

    """ Net Connection
        1. Set default gateway of each host.
        2. Start run master controller.
        3. Set router table of eacg switch.
    """
    for host in topo.domain1:
        net.get(host).cmd("ip route add default via 172.16.20.1")
    for host in topo.domain2:
        net.get(host).cmd("ip route add default via 172.16.10.1")
    for host in topo.domain3:
        net.get(host).cmd("ip route add default via 192.168.30.1")
    net.start()
    c0.cmd("ryu-manager ./master.py &")     
    time.sleep(2)  
    net.get("s1").start([c0, c1])
    net.get("s2").start([c0, c2])
    net.get("s3").start([c0, c3])
    c0.cmd("./script/router.sh")
    c0.cmd("./script/gateway.sh")

    """ Server and Client
        1. Set up simpe nodejs server with html file.
        2. Let clients start request.
    """
    servers = [ net.get("h4"), net.get("h6")]
    for server in servers:  
        server.cmd("cd mock && node index.js &")
    print("Server At {}, {}".format(servers[0].IP(), servers[1].IP()))
    attacker = net.get("h1")
    clients = [ host for host in net.hosts if host not in servers and host != attacker ]
    for client in clients:
        client.cmd("./script/normal.sh {} {} &".format(servers[0].IP(), servers[1].IP()))
    time.sleep(1)
    
    """ User CLI
        1. Start user cli.
        2. stop net after user exist cli.
    """
    CLI(net)
    net.stop()