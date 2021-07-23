import requests
import hoshino
from hoshino import Service, R
from .submit import *

svsub = Service('cpdaily-HFUT-auto', enable_on_default=False, help_='今日校园自动打卡')

# 自动打卡功能
@svsub.scheduled_job('cron', hour='14', minute='15')
async def cpdailyHFUTauto():
    config = getYmlConfig()
    msg = '今日校园自动打卡系统：\n信息正在处理中，请耐心等待。。。'
    await svsub.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)
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

                      自动提交成功！
                '''
                InfoSubmit(emailmsg, user['user']['email'])
                msg = msg + '\n已为'+ f'{user["user"]["username"]}' + '成功提交'
                # await svsub.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)
            else:
                # failed
                printLog('发生错误，终止当前用户的处理')
                # 下面的emailmsg邮件消息内容可随意更改
                emailmsg = '''

你好：

    来自优衣酱~的消息：

                      自动提交失败！
    发生错误，可能的原因是不在填报时间范围内，请联系维护组~
                '''
                InfoSubmit(emailmsg, user['user']['email'])
                msg = msg + '\n发生错误，错误用户为'+ f'{user["user"]["username"]}' + '，可能的原因是不在填报时间范围内，详情请联系维护组'
                # await svsub.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)
        except HTTPError as httpError:
            printLog(f'发生HTTP错误：{httpError}，终止当前用户的处理')
            emailmsg = '''

你好：

    来自优衣酱~的消息：

                      自动提交失败！
    发生HTTP错误，可能的原因是您的密码错误，请联系维护组~
                '''
            InfoSubmit(emailmsg, user['user']['email'])
            msg = msg + '\n发生HTTP错误，已停止用户'+ f'{user["user"]["username"]}' + '的提交，可能的原因是您的密码错误，详情请联系维护组'
            # await svsub.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)
            # process next user
            continue
    
    await svsub.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)
    printLog('所有用户处理结束')
    msg = '今天是' + str(get_time()) + get_week_day(get_time()) + '\n所有用户自动处理结束，详情请看上方信息，个人详情请关注邮件'
    await svsub.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)
