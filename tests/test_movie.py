import sys
import os
import pytest
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from main import (
    FeatureFilm, Cartoon, TVSeries, 
    MovieContainer, CommandProcessor
)

class TestFeatureFilm:
    def test_init_and_attributes(self):
        movie = FeatureFilm("Inception", "Nolan")
        assert movie.title == "Inception"
        assert movie.director == "Nolan"
        assert movie.get_attributes() == {"type": "Игровой", "title": "Inception", "director": "Nolan"}

    def test_str(self):
        movie = FeatureFilm("Inception", "Nolan")
        assert str(movie) == "[Игровой] 'Inception' | Режиссер: Nolan"

class TestCartoon:
    def test_init_valid_method(self):
        movie = Cartoon("Shrek", "компьютерный")
        assert movie.creation_method == "компьютерный"
        
    def test_init_invalid_method(self, caplog):
        with caplog.at_level(logging.INFO):
            movie = Cartoon("Unknown", "неизвестный")
            assert "нестандартный способ создания" in caplog.text

    def test_attributes_and_str(self):
        movie = Cartoon("Shrek", "компьютерный")
        assert movie.get_attributes() == {"type": "Мультфильм", "title": "Shrek", "method": "компьютерный"}
        assert str(movie) == "[Мультфильм] 'Shrek' | Способ: компьютерный"

class TestTVSeries:
    def test_init_and_attributes(self):
        movie = TVSeries("Breaking Bad", "Gilligan", 62)
        assert movie.episodes == 62
        assert movie.get_attributes() == {"type": "Сериал", "title": "Breaking Bad", "director": "Gilligan", "episodes": 62}

    def test_str(self):
        movie = TVSeries("Breaking Bad", "Gilligan", 62)
        assert str(movie) == "[Сериал] 'Breaking Bad' | Режиссер: Gilligan, Серий: 62"

class TestMovieContainer:
    def test_add(self, caplog):
        container = MovieContainer()
        movie = FeatureFilm("Inception", "Nolan")
        with caplog.at_level(logging.INFO):
            container.add(movie)
            assert "Добавлено" in caplog.text
            assert len(container.movies) == 1

    def test_remove_valid_condition(self):
        container = MovieContainer()
        container.add(TVSeries("Show", "Dir", 10))
        container.add(TVSeries("Show2", "Dir", 20))
        container.remove("episodes > 15")
        assert len(container.movies) == 1
        assert container.movies[0].title == "Show"

    def test_remove_invalid_condition(self, caplog):
        container = MovieContainer()
        container.add(FeatureFilm("Inception", "Nolan"))
        with caplog.at_level(logging.ERROR):
            container.remove("invalid condition")
            assert "неверный формат условия" in caplog.text
            assert len(container.movies) == 1 

    def test_evaluate_operators(self):
        container = MovieContainer()
        movie = TVSeries("Show", "Dir", 10)
        
        assert container._evaluate(movie, "episodes == 10") is True
        assert container._evaluate(movie, "episodes != 10") is False
        assert container._evaluate(movie, "episodes > 5") is True
        assert container._evaluate(movie, "episodes < 5") is False
        assert container._evaluate(movie, "title == Show") is True
        assert container._evaluate(movie, "title != Show") is False

    def test_evaluate_missing_attribute(self):
        container = MovieContainer()
        movie = FeatureFilm("Inception", "Nolan")
        assert container._evaluate(movie, "episodes > 5") is False

    def test_evaluate_int_conversion_error(self):
        container = MovieContainer()
        movie = TVSeries("Show", "Dir", 10)
        assert container._evaluate(movie, "episodes == abc") is False

    def test_print_all_empty(self, capsys):
        container = MovieContainer()
        container.print_all()
        captured = capsys.readouterr()
        assert "Контейнер пуст." in captured.out

    def test_print_all_not_empty(self, capsys):
        container = MovieContainer()
        container.add(FeatureFilm("Inception", "Nolan"))
        container.print_all()
        captured = capsys.readouterr()
        assert "Inception" in captured.out

class TestCommandProcessor:
    def test_create_movie_valid(self):
        container = MovieContainer()
        processor = CommandProcessor(container)
        
        assert isinstance(processor._create_movie("Игровой", "Title", ["Dir"]), FeatureFilm)
        assert isinstance(processor._create_movie("Мультфильм", "Title", ["рисованный"]), Cartoon)
        assert isinstance(processor._create_movie("Сериал", "Title", ["Dir", "10"]), TVSeries)

    def test_create_movie_invalid(self):
        container = MovieContainer()
        processor = CommandProcessor(container)
        
        with pytest.raises(ValueError): processor._create_movie("Игровой", "Title", [])
        with pytest.raises(ValueError): processor._create_movie("Мультфильм", "Title", [])
        with pytest.raises(ValueError): processor._create_movie("Сериал", "Title", ["Dir"])
        with pytest.raises(ValueError): processor._create_movie("Сериал", "Title", ["Dir", "not_int"])
        with pytest.raises(ValueError): processor._create_movie("Unknown", "Title", [])

    def test_execute_command_add(self, caplog):
        container = MovieContainer()
        processor = CommandProcessor(container)
        with caplog.at_level(logging.ERROR):
            processor._execute_command("ADD Игровой Inception Nolan")
            assert len(container.movies) == 1
            
            processor._execute_command("ADD Игровой")
            assert "недостаточно аргументов" in caplog.text

    def test_execute_command_rem(self):
        container = MovieContainer()
        processor = CommandProcessor(container)
        container.add(TVSeries("Show", "Dir", 10))
        processor._execute_command("REM episodes > 5")
        assert len(container.movies) == 0

    def test_execute_command_print(self, capsys):
        container = MovieContainer()
        processor = CommandProcessor(container)
        processor._execute_command("PRINT")
        captured = capsys.readouterr()
        assert "Контейнер пуст." in captured.out

    def test_execute_command_unknown(self, caplog):
        container = MovieContainer()
        processor = CommandProcessor(container)
        with caplog.at_level(logging.ERROR):
            processor._execute_command("UNKNOWN")
            assert "Неизвестная команда" in caplog.text

    def test_execute_command_empty(self):
        container = MovieContainer()
        processor = CommandProcessor(container)
        processor._execute_command("")
        processor._execute_command("   ")

    def test_process_file_valid(self, tmp_path):
        container = MovieContainer()
        processor = CommandProcessor(container)
        
        file_content = "ADD Игровой Inception Nolan\nPRINT\n"
        file_path = tmp_path / "commands.txt"
        file_path.write_text(file_content, encoding="utf-8")
        
        processor.process_file(str(file_path))
        assert len(container.movies) == 1

    def test_process_file_not_found(self, caplog):
        container = MovieContainer()
        processor = CommandProcessor(container)
        with caplog.at_level(logging.ERROR):
            processor.process_file("non_existent_file.txt")
            assert "не найден" in caplog.text