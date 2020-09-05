# -*- coding: utf-8 -*-

from rules.rule import *
import math


class Rule(KLCRule):
    """
    Create the methods check and fix to use with the kicad lib files.
    """
    # define which items are checked against which properties
    singular_type_name= {'arcs': 'arc',
                         'circles': 'circle',
                         'polylines': 'polyline',
                         'rectangles': 'rectangle',
                         'texts': 'text'}
    types = {'arcs': ['posx', 'posy', 'radius', 'start_angle', 'end_angle'],
             'circles': ['posx', 'posy', 'radius'],
             'polylines': ['points'],
             'rectangles': ['startx', 'starty', 'endx', 'endy'],
             'texts': ['posx', 'posy', 'direction', 'text']}

    def __init__(self, component):
        super(Rule, self).__init__(component, 'Graphical elements are not duplicated or overlap')

    def check(self):
        """
        Look at all drawing items and try to find duplicates
        Currently this only checks on a very high level, some more detailed checks need to be implemented.
        Possible improvements:
        * Arcs and Circles with the same center and radius
        * Split polylines and rectangles into single lines and check them for overlap
        """
        def check_identical(typ, items, properties):
          identical_items = []

          # there can be no duplicate items if there is less than 2
          if len(items) <= 1:
            return []

          # iterate over items twice, check
          for itm1 in items:
            for itm2 in items:
              # the same item is not a duplicate
              if itm1 is itm2:
                continue

              # check amount of properties that are the same
              is_identical = True
              for prop in properties:
                if itm1[prop] != itm2[prop]:
                  is_identical = False
                  break

              # no properties differ, we consider those items to be identical
              if is_identical:
                # construct a nice message so the user can see which items are considered
                # identical and for which reason
                item_details = [ "{}: {}".format(prop, itm1[prop]) for prop in properties]
                error_msg = "Duplicate {typ:s} ({properties:s})".format(
                        typ=self.singular_type_name[typ],
                        properties=", ".join(item_details))
                identical_items.append(error_msg)
                # no need to iterate over this item in the outer loop again
                items.remove(itm2)
          return(identical_items)


        identical_items = []
        # run the check for each type
        for typ, prop in self.types.items():
          identical_items.extend(check_identical(typ, self.component.draw[typ], prop))

        if len(identical_items) > 0:
            self.error("Graphic elements must not be duplicated.")
            for element in identical_items:
               self.errorExtra(element)

        return False

    def fix(self):
        pass
