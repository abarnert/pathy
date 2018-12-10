import collections.abc

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

def _helprecurse(iterable, keypath, flatten):
    results = []
    join = results.extend if flatten else results.append
    for value in iterable:
        try:
            result = FrozenPather(value)[keypath]
            join(result)
        except LookupError:
            pass
    return results

class FrozenPather(collections.abc.Mapping):
    def __init__(self, collection):
        self.collection = collection
    def __getitem__(self, keypath):
        if isinstance(keypath, tuple):
            first, *rest = keypath
            flatten = any(isinstance(part, (slice, ellipsis)) for part in rest)
            if isinstance(first, slice):
                if (isinstance(self.collection, collections.abc.Mapping) and
                    first == slice(None)):
                    return _helprecurse(self.collection.values(), rest, flatten)
                else:
                    return _helprecurse(self.collection, rest, flatten)
            elif isinstance(first, ellipsis):
                pass # TODO!
            elif rest:
                return FrozenPather(self.collection[first])[rest]
            else:
                return self.collection[first]
                    
class Pather(FrozenPather, collections.abc.MutableMapping):
    pass

def test():
    c = {"things": [
         {"id": 0, "name": "cat", "properties": {"hat": True}},
         {"id": 1, "name": "thing1"},
         {"id": 2, "name": "thing2", "properties": {2: 1}},
         ], "timestamp": datetime(2018, 12, 9, 17, 22, 53, 978855)}
    assert Pather(c)["timestamp"] == datetime(2018, 12, 9, 17, 22, 53, 978855)
    assert Pather(c)["things", 1, "id"] = 1
    assert Pather(c)["things", 1:, "name"] == ["thing1", "thing2"]
    assert Pather(c)["things", :, "properties"] == [{"hat": True}, {2: 1}]
    assert Pather(c)[:, 0, "id"] == [0]
    assert Pather(c)[:, :, "properties"] == [{"hat": True}, {2: 1}]
    # assert Pather(c)[..., "properties"] == [{"hat": True}, {2: 1}]
