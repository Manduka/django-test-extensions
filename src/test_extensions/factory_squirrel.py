
class FactorySquirrel:
    '''
    To switch to using the Squirrel, call it like this:

        print FactorySquirrel().bury(model)

    The Squirrel will recursively store every model object in that model.

    Copy the source out, remove your fixtures =[] line, and call the squirrel
    in your setUp():

        exec 'buried_model.py'

    The Squirrel will rebuild your database, TODO times faster than
    Django's current fixture=[] implementation.
    '''

    #  TODO  mascot of squirrel with coffee & superman cape

    def __init__(self):
        self.created = {}
        self.nuts = '\nsquirrel = FactorySquirrel()\n\n'

    def bury(self, objects):  #  TODO
        for o in flatten([objects]):  self.bury_nut(o)
        return self.nuts

    def bury_nut(self, o):
        typage = self.fetch_object_type(o)
        var_name = self.fetch_object_name(o)
        self.created[var_name] = o

        for f in o._meta.fields:
            if f.rel:
                thang = getattr(o, f.name)

                if thang:
                    self.pre_create_if_needed(thang)  #  TODO  what if it's yourself??

        self.nuts += var_name + ' = squirrel.dig_up(' + typage + ', None'

        for f in o._meta.fields:
            thang = getattr(o, f.name)  #  TODO  useful defaults
          #  except:#  TODO  more accurate exception type & reporting

            if str(getattr(o, f.name).__class__
                   ) in ('<type \'unicode\'>', '<type \'int\'>'):  # TODO now do the other kinds!
                self.nuts += '                , ' + f.name + '=%r\n' % thang
            elif f.rel and thang:
                name = self.fetch_object_name(thang)  #  TODO  what if it's yourself??
                self.nuts += '                , ' + f.name + '=%s\n' % name

        self.nuts += '                )\n'

        for ro in o._meta.get_all_related_objects():
            yo_name = ro.field.name
            items = ro.model.objects.filter(**{yo_name: o.pk}).all()
            self.bury(items)

#  TODO put all in a fixture function

    def pre_create_if_needed(self, o):  #  TODO  fun with system metaphors, and precreate_
        typage = self.fetch_object_type(o)  #  TODO  merge!
        var_name = '%s_%s' % (typage.lower(), str(o.pk))

        if not self.created.has_key(var_name):
            self.bury_nut(o)

    def fetch_object_type(self, o):
        import re
        path = re.search(r"'(.+)'", str(type(o)))
        path = path.group(1).split('.')
        typage = path[-1]
          #  this also slips in the importer, coz we got the variables out
        importer = 'from %s import %s\n' % ('.'.join(path[:-1]), typage)

        if importer not in self.nuts:
            self.nuts = importer + self.nuts

        return typage

    def fetch_object_name(self, o):
        typage = self.fetch_object_type(o)
        return '%s_%s' % (typage.lower(), str(o.pk))

    def fetch_object_name_too(self, o):  #  TODO  use or lose
        import re
        path = re.search(r"'(.+)'", str(type(o)))
        path = path.group(1).split('.')
        typage = path[-1]
        importer = 'from %s import %s\n' % ('.'.join(path[:-1]), typage)

        if importer not in self.nuts:
            self.nuts = importer + self.nuts

        return typage

 #  TODO fix the "grand loop" problem (or just chitter at user for it!)

    def dig_up(self, typage, workalike, **attributes):
        pk_name = typage._meta.pk.name
            # TODO  scrape not FullHistory
        typage.objects.filter(pk=attributes.get(pk_name,-1)).delete()

        #try:
        o = typage.objects.create(**attributes)  #  TODO  don't save to database
        #except:
         #   return None  #  TODO  better recorvery!
        return o

        #  TODO  the assert_xml_tree system should replace its low
       #    level assert doc strings with a high-level one revealing intent

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
