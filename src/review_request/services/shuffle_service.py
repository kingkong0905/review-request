import random
from typing import List


class ShuffleService:
    """Service for shuffling icons for review messages."""

    ICONS = [
        ":pepe_love:",
        ":thankabunch:",
        ":pepelove:",
        ":awthanks:",
        ":pepe-evil:",
        ":pepe-happy:",
        ":lovee:",
        ":pepepray:",
        ":pepe-businessman:",
        ":cat-nodding:",
        ":vayvay:",
        ":prayge:",
        ":yaya:",
        ":thankyou_:",
        ":frog-flower:",
        ":panda-super-saiyan:",
        ":pepebongo:",
        ":amaze:",
        ":thank_u:",
        ":thanks-bowing-bugcat:",
        ":thankyouuuu:",
        ":camon:",
        ":camon2:",
    ]

    @staticmethod
    def shuffle_icons() -> List[str]:
        shuffled_icons = ShuffleService.ICONS.copy()
        random.shuffle(shuffled_icons)
        return shuffled_icons
