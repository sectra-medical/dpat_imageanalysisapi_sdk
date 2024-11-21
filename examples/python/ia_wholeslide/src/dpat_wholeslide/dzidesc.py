"""
dzidesc -- module for common computations done on DeepZoomImage images


DziDescription              <--- represents an entire zoomable image
  |
  |                           there are fixed steps of zooms that can be retrieved, named levels
  |
  |
  +---- DziLevel              <-- the baselevel is the largest and decreasing numbers mean smaller images.
        |
        |
        |
        +--- DziTile          <-- each level consists of columns * rows tiles that are each maximum
                                  (patch_size, patch_size), but might be smaller at the edges of the image.

Example Usage:

    d = DziDescription(87647, 76723, 240)
    for level in d.levels():
        print(level)

Outputs:
    <DziDescription width:87647 height:76723 tile_size:240 overlap:0 baselevel:17 />

    <DziLevel level:2 cols(x):1 rows(y):1 width,height:(2, 2) />
    <DziLevel level:3 cols(x):1 rows(y):1 width,height:(5, 4) />
    <DziLevel level:4 cols(x):1 rows(y):1 width,height:(10, 9) />
    <DziLevel level:5 cols(x):1 rows(y):1 width,height:(21, 18) />
    <DziLevel level:6 cols(x):1 rows(y):1 width,height:(42, 37) />
    <DziLevel level:7 cols(x):1 rows(y):1 width,height:(85, 74) />
    <DziLevel level:8 cols(x):1 rows(y):1 width,height:(171, 149) />
    <DziLevel level:9 cols(x):2 rows(y):2 width,height:(342, 299) />
    <DziLevel level:10 cols(x):3 rows(y):3 width,height:(684, 599) />
    <DziLevel level:11 cols(x):6 rows(y):5 width,height:(1369, 1198) />
    <DziLevel level:12 cols(x):12 rows(y):10 width,height:(2738, 2397) />
    <DziLevel level:13 cols(x):23 rows(y):20 width,height:(5477, 4795) />
    <DziLevel level:14 cols(x):46 rows(y):40 width,height:(10955, 9590) />
    <DziLevel level:15 cols(x):92 rows(y):80 width,height:(21911, 19180) />
    <DziLevel level:16 cols(x):183 rows(y):160 width,height:(43823, 38361) />
    <DziLevel level:17 cols(x):366 rows(y):320 width,height:(87647, 76723) />
"""

import collections
import math
from typing import List, Generator, Tuple

from dpat_wholeslide.geometry import Point, Rect

def dzilevel_at_size(width, height) -> int:
  return int(math.ceil(math.log2(max(width, height))))

def dzilevel_scale_factor_inv(level, max_level) -> float:
  """ inverse of dzilevel_scale_factor """
  # return math.pow(0.5, max_level - level)
  return 1.0 / dzilevel_scale_factor(level, max_level)

def dzilevel_scale_factor(level, max_level) -> float:
  # return 1 << (max_level - level)
  return 2.0**(max_level - level)

# DziTileToImageDescr :: describes how and where a tile should be written when extracting an area
#                        first crop to crop, then place the resulting img into larger data area as designated by place_point
DziTileToImageDescr = collections.namedtuple('DziTileToImageDescr', ['tile', 'crop', 'place_point'])

class DziDescription:
  """
  Utility class for DeepZoomImage calculations
  """
  def __init__(self, base_width: int, base_height: int, tile_size: int,
               tile_overlap: int = 0, magnification: float | None = None,
               resolution: float | None = None):
    self.width = base_width
    self.height = base_height
    self.tile_size = tile_size
    self.tile_overlap = tile_overlap
    self.magnification = magnification
    self.resolution = resolution
    self.format = 'jpeg'

  def baselevel(self) -> int:
    return dzilevel_at_size(self.width, self.height)

  def maxlevel(self) -> int:
    return self.baselevel()

  def level(self, level: int) -> 'DziLevel':
    return DziLevel(self, level)

  def levels(self) -> List['DziLevel']:
    return [self.level(x) for x in range(2, self.maxlevel() + 1)]

  def level_approx_width(self, width: int):
    # first level with .width() >= width
    if width >= self.width:
      return self.level(self.baselevel())
    return next(filter(lambda x: x.width() >= width, self.levels()))

  def level_at_mag(self, magn: float):
    """get DziLevel for given magnification"""
    if not self.magnification:
      raise Exception('magnification not set on this instance, method not available.')
    if magn > self.magnification:
      raise ValueError("requested magnification {} is larger than slide's max {}".format(magn, self.magnification))
    mag_diff = self.magnification / magn
    level_diff = int(round(math.log2(mag_diff)))
    lvl = self.baselevel() - level_diff
    return self.level(lvl)

  def level_at_mpp(self, microns_per_pixel:float, always_smaller=False):
    """
    get lvl closest to requested resolution

    if always_smaller is True, will always return the higher-resolution level (lower mpp)
    """
    if not self.resolution:
      raise Exception('resolution not set on this instance, method not available.')
    slideres = self.resolution
    res_diff = microns_per_pixel / slideres
    level_diff = int(round(math.log2(res_diff)))
    if always_smaller:
      level_diff = math.floor(math.log2(res_diff))
    if res_diff < 1.0:
      level_diff = 0 # no such level available
    lvl = self.baselevel() - level_diff
    lvl_dzi = self.level(lvl)
    mpp_at_level = lvl_dzi.resolution()
    return (lvl_dzi, mpp_at_level, mpp_at_level / microns_per_pixel)

  def __repr__(self):
    return "<DziDescription width:{} height:{} tile_size:{} overlap:{} baselevel:{} />".format(
      self.width, self.height, self.tile_size, self.tile_overlap, self.baselevel())

class DziLevel(object):
  """ represents a single Dzi Level within a DZI """
  def __init__(self, parent: DziDescription, level: int):
    self.parent = parent
    self.level = level
    self.n_cols = self.cols()
    self.n_rows = self.rows()

  def level_scale(self) -> float:
    return dzilevel_scale_factor_inv(self.level, self.parent.baselevel())

  def level_scale_inv(self) -> float:
    # yes, naming is confusing. here for backward compat.
    return dzilevel_scale_factor(self.level, self.parent.baselevel())

  def cols(self) -> int:
    return int(math.ceil((self.width()*1.0) / self.parent.tile_size))

  def rows(self) -> int:
    return int(math.ceil((self.height()*1.0) / self.parent.tile_size))

  def width(self):
    return int(max(1, math.floor(self.parent.width * self.level_scale())))

  def height(self):
    return int(max(1, math.floor(self.parent.height * self.level_scale())))

  def size(self) -> Tuple[int,int]:
    return (self.width(), self.height())

  def n_tiles(self) -> int:
    """ total number of tiles in level """
    return self.cols() * self.rows()

  def magnification(self) -> float | None:
    """ get the magnification of this level, i.e 20.0 for 20X etc. """
    if self.parent.magnification is None:
      return None
    return self.parent.magnification * self.level_scale()

  def resolution(self) -> float | None:
    """ get the resolution of this level in microns per pixel """
    if self.parent.resolution is None:
      return None
    return self.parent.resolution * self.level_scale_inv()

  def tile(self, col, row):
    return DziTile(self, col, row)

  def tiles(self) -> Generator['DziTile', None, None]:
    # images are usually written in stripes, so by col. is faster
    return self.tiles_bycol()

  def tiles_byrow(self) -> Generator['DziTile', None, None]:
    for c in range(0, self.cols()):
      for r in range(0, self.rows()):
        yield self.tile(c, r)

  def tiles_bycol(self) -> Generator['DziTile', None, None]:
    for r in range(0, self.rows()):
      for c in range(0, self.cols()):
        yield self.tile(c, r)

  def tiles_within(self, x, y, width, height) -> Generator['DziTile', None, None]:
    """
    list tiles that intersect with area of given bounding box

    x,y = top left position of bbox, absolute pixels
    """
    col_start = math.floor(x / self.parent.tile_size)
    col_end = math.floor((x+width) / self.parent.tile_size)
    row_start = math.floor(y / self.parent.tile_size)
    row_end = math.floor((y+height) / self.parent.tile_size)
    for r in range(max(row_start, 0), min(row_end+1, self.rows())):
      for c in range(max(col_start, 0), min(col_end+1, self.cols())):
        yield self.tile(c, r)

  def tiles_for_area(self, x, y, width, height) -> Generator['DziTileToImageDescr', None, None]:
    """
    get a DziTileToImageDescr that describes tiles to fetch and how to crop them to get requested area

    x,y = top left position of bbox, absolute pixels
    """
    tiles = self.tiles_within(x,y,width,height)
    for tile in tiles:
      place_origin = Point(tile.col * self.parent.tile_size, tile.row * self.parent.tile_size)
      place_dest = place_origin - Point(x,y)
      crop = tile.crop.clone()
      if place_dest.x < 0:
        crop.left += abs(place_dest.x)
        place_dest.x = 0
      if place_dest.y < 0:
        crop.top += abs(place_dest.y)
        place_dest.y = 0
      yield DziTileToImageDescr(tile, crop, place_dest)

  def tiles_for_level(self):
    return self.tiles_for_area(0,0, self.width(), self.height())

  def __repr__(self):
    return "<DziLevel level:{} cols(x):{} rows(y):{} width,height:{} />".format(
      self.level, self.cols(), self.rows(), self.size())

class DziTile:
  """ a single tile within a parent DziLevel """

  def __init__(self, level: DziLevel, col: int, row: int):
    self.parent = level
    self.level = level.level
    self.col = col
    self.row = row
    if col >= self.parent.n_cols:
      raise Exception(f"column {col} out of bounds for level {level}")
    if row >= self.parent.n_rows:
      raise Exception(f"row {row} out of bounds for level {level}")
    overlap = self.parent.parent.tile_overlap
    t,l,r,b = (overlap,overlap,overlap,overlap) # (l,t,r,b)
    if overlap > 0:
      if self.col == 0: l = 0
      if self.col == self.parent.n_cols-1: r = 0
      if self.row == 0: t = 0
      if self.row == self.parent.n_rows-1: b = 0
    self.overlap = (t,l,r,b)
    tile_size = self.parent.parent.tile_size
    self.width = tile_size+l+r
    self.height = tile_size+t+b
    if self.col == self.parent.n_cols-1:
      # final column
      remainder = self.parent.width() % tile_size
      if remainder == 0: remainder = tile_size
      self.width = remainder+l+r
    if self.row == self.parent.n_rows-1:
      # final row
      remainder = self.parent.height() % tile_size
      if remainder == 0: remainder = tile_size
      self.height = remainder+t+b
    bottom_left = Point(tile_size+l, tile_size+t).clip(Rect((0,0), (self.width, self.height)))
    self.top_left = Point(self.col * tile_size, self.row * tile_size) # placement if overlap is ignored
    self.crop = Rect((l,t), bottom_left)

  def __repr__(self):
    return "<DziTile level:{} col:{} row:{} />".format(
      self.level, self.col, self.row)

  def to_path(self):
    return "{0}/{1}_{2}".format(self.level, self.col, self.row)

if __name__ == "__main__":
  # Example Usage:

  # list levels and tiles
  d = DziDescription(87647, 76723, 240)
  #d.tile_overlap = 0
  print(d)

  # %%
  print("  -- listing levels:")
  for level in d.levels():
    print(level)
    for tile in level.tiles():
      pass
      #print(tile)

  # %% find suitable level
  print("\nfinding approximate width=2000 level:")
  l = d.level_approx_width(2000)
  print(l)

  # %% get tiles in bbox
  for tile in l.tiles_within(512, 418, 1212, 400):
    print(tile)

  # %% get tile dest descriptor
  l = d.level_approx_width(2000)
  for tile in l.tiles_for_area(512, 2150, 520, 400):
    print(tile)
