"""
The recordstore sub-package provides an abstraction layer around storage of
simulation/analysis records, providing a common interface to different storage
methods (simple serialisation, relational database, etc.)

Sub-packages/modules
--------------------

shelve_store - provides the ShelveRecordStore class
django_store - provides the DjangoRecordStore class (if Django is installed)
http_store   - provides the HttpRecordStore class


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

from . import serialization
from .base import RecordStore
from .shelve_store import ShelveRecordStore
try:
    from .django_store import DjangoRecordStore
    have_django = True
except ImportError:
    have_django = False
try:
    import httplib2
    from .http_store import HttpRecordStore
except ImportError:
    pass

from ..core import registry


DefaultRecordStore = have_django and DjangoRecordStore or ShelveRecordStore


def get_record_store(uri):
    """
    Return the :class:`RecordStore` object found at the given URI (which may be
    a URL or filesystem path).
    """
    # print registry.components[RecordStore].values()
    for record_store_class in registry.components[RecordStore].values():
        if record_store_class.accepts_uri(uri):
            store = record_store_class(uri)
            print str(store)
            return store
    return DefaultRecordStore(uri)
