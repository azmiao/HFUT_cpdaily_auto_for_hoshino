from Crypto.Cipher import AES
from requests.exceptions import HTTPError
import http.client
import requests
import time
import datetime
from datetime import timedelta, timezone
import os,base64
import sys
import yaml
import oss2
import json
from urllib.parse import urlparse
from urllib3.exceptions import InsecureRequestWarning
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

# 别问为什么这么多import，问就是能塞进来就塞

# 读取yml配置
def getYmlConfig() -> dict:
    current_dir = os.path.join(os.path.dirname(__file__), 'config.yml')
    file = open(current_dir, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)

def printLog(text: str) -> None:
    """Print log
    
    Print log with date and time and update last log,
    For example:
    
    >>> printLog('test')
    [21-01-18 08:08:08]: test
    
    """
    global lastLog
    print(f'[{"%.2d-%.2d-%.2d %.2d:%.2d:%.2d" % time.localtime()[:6]}]: {text}')
    lastLog = text

def encryptPassword(password: str, key: str) -> str:
    """Encrypt password
    
    Encrypt the password in ECB mode, PKCS7 padding, then Base64 encode the password
    
    Args:
      password:
        The password to encrypt
      key:
        The encrypt key for encryption
        
    Return:
      encryptedPassword:
        Encrypted password
    
    """
    # add padding
    blockSize = len(key)
    padAmount = blockSize - len(password) % blockSize
    padding = chr(padAmount) * padAmount
    encryptedPassword = password + padding
    
    # encrypt password in ECB mode
    aesEncryptor = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    encryptedPassword = aesEncryptor.encrypt(encryptedPassword.encode('utf-8'))
    
    # base64 encode
    encryptedPassword = base64.b64encode(encryptedPassword)
    
    return encryptedPassword.decode('utf-8')

def login(username: str, password: str, requestSession) -> bool:
    """Log in to cas of HFUT
    
    Try to log in with username and password. Login operation contains many jumps,
    there may be some unhandled problems, FUCK HFUT!
    
    Args:
      username:
        Username for HFUT account
      password:
        Password for HFUT account
    
    Return:
      True if logged in successfully
      
    Raises:
      HTTPError: When you are unlucky
    
    """
    # get cookie: SESSION
    ignore = requestSession.get('https://cas.hfut.edu.cn/cas/login')
    ignore.raise_for_status()
    
    # get cookie: JSESSIONID
    ignore = requestSession.get('https://cas.hfut.edu.cn/cas/vercode')
    ignore.raise_for_status()
    
    # get encryption key
    timeInMillisecond = round(time.time_ns() / 100000)
    responseForKey = requestSession.get(
        url='https://cas.hfut.edu.cn/cas/checkInitVercode',
        params={'_': timeInMillisecond})
    responseForKey.raise_for_status()
    
    encryptionKey = responseForKey.cookies['LOGIN_FLAVORING']
    
    # check if verification code is required
    if responseForKey.json():
        printLog('需要验证码，过一会再试试吧。')
        return False
    
    # try to login
    encryptedPassword = encryptPassword(password, encryptionKey)
    checkIdResponse = requestSession.get(
        url='https://cas.hfut.edu.cn/cas/policy/checkUserIdenty',
        params={'_': (timeInMillisecond + 1), 'username': username, 'password': encryptedPassword})
    checkIdResponse.raise_for_status()
    
    checkIdResponseJson = checkIdResponse.json()
    if checkIdResponseJson['msg'] != 'success':
        # login failed
        if checkIdResponseJson['data']['mailRequired'] or checkIdResponseJson['data']['phoneRequired']:
            # the problem may be solved manually
            printLog('需要进行手机或邮箱认证，移步: https://cas.hfut.edu.cn/')
            return False
        printLog(f'处理checkUserIdenty时出现错误：{checkIdResponseJson["msg"]}')
        return False
    requestSession.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    
    loginResponse = requestSession.post(
        url='https://cas.hfut.edu.cn/cas/login',
        data={
            'username': username,
            'capcha': '',
            'execution': 'e1s1',
            '_eventId': 'submit',
            'password': encryptedPassword,
            'geolocation': "",
            'submit': "登录"
        })
    loginResponse.raise_for_status()
    
    requestSession.headers.pop('Content-Type')
    if 'cas协议登录成功跳转页面。' not in loginResponse.text:
        # log in failed
        printLog('登录失败')
        return False
    # log in success
    printLog('登录成功')
    return True

def submit(location: str, requestSession) -> bool:
    """Submit using specific location
    
    submit today's form based on the form submitted last time using specific loaction
    
    Return:
      True if submitted successfully
    
    Args:
      location:
        Specify location information instead of mobile phone positioning
        
    Raises:
      HTTPError: Shit happens
    
    """
    ignore = requestSession.get(
        url='http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/*default/index.do'
    )
    ignore.raise_for_status()
    
    requestSession.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    })
    ignore = requestSession.post(
        url='http://stu.hfut.edu.cn/xsfw/sys/emapfunauth/welcomeAutoIndex.do'
    )
    ignore.raise_for_status()
    
    requestSession.headers.pop('Content-Type')
    requestSession.headers.pop('X-Requested-With')
    ignore = requestSession.get(
        url='http://stu.hfut.edu.cn/xsfw/sys/emapfunauth/casValidate.do',
        params={
            'service': '/xsfw/sys/swmjbxxapp/*default/index.do'
        }
    )
    ignore.raise_for_status()
    
    requestSession.headers.update({
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://stu.hfut.edu.cn/xsfw/sys/swmjbxxapp/*default/index.do'
    })
    ignore = requestSession.get(
        url='http://stu.hfut.edu.cn/xsfw/sys/emappagelog/config/swmxsyqxxsjapp.do'
    )
    ignore.raise_for_status()
    
    # get role config
    requestSession.headers.pop('X-Requested-With')
    requestSession.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    configData = {
        'data': json.dumps({
            'APPID': '5811260348942403',
            'APPNAME': 'swmxsyqxxsjapp'
        })
    }
    roleConfigResponse = requestSession.post(
        url='http://stu.hfut.edu.cn/xsfw/sys/swpubapp/MobileCommon/getSelRoleConfig.do',
        data=configData
    )
    roleConfigResponse.raise_for_status()
    
    roleConfigJson = roleConfigResponse.json()
    if roleConfigJson['code'] != '0':
        # :(
        printLog(f'处理roleConfig时发生错误：{roleConfigJson["msg"]}')
        return False
    
    # get menu info
    menuInfoResponse = requestSession.post(
        url='http://stu.hfut.edu.cn/xsfw/sys/swpubapp/MobileCommon/getMenuInfo.do',
        data=configData
    )
    menuInfoResponse.raise_for_status()
    
    menuInfoJson = menuInfoResponse.json()
    
    if menuInfoJson['code'] != '0':
        # :(
        printLog(f'处理menuInfo时发生错误：{menuInfoJson["msg"]}')
        return False
    
    # get setting... for what?
    requestSession.headers.pop('Content-Type')
    settingResponse = requestSession.get(
        url='http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/getSetting.do',
        data={'data': ''}
    )
    settingResponse.raise_for_status()
    
    settingJson = settingResponse.json()
    
    # get the form submitted last time
    requestSession.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    todayDateStr = "%.2d-%.2d-%.2d" % time.localtime()[:3]
    lastSubmittedResponse = requestSession.post(
        url='http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/getStuXx.do',
        data={'data': json.dumps({'TBSJ': todayDateStr})}
    )
    lastSubmittedResponse.raise_for_status()
    
    lastSubmittedJson = lastSubmittedResponse.json()
    
    if lastSubmittedJson['code'] != '0':
        # something wrong with the form submitted last time
        printLog('上次填报提交的信息出现了问题，本次最好手动填报提交。')
        return False
    
    # generate today's form to submit
    submitDataToday = lastSubmittedJson['data']
    submitDataToday.update({
        'BY1': '1',
        'DFHTJHBSJ': '',
        'DZ_SFSB': '1',
        'DZ_TBDZ': location,
        'GCJSRQ': '',
        'GCKSRQ': '',
        'TBSJ': todayDateStr
    })
    
    # try to submit
    submitResponse = requestSession.post(
        url='http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/saveStuXx.do',
        data={'data': json.dumps(submitDataToday)}
    )
    submitResponse.raise_for_status()
    
    submitResponseJson = submitResponse.json()
    
    if submitResponseJson['code'] != '0':
        # failed
        printLog(f'提交时出现错误：{submitResponseJson["msg"]}')
        return False
    
    # succeeded
    printLog('提交成功')
    requestSession.headers.pop('Referer')
    requestSession.headers.pop('Content-Type')
    return True

def get_time():
    time_conn = http.client.HTTPConnection('www.baidu.com')
    time_conn.request("GET", "/")
    r = time_conn.getresponse()
    ts = r.getheader('date')
    ltime = time.strptime(ts[5:25], "%d %b %Y %H:%M:%S")
    ttime = time.localtime(time.mktime(ltime)+8*60*60)
    dat = datetime.date(ttime.tm_year,ttime.tm_mon,ttime.tm_mday)
    # 下方用于测试用
    # global testtime
    # test1 = "%u-%02u-%02u"%(ttime.tm_year,ttime.tm_mon,ttime.tm_mday)
    # test2 = "%02u:%02u:%02u"%(ttime.tm_hour,ttime.tm_min,ttime.tm_sec)
    # currenttime=test1+" "+test2
    # testtime = str(currenttime)
    return dat

def get_week_day(date):
    week_day = {
        0: '星期一',
        1: '星期二',
        2: '星期三',
        3: '星期四',
        4: '星期五',
        5: '星期六',
        6: '星期日',
    }
    day = date.weekday()
    return week_day[day]

# 邮件信息
def sendEmail(send,msg):
    config = getYmlConfig()
    title_text = '今日校园打卡结果通知'
    my_sender= config['Info']['Email']['account']   # 发件人邮箱账号
    my_pass = config['Info']['Email']['password']   # 发件人邮箱密码
    my_user = send      # 收件人邮箱账号
    for user in config['users']:
        my_username = user['user']['username']  # 收件人学号
    try:
        msg=MIMEText(str(get_time()) + str(msg),'plain','utf-8')
        msg['From']=formataddr(["自动打卡系统", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To']=formataddr([my_username, my_user])              # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject']=title_text               # 邮件的标题

        server=smtplib.SMTP_SSL(config['Info']['Email']['server'], config['Info']['Email']['port'])  # 发件人邮箱中的SMTP服务器，端口是对应邮箱的ssl发送端口
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender,[my_user,],msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:
        printLog("邮件发送失败")
    else: printLog("邮件发送成功")

# 邮件发送
def InfoSubmit(msg, send=None):
    config = getYmlConfig()
    if(None != send):
        if(config['Info']['Email']['enable']): 
            sendEmail(send,msg)