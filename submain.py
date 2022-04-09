import requests
import os
import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from .submit import login_submit
from hoshino import logger

# 自动和手动的 全员提交
async def cpdaily_submit(mode):
    current_dir = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    manage_dir = os.path.join(os.path.dirname(__file__), 'manage.json')
    with open(manage_dir, 'r', encoding='UTF-8') as af:
        m_data = json.load(af)
    msg_list = []
    flag = ''
    for username in list(f_data.keys()):
        await asyncio.sleep(0.5)
        msg_list = await get_msg_list(username, f_data, m_data, mode, msg_list)
        if isinstance(msg_list, str):
            break
    if isinstance(msg_list, str):
        if flag == 'login_failed':
            return '登录超时，可能是网站又又又炸了，请稍后再提交吧'
    logger.info('==所有用户处理结束==')
    if not msg_list:
        msg = f'全部{mode}成功提交'
    else:
        msg = f'全部提交完成，其中部分用户提交出现问题：\n' + '\n'.join(msg_list)
    return msg

# 单独提交
async def single_submit(username, mode):
    current_dir = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    manage_dir = os.path.join(os.path.dirname(__file__), 'manage.json')
    with open(manage_dir, 'r', encoding='UTF-8') as af:
        m_data = json.load(af)
    msg_list = []
    msg_list = await get_msg_list(username, f_data, m_data, mode, msg_list)
    if isinstance(msg_list, str):
        if msg_list == 'login_failed':
            return '登录超时，可能是网站又又又炸了，请稍后再提交吧'
    logger.info(f'=={username}处理结束==')
    if not msg_list:
        msg = f'{username}成功{mode}提交'
    else:
        msg = f'提交出现问题：\n' + '\n'.join(msg_list)
    return msg

# 提交的过程
async def get_msg_list(username, f_data, m_data, mode, msg_list):
    logger.info(f'开始处理用户{username}')
    try:
        # 登录并提交
        flag = await login_submit(username, f_data[username]['password'], m_data['location'])
        if flag:
            if flag == 'success':
                info = f'{mode}提交成功'
            elif flag == 'have_done':
                info = f'{username}已经提交过了'
                msg_list.append(info)
            elif flag == 'need_self':
                info = f'{username}本次请手动填报提交'
                msg_list.append(info)
            elif flag == 'login_failed':
                return flag
            logger.info(info)
            emailmsg = f'''

你好：

    来自{mode}提交系统的消息：

                      {info}
            '''
            await InfoSubmit(username, m_data, emailmsg, f_data[username]['email'], f_data[username]['enable_email'])
        else:
            logger.info(f'{username}发生错误：不在填报时间范围内')
            emailmsg = f'''

你好：

    来自{mode}提交系统的消息：

                      {mode}提交失败！
        {username}发生错误：不在填报时间范围内
            '''
            await InfoSubmit(username, m_data, emailmsg, f_data[username]['email'], f_data[username]['enable_email'])
            msg_list.append(f'{username}发生错误：不在填报时间范围内')
    except requests.HTTPError:
        logger.info(f'{username}发生错误：密码错误')
        emailmsg = f'''

你好：

    来自{mode}提交系统的消息：

                    {mode}提交失败！
        {username}发生错误：密码错误
            '''
        await InfoSubmit(username, m_data, emailmsg, f_data[username]['email'], f_data[username]['enable_email'])
        msg_list.append(f'{username}发生错误：密码错误')
    return msg_list

# 邮件发送
async def InfoSubmit(username, m_data, msg, email, enable_email):
    if not enable_email:
        logger.info("该用户已关闭邮件提醒服务")
        return
    my_sender= m_data['account']   # 发件人邮箱账号
    my_pass = m_data['emailpassword']   # 发件人邮箱密码
    try:
        msg=MIMEText(str(msg),'plain','utf-8')
        msg['From']=formataddr(["自动提交系统", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To']=formataddr([username, email])              # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject']= '提交结果通知'              # 邮件的标题

        server=smtplib.SMTP_SSL(m_data['server'], m_data['port'])  # 发件人邮箱中的SMTP服务器，端口是对应邮箱的ssl发送端口
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, email, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        logger.info("邮件发送成功")
    except Exception:
        logger.info("邮件发送失败")