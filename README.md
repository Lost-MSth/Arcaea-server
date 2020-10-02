# Arcaea-server
一个微型的Arcaea本地服务器  A small local server for Arcaea

## 简介 Introduction
这是基于Python以及Flask的微型本地Arcaea服务器，可以模拟游戏的主要功能，一时兴起在五天之内糊了出来。这可能是我第一次写这种大程序，若有不妥之处，敬请谅解。  
This is a small local Arcaea server based on Python and Flask, which can simulate the main functions of the game. I completed it on the spur of the moment in five days. This may be the first time I have written such a large program. Please understand if there is something wrong with it.
> 虽然看起来很蠢，但是可以用！
> It looks stupid, but it works!

## 说明 Statement
只是很有趣，用处探索中。  
It is just so interesting. What it can do is under exploration.

## 更新日志 Update log
### Version 1.2
- 仍然适用于Arcaea 3.2.0版本 Still for Arcaea 3.2.0
- 新增了网页管理页面，可以通过 http:// HOST IP : PORT /web 进行访问 Add a new management webpage, you can visit http:// HOST IP : PORT /web to use it.
- 修改了character表结构，这将方便以后的角色更新 The character table structure has been modified, which will facilitate the character update in the future.
- 修复了best_score表的时间记录，应该是精确到秒的Unix时间戳 Fix the time record of best_score table. It should be a UNIX timestamp accurate to seconds.
- 修复了一个bug，recent30现在会考虑同一首歌的不同难度 Fix a bug. Now recent30 will consider different difficulties of one song.
> 更新说明：现在你可以使用web管理页面来迁移旧数据了，后台固定账号admin，密码admin  
> 如果使用数据迁移，那么请先清空recent30表数据，或者在迁移后打30首歌手动清除recent30，这次更新后web页面读取原来的recent30表将会报错

> Update note: Now you can use the web management page to migrate old data. Background account is fixed. Username is admin, and password is admin.  
> If you use data migration, please clear the data in the recent30 table first, or manually clear recent30 by playing 30 songs after the migration. After this update, an error will be reported when the web page reads the past recent30 table.

### Version 1.1
- 适用于Arcaea 3.2.0版本 For Arcaea 3.2.0
- 更新了歌曲数据库 Update the song database.
- 角色**梦**可以看到觉醒立绘了 The drawing of uncapped character **Yume** can be seen.
- 修复了一个Bug，现在剧情可以全部解锁了 Fix a bug. Now the plot can be unlocked.
> 更新说明：您若需要做数据迁移，请使用原来的数据库文件**arcaea_database.db**，并使用数据库操作软件打开数据库修改角色数据，SQL命令为
> `Update user_char set is_uncapped=1, is_uncapped_override=1 where character_id=21;`  

> Update note: If you need to do data migration, please use the original database file **arcaea_ database.db**, and use the database operation software to open the database to modify the character data. The SQL command is
> `Update user_char set is_uncapped=1, is_uncapped_override=1 where character_id=21;`

### Version 1.0
- 适用于Arcaea 3.1.2版本 For Arcaea 3.1.2

## 运行环境与依赖 Running environment and requirements
- Windows操作系统 Windows operating system
- Python 3
- Flask模块 Flask module
- Charles

## 环境搭建 Environment construction
[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Environment-construction)

## 使用说明 Instruction for use
[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Instruction-for-use)

## 注意 Attentions
[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E6%B3%A8%E6%84%8F)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Attentions)

## 鸣谢 Thanks
歌曲数据库来自 Using song database from
[BotArcAPI releases](https://github.com/TheSnowfield/BotArcAPI/releases)

## 联系方式 Contact
如有必要，可以联系本人 Contact me if necessary  
邮箱 Email：th84292@foxmail.com

## 支持一下 Support me
生活不易。 Life is not easy.  
[支付宝 Alipay](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/Alipay.jpg)  
[微信 WeChat](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/WeChat.png)

## 使用许可 Use license
[MIT](LICENSE) © Lost
