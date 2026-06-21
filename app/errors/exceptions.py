class TaskTrackerError(Exception):
    """Базовое исключение приложения."""
    pass


class TaskNotFoundError(TaskTrackerError):
    """Задача не найдена."""
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task with id={task_id} not found")


class TaskCreationError(TaskTrackerError):
    """Ошибка создания задачи."""
    pass


class UserNotFoundError(TaskTrackerError):
    """Пользователь не найден."""
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with id={user_id} not found")


class UserCreationError(TaskTrackerError):
    """Ошибка создания пользователя."""
    pass


class CommentNotFoundError(TaskTrackerError):
    """Комментарий не найден."""
    def __init__(self, comment_id: int):
        self.comment_id = comment_id
        super().__init__(f"Comment with id={comment_id} not found")


class CommentCreationError(TaskTrackerError):
    """Ошибка создания комментария."""
    pass


class ConflictError(TaskTrackerError):
    """Конфликт состояния."""
    pass
