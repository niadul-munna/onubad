import unittest
from unittest import mock

from translate_tool import translator
from translate_tool.translator import translate, detect_lang, TranslationError


def _resp(json_data, status_code=200):
    r = mock.Mock()
    r.json.return_value = json_data
    r.status_code = status_code
    r.raise_for_status.return_value = None
    return r


class DetectLangTests(unittest.TestCase):
    def test_bengali_text_detected_as_bn(self):
        self.assertEqual(detect_lang("আমি বাংলায় কথা বলি"), "bn")

    def test_ascii_text_detected_as_en(self):
        self.assertEqual(detect_lang("hello world"), "en")

    def test_mixed_text_with_bengali_is_bn(self):
        self.assertEqual(detect_lang("hello আমি"), "bn")


class TranslateTests(unittest.TestCase):
    def test_mymemory_success_returns_translated_text(self):
        payload = {"responseStatus": 200,
                   "responseData": {"translatedText": "হ্যালো"}}
        with mock.patch.object(translator, "requests") as rq:
            rq.get.return_value = _resp(payload)
            out = translate("hello", "en", "bn")
        self.assertEqual(out, "হ্যালো")

    def test_falls_through_to_google_when_mymemory_quota_exceeded(self):
        mymemory_quota = {"responseStatus": 403,
                          "responseData": {"translatedText": "QUOTA EXCEEDED"}}
        google_payload = [[["হ্যালো", "hello", None, None]]]

        def fake_get(url, params=None, timeout=None):
            if "mymemory" in url:
                return _resp(mymemory_quota)
            return _resp(google_payload)

        with mock.patch.object(translator, "requests") as rq:
            rq.get.side_effect = fake_get
            out = translate("hello", "en", "bn")
        self.assertEqual(out, "হ্যালো")

    def test_raises_translation_error_when_all_providers_fail(self):
        with mock.patch.object(translator, "requests") as rq:
            rq.get.side_effect = Exception("network down")
            with self.assertRaises(TranslationError):
                translate("hello", "en", "bn")

    def test_empty_input_returns_empty_without_network(self):
        with mock.patch.object(translator, "requests") as rq:
            self.assertEqual(translate("   ", "en", "bn"), "")
            rq.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
