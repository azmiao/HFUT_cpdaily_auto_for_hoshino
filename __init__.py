import yaml
import re
import time
import os,base64
import asyncio
from collections import defaultdict
import hoshino
from hoshino import Service, R, priv
from hoshino.typing import *
from hoshino.util import FreqLimiter, concat_pic, pic2b64, silence
from .submit import *
from .submain import *


# ============下方信息注意填写完整============

# 下方True即为开启邮箱功能
emailenable = True
# account为邮箱账户（发件人）
account = 'xxxxxxxxx@xxxxx.com'
# emailpassword不是邮箱密码，而是邮箱的授权码，可进入邮箱设置生成
emailpassword = 'xxxxxxxxx'
# port为邮箱发送端口，百度一下你就知道，例如163邮箱的port为465
port = 465
# 填写邮件的smtp服务器，百度一下：qq/163等等邮箱smtp服务器，即可，例如下面的是163的
server = 'smtp.163.com'

# 下方填入自己的信息，作为初始化信息用
# owneremail是自己接受打卡结果的邮箱，qq邮箱也行
owneremail = 'xxxxxxxxx@xxxx.com'
# location位置，合工大的就不用改了
location = '安徽省合肥市蜀山区'
# 自己疫情信息收集的密码，尽量一次填对，错多了会有验证码就难搞了，登录密码应该是这个的密码 https://cas.hfut.edu.cn/cas/login
ownerpassword = 'xxxxxxxxxx'
# 自己的学号，十位数，别填错了
ownerusername = '2333333333'

# ============上方信息注意填写完整============


sv = Service('cpdaily-HFUT-init', enable_on_default=False, bundle='打卡初始化')

# 创建config.yml文件并初始化基础信息
@sv.on_fullmatch("今日校园初始化")
async def createinfo(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        msg = '很抱歉您没有权限进行此操作，该操作仅限维护组'
        await bot.send(ev, msg)
        return
    data = {'Info': {
        'Email': 
        {'account': account,
        'enable': emailenable, 
        'password': emailpassword, 
        'port': port, 
        'server': server}}, 
        'users': 
        [{'user': 
        {'email': owneremail, 
        'location': location, 
        'password': ownerpassword, 
        'username': ownerusername}}]}

    current_dir = os.path.join(os.path.dirname(__file__), 'config.yml')
    with open(current_dir, "w", encoding="UTF-8") as f:
        yaml.dump(data, f,allow_unicode=True)
    msg = '初始化成功'
    await bot.send(ev, msg)

@sv.on_prefix('添加用户')
async def addinfo(bot, ev):
    await _addinfo(bot, ev, region=1)

# 为多用户模式添加额外用户
async def _addinfo(bot, ev: CQEvent, region: int):
    # 处理输入数据
    alltext = ev.message.extract_plain_text()

    nametext_dir = re.findall(r" .*",alltext)
    for name_dir in nametext_dir:
        username = alltext.replace(name_dir,'')
    # msg = username
    # await bot.send(ev, msg)
    if len(username) == 10:
        # print('username = ' + username)
        msg1 = '\n学号 = ' + username
        # await bot.send(ev, msg)

        passtext = re.findall(r" .+? ",alltext)
        for password in passtext:
            password = password.replace(' ','')
        # print('password = ' + password)
        msg2 = '\n密码 = ' + password
        # await bot.send(ev, msg)

        qqtext = re.findall(r" .*",alltext)
        for qq in qqtext:
            pass_dir = password + ' '
            qq = qq.replace(pass_dir,'')
            qq = qq.replace(' ','')
            email = qq + '@qq.com'
        # print('qq = ' + qq)
        msg3 = '\nQQ = ' + qq
        # await bot.send(ev, msg)

        self_id = ev.self_id
        msg = '正在添加您的信息：'
        msg4 = '\n请尽快确认您的信息，本消息将在五秒后撤回'
        msg = msg + msg1 + msg2 + msg3 + msg4
        msgback = await bot.send(ev, msg)
        msg_id = msgback['message_id']
        await asyncio.sleep(5)
        await bot.delete_msg(self_id=self_id, message_id=msg_id)
        
        current_dir = os.path.join(os.path.dirname(__file__), 'config.yml')
        file = open(current_dir, 'r', encoding="UTF-8")
        file_data = file.read()
        file.close()
        config = yaml.load(file_data, Loader=yaml.FullLoader)

        data = {'user': {
            'email': email, 
            'location': location, 
            'password': password, 
            'username': username}}

        config["users"].append(data)

        with open(current_dir, "w", encoding="UTF-8") as f:
            yaml.dump(config, f,allow_unicode=True)
        msg = username + '的信息添加完成'
        await bot.send(ev, msg)
    else:
        msg = '学号格式错误，请重新输入'
        await bot.send(ev, msg)

@sv.on_prefix('删除用户')
async def delinfo(bot, ev):
    await _delinfo(bot, ev, region=1)

# 删除错误信息用户
async def _delinfo(bot, ev: CQEvent, region: int):
    uid = ev.user_id
    superqq = get_superqq()
    # 处理输入数据
    textname = ev.message.extract_plain_text()
    config = getYmlConfig()
    setnum = 0
    for user in config['users']:
        if user['user']['username'] == str(textname):
            qq = user['user']['email'].replace('@qq.com', '')
            if int(qq) != uid and uid != int(superqq):
                msg = '您不是该学号对应QQ本人，需要删除需要本人操作或联系管理员操作!'
                await bot.send(ev, msg)
                return
            # print(user['user']['username'])
            msg = '正在删除' + textname + '的所有信息'
            await bot.send(ev, msg)

            data = {'user': {
            'email': user['user']['email'], 
            'location': user['user']['location'], 
            'password': user['user']['password'], 
            'username': user['user']['username']}}
            config["users"].remove(data)
            current_dir = os.path.join(os.path.dirname(__file__), 'config.yml')
            with open(current_dir, "w", encoding="UTF-8") as f:
                yaml.dump(config, f,allow_unicode=True)

            msg = textname + '的信息删除成功'
            await bot.send(ev, msg)
            setnum = 1
    if setnum == 0:
        msg = '未找到此用户'
        await bot.send(ev, msg)

# 查看所有用户
@sv.on_fullmatch("打卡用户列表")
async def allinfo(bot, ev):
    config = getYmlConfig()
    msg = '使用该打卡功能的用户有：'
    for user in config['users']:
        msg = msg + '\n' + user['user']['username']
    await bot.send(ev, msg)
