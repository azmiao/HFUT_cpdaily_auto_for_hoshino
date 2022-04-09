from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import time
import json
import requests

from hoshino import logger

# 加密密码
async def encryptPassword(password: str, key: str) -> str:
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
    aesEncryptor = Cipher(algorithms.AES(key.encode('utf-8')),
                          modes.ECB(),
                          backend=default_backend()).encryptor()
    encryptedPassword = aesEncryptor.update(
        encryptedPassword.encode('utf-8')) + aesEncryptor.finalize()

    # base64 encode
    encryptedPassword = base64.b64encode(encryptedPassword)

    return encryptedPassword.decode('utf-8')

# 登录并提交
async def login_submit(username: str, password: str, location: str):
    #### 开始登录
    requestSession = requests.session()
    requestSession.headers.update({
        'User-Agent':
        'Mozilla/5.0 (Linux; Android 12; 114514FUCK) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.73 Mobile Safari/537.36',
        'Accept':
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    })

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
        logger.info('需要验证码，过一会再试试吧。')
        return False

    # try to login
    encryptedPassword = await encryptPassword(password, encryptionKey)
    checkIdResponse = requestSession.get(
        url='https://cas.hfut.edu.cn/cas/policy/checkUserIdenty',
        params={
            '_': (timeInMillisecond + 1),
            'username': username,
            'password': encryptedPassword
        })
    checkIdResponse.raise_for_status()

    checkIdResponseJson = checkIdResponse.json()
    if checkIdResponseJson['msg'] != 'success':
        # login failed
        if checkIdResponseJson['data']['mailRequired'] or checkIdResponseJson['data']['phoneRequired']:
            # the problem may be solved manually
            logger.info('需要进行手机或邮箱认证，移步: https://cas.hfut.edu.cn/')
            return False
        logger.info(f'处理checkUserIdenty时出现错误：{checkIdResponseJson["msg"]}')
        return False
    requestSession.headers.update(
        {'Content-Type': 'application/x-www-form-urlencoded'})

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
        logger.info('登录失败')
        return False
    # log in success
    logger.info('登录成功')

    #### 开始提交
    ignore = requestSession.get(
        url='http://stu.hfut.edu.cn/xsfw/sys/swmjbxxapp/*default/index.do')
    # always 502, ignore this
    #ignore.raise_for_status()

    requestSession.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    })
    ignore = requestSession.post(
        url='http://stu.hfut.edu.cn/xsfw/sys/emapfunauth/welcomeAutoIndex.do')
    ignore.raise_for_status()

    requestSession.headers.pop('Content-Type')
    requestSession.headers.pop('X-Requested-With')
    ignore = requestSession.get(
        url='http://stu.hfut.edu.cn/xsfw/sys/emapfunauth/casValidate.do',
        params={'service': '/xsfw/sys/swmjbxxapp/*default/index.do'})
    ignore.raise_for_status()

    requestSession.headers.update({
        'X-Requested-With':
        'XMLHttpRequest',
        'Referer':
        'http://stu.hfut.edu.cn/xsfw/sys/swmjbxxapp/*default/index.do'
    })
    ignore = requestSession.get(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/emappagelog/config/swmxsyqxxsjapp.do')
    ignore.raise_for_status()

    # get role config
    requestSession.headers.pop('X-Requested-With')
    requestSession.headers.update(
        {'Content-Type': 'application/x-www-form-urlencoded'})
    configData = {
        'data':
        json.dumps({
            'APPID': '5811260348942403',
            'APPNAME': 'swmxsyqxxsjapp'
        })
    }
    roleConfigResponse = requestSession.post(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swpubapp/MobileCommon/getSelRoleConfig.do',
        data=configData)
    roleConfigResponse.raise_for_status()

    roleConfigJson = roleConfigResponse.json()
    if roleConfigJson['code'] != '0':
        # :(
        logger.info(f'处理roleConfig时发生错误：{roleConfigJson["msg"]}')
        return False

    # get menu info
    menuInfoResponse = requestSession.post(
        url= 'http://stu.hfut.edu.cn/xsfw/sys/swpubapp/MobileCommon/getMenuInfo.do',
        data=configData)
    menuInfoResponse.raise_for_status()

    menuInfoJson = menuInfoResponse.json()

    if menuInfoJson['code'] != '0':
        # :(
        logger.info(f'处理menuInfo时发生错误：{menuInfoJson["msg"]}')
        return False

    todayDateStr = "%.2d-%.2d-%.2d" % time.localtime()[:3]

    # if submitted
    ifSubmitted = requestSession.post(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/judgeTodayHasData.do',
        data={'data': json.dumps({'TBSJ': todayDateStr})})
    ifSubmittedJson = ifSubmitted.json()
    if not ifSubmittedJson.get('data', None):
        return 'login_failed'
    if len(ifSubmittedJson['data']) == 1:
        logger.info('今天已经打过卡了，处理结束')
        return 'have_done'

    # get setting... for what?
    requestSession.headers.pop('Content-Type')
    settingResponse = requestSession.get(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/getSetting.do',
        data={'data': ''})
    settingResponse.raise_for_status()

    settingJson = settingResponse.json()

    # get the form submitted last time
    requestSession.headers.update(
        {'Content-Type': 'application/x-www-form-urlencoded'})
    lastSubmittedResponse = requestSession.post(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/getStuXx.do',
        data={'data': json.dumps({'TBSJ': todayDateStr})})
    lastSubmittedResponse.raise_for_status()

    lastSubmittedJson = lastSubmittedResponse.json()

    if lastSubmittedJson['code'] != '0':
        # something wrong with the form submitted last time
        logger.info('上次填报提交的信息出现了问题，本次最好手动填报提交。')
        return 'need_self'

    studentKeyResponse = requestSession.post(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/studentKey.do',
        data={})
    studentKeyJson = studentKeyResponse.json()

    # generate today's form to submit
    submitDataToday = lastSubmittedJson['data']
    submitDataToday.update({
        'BY1': '1',
        'DFHTJHBSJ': '',
        'DZ_SFSB': '1',
        'DZ_TBDZ': location,
        'GCJSRQ': '',
        'GCKSRQ': '',
        'TBSJ': todayDateStr,
        'studentKey': studentKeyJson['data']['studentKey']
    })

    paramKeyResponse = requestSession.post(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/setCode.do',
        data={'data': json.dumps(submitDataToday)})
    paramKeyJson = paramKeyResponse.json()

    # try to submit
    submitResponse = requestSession.post(
        url=
        'http://stu.hfut.edu.cn/xsfw/sys/swmxsyqxxsjapp/modules/mrbpa/saveStuXx.do',
        data={'data': json.dumps(paramKeyJson['data'])})
    submitResponse.raise_for_status()

    submitResponseJson = submitResponse.json()

    if submitResponseJson['code'] != '0':
        # failed
        logger.info(f'提交时出现错误：{submitResponseJson["msg"]}')
        return False

    # succeeded
    logger.info('提交成功')
    requestSession.headers.pop('Referer')
    requestSession.headers.pop('Content-Type')
    return 'success'