"""
Utilities module
"""

# Импортируем напрямую из database
from ..database import is_admin, is_super_admin

# Импортируем все константы из модулей
from .buttons import *
from .messages import *
from .callbacks import *
from .constants import *

# Для обратной совместимости импортируем из старого texts.py
from .texts import *
