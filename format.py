#!./bin/python

import argparse
import re
import sys

from lxml import etree

SEP = "  "      # 2 spaces
MAX_LINE_WIDTH = 100


def format_attr_name(attrname, nsmap):
    """ Returns the human readable attribute name (like metal:define-macro)
    """

    for name, uri in nsmap.items():
        attrname = attrname.replace('{%s}' % uri, name and (name + ':') or '')

    attrname = attrname.replace('{http://www.w3.org/XML/1998/namespace}', '')

    return attrname


def format_attr_value(name, value, indent):
    """ Returns a string such as: name="value"
    """

    # assumes value is string

    if '  ' in value:
        # XML standard doesn't allow new lines in attribute values
        # but in case of zpt and zcml files, where we have multiple long
        # interface names or multiple defines declarations, we want to realign
        # these values
        sep = '\n' + SEP * (indent + 1) + ' ' * len('{}="'.format(name))
        value = re.sub(r'(\s\s+)', sep, value)

    return '{}="{}"'.format(name, value)


def format_attrs(node, tag, indent, add_namespaces):
    rendered_attributes = ""

    attrs = []

    if add_namespaces:  # only added on top node
        for name, uri in node.nsmap.items():
            attr = 'xmlns{}{}="{}"'.format(
                name and ':' or '',
                name or '',
                uri
            )
            attrs.append(attr)

    for prefixed_name, value in node.attrib.items():
        name = format_attr_name(prefixed_name, node.nsmap)
        formatted_attr = format_attr_value(name, value, indent)
        attrs.append(formatted_attr)

    if attrs:
        attrs = sorted(set(attrs))      # could sort according to algorithm

        if len(attrs) == 1:
            rendered_attributes += " " + attrs[0]
        else:
            # if any attribute value has a new line, don't "inline" attributes

            if bool([True for x in attrs if '\n' in x]):
                for attr in attrs:
                    rendered_attributes += "\n" + SEP * (indent + 1) + attr
            else:
                # first, try to "inline" all attributes
                attempt = " ".join(attrs)

                if len(SEP * indent + tag + ' ' + attempt) > MAX_LINE_WIDTH:
                    for attr in attrs:
                        rendered_attributes += "\n" + SEP * (indent + 1) + attr
                else:
                    rendered_attributes += " " + attempt

    return rendered_attributes


def format_tag(node, indent=0, add_namespaces=False):
    """ Renders and returns an incomplete node, like <div color="red"
    """

    tag = node.tag

    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return str(node)
    else:
        # see http://www.jclark.com/xml/xmlns.htm

        uri = "{%s}" % node.nsmap[node.prefix]

        tag = tag.replace(uri, '')

    prefix = node.prefix and (node.prefix + ":") or ""

    nodetag = "<" + prefix + tag
    rendered_attributes = format_attrs(node, nodetag, indent, add_namespaces)

    return nodetag + rendered_attributes


def format_end_node(node, children, indentlevel):
    """ Renders the end tag, like: "sometext</div>"
    """

    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return format_inline_text(node.tail or '', node, indentlevel)

    text = (node.text or "")        # .strip()

    if not (text or children):
        return format_inline_text(node.tail, node, indentlevel)

    # see http://www.jclark.com/xml/xmlns.htm
    tag = node.tag

    if node.nsmap:
        uri = "{%s}" % node.nsmap[node.prefix]
        tag = tag.replace(uri, '')

    prefix = node.prefix and (node.prefix + ":") or ""

    base = "</" + prefix + tag + ">"

    return base + format_inline_text(node.tail, node, indentlevel)


def format_inline_text(node_text, node, indentlevel):
    """ Text can be whitespace or real text.
    """

    if not node_text:
        return ''

    # if ('\n' not in node_text) and len(node_text) < 60:

    if ('\n' not in node_text):  # don't add indenting to very short text
        indentlevel = 0

    sep = SEP * indentlevel

    out = []

    for line in node_text.split('\n'):
        if line.strip():
            out.append(sep + line.strip())
        else:
            out.append('')

    return '\n'.join(out)

    return '\n'.join(
        [l.strip() for l in node_text.split('\n')]
    )


def visit_node(node, indentlevel, add_namespaces, acc):
    """ Recursively format a node

    It uses the acc list to accumulate lines for output
    """

    f = format_tag(node, indentlevel, add_namespaces=add_namespaces)
    children = list(node.iterchildren())

    # f += format_inline_text(node.tail, node, indentlevel)

    if node.__class__ is not etree._Comment:
        if children or node.text:
            # this node has children or inline text, needs end tag
            f += ">"
            f += format_inline_text(node.text, node, indentlevel)
        else:
            f += " />"

    line = (SEP * indentlevel, f)
    acc.append(line)

    nextlevel = indentlevel

    # need to look ahead and render the child node, to see if it should be
    # formatted on inline or not

    if len(node.xpath('.//node()')) > 1:
        nextlevel += 1

    for child in children:
        visit_node(child, nextlevel, False, acc)

    endline = format_end_node(node, children, indentlevel) or ''

    if endline:
        if ('\n' not in (node.text or '')) and not children:
            indentlevel = 0
        acc.append((SEP * indentlevel, endline))        # [:-1]


def _print_acc(acc):
    out = ""

    for sep, text in acc:
        out += sep + text

    return cleanup_whitespace(out)


def cleanup_whitespace(text):
    """ Removes the empty whitespace before end of lines """

    out = []

    for line in text.split('\n'):
        line = re.sub(r'(\s+$)', '', line)
        out.append(line)

    return '\n'.join(out)


def format_text_as_xml(text):
    e = etree.fromstring(text)

    # TODO: keep original xml declaration, if it exists?
    lines = [('', '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')]

    visit_node(e, 0, add_namespaces=True, acc=lines)

    return _print_acc(lines)


def main():
    parser = argparse.ArgumentParser(description="XML Formatting tool")

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)

    args = parser.parse_args()
    text = args.infile.read().encode('utf-8')

    out = format_text_as_xml(text)
    args.outfile.write(out)


if __name__ == "__main__":
    main()
