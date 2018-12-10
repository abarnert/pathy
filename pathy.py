import collections.abc

# TODO:
# * What should c[...] return? Currently it's just c[:] or c.values().
# * Mutation
# * Should __contains__ do anything special?

# Pather wraps a (usually nested) sequence or mapping, extending
# the usual interface to allow simpler deep searches, including the
# equivalent of wildcard matches (a la XPath, KVC, dpath, etc.).
#
# A Pather can be indexed with a single key or index, which is just
# passed through:
#
#     >>> c = {"things": [
#              {"id": 0, "name": "cat", "properties": {"hat": True}},
#              {"id": 1, "name": "thing1"},
#              {"id": 2, "name": "thing2", "properties": {2: 1}},
#             ], "timestamp": datetime(2018, 12, 9, 17, 22, 53, 978855)}
#
#     >>> Pather(c)["timestamp"]
#     datetime(2018, 12, 9, 17, 22, 53, 978855)
#
# You can also use a tuple, which is applied recursively:
#
#     >>> Pather(c)["things", 1, "id"]
#     1
#
# This is equivalent to:
#     >>> c["things"][1]["id"]
#
# Any element of the tuple can be a slice, which allows you to do the
# equivalent of a comprehension over that slice, without having to write
# the comprehension:
#
#     >>> Pather(c)["things", 1:, "name"]
#     ["thing1", "thing2"]
#     >>> [thing["name"] for thing in c["things"][1:]]
#     ["thing1", "thing2"]
#
# Also, if one or more of the collections along the path is empty, you
# won't get a KeyError, which would be clumsy to do in a comprehension:
#
#     >>> Pather(c)["things", :, "properties"]
#     [{"hat": True}, {2: 1}]
#     >>> [thing["properties"] for thing in c["things"]
#     ...  if haskey(thing, "properties")]
#     [{"hat": True}, {2: 1}]
#
# You can even slice a dictionary (although only with the bare : full slice),
# which works the same way:
#
#     >>> Pather(c)[:, 0, "id"]
#     [0]
#     >>> [element[0]["id"] for element in c if isinstance(element, Sequence)]
#     [0]
#
# Providing multiple slices gives a flattened sequence of the results, not
# a nested one, which you really wouldn't want to write as a comprehension:
#
#     >>> Pather(c)[:, :, "properties"]
#     [{"hat": True}, {2: 1}]
#     >>> [subelement["id"]
#     ...  for element in c if isinstance(element, Sequence)
#     ...  for subelement in element.values()
#     ...  if haskey(subelement, "id")]
#     [{"hat": True}, {2: 1}]
#
# Finally, you can use an ellipsis to recurse down zero or more levels,
# similar to the "**" in recursive glob, XPath, etc.:
#
#    >>> Pather(c)[..., "properties"]
#     [{"hat": True}, {2: 1}]
#
# There are things that can be expressed in, e.g., XPath that can't be done
# with a simple recursive pathing library, like finding all things that
# have properties. If you need any of those things, you're probably better
# off using an XPath-like library than trying to bang it into shape with
# a comprehension over an ellipsis pather lookup.

def _helprecurse(iterable, keypath, flatten):
    results = []
    join = results.extend if flatten else results.append
    for value in iterable:
        try:
            result = FrozenPather(value)[keypath]
            join(result)
        except (LookupError, TypeError):
            pass
    return results

def _isnonstringsequence(x):
    return (isinstance(x, collections.abc.Sequence) and not 
            isinstance(x, (str, collections.abc.ByteString)))

class FrozenPather(collections.abc.Mapping):
    def __init__(self, collection):
        self.collection = collection
    def __iter__(self):
        return iter(self.collection)
    def __len__(self):
        return len(self.collection)
    def __getitem__(self, keypath):
        if isinstance(keypath, tuple):
            first, *rest = keypath
            rest = tuple(rest)
        else:
            first, rest = keypath, ()
        flatten = any(isinstance(part, (slice, type(Ellipsis)))
                      for part in rest)
        if isinstance(first, slice):
            if (isinstance(self.collection, collections.abc.Mapping) and
                first == slice(None)):
                subcollection = self.collection.values()
            else:
                subcollection = self.collection[first]
            if not rest:
                return subcollection
            else:
                return _helprecurse(subcollection, rest, flatten)
        elif first is Ellipsis:
            if isinstance(self.collection, collections.abc.Mapping):
                subcollection = self.collection.values()
            elif _isnonstringsequence(self.collection):
                subcollection = self.collection
            else:
                return self.collection if not rest else []
            if not rest:
                return subcollection
            elif not subcollection:
                return []
            else:
                return (_helprecurse(subcollection, (slice(None), *rest), True) +
                        _helprecurse(subcollection, rest, True))
        else:
            if not rest:
                return self.collection[first]
            else:
                return FrozenPather(self.collection[first])[rest]
                    
class Pather(FrozenPather):#, collections.abc.MutableMapping):
    pass

def test():
    from datetime import datetime
    c = {"things": [
         {"id": 0, "name": "cat", "properties": {"hat": True}},
         {"id": 1, "name": "thing1"},
         {"id": 2, "name": "thing2", "properties": {2: 1}},
         ], "timestamp": datetime(2018, 12, 9, 17, 22, 53, 978855)}
    assert Pather(c)["timestamp"] == datetime(2018, 12, 9, 17, 22, 53, 978855)
    assert Pather(c)["things", 1, "id"] == 1
    assert Pather(c)["things", 1:, "name"] == ["thing1", "thing2"]
    assert Pather(c)["things", :, "properties"] == [{"hat": True}, {2: 1}]
    assert Pather(c)[:, 0, "id"] == [0]
    assert Pather(c)[:, :, "properties"] == [{"hat": True}, {2: 1}]
    assert Pather(c)[..., "properties"] == [{"hat": True}, {2: 1}]
