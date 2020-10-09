import os
import sqlite3


def update_user_char(c):
    # 用character数据更新user_char
    c.execute('''select * from character''')
    x = c.fetchall()
    c.execute('''select user_id from user''')
    y = c.fetchall()
    if x and y:
        for j in y:
            for i in x:
                c.execute('''delete from user_char where user_id=:a and character_id=:b''', {
                          'a': j[0], 'b': i[0]})
                c.execute('''insert into user_char values(:a,:b,:c,:d,:e,:f,:g,:h,:i,:j,:k,:l,:m,:n,:o)''', {
                    'a': j[0], 'b': i[0], 'c': i[2], 'd': i[3], 'e': i[4], 'f': i[5], 'g': i[6], 'h': i[7], 'i': i[8], 'j': i[9], 'k': i[10], 'l': i[11], 'm': i[12], 'n': i[14], 'o': i[15]})


def update_database():
    # 将old数据库不存在数据加入到新数据库上，并删除old数据库
    # 对于arcaea_datebase.db，更新best_score，friend，recent30，user，user_world并用character数据更新user_char
    # 对于arcsong.db，更新songs
    if os.path.isfile("database/old_arcaea_database.db") and os.path.isfile("database/arcaea_database.db"):
        conn1 = sqlite3.connect('./database/old_arcaea_database.db')
        c1 = conn1.cursor()
        conn2 = sqlite3.connect('./database/arcaea_database.db')
        c2 = conn2.cursor()

        # user
        c1.execute('''select * from user''')
        x = c1.fetchall()
        if x:
            for i in x:
                c2.execute(
                    '''select exists(select * from user where user_id=:a)''', {'a': i[0]})
                if c2.fetchone() == (0,):
                    c2.execute('''insert into user values(:a0,:a1,:a2,:a3,:a4,:a5,:a6,:a7,:a8,:a9,:a10,:a11,:a12,:a13,:a14,:a15,:a16,:a17,:a18,:a19,:a20,:a21,:a22,:a23,:a24,:a25)''', {
                        'a0': i[0], 'a1': i[1], 'a2': i[2], 'a3': i[3], 'a4': i[4], 'a5': i[5], 'a6': i[6], 'a7': i[7], 'a8': i[8], 'a9': i[9], 'a10': i[10], 'a11': i[11], 'a12': i[12], 'a13': i[13], 'a14': i[14], 'a15': i[15], 'a16': i[16], 'a17': i[17], 'a18': i[18], 'a19': i[19], 'a20': i[20], 'a21': i[21], 'a22': i[22], 'a23': i[23], 'a24': i[24], 'a25': i[25]})

        # friend
        c1.execute('''select * from friend''')
        x = c1.fetchall()
        if x:
            for i in x:
                c2.execute(
                    '''select exists(select * from friend where user_id_me=:a and user_id_other=:b)''', {'a': i[0], 'b': i[1]})
                if c2.fetchone() == (0,):
                    c2.execute('''insert into friend values(:a,:b)''', {
                               'a': i[0], 'b': i[1]})

        # best_score
        c1.execute('''select * from best_score''')
        x = c1.fetchall()
        if x:
            for i in x:
                c2.execute('''select exists(select * from best_score where user_id=:a and song_id=:b and difficulty=:c)''', {
                           'a': i[0], 'b': i[1], 'c': i[2]})
                if c2.fetchone() == (0,):
                    c2.execute('''insert into best_score values(:a0,:a1,:a2,:a3,:a4,:a5,:a6,:a7,:a8,:a9,:a10,:a11,:a12,:a13)''', {
                        'a0': i[0], 'a1': i[1], 'a2': i[2], 'a3': i[3], 'a4': i[4], 'a5': i[5], 'a6': i[6], 'a7': i[7], 'a8': i[8], 'a9': i[9], 'a10': i[10], 'a11': i[11], 'a12': i[12], 'a13': i[13]})

        # recent30
        c1.execute('''select * from recent30''')
        x = c1.fetchall()
        if x:
            for i in x:
                c2.execute(
                    '''select exists(select * from recent30 where user_id=:a)''', {'a': i[0]})
                if c2.fetchone() == (0,):
                    c2.execute('''insert into recent30 values(:a0,:a1,:a2,:a3,:a4,:a5,:a6,:a7,:a8,:a9,:a10,:a11,:a12,:a13,:a14,:a15,:a16,:a17,:a18,:a19,:a20,:a21,:a22,:a23,:a24,:a25,:a26,:a27,:a28,:a29,:a30,:a31,:a32,:a33,:a34,:a35,:a36,:a37,:a38,:a39,:a40,:a41,:a42,:a43,:a44,:a45,:a46,:a47,:a48,:a49,:a50,:a51,:a52,:a53,:a54,:a55,:a56,:a57,:a58,:a59,:a60)''', {'a0': i[0], 'a1': i[1], 'a2': i[2], 'a3': i[3], 'a4': i[4], 'a5': i[5], 'a6': i[6], 'a7': i[7], 'a8': i[8], 'a9': i[9], 'a10': i[10], 'a11': i[11], 'a12': i[12], 'a13': i[13], 'a14': i[14], 'a15': i[15], 'a16': i[16], 'a17': i[17], 'a18': i[
                        18], 'a19': i[19], 'a20': i[20], 'a21': i[21], 'a22': i[22], 'a23': i[23], 'a24': i[24], 'a25': i[25], 'a26': i[26], 'a27': i[27], 'a28': i[28], 'a29': i[29], 'a30': i[30], 'a31': i[31], 'a32': i[32], 'a33': i[33], 'a34': i[34], 'a35': i[35], 'a36': i[36], 'a37': i[37], 'a38': i[38], 'a39': i[39], 'a40': i[40], 'a41': i[41], 'a42': i[42], 'a43': i[43], 'a44': i[44], 'a45': i[45], 'a46': i[46], 'a47': i[47], 'a48': i[48], 'a49': i[49], 'a50': i[50], 'a51': i[51], 'a52': i[52], 'a53': i[53], 'a54': i[54], 'a55': i[55], 'a56': i[56], 'a57': i[57], 'a58': i[58], 'a59': i[59], 'a60': i[60]})

        # user_world
        c1.execute('''select * from user_world''')
        x = c1.fetchall()
        if x:
            for i in x:
                c2.execute(
                    '''select exists(select * from user_world where user_id=:a and map_id=:b)''', {'a': i[0], 'b': i[1]})
                if c2.fetchone() == (0,):
                    c2.execute('''insert into user_world values(:a0,:a1,:a2,:a3,:a4)''', {
                               'a0': i[0], 'a1': i[1], 'a2': i[2], 'a3': i[3], 'a4': i[4]})

        update_user_char(c2)
        conn1.commit()
        conn1.close()
        conn2.commit()
        conn2.close()
        os.remove('database/old_arcaea_database.db')

    # songs
    if os.path.isfile("database/old_arcsong.db") and os.path.isfile("database/arcsong.db"):
        conn1 = sqlite3.connect('./database/old_arcsong.db')
        c1 = conn1.cursor()
        conn2 = sqlite3.connect('./database/arcsong.db')
        c2 = conn2.cursor()

        c1.execute('''select * from songs''')
        x = c1.fetchall()
        if x:
            for i in x:
                c2.execute(
                    '''select exists(select * from songs where sid=:a)''', {'a': i[0]})
                if c2.fetchone() == (0,):
                    c2.execute('''insert into songs values(:a0,:a1,:a2,:a3,:a4,:a5,:a6,:a7,:a8,:a9,:a10,:a11,:a12,:a13,:a14,:a15,:a16,:a17,:a18,:a19,:a20,:a21,:a22,:a23,:a24,:a25,:a26,:a27)''', {'a0': i[0], 'a1': i[1], 'a2': i[2], 'a3': i[3], 'a4': i[4], 'a5': i[5], 'a6': i[6], 'a7': i[7], 'a8': i[
                               8], 'a9': i[9], 'a10': i[10], 'a11': i[11], 'a12': i[12], 'a13': i[13], 'a14': i[14], 'a15': i[15], 'a16': i[16], 'a17': i[17], 'a18': i[18], 'a19': i[19], 'a20': i[20], 'a21': i[21], 'a22': i[22], 'a23': i[23], 'a24': i[24], 'a25': i[25], 'a26': i[26], 'a27': i[27]})

        conn1.commit()
        conn1.close()
        conn2.commit()
        conn2.close()
        os.remove('database/old_arcsong.db')
