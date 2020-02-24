# -*- coding: utf-8 -*-

from rules.rule import *
import math


class Rule(KLCRule):
    """
    Create the methods check and fix to use with the kicad lib files.
    """
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
              i = 0
              for prop in properties:
                if itm1[prop] == itm2[prop]:
                  i += 1
              # are all properties checked the same? if yes we consider this a duplicate
              if i == len(properties):
                # really hacky string manipulation. remote the plural 's' from the typ
                msg = "Duplicate %s (" % typ[:-1]
                for prop in properties:
                  msg += "%s: %s, " % (prop, itm1[prop])
                # more hacky text stuff, remove the ', ' of the last element
                msg = msg[:-2] + ")"
                identical_items.append(msg)
                # no need to iterate over this item in the outer loop again
                items.remove(itm2)
          return(identical_items)

        # define which items are checked against which properties
        types = {'arcs': ['posx', 'posy', 'radius', 'start_angle', 'end_angle'], \
                 'circles': ['posx', 'posy', 'radius'], \
                 'polylines': ['points'], \
                 'rectangles': ['startx', 'starty', 'endx', 'endy'], \
                 'texts': ['posx', 'posy', 'direction', 'text']}

        dups = []
        # run the check for each type
        for typ, prop in types.items():
          dups.extend(check_identical(typ, self.component.draw[typ], prop))

        if len(dups) > 0:
            self.error("Graphic elements must not be duplicated.")
            for dup in dups:
               self.errorExtra(dup)

        return False

    def fix(self):
        pass
