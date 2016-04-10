
from aiohttp.web import View, Response

from sunhead.serializers import JSONSerializer


class JSONView(View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = JSONSerializer()

    def json_response(self, context_data=None):
        if context_data is None:
            context_data = {}

        json_data = self._serializer.serialize(context_data)
        response = Response(text=json_data, content_type="application/json")

        return response

    def created_response(self, context_data=None, location=None):
        if context_data is not None:
            context_data = self._serializer.serialize(context_data)

        headers = {
            "Location": location,
        }

        response = Response(text=context_data, status=201, headers=headers)
        return response
