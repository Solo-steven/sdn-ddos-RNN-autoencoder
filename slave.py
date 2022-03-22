from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.lib import hub
from ryu.lib.hub import spawn

import csv, time
import pandas as pd
import numpy as np
from model import RNNAutoEncoderDetector

""" Four State: Collecting, Training, Detecting, Progressing
    1. COLLECTING: collection switchs data
    2. Training: traning autoencoder.
    3. Detecting: detection Is DDoS Happening.
    4. Progressing: DDoS is Hapening.
"""

# State Variable
COLLECTING = "COLLECTING"
TRAINING = "TRAINING"
DETECTING = "DETECTING"
PROGRESSING = "PROGRESSING"

class SlaveController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(SlaveController, self).__init__(*args, **kwargs)
        self.state = COLLECTING
        self.datapath = None
        self.monitor = None
        self.start_train =  None
        self.time_interval = 1
        # Training Paramemeter
        self.traning_time = 180
        self.autoencoder = RNNAutoEncoderDetector()
        self.window = []
    # Role Request: Init Job
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
            print(" ===== [REGISTER SWITCH]: {} ===== ".format(datapath.id))
            print("Start collecting switch data for {} s".format(self.traning_time))
            self.datapath = datapath
            self.monitor = spawn(self._monitor)
            self.start_train = spawn(self._start_train)
            with open("./data/data{}.csv".format(datapath.id), "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    'datapath_id', 'dst_ip_count', 'src_ip_count', 'byte_count', 'packet_count', 'flow_count'
                ])
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _handle_state_change(self, ev):
        if ev.state == DEAD_DISPATCHER and ev.datapath is self.datapath:
            print("[DISCONNECT SWITCH]:", ev.datapath.id)
            self.datapath = None
    # Flow Stats Request
    def _monitor(self):
        while True:
            if self.datapath is not None:
                if self.state == COLLECTING or self.state == DETECTING:
                    parser = self.datapath.ofproto_parser
                    flow_state_req = parser.OFPFlowStatsRequest(self.datapath)
                    self.datapath.send_msg(flow_state_req)
                elif self.state == TRAINING:
                    df = pd.read_csv("./data/data{}.csv".format(self.datapath.id))
                    self.autoencoder.train(df.drop(["datapath_id"], axis=1))
                    self.state = DETECTING
                    print(" ===== Start Detecting Mode =====".format(time.time()))
                elif self.state == PROGRESSING:
                    continue
            hub.sleep(self.time_interval)
    def _start_train(self):
        hub.sleep(self.traning_time)
        print(" ===== Stop Collection, Start Training Model ===== ")
        self.state = TRAINING
        return
    # Flow Stats Reply
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, [MAIN_DISPATCHER])
    def _handle_flow_stats_reply(self, ev):
        if self.state == TRAINING or self.state == PROGRESSING:
            return
        datapath = ev.msg.datapath
        body = ev.msg.body         
        dst_ip_count = 0
        src_ip_count = 0
        byte_count = 0
        packet_count = 0
        flow_count =  len(body)       
        for flow in body:
            byte_count += flow.byte_count
            packet_count += flow.packet_count
            # Dst Number
            if "ipv4_dst" in flow.match:
                dst_ip_count +=  len(flow.match["ipv4_dst"])
            if "ipv6_dst" in flow.match:
                dst_ip_count += len(flow.match["ipv6_dst"])
            if "arp_spa" in flow.match:
                dst_ip_count = dst_ip_count + len(flow.match["arp_spa"])
            # Src Number
            if "ipv4_src" in flow.match:
                src_ip_count += len(flow.match["ipv4_src"])
            if "ipv6_src" in flow.match:
                src_ip_count += len(flow.match["ipv6_src"])
            if "arp_tpa" in flow.match:
                src_ip_count += len(flow.match["arp_tpa"])
        data = [datapath.id, dst_ip_count, src_ip_count, byte_count, packet_count, flow_count]
        if self.state == COLLECTING:
            with open("./data/data{}.csv".format(self.datapath.id), "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(data)
        elif self.state == DETECTING:
            if len(self.window) >= 15:
                self.window = self.window[1:]
                self.window.append(data[1:])
                print(self.autoencoder.predict(np.array(self.window)))
            else:
                self.window.append(data[1:])

            