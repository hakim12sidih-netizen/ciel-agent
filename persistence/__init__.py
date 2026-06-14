from __future__ import annotations

from ciel.persistence.core import (
    save_state,
    load_state,
    clear_state,
    save_chat_message,
    load_chat_history,
    create_session,
    get_session,
    list_sessions,
    save_credential,
    get_credential,
    list_credentials,
    delete_credential,
    register_plugin,
    get_plugin,
    list_plugins,
    is_plugin_enabled,
    install_autostart,
    remove_autostart,
    is_autostart_enabled,
    create_boot_script,
    register_shutdown_handler,
    get_status,
    DB_PATH,
)

__all__ = [
    "save_state", "load_state", "clear_state",
    "save_chat_message", "load_chat_history",
    "create_session", "get_session", "list_sessions",
    "save_credential", "get_credential", "list_credentials", "delete_credential",
    "register_plugin", "get_plugin", "list_plugins", "is_plugin_enabled",
    "install_autostart", "remove_autostart", "is_autostart_enabled",
    "create_boot_script", "register_shutdown_handler", "get_status",
    "DB_PATH",
]
