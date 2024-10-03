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

### Version 2.12.0

> v2.11.3.1 ~ v2.11.3.20 for Arcaea 5.2.0 ~ 5.10.4
>
> Here are not some bug fixes.
>
> 注意：Link Play 2.0 无法兼容旧版本客户端。  Note: Link Play 2.0 is not compatible with older client versions.

- 适用于 Arcaea 5.10.4 版本
  For Arcaea 5.10.4
- 添加一些新搭档和搭档的觉醒形态，并支持他们的技能
  Add some new partners, uncap some others, and add support for their skills.
- 支持 Link Play 2.0 的几乎所有功能
  Add almost whole support for Link Play 2.0.
- 支持新谱面难度 ETR
  Adapt to the new difficulty ETR.
- 支持内容捆绑包（热更新），包含两种更新模式
  Add support for content bundles (hot update), including two update modes.
- 支持新手任务系统
  Add support for missions.
- 更新 Recent 30 机制，修改其表结构
  Update Recent 30 mechanism. Alter Recent 30 table structure.
- PTT 机制更新：添加了推分保护
  PTT mechanism: Change first play protection to new best protection.
- 调整世界排名机制使其更接近于官服
  Adjust world rank mechanism to be closer to the official one.
- 重构世界模式，并调整了一些搭档的技能效果和进度计算逻辑
  Code refactor for World Mode, and adjust some skills and the logic of progress calculation.
- 支持世界模式的陷落梯子
  Add support for Breached World Map.
- 添加了一个陷落梯子例子（#148）
  Add an example breached map. (#148)
- 变更残片购买体力的恢复时间为 23 小时
  Change the recover time of using fragments buying stamina to 23 hours.
- 支持设置多个可使用的和旧的游戏 API 前缀，其中旧的前缀会通知用户更新客户端
  Add some endpoints for old API prefixes to notify users to update the client; add support for multiple game prefixes.
- 支持用户自销毁账号（默认不开启）
  Add support for users destroy their own accounts. (default unable)
- 添加对“单曲兑换券”的不完整支持
  Incomplete support for "pick_ticket".
- 世界模式地图文件夹中可以包含子文件夹了
  Make the world maps' folder can have sub folders.
- 支持后台和 API 刷新 Recent 30 的定数评分
  Add support for refreshing ratings of Recent 30 via API and webpage.
- 添加对 IP 及设备的用户注册频率限制
  Add the IP and the device rate limiters for user register.
- 修复当用户再次通过已经通过的段位时无法正常上传分数的问题（by Guzi422）
  Fix the bug that the player cannot upload the score when completing a course again. (by Guzi422)
- 修复段位模式最高分在用户未完整完成挑战时不更新的逻辑问题
  Fix a logical bug that the course's high score will not update if the user does not complete the whole course challenge.
- 修复 Link Play 相关 API 接口报错的问题
  Fix a bug that API for Link Play cannot work.
- 修复依赖问题：cryptography >= 35.0.0
  Fix requirements: cryptography >= 35.0.0
- 修复 `songlist` 解析问题（#156）
  Fix a `songlist` parser problem. (#156)
- 修复技能 skill_amane 在世界地图台阶类型为空时报错的问题
  Fix a bug that "skill_amane" may arise error when the step type of world map is null.
- 支持自动添加搭档“光 & 对立 (Reunion)”和“光 (Fatalis)”，以尝试解决最终章的解锁问题（#110 #164）
  Add support for automatically adding partner "Hikari & Tairitsu (Reunion)" and "Hikari (Fatalis)", to try to unlock Finale stories correctly. (#110 #164)
- 修复 `songlist` 文件存在时视频文件无法下载的问题（#177）
  Fix a bug that the video files cannot be downloaded when
the `songlist` file exists. (#177)
- 修复 Link Play 中玩家全部返回房间后上一首曲子成绩消失的问题
  Fix a bug that the last song's scores will disappear when all players return to room in Link Play.
- 工具 `update_song.py` 支持 ETR 难度
  Add support for ETR difficulties in the `update_song.py` tool.
- 添加发送错误信息的小工具测试服务端
  Add a small tool test server to send error message.

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

## 支持一下 Support me

生活不易。 Life is not easy.  
[支付宝 Alipay](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/Alipay.jpg)  
[微信 WeChat](https://github.com/Lost-MSth/Arcaea-server/blob/master/pic/WeChat.png)

## 使用许可 Use license

[MIT](LICENSE) © Lost
