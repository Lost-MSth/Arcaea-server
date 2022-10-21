import os
import sys
from importlib import import_module

# 数据库初始化文件，删掉arcaea_database.db文件后运行即可，谨慎使用


def main(core_path: str = '../', db_path: str = './arcaea_database.db', init_folder_path: str = './init'):
    sys.path.append(os.path.join(sys.path[0], core_path))
    sys.path.append(os.path.join(sys.path[0], core_path, './core/'))
    init = import_module('init').DatabaseInit(db_path, init_folder_path)
    init.init()


if __name__ == '__main__':
    main()
