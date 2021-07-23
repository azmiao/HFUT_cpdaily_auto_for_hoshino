
## 注意

若其他学校同学需要可自行更改

打卡脚本来自@RayAlto
传送门：https://github.com/RayAlto/HFUT-cpdaily-auto

本人将该脚本编写成HoshinoBot的插件，并在原来的基础上添加了邮件提醒和其他交互小功能，可实现在QQ群里管理所有信息和自动或手动打卡，然后去除了server酱功能

## 代码比较冗杂，望见谅

该插件适用于合肥工业大学，今日校园里的疫情信息收集，就是那个点开上面显示每日报平安的那个，其他学校可自己尝试更改，目前今日校园打卡有两个系统，如果是另一个今日校园打卡系统，可看我另一个仓库，里面有写子墨大佬的脚本来源

## 更新日志

21-07-23    v1.4    学号对应的QQ号可以删除自己的信息，无需管理员操作。并修改一些print为printlog(应该会减少一点hoshino占用问题，不会出现其他问题吧？)

21-05-19    v1.3    修复部分代码，并调整了消息，防止刷屏

21-03-25    v1.2    新增单独打卡仅限QQ号本人或者维护组，维护组QQ可以手动在`submain.py`最上面进行设置

21-03-21    v1.1    新增单独打卡功能，新增自动撤回添加用户的确认消息功能，感谢群里的大佬们教我抄代码（

21-03-20    v1.0    first commit

## HFUT_cpdaily_auto_for_hoshino

一个适用hoshinobot的打卡插件

本插件仅供学习研究使用，插件免费，禁止用于任何收费代挂，否则一切后果自己承担

## 项目地址：
https://github.com/azmiao/HFUT_cpdaily_auto_for_hoshino

## 功能
```
命令&功能：

[打卡帮助] 查看帮助

[今日校园初始化] 初始化用户信息（仅限超级管理员）

[添加用户 学号 密码 QQ] 添加新用户  (注意参照格式：添加用户 2018214233 xxxaaa 23332)

[删除用户 学号] 删除信息（仅限本人或超级管理员）

[全员打卡] 今日校园全员手动打卡（仅限超级管理员）

[单独打卡 2018xxxxxx] 顾名思义

{自动打卡} 该功能无需命令，开启后每天14点15分自动完成

[打卡用户列表] 看所有用户
```
## 简单食用教程：

可看下方链接：

https://www.594594.xyz/2021/03/20/HFUT_cpdaily_auto_for_hoshino/

或本页面：

1. git clone本插件：

在 HoshinoBot\hoshino\modules 目录下使用以下命令拉取本项目
```
git clone https://github.com/azmiao/HFUT_cpdaily_auto_for_hoshino
```

2. 安装依赖：

到HoshinoBot\hoshino\modules\HFUT_cpdaily_auto_for_hoshino目录下，打开powershell运行
```
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. 打开HFUT_cpdaily_auto_for_hoshino文件夹下的`__init__.py`文件，将最上方要填写的参数填好。然后在`submain.py`最上面进行设置超级管理员QQ

4. 在 HoshinoBot\hoshino\config\ `__bot__.py` 文件的 MODULES_ON 加入 'HFUT_cpdaily_auto_for_hoshino'

然后重启 HoshinoBot即可使用

5. 手动开启功能：（为了防止不需要的群误触）

在某个群里发消息输入下文以开启该群的主功能（必须开）
```
开启 cpdaily-HFUT
```
在某个群里发消息输入下文以开启该群的初始化功能（必须开）
```
开启 cpdaily-HFUT-init
```
在某个群里发消息输入下文以开启自动打卡功能（想每天14点15分自动完成的开，注意该功能最多只能在一个群开启，否则会触发多个任务）
```
开启 cpdaily-HFUT-auto
```

可以通过发消息输入"lssv"查看这几个功能前面是不是⚪来确认是否开启成功

6. 到一个开启cpdaily-HFUT-init功能的群里，直接发送'今日校园初始化'进行初始化，若无反应请看报错信息

7. 初始化完成后就可以正常使用功能了，其他功能可以直接发送'打卡帮助'看