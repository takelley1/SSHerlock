"""Tests for all classes in utils.py"""

# pylint: disable=import-error, missing-class-docstring, missing-function-docstring, invalid-str-returned, no-member, invalid-name

from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from ssherlock_server.utils import (
    check_private_key,
)  # Adjust the import according to your app structure

SSHERLOCK_SERVER_RUNNER_TOKEN = "myprivatekey"


class CheckPrivateKeyTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_no_authorization_header(self):
        request = self.factory.get("/request_job")
        response = check_private_key(request)
        expected_response = JsonResponse(
            {"message": "Authorization header not provided."}, status=400
        )

        self.assertEqual(response.status_code, expected_response.status_code)
        self.assertJSONEqual(
            response.content.decode("utf-8"), expected_response.content.decode("utf-8")
        )

    def test_invalid_authorization_header_format(self):
        request = self.factory.get("/request_job", HTTP_AUTHORIZATION="InvalidFormat")
        response = check_private_key(request)
        expected_response = JsonResponse(
            {"message": "Invalid Authorization header format."}, status=400
        )

        self.assertEqual(response.status_code, expected_response.status_code)
        self.assertJSONEqual(
            response.content.decode("utf-8"), expected_response.content.decode("utf-8")
        )

    def test_incorrect_authorization_token(self):
        request = self.factory.get(
            "/request_job", HTTP_AUTHORIZATION="Bearer wrongtoken"
        )
        response = check_private_key(request)
        expected_response = JsonResponse(
            {"message": "Authorization token incorrect."}, status=404
        )

        self.assertEqual(response.status_code, expected_response.status_code)
        self.assertJSONEqual(
            response.content.decode("utf-8"), expected_response.content.decode("utf-8")
        )

    def test_correct_authorization_token(self):
        request = self.factory.get(
            "/request_job", HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}"
        )
        response = check_private_key(request)

        self.assertIsNone(response)
