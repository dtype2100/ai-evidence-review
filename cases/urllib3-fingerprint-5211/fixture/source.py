"""urllib3 pre-fix function excerpt; package dependencies are local stand-ins.

Original function: https://github.com/urllib3/urllib3/blob/7a802a49bb7880624b5fa0053dd7cc77b94966c2/src/urllib3/util/ssl_.py#L107-L138
MIT license and copyright notice: ../LICENSE.txt
"""

import hashlib
import hmac
from binascii import unhexlify


class SSLError(Exception):
    pass


HASHFUNC_MAP = {
    length: getattr(hashlib, algorithm, None)
    for length, algorithm in ((32, "md5"), (40, "sha1"), (64, "sha256"))
}


def assert_fingerprint(cert: bytes | None, fingerprint: str) -> None:
    """
    Checks if given fingerprint matches the supplied certificate.

    :param cert:
        Certificate as bytes object.
    :param fingerprint:
        Fingerprint as string of hexdigits, can be interspersed by colons.
    """

    if cert is None:
        raise SSLError("No certificate for the peer.")

    fingerprint = fingerprint.replace(":", "").lower()
    digest_length = len(fingerprint)
    if digest_length not in HASHFUNC_MAP:
        raise SSLError(f"Fingerprint of invalid length: {fingerprint}")
    hashfunc = HASHFUNC_MAP.get(digest_length)
    if hashfunc is None:
        raise SSLError(
            f"Hash function implementation unavailable for fingerprint length: {digest_length}"
        )

    # We need encode() here for py32; works on py2 and p33.
    fingerprint_bytes = unhexlify(fingerprint.encode())

    cert_digest = hashfunc(cert).digest()

    if not hmac.compare_digest(cert_digest, fingerprint_bytes):
        raise SSLError(
            f'Fingerprints did not match. Expected "{fingerprint}", got "{cert_digest.hex()}"'
        )
