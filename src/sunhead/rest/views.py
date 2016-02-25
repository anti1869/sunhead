
from aiohttp.web import View, Response
import simplejson as json


class JSONView(View):

    def json_response(self, context_data=None):
        if context_data is None:
            context_data = {}

        json_data = json.dumps(context_data)
        response = Response(text=json_data, content_type="application/json")

        return response
