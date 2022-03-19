from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.lib import hub
from ryu.lib.hub import spawn

class SlaveController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(SlaveController, self).__init__(*args, **kwargs)
        """ Three State: Collection, Training, Detection
              1. Collection: collection switchs data
              2. Training: traning autoencoder.
              3. Detection: detection Is DDoS Happening.
        """
        self.state = "COLLECTION"
        self.datapaths = {}
        self.monitor = spawn(self._monitor)
    # Role Request
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _handle_switch_feature(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        role_request = parser.OFPRoleRequest(datapath, ofproto.OFPCR_ROLE_SLAVE, 0)
        datapath.send_msg(role_request)
    @set_ev_cls(ofp_event.EventOFPRoleReply, MAIN_DISPATCHER)
    def _handle_role_reply(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        if msg.role == ofproto.OFPCR_ROLE_SLAVE:
            print("[REGISTER SWITCH]:", datapath.id)
            self.datapaths[datapath.id] = datapath
    # Flow Stats Request
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _handle_state_change(self, ev):
        if ev.state == DEAD_DISPATCHER:
            if ev.datapath in self.datapaths:
                print("[DISCONNECT SWITCH]:", ev.datapath.id)
                del self.datapaths[ev.datapath.id]
    def _monitor(self):
        while True:
            if self.state != "COLLECTION":
                return
            for datapath in self.datapaths.values():
                parser = datapath.ofproto_parser
                flow_state_req = parser.OFPFlowStatsRequest(datapath)
                datapath.send_msg(flow_state_req)
            hub.sleep(3)
    # Flow Stats Reply
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, [MAIN_DISPATCHER])
    def _handle_flow_stats_reply(self, ev):
        body = ev.msg.body
        
        dst_number = 0
        src_number = 0
        
        byte_count = 0
        packet_count = 0
        flow_count =  len(body);
        
        for flow in body:
            byte_count += flow.byte_count
            packet_count += flow.packet_count
            # Dst Number
            if "ipv4_dst" in flow.match:
                dst_number +=  len(flow.match["ipv4_dst"])
            if "ipv6_dst" in flow.match:
                dst_number += len(flow.match["ipv6_dst"])
            if "arp_spa" in flow.match:
                dst_number = dst_number + len(flow.match["arp_spa"])
            # Src Number
            if "ipv4_src" in flow.match:
                src_number += len(flow.match["ipv4_src"])
            if "ipv6_src" in flow.match:
                src_number += len(flow.match["ipv6_src"])
            if "arp_tpa" in flow.match:
                src_number += len(flow.match["arp_tpa"])
        
        print(dst_number, src_number, byte_count, packet_count, flow_count)