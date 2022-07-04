from rest_framework.routers import SimpleRouter

class NotSoSimpleRouter(SimpleRouter):
    """
    Adds a detail route for "upload" function which uses post
    """

    def __init__(self, trailing_slash=True):
        super().__init__(trailing_slash)
        self.routes[2].mapping["post"] = "upload"