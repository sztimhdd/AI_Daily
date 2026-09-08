import base64
import io
import json
import unittest
from unittest.mock import patch
from ai_daily import visuals


class VertexRouteTests(unittest.TestCase):
    def test_flash_image_uses_global_endpoint(self):
        captured = []
        def respond(req, **kwargs):
            captured.append(req.full_url)
            return io.BytesIO(json.dumps({'candidates': [{'content': {'parts': [
                {'inlineData': {'data': base64.b64encode(b'image').decode()}}
            ]}}]}).encode())
        with patch.object(visuals.urllib.request, 'urlopen', respond):
            self.assertEqual(visuals.generate_image('draw', 'gemini-3.1-flash-image', token='fake', project='test'), b'image')
        self.assertEqual(captured, ['https://aiplatform.googleapis.com/v1beta1/projects/test/locations/global/publishers/google/models/gemini-3.1-flash-image:generateContent'])
