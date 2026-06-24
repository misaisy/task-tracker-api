from app.dependencies.auth import get_current_user as get_current_user
from app.dependencies.auth import require_admin as require_admin
from app.dependencies.auth import require_owner_or_admin as require_owner_or_admin
from app.dependencies.db import get_db as get_db
from app.dependencies.services import get_comment_service as get_comment_service
from app.dependencies.services import get_task_service as get_task_service
from app.dependencies.services import get_user_service as get_user_service
from app.dependencies.settings import get_settings as get_settings
