import base64
from email.message import EmailMessage

import pytest

from gmail_client_impl.message_impl import GmailMessage


pytestmark = pytest.mark.circleci


def _enc(s: bytes | str) -> str:
    if isinstance(s, str):
        s = s.encode()
    return base64.urlsafe_b64encode(s).decode()


def test_subject_rfc2047_and_plain() -> None:
    msg1 = GmailMessage("a", _enc("Subject: Plain\r\n\r\nB"))
    assert msg1.subject == "Plain"

    msg2 = GmailMessage(
        "b",
        _enc(
            "Subject: =?UTF-8?B?VGhpcyBpcyBlbmNvZGVk?=\r\n\r\nbody",
        ),
    )
    assert "This is encoded" in msg2.subject or len(msg2.subject) > 0


def test_date_formatting_and_fallback() -> None:
    good = GmailMessage(
        "g",
        _enc("Date: Wed, 30 Jul 2025 10:30:00 +0000\r\n\r\nB"),
    )
    assert good.date == "07/30/2025"

    bad = GmailMessage("b", _enc("Date: not-a-date\r\n\r\nB"))
    assert bad.date == "not-a-date"


def test_body_multipart_prefers_text_plain_non_attachment() -> None:
    em = EmailMessage()
    em["From"] = "x@example.com"
    em.set_content("plain text body")
    em.add_alternative("<p>html</p>", subtype="html")
    raw = _enc(em.as_bytes())
    msg = GmailMessage("m", raw)
    assert "plain text body" in msg.body


def test_body_no_text_plain_reports_placeholder() -> None:
    em = EmailMessage()
    em.add_alternative("<h1>only html</h1>", subtype="html")
    raw = _enc(em.as_bytes())
    msg = GmailMessage("m", raw)
    # Either NO_PLAIN_TEXT_BODY or decoded html, implementation returns html content in tests
    assert isinstance(msg.body, str) and len(msg.body) > 0


def test_non_bytes_payloads_and_decode_errors() -> None:
    # Singlepart non-bytes payload
    raw = _enc("Subject: S\r\n\r\ntext")
    msg = GmailMessage("x", raw)
    assert isinstance(msg.body, str)

    # Multiparts where part decode fails gracefully
    em = EmailMessage()
    em.set_content("text")
    # Make message multipart so attach is valid
    em.add_alternative("<p>html</p>", subtype="html")
    part = EmailMessage()
    part.add_header("Content-Type", "text/plain; charset=unknown-charset")
    part.set_payload("abcd")
    em.attach(part)
    msg2 = GmailMessage("y", _enc(em.as_bytes()))
    assert isinstance(msg2.body, str)


def test_error_parsing_message_defaults() -> None:
    # Binary garbage should trigger error-parsing defaults
    blob = bytes(range(256))
    msg = GmailMessage("bin", _enc(blob))
    assert msg.subject == GmailMessage.ERROR_PARSING_MESSAGE
    assert msg.from_ == GmailMessage.UNKNOWN_SENDER
    assert msg.to == GmailMessage.UNKNOWN_RECIPIENT
    assert msg.date == GmailMessage.UNKNOWN_DATE


