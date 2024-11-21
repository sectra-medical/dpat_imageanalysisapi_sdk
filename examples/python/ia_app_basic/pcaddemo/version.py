"""
version info
"""

__version__ = "0.1.0"

# this is the minimum version we require, we do not support
# servers that run earlier versions.
#
# Bump this number when you add expectations on API datastructures or endpoints only
# present from version X.Y onward.
#
# 1.5 here corresponds to DPAT 3.0 and we make use of /slides/<id>/info endpoint
#     only available from this version and onward
SECTRA_IA_API_MIN_VERSION = "1.5"

# this is the highest version we've explicitly tested with
# higher-capable servers should fallback to this api version to ensure compatability
#
# Bump this to the highest number you've tested with.
# If you are lazy, set:
# SECTRA_IA_API_MAX_VERSION = SECTRA_IA_API_MIN_VERSION
# (you might lose some enhancements that you do not rely on anyway)
SECTRA_IA_API_MAX_VERSION = "1.8"
