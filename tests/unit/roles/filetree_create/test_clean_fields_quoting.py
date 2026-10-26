from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""Regression tests for clean_fields.j2 scalar quoting (issue #99)."""

import pathlib
import re
import tempfile
import unittest

import yaml

try:
    from ansible.parsing.dataloader import DataLoader
    from ansible.template import Templar
    from ansible.utils.unsafe_proxy import AnsibleUnsafeText, wrap_var

    HAS_ANSIBLE = True
except ImportError:
    HAS_ANSIBLE = False

try:
    from ansible.template import trust_as_template
except ImportError:

    def trust_as_template(value):
        return value


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
TEMPLATE_DIR = REPO_ROOT / "roles" / "filetree_create" / "templates"
CLEAN_FIELDS = (TEMPLATE_DIR / "clean_fields.j2").read_text(encoding="utf-8")

_WRAPPER = """\
{% from 'clean_fields.j2' import discard_unwanted_fields %}
{% set __excluded_fields = [] %}
{% set __empty_values = [None, '', {}, []] %}
{% set __reduce_to_name = [] %}
{% set __translate = [] %}
{{ discard_unwanted_fields(value, __excluded_fields, __empty_values, __reduce_to_name, __translate) }}
"""


@unittest.skipUnless(HAS_ANSIBLE, "ansible-core is required")
class TestCleanFieldsQuoting(unittest.TestCase):
    def _render(self, value):
        # Render via a real file under the templates dir so {% from %} resolves.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".j2",
            dir=str(TEMPLATE_DIR),
            delete=False,
        ) as handle:
            handle.write(_WRAPPER)
            wrapper_path = pathlib.Path(handle.name)
        try:
            loader = DataLoader()
            loader.set_basedir(str(TEMPLATE_DIR))
            templar = Templar(loader=loader, variables={"value": value})
            rendered = templar.template(trust_as_template(wrapper_path.read_text(encoding="utf-8")))
            return rendered.strip() if isinstance(rendered, str) else rendered
        finally:
            wrapper_path.unlink(missing_ok=True)

    def test_quotes_colon_in_plain_string(self):
        rendered = self._render("Auto-publish: 2026-10-04 21:00:29")
        self.assertEqual(rendered, "'Auto-publish: 2026-10-04 21:00:29'")

    def test_quotes_colon_in_ansible_unsafe_text(self):
        # On ansible-core 2.16, type_debug is AnsibleUnsafeText (not str); quoting
        # must still apply so flow-style versions maps stay valid YAML (#99).
        unsafe_value = AnsibleUnsafeText("Auto-publish: 2026-10-04 21:00:29")
        rendered = self._render(unsafe_value)
        self.assertEqual(rendered, "'Auto-publish: 2026-10-04 21:00:29'")

    def test_quotes_colon_in_wrap_var_string(self):
        rendered = self._render(wrap_var("Auto-publish: 2026-10-04 21:00:29"))
        self.assertEqual(rendered, "'Auto-publish: 2026-10-04 21:00:29'")

    def test_versions_flow_map_with_unsafe_description_is_valid_yaml(self):
        versions = [
            {
                "version": "83.0",
                "published": wrap_var("2026-10-04 21:00:29 +0200"),
                "description": wrap_var("Auto-publish: 2026-10-04 21:00:29"),
                "filters_applied": True,
            }
        ]
        rendered = self._render(versions)
        parsed = yaml.safe_load("versions: " + rendered + "\n")
        self.assertEqual(
            parsed["versions"][0]["description"],
            "Auto-publish: 2026-10-04 21:00:29",
        )
        self.assertRegex(rendered, r"description:\s*'Auto-publish: 2026-10-04 21:00:29'")

    def test_macro_uses_is_string_not_type_debug_str(self):
        # Guard against regressing to type_debug == 'str', which skips quoting on 2.16.
        self.assertRegex(CLEAN_FIELDS, r"\bis string\b")
        self.assertIsNone(re.search(r"type_debug\s*==\s*'str'", CLEAN_FIELDS))


if __name__ == "__main__":
    unittest.main()
