# 环境配置

推荐系统 : Ubuntu 20.04

python版本 : Python 3.*

运行前需要执行的命令:    
```bash
sudo apt-get update
sudo apt-get install python3-dev -y
sudo apt-get install screen -y
pip3 install bs4 lxml web3
```

# 文件配置

19-24行 更换为自己的key，都是免费申请的

26行 MAX_GAS_FEE 能接受的最大gas_fee

27行 MAX_MINT_PER_NFT 最大的可mint数量，超过则跳过（不精准）

29行 FOLLOW_ADDR_LIST 跟单mint地址，支持多个

30行 MAX_ETH_FOR_FOLLOW 跟单mint时能接受的最大价格（单位：ETH）

32行 blacklist 黑名单，当nft_name中包含这些字符则跳过

# 功能

1. 通过 www.acnft.xyz 中的免费API获取freemint项目

2. 当交易卡住pending时自动取消交易（希望有用）

3. 通过设置黑名单和minted日志中跳过一些仿盘和mint过的nft

4. 范围内随机gasfee（可能某些项目会检测机器人？）

5. 通过TG机器人自动播报mint进度

2022.5.31 更新

6. 增加跟单mint模式 支持多个地址

# 运行

一切配置好后，登入你的服务器（推荐美区，mint时间平均在3秒之内完成，也可以使用自己的机器），输入```screen```打开一个新的终端保证在后台持续运行，然后输入 ```python3 free_mint_nft.py``` 开始运行，如果一切正常的话会和下面的图片一样提示 init success，然后就可以关掉了，下次打开服务器输入```screen -r```即可恢复到终端   

![image](https://github.com/jungleninja/nft-free-mint-bot/blob/main/1.png)

# 其他

discord Xinja#8947    
Yu DAO 社区 [discord](https://discord.gg/zgCCJjZv "discord") 欢迎大家加入一起交流
