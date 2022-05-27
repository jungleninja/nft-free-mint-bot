# 环境配置

推荐系统 : Ubuntu 20.04

python版本 : Python 3.*

运行前需要执行的命令:    
```bash
apt-get update
apt-get install python3-dev
apt-get install screen
pip3 install bs4 lxml web3
```

# 文件配置

16-21行更换为自己的key，都是免费申请的

23行 MAX_GAS_FEE 写入自己能接受的最大gas_fee

25行 blacklist 黑名单，当nft_name中包含这些字符则跳过

# 功能

1. 通过 www.acnft.xyz 中的免费API获取freemint项目

2. 当交易卡住pending时自动取消交易（希望有用）

3. 通过设置黑名单和minted日志中跳过一些仿盘和mint过的nft

4. 范围内随机gasfree和燃烧费（可能某些项目会检测机器人？）

5. 通过TG机器人自动播报mint进度

# 运行

一切配置好后，登入你的服务器（推荐美区，mint时间平均在3秒之内完成，也可以使用自己的机器），输入```screen```打开一个新的终端保证在后台持续运行，然后输入 ```python3 free_mint_nft.py``` 开始运行，如果一切正常的话会和下面的图片一样提示 init success，然后就可以关掉了，下次打开服务器输入```screen -r```即可恢复到终端   

![image](https://github.com/jungleninja/nft-free-mint-bot/blob/main/1.png)

# 其他

本人初入NFT圈对web3交易还不太了解，比如212行中的gas设置我不知如何计算，所以只能范围内随机一个数，我的代码很烂，轻喷

freemint并不能百分之百给你带来收入，**往往都是gas费赔到裤子穿不起**，当然也不排除mint到金狗给你带来收益

我的ETH地址：0xE1e5e54d5782D7F22e441aCc447c5375063eB277 （mint到金狗赏一顿猪脚饭呗）

我的discord Xinja#8947    
Yu DAO 社区 [discord](https://discord.gg/zgCCJjZv "discord") 欢迎大家加入一起交流
