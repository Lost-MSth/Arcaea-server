import os


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

    if not os.path.exists('database/arcsong.db'):
        app.logger.warning('File `database/arcsong.db` is missing.')
        f = False

    return f
