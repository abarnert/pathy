# pathy
A python library for accessing deep collection hierarchies simply

## Introduction

Pather wraps a (usually nested) sequence or mapping, extending the
usual interface to allow simpler deep searches, including the
equivalent of wildcard matches (a la XPath, KVC, dpath, etc.).

Novices generally expect this to be easy, but it isn't. For example,
you get a JSON response back from the YouTube API, and want to know
how to print the title of each movie that has one... and the answer is
for loop with another for loop inside it. Or the answer is to learn a
somewhat complicated XPath-like syntax that doesn't feel like Python
indexing. Or, now, the answer is just the sequence of keys and indices
the way you naively hoped you could do it.

There are plenty of libraries that can help, generally providing a
powerful syntax based on something like XPath or KVC. Sometimes you
need that power (e.g., "find all `things` that have `properties` two
levels down where the `a` property starts with `"spam"`" is the kind
of thing you want to write XPath for), or you need to search giant
JSON documents without parsing them into Python structures in memory,
etc.

But sometimes you really just a simple nested search, and there's no
reason you can't just express that in Python syntax. Python already
has a powerful syntax for multidimensional indexing, designed
for NumPy but just as usable for our purposes; the only thing missing
is a library to apply that syntax to JSON-style nested dict-and-list
structures. Hence this library.

## Example

Let's take a simple structure you might get back from a JSON request.

     >>> c = {"things": [
              {"id": 0, "name": "cat", "properties": {"hat": True}},
              {"id": 1, "name": "thing1"},
              {"id": 2, "name": "thing2", "properties": {2: 1}},
             ], "timestamp": datetime(2018, 12, 9, 17, 22, 53, 978855)}

If you just want to get the `timestamp`, that's already so easy that
`Pather` can't make it any easier:

     >>> c["timestamp"]
     datetime(2018, 12, 9, 17, 22, 53, 978855)
     >>> Pather(c)["timestamp"]
     datetime(2018, 12, 9, 17, 22, 53, 978855)

And if you just want to get the id of thing #1, that's also already
dead simple:

     >>> c["things"][1]["id"]
	 1
     >>> Pather(c)["things", 1, "id"]
     1

But what if you want the names of every thing?

    >>> [thing["name"] for thing in c["things"]]
	["cat", "thing1", "thing2"]
	>>> Pather(c)["things", :, "name"]
	["cat", "thing1", "thing2"]

Or the names of a subset of the things?

    >>> [thing["name"] for thing in c["things"][1:]]
	["thing1", "thing2"]
	>>> Pather(c)["things", 1:, "name"]
	["thing1", "thing2"]

Or the properties of every thing that has properties?

     >>> [thing["properties"] for thing in c["things"]
     ...  if haskey(thing, "properties")]
     [{"hat": True}, {2: 1}]
     >>> Pather(c)["things", :, "properties"]
     [{"hat": True}, {2: 1}]

You can do the same slice-as-wildcard trick with dictionaries
(although obviously only with the bare `:` full slice):

     >>> Pather(c)[:, 0, "id"]
     [0]

Also notice that this didn't err out because one of the elements
of `c` isn't subscriptable; the simplest equivalent comprehension
would look something like:

     >>> [element[0]["id"] for element in c.values()
	 ...  if isinstance(element, (Sequence, Mapping))]
     [0]

Even better, you can provide multiple slices in the path, which
acts like a comprehension with nested `for` clauses, but readable:

     >>> [subelement["id"]
     ...  for element in c if isinstance(element, Sequence)
     ...  for subelement in element.values()
     ...  if haskey(subelement, "id")]
     [{"hat": True}, {2: 1}]
     >>> Pather(c)[:, :, "properties"]
     [{"hat": True}, {2: 1}]

Or you can use an ellipsis (`...`) to represent 0 or more bare slices,
similar to the "**" in recursive glob, XPath, etc. (and, of course, to
the way NumPy uses `...`):

    >>> Pather(c)[..., "properties"]
    [{"hat": True}, {2: 1}]

## Details

To use the library, first you construct a `Pather` wrapping a
collection, then you index the `Pather`.

Construction is very cheap; the object is really just there to allow
indexing syntax. So, you can do this on the fly, as in the examples
above--or, if you plan to do lots of path searches on the same
collection, you can store a `Pather` and reuse it. Whichever is more
readable in each case, do that.

### Simple keys

When given a key (or index--the `Pather` doesn't care; it's up to the
wrapped collection) that isn't a tuple, slice, or ellipsis, the
`Pather` just passes the key on to its collection as-is.

### Slices

The bare slice `:`, if the collection is a `Mapping`, is handled by
calling `values()` on the collection. (This is not very useful outside
of a tuple.)

Otherwise, any slice is passed through to the collection as-is.

### Ellipses

An ellipsis on its own is effectively the same as a bare slice. The
only difference is how they work inside a tuple. (There's not much
reason to use one except in a tuple.)

### Tuples

An empty tuple is an error.

A single-element tuple is treated the same as that single
element. (Note: This may change in future versions.)

A tuple of two or more elements is handled recursively: splitting it
into `first, *rest`, applying `[first]`.

If `first` is a bare key, `[*rest]` is just applied to `self[first]`.

If it's a slice, `[*rest]` is applied to each element of
`self[first]`, flattening all of the results together into one list,
and skipping those sub-results that raise an error because some
elements don't have the rest of the key, or aren't
subscriptable. (Note that this doesn't mean you can never get a
`LookupError` from `Pather`--e.g., if you put a missing key before a
slice, you'll get a `KeyError` before reaching the slice.)

If it's an ellipsis, `[*rest]` and `[..., *rest]` are both applied to
each element of `self[:]`, with the same flattening and
skipping. Except in the case where `self[:]` is a string-like type, in
which case it isn't recursed into. (Otherwise, you'd get infinite
recursion on each character of the string.) (Note: This last rule may
change in future versions. Would people expect `[..., 0]` to return the
first character of every leaf string, or the entire first string in
every leaf list of strings? I'm not sure without a real-life use case.)

## TODO

### Docstrings, unit tests

Nuff said.

### Slicing and ellipsing

First, we need a lot more tests to make sure that flattening and
ellipsis-recursing both work as intended.

Should `Pather(c)[:]` really return `c.values()` as a `dict_values`,
rather than returning a list like any more complicated slice
expression. (And, similarly, if `c` is a tuple, range, etc., it
returns whatever that type returns.)

What should an ellipsis with nothing after it do? Right now it's the
same as a bare slice. A flattened list of all leaves seems to make
more sense at first, but try it with any real-life example and it
seems wrong. So maybe the bare slice is fine.

### Single-element tuples

Should a `p[2,]` really be the same as `p[2]`, or should it be the
same as `p[(2,),]`? The former is consistent with NumPy. It's also
slightly simpler to implement the recursion that way. It does slightly
get in the way of pathing dictionaries with actual tuple keys, but how
often does that come up?

What about an empty tuple? Should `p[()]` be an error? Or maybe it
should just return `p` (the closest analogy to NumPy, I think), or
`p[:]`, or `p[...]` (assuming that's different in the first place).

### Containment

It seems like there should be some useful way to use the `in` operator
directly on a `Pather`, but I'm not sure what it would be.

### Mutation

There's no reason we can't implement `__setitem__` and `__delitem__`;
the question is what `__setitem__` should do.

One obvious choice is:

    >>> Pather(c)["things", 1:, "name"] = ["Thing1", "Thing2"]
	
... working like list slice assignment, similar to:

    things = c["thing"][1:]
	assert len(things) = 2
	things[0]["name"] = "Thing1"
	things[1]["name"] = "Thing2"
	
(Obviously, unlike the case with lists, it has to be like complex
slice assigment--that is, you have to assign exactly the right number
of values--even if the slice is simpler. But that's not much of a
problem.)
	
But often what you really want is more like NumPy-style
broadcasting--or at least the simplest possible version of it, so you
can assign a single value to all of the matching positions:

    >>> Pather(c)["things", 1:, "properties", "hat"] = False

Either way, what does this do if some of the things don't have
`properties`?  Create an empty dict on the fly and store it as
`"properties"` and then set its `"hat"`? Skip that thing? Raise an
error? Creating the dicts on the fly sounds good at first, until you
consider what happens with int key components (should a list be
extended on the fly?), and, worse, with ellipses (you wouldn't want to
create a `properties` dict at every level in the tree, right?).

Also, if both options are reasonable, which one do you get when you
pass a string as a value? (The workaround is a lot more obvious if
strings are treated as single values but you want one to be treated as
an iterable, than vice versa: just assign `iter("stuff")`. But it's
still not ideal, especially for generic code where `"stuff"` might be
a variable whose type you don't know because you got it as a parameter
rather than a hardcoded string.)

Look at `dpath`, etc. to see what they do for mutation.

