import os
from shutil import copy, copy2
from core.sql import Connect
from database.database_initialize import main, ARCAEA_SERVER_VERSION
from web.system import update_database


def try_rename(path, new_path):
    # 尝试重命名文件，并尝试避免命名冲突，返回最终路径
    final_path = new_path
    if os.path.exists(new_path):
        i = 1
        while os.path.exists(new_path + str(i)):
            i += 1
        os.rename(path, new_path + str(i))
        final_path = new_path + str(i)
    else:
        os.rename(path, new_path)

    return final_path


def check_before_run(app):
    # 运行前检查关键文件，返回布尔值，其实是因为有人经常忘了

    f = True

    if not os.path.exists('setting.py'):
        app.logger.warning('File `setting.py` is missing.')
        f = False

    if not os.path.exists('database'):
        app.logger.warning('Folder `database` is missing.')
        f = False

    if not os.path.exists('database/songs'):
        app.logger.warning('Folder `database/songs` is missing.')
        f = False

    if not os.path.exists('database/arcaea_database.db'):
        app.logger.warning('File `database/arcaea_database.db` is missing.')
        f = False
        try:
            app.logger.info(
                'Try to new the file `database/arcaea_database.db`.')
            main('./database/')
            app.logger.info(
                'Success to new the file `database/arcaea_database.db`.')
            f = True
        except:
            app.logger.warning(
                'Fail to new the file `database/arcaea_database.db`.')

    else:
        with Connect() as c:
            try:
                c.execute('''select value from config where id="version"''')
                x = c.fetchone()
            except:
                x = None

        # 数据库自动更新，不强求
        if not x or x[0] != ARCAEA_SERVER_VERSION:
            app.logger.warning(
                'Maybe the file `database/arcaea_database.db` is an old version.')
            try:
                app.logger.info(
                    'Try to update the file `database/arcaea_database.db`.')

                path = try_rename('database/arcaea_database.db',
                                  'database/arcaea_database.db.bak')

                try:
                    copy2(path, 'database/arcaea_database.db')
                except:
                    copy(path, 'database/arcaea_database.db')

                if os.path.isfile("database/old_arcaea_database.db"):
                    os.remove('database/old_arcaea_database.db')

                try_rename('database/arcaea_database.db',
                           'database/old_arcaea_database.db')

                main('./database/')
                update_database()

                app.logger.info(
                    'Success to update the file `database/arcaea_database.db`.')

            except:
                app.logger.warning(
                    'Fail to update the file `database/arcaea_database.db`.')

    return f
