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
- 数据同步 Data synchronization
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
[Arcaea-lowi.ro](https://lowi.ro)  
[Arcaea-RhyDown](https://rhydown.com)

## 更新日志 Update log
只保留最新版本 Only keep the latest version.

> 提醒：更新时请注意保留原先的数据库，以防数据丢失。
>
> Tips: When updating, please keep the original database in case of data loss. 


### Version 2.10.0
- 适用于Arcaea 4.1.0版本 For Arcaea 4.1.0
- 新搭档 **咲姬** 已解锁 Unlock the character **Saki**.
- 新搭档 **刹那** 已解锁 Unlock the character **Setsuna**.
- 完善了日志系统 Improve the log system.
- 现在可以利用`songlist`确保`3.aff`以外文件不被下载 Now you can use `songlist` to ensure that files other than `3.aff` should not be downloaded. [#60](https://github.com/Lost-MSth/Arcaea-server/issues/60)
- 适配v4.0.0以下版本的客户端云存档 Ensure that the clients under v4.0.0 can upload the cloud save.
- 优化数据库索引 Optimize database indices.
- 尝试确保LinkPlay服务器的线程安全，现在此功能将作为独立服务端 Try to ensure thread safety in LinkPlay server. Now this function will be served as an independent server.
- 对API接口的分数列表添加歌曲名 Add song names for getting the score list in API.
- 为下载错误增添HTTP状态码 Add HTTP status code when meeting download error.

- 修复iOS客户端因世界模式地图数据闪退的问题 Fix a bug when world maps' data don't have some unnecessary parts the client of iOS may break down.
- 修复API接口无数据`GET`请求导致报错的问题 Fix a bug that `GET` requests without data will report an error in API. [#50](https://github.com/Lost-MSth/Arcaea-server/issues/50)
- 修复`aggregate`请求无法捕获内部错误的问题 Fix a bug that `aggregate` requests will get an error when the inner function raises an error.
- 修复因错误设置主键导致课程模式谱面无法相同的问题 Fix a bug that the charts of a course cannot be the same because of the incorrect primary keys.
- 修复无谱面数据时世界排名分计算出错的问题 Fix a bug that global ranking scores cannot be calculated if there are no chart in the database. [#61](https://github.com/Lost-MSth/Arcaea-server/issues/61)
- 修复条件满足但隐藏段位依然无法解锁的问题 Fix a bug that the hidden courses cannot appear even if their requirements are satisfied.
- 修复Finale挑战中某些无法解锁的问题 Fix a bug that something of the finale challenge cannot be unlocked.
- 修复用户物品数量无法为0的问题，此问题导致了一些购买操作异常 Fix a bug that the users' items will not be zero, which will disturb some purchase operations.
- 修复角色等级能超过最大等级的问题 Fix a bug that the level of the character can exceed the max level.
- 修复使用`以太之滴`升级角色时应答不正确的问题 Fix a bug that the response is incorrect when upgrading the characters by `generic core`.
- 修复`源韵强化`数值显示不正确的问题 Fix a bug that the `prog boost` shows the incorrect value.
- 修复世界模式奖励可能被重复发放的问题 Fix a bug that the rewards can be get repeatedly in World Mode.
- 修复世界Boss的第二管血量无法削减的问题 Fix a bug that second tube of blood of the world boss won't change.
- 修复我的排名显示不正确的问题 Fix a bug that `my rank` doesn't work correctly.
- 修复在歌曲结束后无法及时轮换房主的问题 Fix a bug that the room host will be changed late when finishing a song.


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
~~歌曲数据库来自 Using song database from
[BotArcAPI releases](https://github.com/TheSnowfield/BotArcAPI/releases)~~
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
