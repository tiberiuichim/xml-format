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
        value = re.sub('(\s\s+)', sep, value)

    return '{}="{}"'.format(name, value)


def format_node(node, indent=0, add_namespaces=False):
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

    ret = "<" + prefix + tag
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

                if len(SEP * indent + ret + ' ' + attempt) > MAX_LINE_WIDTH:
                    for attr in attrs:
                        rendered_attributes += "\n" + SEP * (indent + 1) + attr
                else:
                    rendered_attributes += " " + attempt

    return ret + rendered_attributes


def format_end_node(node, children, indentlevel):
    """ Renders the end tag, like: "sometext</div>"
    """

    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return

    text = (node.text or "").strip()

    if not (text or children):
        return format_inline_text(node.tail, node, indentlevel)

    # see http://www.jclark.com/xml/xmlns.htm
    tag = node.tag

    if node.nsmap:
        uri = "{%s}" % node.nsmap[node.prefix]
        tag = tag.replace(uri, '')

    prefix = node.prefix and (node.prefix + ":") or ""

    base = "</" + prefix + tag + ">\n"

    return base + format_inline_text(node.tail, node, indentlevel)


def format_inline_text(node_text, node, indentlevel):
    """ Text can be whitespace or real text.
    """

    if node_text is None:
        return ''

    res = ''

    lines = (node_text or '').split('\n')

    prev = False

    for line in lines:
        text = line.strip()

        if text:
            prev = True
            res += "\n" + SEP + SEP * indentlevel + text
        else:
            if prev:
                res += "\n"

    if not res:
        if (node_text or '').count('\n') > 1:
            return '\n'

    return res


def rec_node(node, indentlevel, add_namespaces, acc):
    """ Recursively format a node

    It uses the acc list to accumulate lines for output
    """

    f = format_node(node, indentlevel, add_namespaces=add_namespaces)
    children = list(node.iterchildren())

    if node.__class__ is not etree._Comment:
        if children or (node.text or '').strip():
            # this node has children or inline text, needs end tag
            f += ">"
        else:
            f += " />"
        f += format_inline_text(node.text, node, indentlevel)
    else:
        f += format_inline_text(node.tail, node, indentlevel)

    line = (SEP * indentlevel, f)
    acc.append(line)

    for child in children:
        rec_node(child, indentlevel + 1, False, acc)

    endline = format_end_node(node, children, indentlevel) or ''

    if endline:
        acc.append((SEP * indentlevel, endline[:-1]))


def format(text):
    e = etree.fromstring(text)

    lines = []
    # TODO: keep original xml declaration, if it exists?
    lines.append(('',
                  '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'))

    rec_node(e, 0, add_namespaces=True, acc=lines)

    return lines


def main():
    parser = argparse.ArgumentParser(description="XML Formatting tool")

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)

    args = parser.parse_args()
    text = args.infile.read().encode('utf-8')

    lines = format(text)

    for line in lines:
        args.outfile.write(line[0] + line[1] + "\n")


if __name__ == "__main__":
    main()
