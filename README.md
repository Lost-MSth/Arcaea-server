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

:x: : 不支持 Not supported  
:warning: : 可能存在问题 / 可能与官方不一样 Possible issues / may differ from official  
:wastebasket: : 不再更新，可能会移除或重构 No longer updated, may be removed or refactored  
:construction: : 建设中 In construction

- 登录、注册 Login and registration
  - 多设备自动封号 Auto-ban of multiple devices
  - :warning: 多设备登录 Multi device login
  - 登录频次限制 Login rate limit
  - :x: 销号 Destroy account
- 成绩上传 Score upload
  - 成绩校验 Score check
  - 成绩排名 Score rank
- 潜力值机制 Potential
  - Best 30
  - :warning: Recent Top 10
- :warning: 世界排名 Global rank
- 段位系统 Course system
- :warning: Link Play
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
- 购买系统 Purchase system
  - 单曲和曲包 Single & Pack
  - :x: 捆绑包 Bundle
  - 折扣 Discount
  - 五周年兑换券 5-th anniversary ticket
  - :x: Extend 包自动降价 Extend pack automatic price reduction
- 奖励系统 Present system
- 兑换码系统 Redeem code system
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
[Arcaea-Konmai Academy](https://616.sb)  

## 更新日志 Update log

只保留最新版本 Only keep the latest version.

> 提醒：更新时请注意保留原先的数据库，以防数据丢失。  
> Tips: When updating, please keep the original database in case of data loss.
>
> 其它小改动请参考各个 commit 信息  
> Please refer to the commit messages for other minor changes.

### Version 2.11.2

- 适用于 Arcaea 4.4.6 版本 For Arcaea 4.4.6
- 新搭档 **奈美（暮光）** 已解锁 Unlock the character **Nami (Twilight)**.
- 新增用户潜力值每日记录功能 Add support for recording users' potential each day.
- 修复搭档 **光 & 对立（Reunion）** 无法觉醒的问题 Fix a bug that the character **Hikari & Tairitsu (Reunion)** cannot be uncapped. (#100)
- 添加 `finale/finale_end` 接口尝试修复最终挑战无法解锁结局的问题 Add the `finale/finale_end` endpoint to try to fix the problem that the endings cannot be unlocked correctly in the finale challenge. (#110)
- 新增获取用户潜力值记录的 API 接口 Add an API endpoint for getting the user's rating records.

## 运行环境与依赖 Running environment and requirements

- Windows / Linux / Mac OS / Android...
- Python >= 3.6
  - Flask >= 2.0
  - Cryptography >= 3.0.0
  - limits >= 2.7.0
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

[中文 / English](https://github.com/Lost-MSth/Arcaea-server/wiki/Q&A)

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
