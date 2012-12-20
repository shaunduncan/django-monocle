"""
Simple collection of signals that can be useful for metric recording
"""
from django.dispatch import Signal


# Cache Signals
cache_miss = Signal(providing_args=['key'])
cache_hit = Signal(providing_args=['key'])


# Consumer Signals
pre_consume = Signal()
post_consume = Signal()
