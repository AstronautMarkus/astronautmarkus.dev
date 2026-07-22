import random as _random

from flask import url_for

# Order of the webring — every junk page except the ring directory itself (/webring).
RING = [
    'junk.best_viewed',
    'junk.geocities',
    'junk.y2k',
    'junk.blink',
    'junk.marquee',
    'junk.dialup',
    'junk.under_construction',
    'junk.guestbook',
    'junk.links',
    'junk.counter',
]


def ring_nav(current_endpoint: str) -> dict:
    """Prev/next/random/list links for the webring widget shown on every junk page."""
    idx = RING.index(current_endpoint)
    prev_ep = RING[idx - 1]
    next_ep = RING[(idx + 1) % len(RING)]
    random_ep = _random.choice([e for e in RING if e != current_endpoint])
    return {
        'ring_prev': url_for(prev_ep),
        'ring_next': url_for(next_ep),
        'ring_random': url_for(random_ep),
        'ring_list': url_for('junk.webring'),
    }
