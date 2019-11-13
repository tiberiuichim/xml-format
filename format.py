#!./bin/python

import argparse

from lxml import etree

SEP = " " * 2


def format_attr_name(attrname, nsmap):
    """ Returns the human readable attribute name (like metal:define-macro)
    """

    for name, uri in nsmap.items():
        attrname = attrname.replace('{%s}' % uri, name and (name + ':') or '')

    attrname = attrname.replace('{http://www.w3.org/XML/1998/namespace}', '')

    return attrname


def format_node(node, indent=0, add_namespaces=False):
    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return node

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
        attr = '{}="{}"'.format(name, value)
        attrs.append(attr)

    extras = ""

    if attrs:
        attrs = sorted(set(attrs))

        for attr in attrs:
            extras += "\n" + SEP * (indent + 1) + attr

    # see http://www.jclark.com/xml/xmlns.htm
    uri = "{%s}" % node.nsmap[node.prefix]

    tag = node.tag.replace(uri, '')
    prefix = node.prefix and (node.prefix + ":") or ""

    ret = "<" + prefix + tag + extras + ">"
    ret += node.text or ''

    return ret


def format_end_node(node):
    if not node.nsmap:
        if node.__class__ is etree._Comment:
            return

    # see http://www.jclark.com/xml/xmlns.htm
    uri = "{%s}" % node.nsmap[node.prefix]

    tag = node.tag.replace(uri, '')
    prefix = node.prefix and (node.prefix + ":") or ""

    return "</" + prefix + tag + ">"


def rec_node(node, indentlevel, add_namespaces, acc):
    """ Recursively format a node
    """
    f = format_node(node, indentlevel, add_namespaces=add_namespaces)
    line = (SEP * indentlevel, f)
    acc.append(line)

    has_children = False

    for child in node.iterchildren():
        has_children = True
        rec_node(child, indentlevel + 1, False, acc)

    if has_children:
        endline = format_end_node(node)

        if endline:
            acc.append((SEP * indentlevel, endline))


def format(text):
    e = etree.fromstring(text)

    lines = []
    lines.append(('',
                  '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'))

    rec_node(e, 0, add_namespaces=True, acc=lines)

    # acc = []
    # add_children(e, acc)
    #
    # for child, level in acc:
    #     lines.append((SEP * level, format_node(child)))
    #
    #     # this needs to be optimized and refactored
    #
    #     if list(child.iterchildren()):
    #         lines.append((SEP * level, format_end_node(child)))

    return lines


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="XML Formatting tool")
    parser.add_argument('path', type=str,)
    args = parser.parse_args()
    path = args.path
    with open(path) as f:
        text = f.read()

    lines = format(text)

    for line in lines:
        print(line[0], line[1])
