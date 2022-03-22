from ryu.app import rest_router
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.lib.packet import packet

## Master Controller Handle Router Logical 

class MasterController(rest_router.RestRouterAPI):
    def __init__(self,*args, **kwargs):
        super(MasterController, self).__init__(*args, **kwargs)