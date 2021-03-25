import logging
from unittest import TestCase
from chalicelib.utils.logging import init_logging


class LoggingTest(TestCase):
    def test_valid_log_level(self):
        init_logging("my_service", "DEBUG")
        logger = logging.getLogger(__name__)
        self.assertEqual(logging.getLevelName(logger.getEffectiveLevel()), logging.getLevelName(logging.DEBUG))

    def test_invalid_log_level(self):
        self.assertRaises(ValueError, init_logging, "my_service", "debg")

    def test_blank_log_level(self):
        self.assertRaises(ValueError, init_logging, "my_service", "")

    def test_lowercase_log_level(self):
        init_logging("my_service", "info")
        logger = logging.getLogger(__name__)
        self.assertEqual(logging.getLevelName(logger.getEffectiveLevel()), logging.getLevelName(logging.INFO))
