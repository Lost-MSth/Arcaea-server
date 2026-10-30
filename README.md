# Arcaea-server

一个微型的 Arcaea 本地服务器  A small local server for Arcaea

## 简介 Introduction

这是基于 Python 以及 Flask 的微型本地 Arcaea 服务器，可以模拟游戏的主要功能。这可能是我第一次写这种大程序，若有不妥之处，敬请谅解。  

本程序主要用于学习研究，不得用于任何商业行为，否则后果自负，这不是强制要求，只是一个提醒与警告。  

This is a small local Arcaea server based on Python and Flask, which can simulate the main functions of the game. This may be the first time I have written such a large program. Please understand if there is something wrong with it.  

This procedure is mainly used for study and research, and shall not be used for any commercial activities, otherwise the consequences will be borne by oneself. This is not a mandatory requirement, just a reminder and warning.

> 虽然看起来很蠢，但是可以用！
> It looks stupid, but it works!

## 特性 Features

:x: : 不支持 Not supported  
:warning: : 可能存在问题 / 可能与官方不一样 Possible issues / may differ from official  
:wastebasket: : 不再更新，可能会移除或重构 No longer updated, may be removed or refactored  
:construction: : 建设中 In construction

- 登录、注册 Login and registration
  - 多设备自动封号 Auto-ban of multiple devices
  - :warning: 多设备登录 Multi device login
  - 登录频次限制 Login rate limit
  - 注册频次限制 Register rate limit
  - :warning: 销号 Destroy account
- 成绩上传 Score upload
  - 成绩校验 Score check
  - 成绩排名 Score rank
- 潜力值机制 Potential
  - Best 30
  - :warning: Recent Top 10
- 世界排名 Global rank
- 段位系统 Course system
- :warning: Link Play 2.0
- 好友系统 Friends
  - :x: 好友位提升 Max friend number increase
- 云端存档 Cloud save
  - 尝试全剧情、曲目解锁 Try to unlock all the stories and songs
- 世界模式 World mode
  - 体力系统 Stamina system
  - :warning: 普通梯子强化和绳子强化 Normal steps boost & beyond boost
  - :warning: 角色技能 Character skills
- 歌曲下载 Songs downloading
  - :x: 加密下载 Encrypted downloading
  - 下载校验 Download check
  - 下载频次限制 Download rate limit
- 内容捆绑包热更新 Content bundle hot update
- 购买系统 Purchase system
  - 单曲和曲包 Single & Pack
  - :x: 捆绑包 Pack bundle
  - 折扣 Discount
  - 五周年兑换券 5-th anniversary ticket
  - 单曲兑换券 Pick ticket
  - :x: Extend 包自动降价 Extend pack automatic price reduction
- 奖励系统 Present system
- 兑换码系统 Redeem code system
- 新手任务 Missions
- 角色系统 Character system
- 数据记录 Data recording
  - 用户成绩 Users' scores
  - 用户每日潜力值 Users' daily potential
- :wastebasket: 简单的网页管理后台 Simple web admin backend
- :construction: API
- 服务器日志 Server log

## 说明 Statement

只是很有趣，用处探索中。  
It is just so interesting. What it can do is under exploration.

## 下载 Download

[这里 Here](https://github.com/Lost-MSth/Arcaea-server/releases)

[Arcaea-CN official](https://arcaea.lowiro.com/zh)  

## 更新日志 Update log

只保留最新版本 Only keep the latest version.

> 提醒：更新时请注意保留原先的数据库，以防数据丢失。  
> Tips: When updating, please keep the original database in case of data loss.
>
> 其它小改动请参考各个 commit 信息。  
> Please refer to the commit messages for other minor changes.

### Version 2.13.0

> v2.12.1.1 ~ v2.13.0.0 for Arcaea 6.8.0 ~ 7.1.0
>
> Here are not all bug fixes and features.

- 适用于 Arcaea 7.1.0 版本  
  For Arcaea 7.1.0
- 添加一些新搭档和搭档的觉醒形态，补充技能支持  
  Add new partners and awakening forms, extend skill support.
- 支持 “Insight (Nullified)” 的技能状态和动态能力加成，以及 “NENE & silky6” 的获胜加成  
  Add support for the skill state and dynamic stat bonuses of “Insight (Nullified)”, and the win bonus of “NENE & silky6”.
- 添加 Maya 觉醒、Saya (Absolution) 和 Insight (Nullified) 的解锁接口，并修复部分解锁响应错误  
  Add endpoints for Maya’s awakening and for unlocking Saya (Absolution) and Insight (Nullified), and fix some unlock response errors.
- 支持新版潜力值机制，增加 Best 10、Best 50 权重和通关加成，并保留自定义权重配置  
  Add support for the new Potential system with Best 10 and Best 50 weights and a clear bonus, while keeping the weights configurable.
- 部分支持 World Parallel 模式及同步率加成  
  Add partial support for World Parallel mode and its synchronization bonus.
- 更新 Link Play 协议  
  Update the Link Play protocol.
- 支持玩家资料卡的公开状态和名片背景设置  
  Add support for profile visibility and custom banner settings.
- 支持玩家设置展示搭档  
  Add support for showcase partner settings.
- 支持分片式内容捆绑包热更新  
  Add support for multipart content bundles.
- 支持通过 nginx 远程下载歌曲与内容捆绑包  
  Add support for remote song and content bundle downloads through nginx.
- 支持通过 S3 兼容存储远程下载歌曲与内容捆绑包  
  Add support for remote song and content bundle downloads through S3-compatible storage.
- 支持 Gunicorn 部署  
  Add support for Gunicorn deployment.
- 支持通过 `LOG_FOLDER_PATH` 设置日志目录  
  Add support for configuring the log directory with `LOG_FOLDER_PATH`.
- 为部分管理 API 添加数量查询功能  
  Add count queries to some management API endpoints.
- 添加获取用户简要信息的管理 API  
  Add a management API endpoint for retrieving brief user information.
- 添加获取服务端版本、技能列表和潜力值配置等常量的 API  
  Add an API endpoint for retrieving server versions, skill IDs, Potential settings, and other constants.
- 添加获取服务端时间的 API  
  Add an API endpoint for retrieving the server time.
- 添加刷新所有用户潜力值和世界排名分数的操作  
  Add an operation to refresh all users’ Potential and world ranking scores.
- 添加世界排名开关，并修复世界排名无法关闭的问题  
  Add an option to disable world rankings and fix the option not taking effect.
- 添加在线名片背景全解锁选项  
  Add an option to unlock all online banners.
- 添加全曲解锁时保留世界地图奖励曲锁定的选项  
  Add an option to keep world map reward songs locked when full song unlocking is enabled.
- 在云端存档全解锁功能中加入 Link Play 贴纸解锁支持  
  Extend cloud save unlocking to include Link Play stickers.
- 在网页管理后台添加世界地图数据刷新按钮  
  Add a world map data refresh button to the web admin interface.
- 修复以导入方式启动服务时缺少初始化操作的问题  
  Fix missing initialization when the application is started by importing it.
- 修复 Link Play 中部分歌曲解锁状态错误的问题  
  Fix incorrect unlock states for some songs in Link Play.
- 修复新手任务可重复完成或领取奖励的问题  
  Fix repeated mission completion and reward claims.
- 修复数据库升级时部分任务进度和用户扩展数据未迁移的问题  
  Fix missing migration of some mission progress and user metadata during database upgrades.
- 修复部分 Beyond 谱面的独立音频文件未下载的问题  
  Fix missing audio override downloads for some Beyond charts.
- 修复搭档技能无法通过管理 API 修改的问题  
  Fix partner skill changes not taking effect through the management API.
- 修复洞烛侵入触发时与部分搭档随机技能参数冲突的问题  
  Fix conflicting play parameters when Insight’s invasion is triggered while using certain partners with random skill parameters.
- 修复 Beyond 世界模式结算中搭档倍率显示为零的问题  
  Fix the partner multiplier being displayed as zero in Beyond world mode results.
- 优化歌曲文件缓存  
  Optimize song file caching.
- 优化成绩列表的歌曲名称查询  
  Optimize song name queries for score lists.

## 运行环境与依赖 Running environment and requirements

- Windows / Linux / Mac OS / Android...
- Python >= 3.6
  - Flask >= 2.0
  - Cryptography >= 35.0.0
  - limits >= 2.7.0
- Charles, IDA, proxy app... (optional)

## 子项目 Sub repositories

[Arcaea-Server-Wiki](https://arcaea.lost-msth.cn/Arcaea-Server/)
: 项目文档 Project documentation

[Arcaea-Bundler](https://github.com/Lost-MSth/Arcaea-Bundler)
: 用于生成和解包内容捆绑包  Used to pack or unpack content bundles

[Arcaea-Server-Frontend](https://github.com/Lost-MSth/arcaea_server_frontend)
: In building

## 旧的说明 Old wiki

<!--
### 环境搭建 Environment construction
[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E7%8E%AF%E5%A2%83%E6%90%AD%E5%BB%BA)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Environment-construction)
-->

### 使用说明 Instruction for use

[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Instruction-for-use)

### 注意 Attentions

[中文](https://github.com/Lost-MSth/Arcaea-server/wiki/%E6%B3%A8%E6%84%8F)  
[English](https://github.com/Lost-MSth/Arcaea-server/wiki/Attentions)

### Q&A

[中文 / English](https://github.com/Lost-MSth/Arcaea-server/wiki/Q&A)

## AI 使用声明 AI usage statement

在本项目中 AI 仅用于辅助开发，代码仍主要由人工编写。  
The AI tools used in this project are only for assisting development and will not replace manually written code.

## 鸣谢 Thanks

歌曲数据库来自 Using song database from
~~[BotArcAPI releases](https://github.com/TheSnowfield/BotArcAPI/releases)~~
[ArcaeaSongDatabase](https://github.com/Arcaea-Infinity/ArcaeaSongDatabase)
[ArcaeaSongDatabase Fork](https://github.com/CuSO4Deposit/ArcaeaSongDatabase)

> 从v2.9开始不再提供歌曲数据  
> Since v2.9, song data will not be provided.

网站图标来自 Using favicon from [black fate - てんてん - pixiv](https://www.pixiv.net/artworks/82374369)

## 联系方式 Contact

如有必要，可以联系本人 Contact me if necessary  
邮箱 Email：arcaea@lost-msth.cn

<!-- ## 支持一下 Support me

生活不易。 Life is not easy.  
[支付宝 Alipay](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/Alipay.jpg)  
[微信 WeChat](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/WeChat.png) -->

## 使用许可 Use license

[MIT](LICENSE) © Lost
