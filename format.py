#!./bin/python

import argparse
import re
import sys

from lxml import etree

SEP = "  "      # 2 spaces


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

    if '  ' in value:
        # XML standard doesn't allow new lines in attribute values
        # but in case of zpt and zcml files, where we have multiple long
        # interface names or multiple defines declarations, we want to realign
        # these values
        sep = '\n' + SEP * (indent + 1) + ' ' * len('{}="'.format(name))
        value = re.sub('(\s\s+)', sep, value)

    return '{}="{}"'.format(name, value)


def format_node(node, indent=0, add_namespaces=False):
    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return str(node)

    # see http://www.jclark.com/xml/xmlns.htm
    uri = "{%s}" % node.nsmap[node.prefix]

    tag = node.tag.replace(uri, '')
    prefix = node.prefix and (node.prefix + ":") or ""

    ret = "<" + prefix + tag

    attrs = []

    if add_namespaces:
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

    extras = ""

    if attrs:
        attrs = sorted(set(attrs))      # could sort according to algorithm

        if len(attrs) == 1:
            extras += " " + attrs[0]
        else:
            has_newline = bool([True for x in attrs if '\n' in x])

            if has_newline:
                for attr in attrs:
                    extras += "\n" + SEP * (indent + 1) + attr
            else:
                # first, try to inline all attributes
                attempt = " ".join(attrs)

                if len(SEP * indent + ret + ' ' + attempt) > 100:
                    for attr in attrs:
                        extras += "\n" + SEP * (indent + 1) + attr
                else:
                    extras += " " + attempt

    ret += extras

    return ret


def format_end_node(node, children, indentlevel):
    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return

    text = (node.text or "").strip()

    if not (text or children):
        return format_text(node.tail, indentlevel)

    # see http://www.jclark.com/xml/xmlns.htm
    uri = "{%s}" % node.nsmap[node.prefix]

    tag = node.tag.replace(uri, '')
    prefix = node.prefix and (node.prefix + ":") or ""

    base = "</" + prefix + tag + ">\n"

    return base + format_text(node.tail, indentlevel)


def format_text(node_text, indentlevel):
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
    """

    f = format_node(node, indentlevel, add_namespaces=add_namespaces)
    children = list(node.iterchildren())

    if node.__class__ is not etree._Comment:
        if children or (node.text or '').strip():
            f += ">"
        else:
            f += " />"
        f += format_text(node.text, indentlevel)
    else:
        f += format_text(node.tail, indentlevel)

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
    lines.append(('',
                  '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'))

    rec_node(e, 0, add_namespaces=True, acc=lines)

    return lines


if __name__ == "__main__":

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
