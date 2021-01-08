# Arcaea-server
一个微型的Arcaea本地服务器  A small local server for Arcaea

## 简介 Introduction
这是基于Python以及Flask的微型本地Arcaea服务器，可以模拟游戏的主要功能，一时兴起在五天之内糊了出来。这可能是我第一次写这种大程序，若有不妥之处，敬请谅解。  
This is a small local Arcaea server based on Python and Flask, which can simulate the main functions of the game. I completed it on the spur of the moment in five days. This may be the first time I have written such a large program. Please understand if there is something wrong with it.
> 虽然看起来很蠢，但是可以用！
> It looks stupid, but it works!

## 特性 Features
有以下 We have：
- 登录、注册 Login and registration
- 成绩上传 Score upload
- PTT
- 排名 Rank
- 好友系统 Friends
- 数据同步 Data synchronization
- 爬梯 Climbing steps
- 自定义世界模式 Customizable World Mode
- 自定义歌曲下载 Customizable songs download
- 单曲和曲包购买（没啥用） Single songs and song packs purchase(useless)
- 奖励系统 Present system
- 兑换码系统 Redeem code system
- 全角色立绘 All character drawings
- 角色技能 Character skills
- 自定义角色属性 Customizable characters attributes
- 全剧情解锁 Unlock all the stories
- 后台查询 Background search
- 后台自定义信息 Customize some things in the background
- 成绩校验 Score check
- 下载校验 Download check

没有以下 We don't have：
- 角色数值 Character characteristic value
- 服务器安全性保证 Server security assurance

可能有问题 There may be problems：
- Recent 30
- 一些歌曲的解锁 Some songs' unlocking

## 说明 Statement
只是很有趣，用处探索中。  
It is just so interesting. What it can do is under exploration.


## 下载 Download
[这里 Here](https://github.com/Lost-MSth/Arcaea-server/releases)

[Arcaea](https://konmai.cn/#arcaea)

## 更新日志 Update log
只保留最新版本 Only keep the latest version.

> 提醒：更新时请注意保留原先的数据库，以防数据丢失
>
> Tips: When updating, please keep the original database in case of data loss.

### Version 2.0
- 适用于Arcaea 3.4.1版本 For Arcaea 3.4.1
- 更新API接口至13 Update API interface to 13.
- 更新了歌曲数据库 Update the song database.
- 新增了兑换码系统 Add the redeem code system.
- 优化了下载时文件MD5的读取速度 Optimize the reading speed of MD5 when downloading.
- 新增初见保护 Add initial protection.
- EX保护机制修改，现在重复歌曲若分数较高，会刷新r30中最早的记录，并保证ptt不下降，仍不清楚能否正常起效 EX protection mechanism has been modified. If the score of one repetitive song is higher, it will refresh the earliest record in r30 and ensure that PTT won't not drop. It is still unclear whether it can work normally.
- 数据迁移机制修改，现在重复数据以旧数据库数据为准 The database migration mechanism has been modified. Now the duplicate data is subject to the old database data.
- 机制修改，数据库缺少歌曲定数会当做Unrank处理 The mechanism has been modified. The lack of chart constant of songs in the database will be treated as unrank.
- 后台新增用户密码修改、用户封禁和成绩清除 Add user password modification, user ban and score clearance in the background.
- 游戏内数据同步将记录同步时间 Data synchronization in game will record synchronization time.
- 修复了一些Bug Fix some bugs.

> 提醒：本次更新针对了API接口更新，将无法兼容Arcaea 3.4.1以下版本
>
> Tips: 

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
