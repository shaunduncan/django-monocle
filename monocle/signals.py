"""
Various types of signals that may be useful for various recording. The following
signals are exposed

* ``cache_miss`` - sent when a request for cached resource returns None
* ``cache_hit`` - sent when a request for cached resource returns not None
* ``pre_consume`` - sent on request to consume content, prior to enrichment
* ``post_consume`` - sent before returning enriched content from consumption
"""
from django.dispatch import Signal


# Cache Signals
cache_miss = Signal(providing_args=['key'])
cache_hit = Signal(providing_args=['key'])


# Consumer Signals
pre_consume = Signal()
post_consume = Signal()
