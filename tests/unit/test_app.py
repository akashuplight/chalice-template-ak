from unittest import TestCase

import app


class AppTest(TestCase):

    # health Tests
    def test_get_health_return_response(self):

        # ARRANGE
        # ACT
        response = app.get_health()

        # ASSERT
        expected_response_json = {"status": "OK"}
        self.assertEqual(expected_response_json, response)
