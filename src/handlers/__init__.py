from .start import register_start
from .navigation import register_navigation
from .admin_panel import register_admin_panel
from .admin_add import register_admin_add
from .admin_edit import register_admin_edit
from .admin_delete import register_admin_delete
from .admin_clear import register_admin_clear
from .admin_cancel import register_admin_cancel

def register_handlers(dp, bot):
    # Порядок регистрации важен - сначала специфичные, потом общие
    register_start(dp)
    register_navigation(dp)
    register_admin_panel(dp, bot)
    register_admin_add(dp)
    register_admin_edit(dp)
    register_admin_delete(dp)
    register_admin_clear(dp, bot)
    register_admin_cancel(dp)  # Должен быть последним для перехвата всех admin_cancel

    
