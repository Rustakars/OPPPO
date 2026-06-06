import shlex
import re
from abc import ABC, abstractmethod
from typing import List, Dict

class Movie(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_attributes(self) -> dict:
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
            print(f"Предупреждение: нестандартный способ создания '{creation_method}'")
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
        print(f"Добавлено: {movie}")

    def remove(self, condition: str):
        initial_count = len(self.movies)
        self.movies = [m for m in self.movies if not self._evaluate(m, condition)]
        removed_count = initial_count - len(self.movies)
        print(f"Удалено объектов по условию '{condition}': {removed_count}")

    def _evaluate(self, movie: Movie, condition: str) -> bool:
        """Проверяет, соответствует ли фильм условию (например, 'episodes > 10')"""
        match = re.match(r'(\w+)\s*(==|!=|>|<)\s*(.+)', condition.strip())
        if not match:
            print(f"Ошибка: неверный формат условия '{condition}'. Используйте: атрибут оператор значение")
            return False

        attr, op, val_str = match.groups()
        attrs = movie.get_attributes()

        if attr not in attrs:
            return False

        val = attrs[attr]

        try:
            val_to_compare = int(val_str)
        except ValueError:
            val_to_compare = val_str.strip('"\'')

        if op == '==':
            return str(val) == str(val_to_compare)
        elif op == '!=':
            return str(val) != str(val_to_compare)
        elif op in ('>', '<'):
            try:
                return eval(f"{int(val)} {op} {val_to_compare}")
            except (ValueError, TypeError):
                return False
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
                    
                    print(f"Выполнение команды (строка {line_num}): {line}")
                    self._execute_command(line)
        except FileNotFoundError:
            print(f"Ошибка: Файл '{filepath}' не найден.")

    def _execute_command(self, line: str):
        parts = shlex.split(line)
        if not parts:
            return

        cmd = parts[0].upper()
        
        if cmd == 'ADD':
            if len(parts) < 3:
                print("Ошибка ADD: недостаточно аргументов. Формат: ADD <Тип> <Название> <Параметры>")
                return
            
            m_type = parts[1]
            title = parts[2]
            
            if m_type == "Игровой":
                if len(parts) >= 4:
                    self.container.add(FeatureFilm(title, parts[3]))
                else:
                    print("Ошибка: Для игрового фильма нужен режиссер.")
            elif m_type == "Мультфильм":
                if len(parts) >= 4:
                    self.container.add(Cartoon(title, parts[3]))
                else:
                    print("Ошибка: Для мультфильма нужен способ создания.")
            elif m_type == "Сериал":
                if len(parts) >= 5:
                    try:
                        episodes = int(parts[4])
                        self.container.add(TVSeries(title, parts[3], episodes))
                    except ValueError:
                        print("Ошибка: Количество серий должно быть целым числом.")
                else:
                    print("Ошибка: Для сериала нужны режиссер и количество серий.")
            else:
                print(f"Ошибка: Неизвестный тип фильма '{m_type}'. Доступны: Игровой, Мультфильм, Сериал.")
                
        elif cmd == 'REM':
            condition = " ".join(parts[1:])
            self.container.remove(condition)
            
        elif cmd == 'PRINT':
            self.container.print_all()
            
        else:
            print(f"Ошибка: Неизвестная команда '{cmd}'.")

if __name__ == "__main__":
    test_file = "commands.txt"

    print("=== Запуск обработки команд из файла ===\n")
    container = MovieContainer()
    processor = CommandProcessor(container)
    processor.process_file(test_file)