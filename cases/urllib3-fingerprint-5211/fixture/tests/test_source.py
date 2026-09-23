import unittest

from source import SSLError, assert_fingerprint


class FingerprintTests(unittest.TestCase):
    def test_nonhex_fingerprint_raises_ssl_error(self):
        with self.assertRaises(SSLError):
            assert_fingerprint(b"certificate", "g" * 32)
