import logging
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    logger.info(
        "JWT tokens issued",
        extra={
            "user_id": user.id,
            "email": getattr(user, "email", None),
            "is_active": user.is_active,
        },
    )

    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
