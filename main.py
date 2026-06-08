import shlex
import re
from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CONDITION_PATTERN = re.compile(r'^(\w+)\s*(==|!=|>|<)\s*(.+)$')

class Movie(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_attributes(self) -> Dict[str, Any]:
        """Возвращает словарь атрибутов для проверки условий"""
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class FeatureFilm(Movie):
    def __init__(self, title: str, director: str):
        super().__init__(title)
        self.director = director

    def get_attributes(self) -> dict:
        return {"type": "Игровой", "title": self.title, "director": self.director}

    def __str__(self):
        return f"[Игровой] '{self.title}' | Режиссер: {self.director}"

class Cartoon(Movie):
    VALID_METHODS = {"рисованный", "кукольный", "пластилиновый", "компьютерный"}

    def __init__(self, title: str, creation_method: str):
        super().__init__(title)
        if creation_method not in self.VALID_METHODS:
            logger.info(f"Предупреждение: нестандартный способ создания '{creation_method}'")
        self.creation_method = creation_method

    def get_attributes(self) -> dict:
        return {"type": "Мультфильм", "title": self.title, "method": self.creation_method}

    def __str__(self):
        return f"[Мультфильм] '{self.title}' | Способ: {self.creation_method}"


class TVSeries(Movie):
    def __init__(self, title: str, director: str, episodes: int):
        super().__init__(title)
        self.director = director
        self.episodes = episodes

    def get_attributes(self) -> dict:
        return {"type": "Сериал", "title": self.title, "director": self.director, "episodes": self.episodes}

    def __str__(self):
        return f"[Сериал] '{self.title}' | Режиссер: {self.director}, Серий: {self.episodes}"

class MovieContainer:
    def __init__(self):
        self.movies: List[Movie] = []

    def add(self, movie: Movie):
        self.movies.append(movie)
        logger.info(f"Добавлено: {movie}")

    def remove(self, condition: str):
        initial_count = len(self.movies)
        self.movies = [m for m in self.movies if not self._evaluate(m, condition)]
        removed_count = initial_count - len(self.movies)
        logger.info(f"Удалено объектов по условию '{condition}': {removed_count}")

    def _evaluate(self, movie: Movie, condition: str) -> bool:
        """Проверяет, соответствует ли фильм условию (например, 'episodes > 10')"""
        match = CONDITION_PATTERN.match(condition.strip())
        if not match:
            logger.error(f"Ошибка: неверный формат условия '{condition}'. Используйте: атрибут оператор значение")
            return False

        attr, op, val_str = match.groups()
        attrs = movie.get_attributes()

        if attr not in attrs:
            return False

        val = attrs[attr]

        try:
            if isinstance(val, int):
                val_to_compare = int(val_str)
            elif isinstance(val, float):
                val_to_compare = float(val_str)
            else:
                val_to_compare = val_str.strip('"\'')
        except ValueError:
            val_to_compare = val_str.strip('"\'')

        if op == '==':
            return val == val_to_compare
        elif op == '!=':
            return val != val_to_compare
        elif op == '>':
            return isinstance(val, (int, float)) and isinstance(val_to_compare, (int, float)) and val > val_to_compare
        elif op == '<':
            return isinstance(val, (int, float)) and isinstance(val_to_compare, (int, float)) and val < val_to_compare

        return False

    def print_all(self):
        print("\n--- Содержимое контейнера ---")
        if not self.movies:
            print("Контейнер пуст.")
        for m in self.movies:
            print(m)
        print("-----------------------------\n")


class CommandProcessor:
    def __init__(self, container: MovieContainer):
        self.container = container

    def process_file(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    logger.info(f"Выполнение команды (строка {line_num}): {line}")
                    self._execute_command(line)
        except FileNotFoundError:
            logger.error(f"Ошибка: Файл '{filepath}' не найден.")

    def _execute_command(self, line: str):
        parts = shlex.split(line)
        if not parts:
            return

        cmd = parts[0].upper()
        
        if cmd == 'ADD':
            if len(parts) < 3:
                logger.error("Ошибка ADD: недостаточно аргументов. Формат: ADD <Тип> <Название> <Параметры>")
                return
            
            m_type = parts[1]
            title = parts[2]
            params = parts[3:]
            
            try:
                movie = self._create_movie(m_type, title, params)
                self.container.add(movie)
            except ValueError as e:
                logger.error(f"Ошибка ADD: {e}")  
        elif cmd == 'REM':
            condition = " ".join(parts[1:])
            self.container.remove(condition)
            
        elif cmd == 'PRINT':
            self.container.print_all()
            
        else:
            logger.error(f"Ошибка: Неизвестная команда '{cmd}'.")
    
    def _create_movie(self, m_type: str, title: str, params: List[str]) -> Movie:
        if m_type == "Игровой":
            if len(params) >= 1:
                return FeatureFilm(title, params[0])
            raise ValueError("Для игрового фильма нужен режиссер.")
        elif m_type == "Мультфильм":
            if len(params) >= 1:
                return Cartoon(title, params[0])
            raise ValueError("Для мультфильма нужен способ создания.")
        elif m_type == "Сериал":
            if len(params) >= 2:
                try:
                    episodes = int(params[1])
                    return TVSeries(title, params[0], episodes)
                except ValueError:
                    raise ValueError("Количество серий должно быть целым числом.")
            raise ValueError("Для сериала нужны режиссер и количество серий.")
        else:
            raise ValueError(f"Неизвестный тип фильма '{m_type}'. Доступны: Игровой, Мультфильм, Сериал.")

if __name__ == "__main__":
    test_file = "commands.txt"

    print("=== Запуск обработки команд из файла ===\n")
    container = MovieContainer()
    processor = CommandProcessor(container)
    processor.process_file(test_file)