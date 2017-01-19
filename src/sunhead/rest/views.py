
from aiohttp.web import View, Response, HTTPCreated

from sunhead.serializers import JSONSerializer


class BasicView(View):

    def basic_response(self, text=None, **kwargs):
        response = Response(text=text, content_type="text/plain", **kwargs)
        return response


class JSONView(BasicView):

    SERIALIZE_KWARGS = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serializer = JSONSerializer()

    def json_response(self, context_data=None):
        if context_data is None:
            context_data = {}

        json_data = self._serializer.serialize(context_data, **self.SERIALIZE_KWARGS)
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
