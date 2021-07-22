from hoshino.util import FreqLimiter, concat_pic, pic2b64, silence
import requests
import hoshino
from hoshino import Service, R, priv
from hoshino.typing import *
from .submit import *

superqq = 23333333 #超级管理员QQ

sv_help = '''
=====命令=====
注意：[]内为指令，外为改指令实现的功能

自动打卡无需命令，14.15自动打卡
==============

[今日校园初始化] 初始化（限维护组）

[添加用户 学号 密码 QQ] 添加新用户
(格式:添加用户 2018214233 233 2333)

[删除用户 学号] 删除信息（限维护组）

[全员打卡] 全员手动打卡（限维护组）

[单独打卡 2018xxxxxx] 顾名思义

[打卡用户列表] 看所有用户
'''.strip()

sv = Service('cpdaily-HFUT', help_=sv_help, enable_on_default=False, bundle='今日校园订阅')

# 传参
def get_superqq():
    superqq_tmp = superqq
    return superqq_tmp

#帮助界面
@sv.on_fullmatch("打卡帮助")
async def help(bot, ev):
    await bot.send(ev, sv_help)

#手动打卡功能
@sv.on_fullmatch(('全员打卡','今日校园打卡'))
async def cpdailyHFUT(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        msg = '很抱歉您没有权限进行全员打卡，该操作仅限维护组。若需要单独打卡请输入“单独打卡 2018xxxxxx”'
        await bot.send(ev, msg)
        return
    config = getYmlConfig()
    bot = hoshino.get_bot()
    msg = '今日校园打卡系统（手动模式）：正在开始处理'
    await bot.send(ev, msg)
    msg = '以下为详细信息：'
    for user in config['users']:
        requestSession = requests.session()
        requestSession.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        })
        printLog(f'开始处理用户{user["user"]["username"]}')
        try:
            # login and submit
            if login(user['user']['username'], user['user']['password'], requestSession) and submit(user['user']['location'], requestSession):
                # succeed
                printLog('当前用户处理成功')
                # 下面的emailmsg邮件消息内容可随意更改
                emailmsg = '''

你好：

    来自优衣酱~的消息：

                      手动提交成功！
                '''
                InfoSubmit(emailmsg, user['user']['email'])
                msg = msg + '\n已为'+ f'{user["user"]["username"]}' + '完成提交'
                # await bot.send(ev, msg)
            else:
                # failed
                printLog('发生错误，终止当前用户的处理')
                # 下面的emailmsg邮件消息内容可随意更改
                emailmsg = '''

你好：

    来自优衣酱~的消息：

                      手动提交失败！
    原因未知，可能的原因是不在填报时间范围内，请联系维护组~
                '''
                InfoSubmit(emailmsg, user['user']['email'])
                msg = msg + '\n发生错误，错误用户为'+ f'{user["user"]["username"]}' + '，可能的原因是不在填报时间范围内，详情请联系维护组'
                # await bot.send(ev, msg)
        except HTTPError as httpError:
            print(f'发生HTTP错误：{httpError}，终止当前用户的处理')
            emailmsg = '''

你好：

    来自优衣酱~的消息：

                      手动提交失败！
    发生HTTP错误，可能的原因是您的密码错误，详情请联系维护组~
                '''
            InfoSubmit(emailmsg, user['user']['email'])
            msg = msg + '\n发生HTTP错误，已停止用户'+ f'{user["user"]["username"]}' + '的提交，可能的原因是您的密码错误，详情请联系维护组'
            # await bot.send(ev, msg)
            # process next user
            continue

    await bot.send(ev, msg)
    printLog('所有用户处理结束')
    msg = '今天是' + str(get_time()) + get_week_day(get_time()) + '\n所有用户手动处理结束，今日校园打卡结果已出，详情请关注邮件'
    await bot.send(ev, msg)

@sv.on_prefix('单独打卡')
async def onlyinfo(bot, ev):
  await _onlyinfo(bot, ev, region=1)

# 单独用户打卡
async def _onlyinfo(bot, ev: CQEvent, region: int):
    # 处理输入数据
    textname = ev.message.extract_plain_text()
    config = getYmlConfig()
    uid = ev.user_id
    setnum = 0
    for user in config['users']:
        requestSession = requests.session()
        requestSession.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        })
        if user['user']['username'] == str(textname):
            setnum = 1
            qq = user['user']['email'].replace('@qq.com','')
            if int(qq) == uid or uid == int(superqq):
                # print(user['user']['username'])
                msg = '正在为' + textname + '单独打卡'
                await bot.send(ev, msg)
                try:
                    # login and submit
                    if login(user['user']['username'], user['user']['password'], requestSession) and submit(user['user']['location'], requestSession):
                        # succeed
                        printLog('当前用户处理成功')
                        # 下面的emailmsg邮件消息内容可随意更改
                        emailmsg = '''

你好：

    来自优衣酱~的消息：

                      手动提交成功！
                '''
                        InfoSubmit(emailmsg, user['user']['email'])
                        msg = '已为'+ f'{user["user"]["username"]}' + '完成提交'
                        await bot.send(ev, msg)
                    else:
                        # failed
                        printLog('发生错误，终止当前用户的处理')
                        # 下面的emailmsg邮件消息内容可随意更改
                        emailmsg = '''

你好：

    来自优衣酱~的消息：

                      手动提交失败！
    发生错误，可能的原因是不在填报时间范围内，请联系维护组~
                '''
                        InfoSubmit(emailmsg, user['user']['email'])
                        msg = '发生错误，错误用户为'+ f'{user["user"]["username"]}' + '，可能的原因是不在填报时间范围内，详情请联系维护组'
                        await bot.send(ev, msg)
                except HTTPError as httpError:
                    print(f'发生HTTP错误：{httpError}，终止当前用户的处理')
                    emailmsg = '''

你好：

    来自优衣酱~的消息：

                      手动提交失败！
    发生HTTP错误，可能的原因是您的密码错误，请联系维护组~
                '''
                    InfoSubmit(emailmsg, user['user']['email'])
                    msg = '发生HTTP错误，已停止用户'+ f'{user["user"]["username"]}' + '的提交，可能的原因是您的密码错误，详情请联系维护组'
                    await bot.send(ev, msg)
            else:
                msg = '您不是该学号本人或维护组。为了安全起见，无法代人手动打卡！如需代打卡请联系维护组'
                await bot.send(ev, msg)
                return

            msg = textname + '单独打卡成功，详情请关注邮件'
            await bot.send(ev, msg)
            
    if setnum == 0:
        msg = '未找到此用户'
        await bot.send(ev, msg)