# -*- coding: utf-8 -*-
import os
import re

# Test classes inherit from the Django TestCase
from django.test import TestCase

# If you're wanting to do direct database queries you'll need this
from django.db import connection

# The BeautifulSoup HTML parser is useful for testing markup fragments
from BeautifulSoup import BeautifulSoup as Soup

# needed to login to the admin
from django.contrib.auth.models import User

from django.utils.encoding import smart_str

class Common(TestCase):
    """
    This class contains a number of custom assertions which
    extend the default Django assertions. Use this as the super
    class for you tests rather than django.test.TestCase
    """

    # a list of fixtures for loading data before each test
    fixtures = []

    def setUp(self):
        """
        setUp is run before each test in the class. Use it for
        initilisation and creating mock objects to test
        """
        pass

    def tearDown(self):
        """
        tearDown is run after each test in the class. Use it for
        cleaning up data created during each test
        """
        pass

    # A few useful helpers methods

    def execute_sql(*sql):
        "execute a SQL query and return the cursor"
        cursor = connection.cursor()
        cursor.execute(*sql)
        return cursor

    # Custom assertions

    def assert_equal(self, *args, **kwargs):
        'Assert that two values are equal'

        return self.assertEqual(*args, **kwargs)

    def assert_not_equal(self, *args, **kwargs):
        "Assert that two values are not equal"
        
        return not self.assertNotEqual(*args, **kwargs)  #  TODO  reflect me into the report!

    def deny_equal(self, *args, **kwargs):
        "Deny that two values are equal; otherwise, reflect them"
        
        return not self.assertNotEqual(*args, **kwargs)  #  TODO  reflect me into the report!

    def assert_contains(self, needle, haystack, diagnostic=''):
        'Assert that one value (the hasystack) contains another value (the needle)'
        diagnostic = diagnostic + "\nContent should contain `%s' but doesn't:\n%s" % (needle, haystack)
        diagnostic = diagnostic.strip()
        return self.assert_(needle in haystack, diagnostic)  #  TODO  reflect me into the report!

    def assert_doesnt_contain(self, needle, haystack):  #  CONSIDER  deprecate me for deny_contains
        "Assert that one value (the hasystack) does not contain another value (the needle)"
        return self.assert_(needle not in haystack, "Content should not contain `%s' but does:\n%s" % (needle, haystack))

    def deny_contains(self, needle, haystack):
        "Assert that one value (the hasystack) does not contain another value (the needle)"
        return self.assert_(needle not in haystack, "Content should not contain `%s' but does:\n%s" % (needle, haystack))

    def assert_regex_contains(self, pattern, string, flags=None):
        'Assert that the given regular expression matches the string'

        flags = flags or 0
        disposition = re.search(pattern, string, flags)
        self.assertTrue(disposition != None, repr(smart_str(pattern)) + ' should match ' + repr(smart_str(string)))

    def deny_regex_contains(self, pattern, slug):
        'Deny that the given regular expression pattern matches a string'

        r = re.compile(pattern)

        self.assertEqual( None,
                          r.search(smart_str(slug)),
                          pattern + ' should not match ' + smart_str(slug) )

    def assert_count(self, expected, model):
        "Assert that their are the expected number of instances of a given model"
        actual = model.objects.count()
        self.assert_equal(expected, actual, "%s should have %d objects, had %d" % (model.__name__, expected, actual))

    def assert_counts(self, expected_counts, models):
        "Assert than a list of numbers is equal to the number of instances of a list of models"
        if len(expected_counts) != len(models):
            raise("Number of counts and number of models should be equal")
        actual_counts = [model.objects.count() for model in models]
        self.assert_equal(expected_counts, actual_counts, "%s should have counts %s but had %s" % ([m.__name__ for m in models], expected_counts, actual_counts))

    def assert_is_instance(self, model, obj):
        "Assert than a given object is an instance of a model"
        self.assert_(isinstance(obj, model), "%s should be instance of %s" % (obj, model))

    def assert_raises(self, *args, **kwargs):
        "Assert than a given function and arguments raises a given exception"
        return self.assertRaises(*args, **kwargs)

    def assert_attrs(self, obj, **kwargs):
        "Assert a given object has a given set of attribute values"
        for key in sorted(kwargs.keys()):
            expected = kwargs[key]
            actual = getattr(obj, key)
            self.assert_equal(expected, actual, u"Object's %s expected to be `%s', is `%s' instead" % (key, expected, actual))

    def assert_key_exists(self, key, item):
        "Assert than a given key exists in a given item"
        try:
            self.assertTrue(key in item)
        except AssertionError:
            print 'no %s in %s' % (key, item)
            raise AssertionError

    def assert_file_exists(self, file_path):
        "Assert a given file exists"
        self.assertTrue(os.path.exists(file_path), "%s does not exist!" % file_path)

    def assert_has_attr(self, obj, attr):
        "Assert a given object has a give attribute, without checking the values"
        try:
            getattr(obj, attr)
            assert(True)
        except AttributeError:
            assert(False)

    def assert_stderr(self, lamb, expected=None):
        '''
        Pass methods that spew into this to squelch or optionally assert their output,
        without getting it all over your console.
        '''

        from StringIO import StringIO
        import sys
        waz = sys.stderr
        sys.stderr = StringIO()

        try:
            lamb()
            string = sys.stderr.getvalue()
            if expected:  self.assert_regex_contains(string, expected)
            return string
        finally:
            del sys.stderr
            sys.stderr = waz

    def _xml_to_tree(self, xml, forgiving=False):
        from lxml import etree
        from lxml.etree import XMLSyntaxError
        self._xml = xml

        if not isinstance(xml, basestring):
            self._xml = str(xml)  #  TODO  tostring
            return xml

        try:
            if '<html' in xml[:200]:
                parser = etree.HTMLParser(recover=forgiving)
                return etree.HTML(str(xml), parser)
            else:
                parser = etree.XMLParser(recover=forgiving)
                return etree.XML(str(xml))

        except XMLSyntaxError, e:
            yo = re.search(r'line (\d+)', str(e.message))
            line = int(yo.groups()[0])
            culprit = xml.split('\n')[line - 2: line + 2]
            self.assert_(False, '\n'.join([e.message] + culprit))

    def assert_xml(self, xml, xpath, **kw):
        'Check that a given extent of XML or HTML contains a given XPath, and return its first node'

        if hasattr(xpath, '__call__'):
            return self.assert_xml_tree(xml, xpath, **kw)

        tree = self._xml_to_tree(xml, forgiving=kw.get('forgiving', False))
        deep_map = {}

        for q in tree.getroottree().xpath('//*'):  #  ERGO only rip nodes which _have_ more namespacies
            deep_map.update(q.nsmap)  #  ERGO and note this gleefully wrecks nesting... See http://c2.com/cgi/wiki?XmlSucks

        nodes = tree.xpath(xpath, namespaces=deep_map)
        self.assertTrue(len(nodes) > 0, xpath + ' should match ' + self._xml)
        node = nodes[0]
        if kw.get('verbose', False):  self.reveal_xml(node)  #  "Where have ye been? What have ye seen?"--Morgoth
        return node

    def assert_xml_tree(self, sample, block, **kw):  #  TODO  less sucktacular name!
        from lxml.builder import ElementMaker # TODO document we do lxml only !
        doc = block(ElementMaker())   #  TODO  or just pass in an element maker
        path = self._convert_nodes_to_nested_path(doc)
        result = self.assert_xml(sample, path, **kw)  #  this checks nesting
          #  CONSIDER  now detect which parts failed!!!
        doc_order = -1

        for node in doc.xpath('//*'):
            doc_order = self._assert_xml_node(doc_order, kw, node, sample)
              # TODO  amalgamate all errors - don't just kack on the first one!

        return result

    def _assert_xml_node(self, doc_order, kw, node, sample):
        nodes = [self._node_to_predicate(a) for a in node.xpath('ancestor-or-self::*')]
        path = '//' + '/descendant::'.join(nodes)
        node = self.assert_xml(sample, path, **kw)
        location = len(node.xpath('preceding::*'))
        self.assertTrue(doc_order <= location, 'Nodes should appear in order ' + path)
        return location

    def _convert_nodes_to_nested_path(self, node):
        path = 'descendant-or-self::' + self._node_to_predicate(node)
        nodes = node.xpath('*')
        paths = [ '[ ' + self._convert_nodes_to_nested_path(n) + ' ]' for n in nodes ]
        path += ''.join(paths)
        return path

    def _node_to_predicate(self, node):
        path = node.tag

        for key, value in node.attrib.items():
            path += '[ contains(@%s, "%s") ]' % (key, value) # TODO  warn about (then fix) quote escaping bugs

        if node.text:  #  TODO  document only leaf nodes may check for text or attributes
            path += '[ contains(text(), "%s") ]' % node.text

        return path

    def reveal_xml(self, node):
        'Spews an XML node as source, for diagnosis'

        from lxml import etree
        print etree.tostring(node, pretty_print=True)  #  CONSIDER  does pretty_print work? why not?

    def deny_xml(self, xml, xpath):
        'Check that a given extent of XML or HTML does not contain a given XPath'

        tree = self._xml_to_tree(xml)
        nodes = tree.xpath(xpath)
        self.assertEqual(0, len(nodes), xpath + ' should not appear in ' + self._xml)

    def convert_xml_to_element_maker(self, thang):
        'script that coverts XML to its ElementMaker notation'

        from lxml import etree
        doc = etree.XML(thang)
        return self._convert_child_nodes(doc)

    def _convert_child_nodes(self, node, depth=0):
        code = '\n' + ' ' * depth * 2 + 'XML.' + node.tag + '('
        children = node.xpath('*')

        if node.text and not re.search('^\s*$', node.text):
            code += repr(node.text)
            if node.attrib or children:  code += ', '

        if children:
            child_nodes = [ self._convert_child_nodes(n, depth + 1) for n in children ]
            code += (',' ).join(child_nodes)
            if node.attrib:  code += ', '

        if node.attrib:
            attribs = [ '%s=%r' % (kv) for kv in node.attrib.items() ]
            code += ', '.join(attribs)

        code += ')'
        return code

