"""Role to permission map. This constant is the source of truth and is copied into the database at startup."""

USER_PERMISSIONS = {
    "post:create",
    "post:update_own",
    "post:delete_own",
    "comment:create",
    "comment:delete_own",
    "like:toggle",
    "export:own",
    "blog:update_own",
    "upload:create",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": set(USER_PERMISSIONS),
    "moderator": set(USER_PERMISSIONS) | {"comment:moderate", "post:moderate"},
    "admin": set(USER_PERMISSIONS)
    | {
        "comment:moderate",
        "post:moderate",
        "audit:read",
        "user:read",
        "query:explain",
        "permission:read",
        "webhook:read",
    },
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
