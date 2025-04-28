from .smol_ai import SmolAISpider
from .techcrunch_ai import TechCrunchAISpider
from .futurepedia import FuturepediaSpider
# from .huggingface import HuggingFaceSpider
# TODO: add more spiders (decoder, wired, etc.) here

SPIDERS = [SmolAISpider, TechCrunchAISpider, FuturepediaSpider] 