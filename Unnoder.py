from os import name
from pathlib import Path
from collections import defaultdict, deque
from pkgutil import extend_path
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

    def __check__nodes_file(self) -> dict:
        """Проходит по очереди по всем папкам
        Ищет пары 3 файлов с нужными файлами для потребности узла
        Возвращает словарь с именем потребности в ключе,
        а в значении хранит словарь
        словарь имеет в качестве ключа расширение файла, а в значении его путь

        return: dict с названием потребности и всеми требуемыми файлами
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

    def __check_name_yz(self, name_yz: str) -> bool:
        """проверяет является ли имя узла подходящим

        Args:
            name_yz (str): Имя узла

        Returns:
            bool: True если имя соотвтетсвует,
                    False не соотетствует
        """
        return bool(re.search(r".+\.000(?:\*[A-Z])?$", name_yz))

    def __read_nodes_file(self, file_potreb_tree: dict) -> tuple:
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

            yz_tree = defaultdict(lambda: defaultdict(int))
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
                                if data_list[1] in yz_tree[data_list[0]]:
                                    print(f"В {data_list[0]} уже есть {data_list[1]}")
                                    raise KeyError
                                yz_tree[data_list[0]][data_list[1]] = data_list[2]
                        elif data_list.__len__() == 1:
                            yz_name = line.strip()
                            if yz_name not in yz_tree.keys():
                                yz_tree[yz_name]
                        bool_re = False
                    else:
                        # получаем массив из строки
                        # состоящий из значений заключенный в кавычках
                        data_list = re.findall('"([^,]*)"', line)
                        if data_list.__len__() > 0:
                            bool_re = True
            return yz_tree

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

            # проверяет на повторение расшифровок у стандартных изделий
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

            # Чистка от узлов
            for key, items in tuple(DT.items()):
                for item in tuple(items):
                    if self.__check_name_yz(item):
                        del DT[key][item]

            return DT, SD, TB

        def merge_sd(sd_tree: dict, name_sd: dict) -> dict:
            """Заменяет именя ключей в sd_tree
            на имена ключей в sd_name

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

        def transfer_SV_Y(yz_tree: dict, dt_tree: dict) -> dict:
            """Убирает сварные из поузловой входимости
            переносит их в разряд деталей
            возвращает словарь со сварными деталями

            Args:
                yz_tree (dict): Словарь с поузловой входимостью
                dt_tree (dict): Словарь с подетальной входимостью

            Returns:
                dict: Словарь со сварными узлами
            """

            sv_y_tree = defaultdict(dict)
            sv_d_tree = defaultdict(lambda: defaultdict(int))
            # пересмоттреть

            def transver_to_dtTree(name_yz: str, val: dict, mul_count=1):
                """Переносит в детали узлов, сварные детали

                Args:
                    name_yz (str): Имя родительского узла
                    val (dict): Словарь с подъузлами родительского узла
                    mul_count (int, optional): коэфициент умножения для подъузлов. Defaults to 1.
                """
                nonlocal yz_tree
                nonlocal dt_tree

                for yz, count in val.items():
                    if self.__check_name_yz(yz):
                        continue
                    # Если входящая деталь является узлом

                    elif yz in yz_tree.keys():
                        count *= mul_count
                        transver_to_dtTree(
                            name_yz,
                            yz_tree[yz],
                            mul_count=count)
                    count *= mul_count
                    # Проверка на заимствованные сварные узлы
                    if not re.search(r"\*[A-Z]?$", yz):
                        dt_tree[name_yz][yz] += count

                    for key, val in dt_tree[yz].items():
                        dt_tree[name_yz][key] += val * count

            def generate_SV_Y(name_yz: str, val: dict):
                """Копирует узлы и детали сварных узлов в отдельные таблицы
                Args:
                    name_yz (str): _description_
                    val (dict): _description_
                """
                nonlocal yz_tree
                nonlocal dt_tree
                nonlocal sv_y_tree
                nonlocal sv_d_tree

                for yz, count in val.items():
                    if self.__check_name_yz(yz):
                        continue

                    elif yz in yz_tree.keys():
                        generate_SV_Y(yz, yz_tree[yz])
                    
                    # if not re.search(r"\*[A-Z]?$", yz):
                        
                    sv_y_tree[name_yz][yz] = count
                    sv_d_tree[yz].update(dt_tree[yz])
                    # for key, val in dt_tree[yz].items():
                    #     sv_d_tree[yz][key] = val




            # Перенос сварных в детали
            for main_yz, val in yz_tree.items():
                # Если это не обычный узел
                if not self.__check_name_yz(main_yz):
                    continue
                transver_to_dtTree(main_yz, val)
                generate_SV_Y(main_yz, val)

            for key in sv_d_tree.keys():
                try:
                    del yz_tree[key]
                except KeyError:
                    pass
                del dt_tree[key]
                


            return sv_d_tree
 
        YZ_tree = defaultdict(dict)
        DT_tree = defaultdict(dict)
        TB_tree = defaultdict(dict)
        SD_name = defaultdict(dict)

        for potreb_name, files in file_potreb_tree.items():
            get_yz = read_PDSE(files[".SE1"])
            get_sd_name = read_SPRNA(files[".SP1"])
            get_dt, get_sd, get_tb = read_PDPR(files[".PR1"])
            # Кореекция get_sd (переименовывание стандартных деталей)
            get_sd = merge_sd(get_sd, get_sd_name)
            del get_sd_name
            # Перенос сварных узлов
            sv_y_tree = transfer_SV_Y(get_yz, get_dt)
            return sv_y_tree
            


            # print()
            # print(get_yz)

    def test_function(self):
        files_dict = self.__check__nodes_file()
        return self.__read_nodes_file(files_dict)
        



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



def transfer_SV_Y(yz_tree: dict, dt_tree: dict) -> dict:
    """Убирает сварные из поузловой входимости
    переносит их в разряд деталей
    возвращает словарь со сварными деталями

    Args:
        yz_tree (dict): Словарь с поузловой входимостью
        dt_tree (dict): Словарь с подетальной входимостью

    Returns:
        dict: Словарь со сварными узлами
    """
    
    sv_y_tree = defaultdict(list)
    # пересмоттреть
    def transver_to_dtTree(name_yz, val, mul_count=1):
        nonlocal yz_tree
        nonlocal dt_tree

        for yz, count in val.items():
            if re.search(r".+\.000(?:\*[A-Z])?$", yz):
                continue
            # Если входящая деталь является узлом
            elif yz in yz_tree.keys():
                count *= mul_count
                # dt_tree[name_yz][yz] = count
                transver_to_dtTree(
                    name_yz,
                    yz_tree[yz],
                    mul_count=count)
            count *= mul_count
            if not re.search(r"\*[A-Z]?$", yz):
                dt_tree[name_yz][yz] += count

            for key, val in dt_tree[yz].items():
                dt_tree[name_yz][key] += val * count

    # Перенос сварных в детали
    for main_yz, val in yz_tree.items():
        # Если это не обычный узел
        if not re.search(r".+\.000(?:\*[A-Z])?$", main_yz):
            continue
        transver_to_dtTree(main_yz, val)

if __name__ == "__main__":
    # i = {1: {1:3, 2:2, 3:3},}
    # for item in i.values():
    #     print(4 in item.keys())
    # print(i)
    Obj = Unnoder()
    test_dict = Obj.test_function()
    view_dict_date(test_dict)
    # print(re.findall(r".+\.000(?:\*[A-Z])?$", r"fdsfds.000"))

    # yz_test = dict()
    # yz_test.update({"yz_1.000": {
    #                 "yz.000": 2, 
    #                 "yz_sv_y": 3,
    #                 "yz_sv": 4},

    #             "yz_sv_y": {
    #                 "yz_sv_I":3
    #             }})
    

    # dt_test = {"yz_1.000": {
    #                     "det_1": 2,
    #                     "det_2": 3,
    #                     },
    #             "yz_sv_y": {
    #                 "det_y_1": 3,
    #                 "det_y_2": 2
    #             },
    #             "yz_sv": {
    #                 "det_sv_1": 4,
    #                 "det_sv_2": 1
    #             },
    #             "yz_sv_I": {
    #                 "det_I_1": 2,
    #                 "det_I_2": 3
    #             },
    # }
    # dt_test = defaultdict(lambda: defaultdict(int), dt_test)
    # transfer_SV_Y(yz_test, dt_test)
    # view_dict_date(dt_test)
