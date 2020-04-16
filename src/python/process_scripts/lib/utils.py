from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import json

def ensure_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_meta(filename, meta):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(meta, f)


def read_meta(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_dialog_count(data):
    """
    data - result of json.load on output of script_parser.py
    """
    result = {}
    for line in data['dialog']:
        char = line['character']
        result[char] = result.setdefault(char, 0) + 1
    return result


# Code copied from https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/util/lazy_loader.py
"""A LazyLoader class."""


import importlib
import types


class LazyLoader(types.ModuleType):
  """Lazily import a module, mainly to avoid pulling in large dependencies.

  `contrib`, and `ffmpeg` are examples of modules that are large and not always
  needed, and this allows them to only be loaded when they are used.
  """

  # The lint error here is incorrect.
  def __init__(self, local_name, parent_module_globals, name):  # pylint: disable=super-on-old-class
    self._local_name = local_name
    self._parent_module_globals = parent_module_globals

    super(LazyLoader, self).__init__(name)

  def _load(self):
    # Import the target module and insert it into the parent's namespace
    module = importlib.import_module(self.__name__)
    self._parent_module_globals[self._local_name] = module

    # Update this object's dict so that if someone keeps a reference to the
    #   LazyLoader, lookups are efficient (__getattr__ is only called on lookups
    #   that fail).
    self.__dict__.update(module.__dict__)

    return module

  def __getattr__(self, item):
    module = self._load()
    return getattr(module, item)

  def __dir__(self):
    module = self._load()
    return dir(module)
