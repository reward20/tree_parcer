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

    def __move_files_with_name_check(
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

    def test_function(self):
        return self.__check__nodes_file()


    def __read_nodes_file(self):
        """
        Read input nodes file in unnodes_path
         return list/dict data nodes
        """
        def read_PDSE(SE1_file: Path) -> defaultdict:
            """
                read PDSE file and return info in view dict
            Args:
                SE1_file (Path): path for PDSE file

            Raises:
                KeyError: _description_

            Returns:
                defaultdict: _description_
            """

            list_tree = defaultdict(dict)
            data_list = list()
            # Переменная если находит строку 
            # соответствующее регулярному выражению
            bool_re = False
            # Открываем файл в нужной кодировке
            with open(SE1_file, encoding="cp866", mode="r") as file:
                for line in file:
                    if bool_re:
                        # получаем число из строки
                        count = re.findall(r"^[\d]+$", line)
                        if count:
                            data_list.append(int(count[0]))
                            if data_list.__len__() == 3:
                                if data_list[1] in list_tree[data_list[0]]:
                                    print(f"В {data_list[0]} уже есть {data_list[1]}")
                                    raise KeyError
                                list_tree[data_list[0]][data_list[1]] = data_list[2]
                        elif data_list.__len__() == 1:
                            yz_name = line.strip()
                            if yz_name not in list_tree.keys():
                                list_tree[yz_name]
                        bool_re = False
                    else:
                        # получаем массив из строки
                        # состоящий из значений заключенный в кавычках
                        data_list = re.findall('"([^,]*)"', line)
                        if data_list.__len__() > 0:
                            bool_re = True
            return list_tree

        def read_SPRNA(SPRNA_file: Path) -> dict:
            """
            Считывает файл с наименование стандартных 
            """
            temp = list()
            SPRN = dict()
            with open(SPRNA_file, encoding="cp866", mode="r") as file:
                for line in file:
                    if temp:
                        # Добавляем строку 
                        SPRN[temp[0]] = line.strip("\n")
                        temp = []
                    else:
                        temp = (re.findall(r'\("(.*)"\)', line))

            if len(set(SPRN.values())) != len(SPRN.values()):
                table = defaultdict(list)
                for key, item in SPRN.items():
                    table[item].append(key)

                for key, item in table.items():
                    if len(item) > 1:
                        print("Дубликаты названий стандартных изделий:")
                        for name_dub in item:
                            print(f"{name_dub}-> ({key})")
                raise KeyError
            return SPRN




    
def read_PDPR(PR1_file: Path):
    """
    Считывает данные из файла с входисотью деталей
    """
    temp = list()
    TB = defaultdict(dict)
    DT = defaultdict(dict)
    SD = defaultdict(dict)
    with open(PR1_file, encoding="cp866", mode="r") as file:
        for line in file:
            if temp.__len__() > 2:
                count = re.findall("^[\d]+$", line)  # Добавляем строку
                if count and temp.__len__() >= 3:
                    count = int(count[0])
                    if re.fullmatch("^[12]?$", temp[1]):
                        if len(temp) == 4:
                            TB[temp[3]][temp[2]] = count
                    else:
                        if " " in temp[1]:
                            SD[temp[2]][temp[1]] = count
                        else:
                            DT[temp[2]][temp[1]] = count
                temp.clear()
            else:
                temp = (re.findall('"([^,]*)"', line))

    #Чистка от узлов
    for key, items in tuple(DT.items()):
        for item in tuple(items):
            if re.search(r".*\.000[A-Z\*]{0,2}$", item):
                del DT[key][item]

    return DT, SD, TB


if __name__ == "__main__":
    Obj = Unnoder()
    test_dict = Obj.test_function()

    test_dict = test_dict.popitem()[1]
    # print(test_dict)
    for key, val in (read_PDPR(test_dict[".PR1"])).items():
        print(f"({key}), ({val})")
        print()

    print(re.findall(r".*(?:(?:\*[A-Z]{1}){,1})", "afdf*A"))