from .action1 import Action1
from .card_dist_high import CardDistHigh
from .card_dist_low import CardDistLow
from .card1 import Card1
from .environment1 import Environment1
from .environment2 import Environment2

NOVELTY_LIST = [cls for cls in locals().values() if isinstance(cls, type)]
NOVELTY_LIST.append('RANDOM')