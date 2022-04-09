import os
import asyncio
import json
from hoshino import Service, logger, priv
from .submain import cpdaily_submit, single_submit

# 首次启动时若配置文件不存在则自动生成配置文件
current_dir = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(current_dir):
    init_data = {}
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(init_data, f, indent=4, ensure_ascii=False)
    logger.info(f'cpdaily配置文件不存在，现已成功创建')

sv_help = '''
[添加用户 学号 密码 QQ] 添加新用户

[删除用户 学号] 删除信息（限本人或维护组）

[全员打卡] 全员手动打卡（限维护组）

[单独打卡 学号] 顾名思义

[开启打卡邮件提醒 学号] 添加用户默认开启（限本人或维护组）

[关闭打卡邮件提醒 学号] 不想要就关闭了它（限本人或维护组）

[打卡用户列表] 看看所有用户
'''.strip()

sv = Service('cpdaily_v2', help_=sv_help, enable_on_default=False, visible=False)
svau = Service('cpdaily_v2_auto', enable_on_default=False, visible=False)

# 帮助界面
@sv.on_fullmatch("打卡帮助")
async def help(bot, ev):
    await bot.send(ev, sv_help)

# 为多用户模式添加额外用户
@sv.on_prefix('添加用户')
async def addinfo(bot, ev):
    self_id = ev.self_id
    alltext = ev.message.extract_plain_text()
    text_list = alltext.split(' ', 2)
    username = text_list[0]
    # 判断是否是十位数
    if not len(username) == 10:
        msg = '添加失败！学号必须是10位数'
        await bot.finish(ev, msg)
    password = text_list[1]
    qq = text_list[2]
    email = qq + '@qq.com'
    msg = f'正在添加您的信息：\n学号 = {username}\n密码 = {password}\nQQ = {qq}\n请尽快确认您的信息，本消息将在五秒后撤回'
    msgback = await bot.send(ev, msg)
    msg_id = msgback['message_id']
    await asyncio.sleep(5)
    await bot.delete_msg(self_id=self_id, message_id=msg_id)
    
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    manage_dir = os.path.join(os.path.dirname(__file__), 'manage.json')
    with open(manage_dir, 'r', encoding='UTF-8') as af:
        m_data = json.load(af)
    enable_default = m_data['enable_default']
    location = m_data['location']
    f_data[username] = {
        'password': password,
        'email': email,
        'location': location,
        'enable_email': enable_default
    }
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(f_data, f, indent=4, ensure_ascii=False)
    msg = f'{username}的信息添加完成'
    await bot.send(ev, msg)

# 删除用户
@sv.on_prefix('删除用户')
async def delinfo(bot, ev):
    uid = str(ev.user_id)
    username = str(ev.message)
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    if username not in list(f_data.keys()):
        msg = f'未找到此用户:{username}'
        await bot.finish(ev, msg)
    qq = f_data[username]['email'].replace('@qq.com', '')
    if not priv.check_priv(ev, priv.SUPERUSER) and uid != qq:
        msg = '您不是该学号对应QQ本人，需要删除需要本人操作或联系管理员操作!'
        await bot.finish(ev, msg)
    f_data.pop(username)
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(f_data, f, indent=4, ensure_ascii=False)
    msg = f'{username}的信息删除成功'
    await bot.send(ev, msg)

# 查看所有用户
@sv.on_fullmatch("打卡用户列表")
async def allinfo(bot, ev):
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    user_list = list(f_data.keys())
    msg = '使用该功能的用户有：\n' + '\n'.join(user_list)
    await bot.send(ev, msg)

# 全员手动提交
@sv.on_fullmatch('全员打卡')
async def submit_all(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        msg = '很抱歉您没有权限进行全员提交，该操作仅限维护组。若需要单独提交请输入“单独打卡 学号”'
        await bot.finish(ev, msg)
    msg = await cpdaily_submit('手动')
    await bot.send(ev, msg)

# 自动打卡功能
@svau.scheduled_job('cron', hour='14', minute='16')
async def submit_all_auto():
    msg = await cpdaily_submit('自动')
    await svau.broadcast(msg, 'cpdaily-HFUT-auto', 0.2)

# 单独打卡
@sv.on_prefix('单独打卡')
async def submit_single(bot, ev):
    uid = str(ev.user_id)
    username = str(ev.message)
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    if username not in list(f_data.keys()):
        msg = f'未找到此用户:{username}'
        await bot.finish(ev, msg)
    qq = f_data[username]['email'].replace('@qq.com', '')
    if not priv.check_priv(ev, priv.SUPERUSER) and uid != qq:
        msg = '您不是该学号对应QQ本人，需要删除需要本人操作或联系管理员操作!'
        await bot.finish(ev, msg)
    msg = await single_submit(username, '手动')
    await bot.send(ev, msg)

# 开启打卡邮件提醒
@sv.on_prefix('开启打卡邮件提醒')
async def enable_email(bot, ev):
    uid = str(ev.user_id)
    username = str(ev.message)
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    if username not in list(f_data.keys()):
        msg = f'未找到此用户:{username}'
        await bot.finish(ev, msg)
    qq = f_data[username]['email'].replace('@qq.com', '')
    if not priv.check_priv(ev, priv.SUPERUSER) and uid != qq:
        msg = '您不是该学号对应QQ本人，需要删除需要本人操作或联系管理员操作!'
        await bot.finish(ev, msg)
    if f_data[username]['enable_email']:
        msg = '您已经开启了邮件提醒，无需再次开启'
        await bot.finish(ev, msg)
    f_data[username]['enable_email'] = True
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(f_data, f, indent=4, ensure_ascii=False)
    msg = '邮件提醒开启成功'
    await bot.send(ev, msg)

# 关闭打卡邮件提醒
@sv.on_prefix('关闭打卡邮件提醒')
async def disable_email(bot, ev):
    uid = str(ev.user_id)
    username = str(ev.message)
    with open(current_dir, 'r', encoding='UTF-8') as f:
        f_data = json.load(f)
    if username not in list(f_data.keys()):
        msg = f'未找到此用户:{username}'
        await bot.finish(ev, msg)
    qq = f_data[username]['email'].replace('@qq.com', '')
    if not priv.check_priv(ev, priv.SUPERUSER) and uid != qq:
        msg = '您不是该学号对应QQ本人，需要删除需要本人操作或联系管理员操作!'
        await bot.finish(ev, msg)
    if not f_data[username]['enable_email']:
        msg = '您已经关闭了邮件提醒，无需再次关闭'
        await bot.finish(ev, msg)
    f_data[username]['enable_email'] = False
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(f_data, f, indent=4, ensure_ascii=False)
    msg = '邮件提醒关闭成功'
    await bot.send(ev, msg)