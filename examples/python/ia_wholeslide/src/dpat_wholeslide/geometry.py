"""
Basic geometry classes

Point   -- point with (x,y) coordinates
Rect    -- two points, defining a rectangle
"""

import math
from typing import List, Optional, Sequence, Union, Set

class Point:
    """A point identified by (x,y) coordinates.

    supports: +, -, *, /, str, repr

    length        -- calculate length of vector to point from origin
    distance_to   -- calculate distance between two points
    as_tuple      -- construct tuple (x,y)
    clone         -- construct a duplicate
    integerize    -- convert x & y to integers
    floatize      -- convert x & y to floats
    move_to       -- reset x & y
    rotate        -- rotate around the origin
    rotate_about  -- rotate around another point
    """

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, p):
        """Point(x1+x2, y1+y2)"""
        return Point(self.x+p.x, self.y+p.y)

    def __sub__(self, p):
        """Point(x1-x2, y1-y2)"""
        return Point(self.x-p.x, self.y-p.y)

    def __mul__( self, scalar ):
        """Point(x1*x2, y1*y2)"""
        return Point(self.x*scalar, self.y*scalar)

    def __truediv__(self, scalar):
        """Point(x1/x2, y1/y2)"""
        return Point(self.x/scalar, self.y/scalar)

    def __str__(self):
        return "(%s, %s)" % (self.x, self.y)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.x, self.y)

    def length(self):
        return math.sqrt(self.x**2 + self.y**2)

    def distance_to(self, p):
        """Calculate the distance between two points."""
        return (self - p).length()

    def as_tuple(self):
        """(x, y)"""
        return (self.x, self.y)

    def clone(self):
        """Return a full copy of this point."""
        return Point(self.x, self.y)

    def map(self, fn):
        """
        transform x,y with fn

        fn(scalar) -> scalar
        """
        return Point(fn(self.x), fn(self.y))

    def integerize(self):
        """Convert co-ordinate values to integers."""
        return self.map(int)

    def floatize(self):
        """Convert co-ordinate values to floats."""
        return self.map(float)

    def rotate(self, rad):
        """Rotate counter-clockwise by rad radians.

        Positive y goes *up,* as in traditional mathematics.

        Interestingly, you can use this in y-down computer graphics, if
        you just remember that it turns clockwise, rather than
        counter-clockwise.

        The new position is returned as a new Point.
        """
        s, c = [f(rad) for f in (math.sin, math.cos)]
        x, y = (c*self.x - s*self.y, s*self.x + c*self.y)
        return Point(x,y)

    def rotate_about(self, p, theta):
        """Rotate counter-clockwise around a point, by theta degrees.

        Positive y goes *up,* as in traditional mathematics.

        The new position is returned as a new Point.
        """
        return ((self-p).rotate(theta))+p

    def clip(self, rect):
      """ ensure Point is max_x or max_y """
      x = max(min(self.x, rect.bottom_right.x), rect.top_left.x)
      y = max(min(self.y, rect.bottom_right.y), rect.top_left.y)
      return Point(x,y)

class Rect:

    """A rectangle identified by two points.

    The rectangle stores left, top, right, and bottom values.

    Coordinates are based on screen coordinates.

    origin                               top
       +-----> x increases                |
       |                           left  -+-  right
       v                                  |
    y increases                         bottom

    set_points  -- reset rectangle coordinates
    contains  -- is a point inside?
    overlaps  -- does a rectangle overlap?
    top_left  -- get top-left corner
    bottom_right  -- get bottom-right corner
    expanded_by  -- grow (or shrink)
    """

    def __init__(self, pt1, pt2):
        """Initialize a rectangle from two points."""
        if not isinstance(pt1, Point):
          pt1 = Point(pt1[0], pt1[1])
        if not isinstance(pt2, Point):
          pt2 = Point(pt2[0], pt2[1])
        self.set_points(pt1, pt2)

    @classmethod
    def from_bbox(cls, left, top, width, height):
        """ initialize from a bounding box """
        return cls((left, top), (left+width, top+height))

    @classmethod
    def from_bounds(cls, minx, miny, maxx, maxy):
        """ initialize from a bounds box (i.e, shapely)"""
        return cls((minx, miny), (maxx, maxy))

    @property
    def top_left(self):
        """Return the top-left corner as a Point."""
        return Point(self.left, self.top)

    @property
    def bottom_right(self):
        """Return the bottom-right corner as a Point."""
        return Point(self.right, self.bottom)

    @property
    def width(self):
      return self.right - self.left

    @property
    def height(self):
      return self.bottom - self.top

    def __add__(self, p):
        return Rect(self.top_left+p, self.bottom_right+p)

    def __sub__(self, p):
        return Rect(self.top_left-p, self.bottom_right-p)

    def __mul__( self, scalar):
        return Rect(self.top_left*scalar, self.bottom_right*scalar)

    def __truediv__(self, scalar):
        return Rect(self.top_left/scalar, self.bottom_right/scalar)

    def set_points(self, pt1, pt2):
        """Reset the rectangle coordinates."""
        (x1, y1) = pt1.as_tuple()
        (x2, y2) = pt2.as_tuple()
        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)

    def contains(self, pt):
        """Return true if a point is inside the rectangle."""
        x,y = pt.as_tuple()
        return (self.left <= x <= self.right and
                self.top <= y <= self.bottom)

    def overlaps(self, other):
        """Return true if a rectangle overlaps this rectangle."""
        return (self.right > other.left and self.left < other.right and
                self.top < other.bottom and self.bottom > other.top)

    def expanded_by(self, n):
        """Return a rectangle with extended borders.

        Create a new rectangle that is wider and taller than the
        immediate one. All sides are extended by "n" points.
        """
        p1 = Point(self.left-n, self.top-n)
        p2 = Point(self.right+n, self.bottom+n)
        return Rect(p1, p2)

    def map(self, fn):
        """ transform rect by appling fn to all scalar values """
        return Rect(self.top_left.map(fn), self.bottom_right.map(fn))

    def as_tuple(self):
        return (self.left, self.top, self.right, self.bottom)

    def as_bbox(self):
        return (self.left, self.top, self.width, self.height)

    def clone(self):
        """Return a full copy of this Rect."""
        return Rect(self.top_left, self.bottom_right)

    def __str__( self ):
        return "<Rect (%s,%s)-(%s,%s)>" % (self.left,self.top,
                                           self.right,self.bottom)
    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__,
                               Point(self.left, self.top),
                               Point(self.right, self.bottom))

# %%

if __name__ == "__main__":
  p = Point(5, 2)
  p.bounds

  b = Rect((10,10), (40,40))
  b.as_bbox()

  list(p.coords)
