# Arcaea-server

一个微型的Arcaea本地服务器  A small local server for Arcaea

## 简介 Introduction

这是基于Python以及Flask的微型本地Arcaea服务器，可以模拟游戏的主要功能。这可能是我第一次写这种大程序，若有不妥之处，敬请谅解。  

本程序主要用于学习研究，不得用于任何商业行为，否则后果自负，这不是强制要求，只是一个提醒与警告。  

This is a small local Arcaea server based on Python and Flask, which can simulate the main functions of the game. This may be the first time I have written such a large program. Please understand if there is something wrong with it.  

This procedure is mainly used for study and research, and shall not be used for any commercial activities, otherwise the consequences will be borne by oneself. This is not a mandatory requirement, just a reminder and warning.

> 虽然看起来很蠢，但是可以用！
> It looks stupid, but it works!

## 特性 Features

有以下 We have：

- 登录、注册 Login and registration
- 多设备登录 Multi device login
- 成绩上传 Score upload
- PTT
- 世界排名 Global rank
- 排名 Rank
- 段位系统 Course system
- Link Play
- 好友系统 Friends
- 云端存档 Cloud save
- 爬梯 Climbing steps
- 自定义世界模式 Customizable World Mode
- 自定义歌曲下载 Customizable songs download
- 单曲和曲包购买（没啥用） Single songs and song packs purchase(useless)
- 奖励系统 Present system
- 兑换码系统 Redeem code system
- 角色系统 Character system
- 全剧情解锁 Unlock all the stories
- 后台查询 Background search
- 后台自定义信息 Customize some things in the background
- 成绩校验 Score check
- 下载校验 Download check
- 服务器日志 Server log

没有以下 We don't have：

- 服务器安全性保证 Server security assurance

可能有问题 There may be problems：

- Recent 30
- 一些歌曲的解锁 Some songs' unlocking
- 同设备多共存登录 Multiple app logins on the same device

## 说明 Statement

只是很有趣，用处探索中。  
It is just so interesting. What it can do is under exploration.

## 下载 Download

[这里 Here](https://github.com/Lost-MSth/Arcaea-server/releases)

[Arcaea-CN official](https://arcaea.lowiro.com/zh)  
[Arcaea-Konmai Academy](https://616.sb)  

## 更新日志 Update log

只保留最新版本 Only keep the latest version.

> 提醒：更新时请注意保留原先的数据库，以防数据丢失。
>
> Tips: When updating, please keep the original database in case of data loss.

### Version 2.10.1

- 适用于Arcaea 4.1.4版本 For Arcaea 4.1.4
- 新搭档 **天音** 已解锁 Unlock the character **Amane**.
- 为**天音**技能提供支持 Add support for the skill of **Amane**.
- 现在配置文件可以是含有部分选项的文件或模块 At present the setting file can be a module or a file with some of options.
- 添加`waitress`和`gevent`的部署方案支持，并支持日志记录 Add deployment mode `waitress` and `gevent`, and add support for the info log recording of them.
- 为`songlist`添加解析器以指定可下载的文件 Add a parser for `songlist` to specify downloadable files.
- 重构数据库初始化和数据迁移部分 Code refactoring for database initialization and migration.
- 限制用户下载频率将使用第三方限制器，替代数据库 Add a custom limiter and use it for limiting users' download rate instead of using database.
  > 现在需要`limits`模块  
  > Now `limits` module is required.
- 为登录和API登录添加限制器 Add limiter for login and API login.
- `sqlite3`数据库调整为WAL模式并增大缓存 Change journal mode to WAL and enlarge cache size for `sqlite3` database.
- 将下载token放入内存中而不是文件数据库中 Put download token in memory database instead of filesystem database.
- 加速`best_score`表多次查询，表现为歌曲排行榜查询性能提升 Accelerate multiple querying in `best_score` table, which results in performance improvement of song ranklist query.
- 优化歌曲下载部分 Make some optimization for downloading songs.
- **修复更新recent 10时可能出现的死循环问题 Fix a bug that there is a endless loop in calculating recent 10 updating.** (due to 6fcca179182775615115cdb255b3a8223831a8a0)
- 修复课题模式成绩没有rating的问题 Fix a bug that scores in course mode cannot calculate rating.
- 修正搭档数值 Fix a character's value.
- 邮箱长度最大限制提升到64 Change the email max length to 64.
- 新增API接口来获取用户身份与权限 Add a method of API for getting users' roles and powers.
- 新增API接口来修改用户信息 Add a method of API to change the user's info.
- 为API的`GET`请求添加`query`参数支持 Add support for the `query` param in API's `GET` requests.
- 修复API的`best30`接口曲目无数据导致出错的问题 Fix a bug that `best30` of API cannot have scores whose songs are not in database.
- 修复API的`recent30`接口用户成绩数量不足导致出错的问题 Fix a bug that users with no recent scores cannot get `recent30` via API.

## 运行环境与依赖 Running environment and requirements

- Windows/Linux/Mac OS/Android...
- Python >= 3.6
- Flask module >= 2.0, Cryptography module >= 3.0.0, limits >= 2.7.0
- Charles, IDA, proxy app... (optional)

<!--
## 环境搭建 Environment construction
[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Environment-construction)
-->

## 使用说明 Instruction for use

[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Instruction-for-use)

## 注意 Attentions

[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E6%B3%A8%E6%84%8F)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Attentions)

## Q&A

[中文/English](https://github.com/Lost-MSth/Arcaea-server/wiki/Q&A)

## 鸣谢 Thanks

歌曲数据库来自 Using song database from
~~[BotArcAPI releases](https://github.com/TheSnowfield/BotArcAPI/releases)~~
[ArcaeaSongDatabase](https://github.com/Arcaea-Infinity/ArcaeaSongDatabase)

> 从v2.9开始不再提供歌曲数据  
> Since v2.9, song data will not be provided.

网站图标来自 Using favicon from [black fate - てんてん - pixiv](https://www.pixiv.net/artworks/82374369)

## 联系方式 Contact

如有必要，可以联系本人 Contact me if necessary  
邮箱 Email：th84292@foxmail.com

## 支持一下 Support me

生活不易。 Life is not easy.  
[支付宝 Alipay](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/Alipay.jpg)  
[微信 WeChat](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/WeChat.png)

## 使用许可 Use license

[MIT](LICENSE) © Lost
