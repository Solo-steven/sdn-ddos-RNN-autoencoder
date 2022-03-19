from ryu.app import rest_router

## Master Controller Handle Router Logical 

class MasterController(rest_router.RestRouterAPI):
    def __init__(self,*args, **kwargs):
        super(MasterController, self).__init__(*args, **kwargs)