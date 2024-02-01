from pathlib import Path
from collections import defaultdict, deque
import re
from shutil import move
from xml.sax import default_parser_list
import pandas as pd


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
        # Место хранения баз данных
        self.base = Path("base")

        self.csv_path = {"yz": self.base/"yz.csv",
                         "dt": self.base/"dt.csv",
                         "sd": self.base/"sd.csv",
                         "tb": self.base/"td.csv"}

        self.name_col = {"yz": ("Узел_Р", "Узел", "Кол."),
                         "dt": ("Узел_Р", "Деталь", "Кол."),
                         "sd": ("Узел_Р", "СД_деталь", "Кол."),
                         "tb": ("Узел_Р", "Табличка", "Кол.")}

        self.unnodes_path.mkdir(exist_ok=True)
        self.store_data_path.mkdir(exist_ok=True)
        self.complite_path.mkdir(exist_ok=True)
        self.bucket_path.mkdir(exist_ok=True)
        self.base.mkdir(exist_ok=True)

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

    def __check__nodes_file(self) -> dict:
        """Возвращает словарь с именами потребостей
        и необходимыми файлами

        Returns:
            dict: {Имя потребности : {Тип файла: Путь к файлу}}
        """
        
        # Словарь для хранения потребностей и ссылок на файлы
        data_file_dict = defaultdict(dict)

        def check_file_or_dir(check_dir: Path) -> tuple:
            """Возвращает кортеж со списком файлов и папок

            Args:
                check_dir (Path): Проверяемая папка

            Returns:
                tuple: (Файлы, папки)
            """

            list_file = list()
            list_dir = list()

            for file in check_dir.iterdir():
                if file.is_file():
                    list_file.append(file)
                elif file.is_dir():
                    list_dir.append(file)
            return list_file, list_dir

        def restruct_node(list_files: list) -> dict:
            """Возвращает словарь с потребностями и списками их файлов

            Args:
                list_files (list): список файлов

            Returns:
                dict: {Потребность : {Суффикс : Путь до файла}}
            """
            # Словарь для потребностей
            store_dict = defaultdict(dict)
            # Кортеж с типами файлов
            check_suffix = (".PR1", ".SE1", ".SP1")

            # Добавляем файл в словарь если его суффикс разрешен
            for file in list_files:
                if file.suffix.upper() in check_suffix:
                    store_dict[file.stem][file.suffix.upper()] = file
            # Проверяет потребность на наличие всех трех типов файлов
            for key in tuple(store_dict.keys()):
                if not len(store_dict[key]) == len(check_suffix):
                    del store_dict[key]

            return store_dict

        def update_main_dict_files(
                updated_dict: defaultdict,
                input_dict: defaultdict
                ) -> None:
            """Добавляет потребность в основной словарь
            если имя потребности уже есть то тогда присвоить новое имя

            Args:
                updated_dict (defaultdict): обновляемый словарь с потребностями
                input_dict (defaultdict): словарь для переноса
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
            # Добавляю папки в очередь
            deque_dir.extend(list_dir)
            # Получаю словарь потребностей с тремя файлами в каждом
            temp_dict = restruct_node(list_files)
            # Обновляю файлы
            update_main_dict_files(data_file_dict, temp_dict)
 
        return data_file_dict

    def __check_name_yz(self, name_yz: str) -> bool:
        """Проверяет является ли имя узла подходящим

        Args:
            name_yz (str): Имя узла

        Returns:
            bool: True если имя соотвтетсвует,
                False не соотетствует
        """
        return bool(re.search(r".+\.000(?:\*[A-Z])?$", name_yz))

    def __read_nodes_file(self, file_potreb_tree: dict) -> tuple:
        """Читает передаваемые потребности, возвращает кортеж
        со словарями узлов и деталей

        Args:
            file_potreb_tree (dict): Словарь с потребностями

        Raises:
            KeyError: _description_
            KeyError: _description_

        Returns:
            tuple: Кортеж со словарями данных
        """
        def read_PDSE(SE1_file: Path) -> defaultdict:
            """Возвращает содержимое файла PDSE
            с узловой входимостью в виде словаря

            Args:
                SE1_file (Path): path for PDSE file

            Raises:
                KeyError: _description_

            Returns:
                defaultdict: Словарь входимости узлов
            """

            yz_tree = defaultdict(lambda: defaultdict(int))
            data_list = list()
            # Открываем файл в нужной кодировке
            with open(SE1_file, encoding="cp866", mode="r") as file:
                for line in file:
                    if data_list.__len__() > 0:
                        # получаем число из строки
                        if re.search(r"^\s+$", data_list[0]):
                            data_list.clear()
                            continue
                        count = re.findall(r"^[\d]+$", line)
                        if count:
                            data_list.append(int(count[0]))
                            if data_list.__len__() == 3:
                                if data_list[1] in yz_tree[data_list[0]]:
                                    print(f"В {data_list[0]} уже есть {data_list[1]}")
                                    raise KeyError
                                yz_tree[data_list[0]][data_list[1]] = data_list[2]
                        elif data_list.__len__() == 1:
                            yz_name = line.strip()
                            if yz_name not in yz_tree.keys():
                                yz_tree[yz_name]
                        data_list.clear()
                    else:
                        # получаем массив из строки
                        # состоящий из значений заключенный в кавычках
                        data_list = re.findall('"([^,]*)"', line)

            return yz_tree

        def read_SPRNA(SPRNA_file: Path) -> dict:
            """Возвращает содержимое файла SP1
            с названиями стандартных деталей в виде словаря

            Args:
                SPRNA_file (Path): Путь до SP1 файла

            Raises:
                KeyError: Возбуждает исключение если
                в узел входит 2 узла с одинаковыми названиями

            Returns:
                dict: Словарь {Имя стандартной: Название стандартной}
            """
            # Переменная для хранения списка из строки
            temp = list()
            # Словарь для хранения названий стандартных деталей
            SPRN = dict()
            with open(SPRNA_file, encoding="cp866", mode="r") as file:
                for line in file:
                    if temp:
                        # Добавляем строку в словарь
                        SPRN[temp[0]] = line.strip("\n")
                        temp = []
                    else:
                        temp = (re.findall(r'\("(.*)"\)', line))

            # Проверяет на повторение названий у стандартных изделий
            if len(set(SPRN.values())) != len(SPRN.values()):
                # Для каждого названия стандартной,
                # формирует список со всеми стандартными
                # где это название используется
                table = defaultdict(list)
                for key, item in SPRN.items():
                    table[item].append(key)

                print("Дубликаты названий стандартных изделий:")
                for key, item in table.items():
                    # Если название стандартной используется
                    # более чем для одной стандартной
                    if len(item) > 1:
                        for name_dub in item:
                            print(f"{name_dub}-> ({key})")
                raise KeyError("Dublicate name standart details")
            return SPRN

        def read_PDPR(PR1_file: Path) -> tuple:
            """Возвращает содержимое файла PR1
            с входимостью деталей в узлы в виде словаря

            Args:
                PR1_file (Path): путь файла PR1

            Returns:
                tuple: кортеж со словарями табличек, деталей, стандартными
            """
            temp = list()
            # Словарь с табличками 
            TB = defaultdict(lambda: defaultdict(int))
            # Словарь с деталями
            DT = defaultdict(lambda: defaultdict(int))
            # Словарь со стандартными
            SD = defaultdict(lambda: defaultdict(int))

            with open(PR1_file, encoding="cp866", mode="r") as file:
                for line in file:
                    if temp.__len__() > 2:
                        count = re.findall(r"^[\d]+$", line)  # Добавляем строку
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

            # Чистка списка деталей от узлов
            # for key, items in tuple(DT.items()):
            #     for item in tuple(items):
            #         if self.__check_name_yz(item):
            #             del DT[key][item]

            return DT, SD, TB

        def merge_sd(sd_tree: dict, name_sd: dict) -> dict:
            """Заменяет именя ключей в sd_tree
            на имена ключей в name_sd

            Args:
                sd_tree (dict): словарь со стандартными
                name_sd (dict): словарь с именами ключей

            Returns:
                dict: sd_tree c измененными именами ключей
            """

            for val in sd_tree.values():
                for name in tuple(val.keys()):
                    if name not in name_sd.keys():
                        continue
                    val[name_sd.pop(name)] = val.pop(name)
            return sd_tree

        YZ_tree = defaultdict(dict)
        DT_tree = defaultdict(dict)
        TB_tree = defaultdict(dict)
        SD_name = defaultdict(dict)

        for files in file_potreb_tree.values():
            YZ_tree.update(read_PDSE(files[".SE1"]))
            get_sd_name = read_SPRNA(files[".SP1"])
            # Возвращает 3 таблицы в кортеже
            temp_tuple = read_PDPR(files[".PR1"])
            DT_tree.update(temp_tuple[0])
            SD_name.update(temp_tuple[1])
            TB_tree.update(temp_tuple[2])
            # Корекция SD_name (переименовывание стандартных деталей)
            SD_name = merge_sd(SD_name, get_sd_name)
            del get_sd_name
            # Перенос сварных узлов
            # sv_y_tree = transfer_SV_Y(YZ_tree, DT_tree)
        return YZ_tree, DT_tree, SD_name, TB_tree

            # print()
            # print(get_yz)

    def dict_to_csv(self, table: dict, csv_path: Path, name_columns=list) -> None:
        """Записывает переданный словарь в csv_file

        Args:
            table (dict): Записываемый словарь
            csv_path (Path): Путь до csv файла
            name_columns(list|None): Список с названиями столбцов
        """
        def CSV_type_converter() -> dict:
            """Преобразовует словарь в словарь подходящий для записи в CSV

            Returns:
                dict: подходящий словарь для csv
            """
            nonlocal table
            nonlocal name_columns
            csv_dict = defaultdict(list)
            csv_dict[name_columns[0]]
            csv_dict[name_columns[1]]
            csv_dict[name_columns[2]]

            if not len(name_columns) == 3:
                raise IndexError("Len name_columns need == 3")

            for key, val in table.items():
                for key_in, count in val.items():
                    csv_dict[name_columns[0]].append(key)
                    csv_dict[name_columns[1]].append(key_in)
                    csv_dict[name_columns[2]].append(count)
            return csv_dict

        def write_to_csv(csv_dict: dict) -> None:
            """Записывает в словарь в csv файл

            Args:
                csv_dict (dict): подходящий словарь для csv
            """
            nonlocal csv_path
            data = pd.DataFrame(csv_dict)
            data.to_csv(csv_path, sep="^", encoding="cp866", index=False)
            print(data.head(20))

        dict_csv = CSV_type_converter()
        write_to_csv(dict_csv)

    def csv_to_dict(self, path_csv: Path) -> dict:
        return_table = defaultdict(dict)
        if not path_csv.exists():
            return return_table

        table = pd.read_csv(path_csv, sep="^", encoding="cp866", dtype=str)

        for lst in table.to_dict(orient="split")["data"]:
            return_table[lst[0]][lst[1]] = lst[2]
        return return_table

    def update_main_tree(self, dict_list: dict):
        """Обновляет данные из csv файла и записывает обратно

        Args:
            dict_list (dict): словарь с таблицами
        """
        for key, table in dict_list.items():
            up_table = self.csv_to_dict(self.csv_path[key])
            up_table.update(table)
            self.dict_to_csv(
                up_table,
                self.csv_path[key],
                self.name_col[key])

    def main_update(self):

        # Получил словарь с потребностями
        files_dict = self.__check__nodes_file()
        # Получил таблицы из прочитанных файлов
        YZ_tree, DT_tree, SD_name, TB_tree = self.__read_nodes_file(files_dict)
        constr_dict = {"yz": YZ_tree,
                       "dt": DT_tree,
                       "sd": SD_name,
                       "tb": TB_tree}
        self.update_main_tree(constr_dict)

        return YZ_tree, DT_tree, SD_name, TB_tree


def view_dict_date(dict_date: dict) -> None:

    for key, val in dict_date.items():
        print(" ", "_"*41, " ", sep="")
        line = "'{0}'".format(key)

        print(f"|{line:^41}|")
        print("|", "-"*41, "|", sep="")
        if isinstance(val, dict):
            for key, count in val.items():
                key = f"'{key}'"
                print(f"|{key:<35}|{count:^5}|")
        else:
            key = f"'{val}'"
            print(f"|{key:<41}|")
        print("‾"*43)
    print("-"*80)
    print("-"*80)

if __name__ == "__main__":
    # i = {1: {1:3, 2:2, 3:3},}
    # for item in i.values():
    #     print(4 in item.keys())
    # print(i)
    Obj = Unnoder()
    Obj.main_update()

    # if isinstance(test_dict,  tuple):
    #     list(map(view_dict_date, test_dict))
    # else:
    #     view_dict_date(test_dict)
    # 

    # table = defaultdict(lambda: defaultdict(int))
    # table["count"]["num"] += 2
    # table["count"]["num"] = 1
    # view_dict_date(table)
