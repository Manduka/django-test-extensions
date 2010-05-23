from django.test import TestCase


class FactorySquirrel:
    '''
    To switch to using the Squirrel, call it like this:

        print FactorySquirrel().bury(model)

    The Squirrel will recursively store every model object in that model.

    Copy the source out, save it in a file, remove your fixtures =[] line, and call
    the squirrel in your setUp():

        exec 'buried_model.py'

    The Squirrel will rebuild your database, TODO times faster than
    Django's current fixture=[] implementation.
    '''

    #  TODO  mascot of squirrel with coffee & superman cape

    nuts = {}

    def __init__(self, to_database=True):
        self.to_database = to_database
        self.created = {}
#        self.nuts = {}

        self.granary = ( # TODO 'from test_extensions.factory_squirrel import FactorySquirrel\n' +
                         '\n' +
                         'squirrel = FactorySquirrel(to_database=False)\n' +
                         '\n' )

    def bury(self, *objects):  #  TODO  bury -> store
        for o in flatten(objects):  self.bury_one(o)
        return self.granary

    def bury_one(self, nut):
        typage = self.fetch_object_type(nut)
        var_name = self.fetch_object_name(nut)
        self._pre_create_necessary_nuts(nut)
        self.granary += var_name + ' = squirrel.dig_up(' + typage + ', None'

        for f in nut._meta.fields:
            thang = self._safely_get_attribute(f, nut)  #  TODO  useful defaults

            if f.rel and thang:
                name = self.fetch_object_name(thang)  #  TODO  what if it's yourself??
                if self.created.has_key(name):
                    self.granary += '                , ' + f.name + '=%s\n' % name
            elif str(thang.__class__
                   ) in ('<type \'unicode\'>', '<type \'int\'>'):  # TODO now do the other kinds!
                self.granary += '                , ' + f.name + '=%r\n' % thang

        self.granary += '                )\n'
        
        self.created[var_name] = nut

        for ro in nut._meta.get_all_related_objects():
            yo_name = ro.field.name
            items = ro.model.objects.filter(**{yo_name: nut.pk}).all()
            self.bury(items)
 
#  TODO put all in a fixture function

    def _pre_create_necessary_nuts(self, nut):
        for f in nut._meta.fields:
            if f.rel:
                thang = self._safely_get_attribute(f, nut)
                if thang:  self.pre_create_if_needed(thang)  #  TODO  what if it's yourself??

    def _safely_get_attribute(self, f, nut):
        # crash_type = ( (f.rel and f.related and f.related.model) and
          #                  f.related.model.DoesNotExist or object )
        try:
            return getattr(nut, f.name)
        except:
            import sys, traceback
            traceback.print_exc(file=sys.stderr)

    def pre_create_if_needed(self, nut):  #  TODO  fun with system metaphors, and precreate_
        typage = self.fetch_object_type(nut)  #  TODO  merge!
        var_name = '%s_%s' % (typage.lower(), str(nut.pk))

        if not self.created.has_key(var_name):
            self.bury_one(nut)

    def fetch_object_type(self, nut):
        import re
        path = re.search(r"'(.+)'", str(type(nut)))
        path = path.group(1).split('.')
        typage = path[-1]
          #  this also slips in the importer, coz we got the variables out
        importer = 'from %s import %s\n' % ('.'.join(path[:-1]), typage)

        if importer not in self.granary:
            self.granary = importer + self.granary

        return typage

    def fetch_object_name(self, nut):
        typage = self.fetch_object_type(nut)
        return '%s_%s' % (typage.lower(), str(nut.pk))

    def fetch_object_name_too(self, nut):  #  TODO  use or lose
        import re
        path = re.search(r"'(.+)'", str(type(nut)))
        path = path.group(1).split('.')
        typage = path[-1]
        importer = 'from %s import %s\n' % ('.'.join(path[:-1]), typage)

        if importer not in self.granary:
            self.granary = importer + self.granary

        return typage

 #  CONSIDER  fix the "grand loop" problem (or just chitter at user for it!)

    def load_granary_files(self, filename):  #  TODO rename to singular
        #for file in
   #     print self.find_fixture_files(filename)
        # TODO  return da squoil, to chain it

  #  def find_fixture_files(self, filename):
        from django.db.models import get_apps
        import os

        for app in get_apps():
            # path = getattr(app, '__path__', None) TODO  what's this?
            path = os.path.dirname(app.__file__) + '/fixtures/%s_granary.py' % filename
            if os.path.exists(path):
                with open(path, 'w') as q:
                    exec q in globals()  #  TODO  use the passed-in squirrel, not the internal one!

    def test_fix_that_squirrels_nuts(self):
        from django.db.models import get_apps
        import os
        filename = 'order'


    def dig_up(self, typage, workalike, **attributes):
        pk_name = typage._meta.pk.name
            # TODO  scrape not FullHistory
        typage.objects.filter(pk=attributes.get(pk_name,-1)).delete()

        #try:

        nut = typage(**attributes)  #  TODO  don't save to database
        if self.to_database:  nut.save()

        #except:
         #   return None  #  TODO  better recorvery!
        name = self.fetch_object_name(nut)
        self.nuts[name] = nut
        return nut

        #  TODO  the assert_xml_tree system should replace its low
       #    level assert doc strings with a high-level one revealing intent

    
class FactorySquirrelTest(TestCase):
    def _fixture_setup(self):
        self._fs = FactorySquirrel()

        for granary in getattr(self, 'squirrel', []):
            self._fs.load_granary_files(granary)

        return super(FactorySquirrelTest, self)._fixture_setup()

    def _fixture_teardown(self):
#        for nut in self._fs.nuts.values():
            # TODO only if we created it nut.__class__.objects.filter(pk=nut.pk).delete()
 #           del nut
        self._fs.nuts = {}


def flatten(x):  #  TODO  merge me into django-test-extensions/util
    '''Flattens list. Useful for permitting method arguments
       that take either a scalar or a list'''

    r = []
    if hasattr(x, '__iter__'):
        for y in x:
            r.extend(flatten(y))
    else:
        r.append(x)
    return r
