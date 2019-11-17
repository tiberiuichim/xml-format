import unittest

import lxml.etree

from format import (SEP, _print_acc, format_attr_name, format_attr_value,
                    visit_node)


class TestFormat(unittest.TestCase):

    def test_format_attr_name(self):
        assert format_attr_name('div', {}) == 'div'
        nsmap = {
            'browser': 'http://ns.zope.org/browser'
        }
        assert format_attr_name('{http://ns.zope.org/browser}div',
                                nsmap) == 'browser:div'

    def test_format_attr_value(self):
        assert format_attr_value('bla', '1', 0) == 'bla="1"'

        # 7 because: len(bla="), which is 5, plus SEP (2 spaces)
        assert format_attr_value('bla', '1  2', 0) == \
            '''bla="1\n''' + 7 * ' ' + '''2"'''

    def test_simple_node(self):
        root = lxml.etree.fromstring("<div>Bla</div>")
        acc = []
        visit_node(root, 0, False, acc)
        assert len(acc) == 2
        out = _print_acc(acc)

        assert out == """<div>Bla</div>"""

    def test_selfclosed_node(self):
        root = lxml.etree.fromstring("<div />")
        acc = []
        visit_node(root, 0, False, acc)
        assert len(acc) == 1
        assert _print_acc(acc) == "<div />"

    def test_sorted_attribs(self):
        root = lxml.etree.fromstring("""<div color="red" class="blue" />""")
        acc = []
        visit_node(root, 0, False, acc)
        assert len(acc) == 1
        assert _print_acc(acc) == '<div class="blue" color="red" />'

    def test_selfclosed_node_single_attrib(self):
        root = lxml.etree.fromstring("<div color='red' />")
        acc = []
        visit_node(root, 0, False, acc)
        assert len(acc) == 1
        assert _print_acc(acc) == '<div color="red" />'

    def test_selfclosed_node_many_attrib(self):
        root = lxml.etree.fromstring("<div color='red' class='blue' />")
        acc = []
        visit_node(root, 40, False, acc)
        assert len(acc) == 1
        assert _print_acc(acc) == SEP * 40 + \
            '<div\n' \
            + SEP * 41 + 'class="blue"\n' \
            + SEP * 41 + 'color="red" />'

    def test_preserve_comment(self):
        root = lxml.etree.fromstring("<div><!-- some comment --></div>")
        acc = []
        visit_node(root, 0, False, acc)
        assert len(acc) == 3
        assert _print_acc(acc) == '<div><!-- some comment --></div>'

    def test_ns_tag_only_on_demand(self):
        root = lxml.etree.fromstring(
            "<div xmlns='http://bla'><!-- some comment --></div>")
        acc = []
        visit_node(root, 0, False, acc)
        assert len(acc) == 3
        out = _print_acc(acc)
        assert out == '<div><!-- some comment --></div>'

    def test_ns_tag_included(self):
        root = lxml.etree.fromstring(
            "<div xmlns='http://bla'><!-- some comment --></div>")
        acc = []
        visit_node(root, 0, True, acc)
        out = _print_acc(acc)
        assert len(acc) == 3
        assert out == '<div xmlns="http://bla"><!-- some comment --></div>'

    def test_multiple_ns_tag_included(self):
        root = lxml.etree.fromstring(
            "<b:div xmlns='http://bla' xmlns:b="
            "'http://spam'><!-- some comment --></b:div>")
        acc = []
        visit_node(root, 0, True, acc)
        out = _print_acc(acc)
        assert len(acc) == 3
        assert out == '<b:div xmlns:b="http://spam" ' \
            'xmlns="http://bla"><!-- some comment --></b:div>'

    def test_mixed_nodes(self):
        xml = """<div>
  <adapter name="macro_regions" factory=".catalog.macro_regions" />
  <!-- <adapter name="SearchableText" factory=".catalog.climate_adapt_content_searchabletext" /> -->

  ----[ Vocabularies: ]------

  <utility name="eea.climateadapt.aceitems_datatypes" component=".vocabulary.aceitem_datatypes_vocabulary"/>
</div>"""
        root = lxml.etree.fromstring(xml)
        acc = []
        visit_node(root, 0, True, acc)
        out = _print_acc(acc)
        test = '''<div>
  <adapter factory=".catalog.macro_regions" name="macro_regions" />
  <!-- <adapter name="SearchableText" factory=".catalog.climate_adapt_content_searchabletext" /> -->

  ----[ Vocabularies: ]------

  <utility
    component=".vocabulary.aceitem_datatypes_vocabulary"
    name="eea.climateadapt.aceitems_datatypes" />
</div>'''
        assert out == test


if __name__ == '__main__':
    unittest.main()
