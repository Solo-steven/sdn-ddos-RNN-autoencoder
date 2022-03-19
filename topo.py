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
        host_number = 1;
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
    ## Net Setup
    topo = CutomTopo(host_Per_Subdomain=host_Per_Subdomain);
    c0 = RemoteController("c0")
    c1 = RemoteController("c1", port=6553)
    net = Mininet(topo= topo, controller=[c0, c1])
    ## Setup switch for every Host
    for host in topo.domain1:
        net.get(host).cmd("ip route add default via 172.16.20.1")
    for host in topo.domain2:
        net.get(host).cmd("ip route add default via 172.16.10.1")
    for host in topo.domain3:
        net.get(host).cmd("ip route add default via 192.168.30.1")
    ## Setup Controller and Routers
    c0.cmd("ryu-manager ryu.app.rest_router &") 
    time.sleep(2) # Need To Wait a Monment for starting router controller
    net.start()
    c0.cmd("./script/router.sh")
    c0.cmd("./script/gateway.sh")
    ## Setup Server or Client
    servers = [ net.get("h4"), net.get("h6")]
    for server in servers:  
        server.cmd("cd mock && node index.js &")
    clients = [ host for host in net.hosts if host not in servers  ]
    for client in clients:
        client.cmd("./script/client.sh {} {} &".format(servers[0].IP(), servers[1].IP()))
    ## Start CLI
    CLI(net)
    ## Stop Net
    net.stop();