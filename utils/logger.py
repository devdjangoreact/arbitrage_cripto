import os
from sys import stderr

from loguru import logger as loguru_logger


class MultiLogger:
    def __init__(self, log_dir="logs"):
        self.loggers = {}
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Налаштування дефолтного логера (log.log)
        self._setup_default_logger()

    def _setup_default_logger(self):
        # Видаляємо всі попередні обробники
        loguru_logger.remove()

        # Додаємо обробник для stderr (консоль)
        loguru_logger.add(
            stderr,
            format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | [<cyan>{file.name}:{line}</cyan>] - <white>{message}</white>",
        )

        # Додаємо обробник для дефолтного файлу (log.log)
        loguru_logger.add(
            os.path.join(self.log_dir, "log.log"),
            format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | [<cyan>{file.name}:{line}</cyan>] - <white>{message}</white>",
            # Фільтр: записуємо лише повідомлення без project_name (тобто ті, що йдуть через multi_logger.info() тощо)
            filter=lambda record: "project_name" not in record["extra"],
        )

    def _get_logger(self, name):
        if name in self.loggers:
            return self.loggers[name]

        # Створюємо новий логер для проекту
        new_logger = loguru_logger.bind(project_name=name)

        # Додаємо обробник лише для файлу проекту (наприклад, проект1.log)
        file_path = os.path.join(self.log_dir, f"{name}.log")
        new_logger.add(
            file_path,
            format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | [<cyan>{file.name}:{line}</cyan>] - <white>{message}</white>",
            # Фільтр: записуємо лише повідомлення, де project_name == name
            filter=lambda record: record["extra"].get("project_name") == name,
        )

        self.loggers[name] = new_logger
        return new_logger

    def __getitem__(self, name):
        return self._get_logger(name)

    def __getattr__(self, name):
        # Якщо викликається метод логування (info, error, тощо), перенаправляємо до дефолтного loguru_logger
        if name in [
            "debug",
            "info",
            "warning",
            "error",
            "critical",
            "success",
            "exception",
        ]:
            return getattr(loguru_logger, name)
        raise AttributeError(f"'MultiLogger' object has no attribute '{name}'")


# Глобальний екземпляр
logger = MultiLogger()


# Зворотна сумісність з попередньою функцією
def get_logger(log_file="logs/log.log"):
    return logger
