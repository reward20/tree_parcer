from cgitb import strong
from pathlib import Path
from collections import defaultdict, deque
import re
from shutil import move
# import pandas as pd

class Unnoder():

    def __init__(self):
        # Where search node file
        self.unnodes_path = Path("input_nodes")
        # Where store base of nodes
        self.store_data_path = Path("data_store")
        # Where store complite nodes file
        self.complite_path = Path("complite_nodes")
        # Where stored bad nodes file
        self.bucket_path = Path("trash_file")

        self.unnodes_path.mkdir(exist_ok=True)
        self.store_data_path.mkdir(exist_ok=True)
        self.complite_path.mkdir(exist_ok=True)
        self.bucket_path.mkdir(exist_ok=True)

    def move_files_with_name_check(
            self,
            move_file: Path,
            out_path: Path) -> None:
        """Перемещает файл с проверкой на уникальность имени"""
        filename = move_file.name
        i = 1
        while True:
            if (out_path / filename).exists():
                filename = move_file.stem + f"-{i}" + move_file.suffix
                i += 1
            else:
                move(move_file, out_path / filename)
                break

    def __check__nodes_file(self):
        """Проходит по очереди по всем папкам
        Ищет пары 3 файлов с нужными файлами для потребности узла
        Возвращает словарь с именем потребности в ключе,
        а в значении хранит словарь
        словарь имеет в качестве ключа расширение файла, а в значении его путь
        """
        # Словарь для хранения потребностей и ссылок на файлы
        data_file_dict = defaultdict(dict)

        def check_file_or_dir(check_dir: Path) -> tuple:
            # Проверяет переданную папку на файлы и папки
            # Возвращает кортеж в виде (файлы, папки)

            list_file = list()
            list_dir = list()

            for file in check_dir.iterdir():
                if file.is_file():
                    list_file.append(file)
                elif file.is_dir():
                    list_dir.append(file)
            return list_file, list_dir

        def restruct_node(list_files: list) -> dict:
            # Словарь для словарей потребностей
            store_dict = defaultdict(dict)
            # Кортеж с суффиксами для каждого файла
            check_suffix = (".PR1", ".SE1", ".SP1")

            # Добавляем файл в словарь если его суффикс разрешен
            for file in list_files:
                if file.suffix.upper() in check_suffix:
                    store_dict[file.stem][file.suffix.upper()] = file
            # Проверяем словарь на наличие всех трех суффиксов

            for key in tuple(store_dict.keys()):
                if not len(store_dict[key]) == len(check_suffix):
                    del store_dict[key]

            return store_dict

        def update_main_dict_files(
                updated_dict: defaultdict,
                input_dict: defaultdict
                ) -> None:
            """Обновляет основной словарь, значениями
            из передаваемого словаря проверяя на дубликаты названий

            Args:
                temp_dict (defaultdict): словарь с элементами потребности
            """
            main_keys = updated_dict.keys()
            inputed_keys = input_dict.keys()

            for up_keys in inputed_keys:
                update_keys = up_keys
                if update_keys in main_keys:
                    i = 1
                    while update_keys in main_keys:
                        update_keys += f"-{i}"
                        i += 1
                updated_dict[update_keys] = input_dict[up_keys]

        # Очередь для хранения всех папок
        deque_dir = deque()
        deque_dir.append(self.unnodes_path)

        while deque_dir:
            check_dir = deque_dir.popleft()
            # получаю массив файлов и папок
            list_files, list_dir = check_file_or_dir(check_dir)
            deque_dir.extend(list_dir)  # Добавляю все папки
            # Получаю словарь потребностей со всеми тремя файлами в каждом
            temp_dict = restruct_node(list_files)
            update_main_dict_files(data_file_dict, temp_dict)

        return data_file_dict

            # if list_files:
            #     restruct_node(list_files)




    def __read_nodes_file(self):
        """
        Read input nodes file in unnodes_path
         return list/dict data nodes
        """
        pass

    def test_function(self):
        self.__check__nodes_file()

if __name__ == "__main__":
    Obj = Unnoder()
    Obj.test_function()