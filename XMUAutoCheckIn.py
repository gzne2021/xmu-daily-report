from selenium import webdriver
# import selenium.webdriver.support.ui as ui
import os
import time
import logging

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import smtplib

# from selenium.webdriver.chrome.options import Options
# chrome_options = Options()
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')
# chrome_options.add_argument('--headless')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Login_URL = 'https://xmuxg.xmu.edu.cn/login'
Login_URL = 'https://ids.xmu.edu.cn/authserver/login?service=https://xmuxg.xmu.edu.cn/login/cas/xmu'
Checkin_URL = 'https://xmuxg.xmu.edu.cn/app/214'


def checkin(username, passwd):
    driver = webdriver.Chrome()
    
    logger.info("进入登录页面")
    driver.get(Login_URL)
    driver.maximize_window()

    # 这里直接定位到登录页面了，所以下面步骤不需要
#     logintab = driver.find_element_by_class_name('login-tab')
#     login = driver.find_element_by_xpath("//*[@class='buttonBox']/button[2]")
#     login.click()

    # 输入用户名密码
    time.sleep(1)
    a = driver.find_element_by_id('username')
    b = driver.find_element_by_id('password')
    a.send_keys(username)
    b.send_keys(passwd)

    # 点击登录，相当玄学，有可能提示找不到该元素，那时候就手动打卡吧
    run = True
    now = time.time()
    while run:
        try:
            login = driver.find_element_by_xpath("//*[@id='casLoginForm']/p[5]")
            login.click()
            logger.info("已定位到元素")
            break
        except:
            logger.info("还未定位到元素!")
            if (time.time() - now) > 10:
                run = False
                return '运气不好，遇上了玄学问题'

    # 重新跳转到打卡页面
    driver.get(Checkin_URL)

    now = time.time()
    while True:
        try:
            time.sleep(1)
            form = driver.find_element_by_xpath("//*[@class='gm-scroll-view']/div[2]")
            form.click()
            break
        except:
            time.sleep(1)
            logger.info("获取\"我的表单\"失败，重试中")
            if (time.time() - now) > 10:
                run = False
                return '获取\"我的表单\"失败'

    now = time.time()
    while True:
        try:
            time.sleep(1)
            text = driver.find_element_by_xpath("//*[@id='select_1582538939790']/div[1]/div[1]/span[1]").text
            break
        except:
            time.sleep(1)
            logger.info("查找框内文本失败，重试中")
            if (time.time() - now) > 10:
                run = False
                return '查找框内文本失败'

    if text == '请选择':
        now = time.time()
        while True:
            try:
                # 定位填“是”的页面
                yes = driver.find_element_by_xpath("//*[@id='select_1582538939790']/div[1]/div[1]")
                yes.click()
                break
            except:
                time.sleep(1)
                logger.info("点击\"是\"失败，重试中")
                if (time.time() - now) > 10:
                    run = False
                    return '点击\"是\"失败'

        now = time.time()
        while True:
            try:
                yes = driver.find_element_by_xpath("//*[@class='v-select-cover']/ul[1]/div[1]")
                yes.click()
                break
            except:
                time.sleep(1)
                logger.info("确认\"是\"失败，重试中")
                if (time.time() - now) > 10:
                    return '确认\"是\"失败'
        save = driver.find_element_by_xpath("//*[@class='preview-container']/div[1]/div[1]/span[1]/span[1]")
        save.click()

        time.sleep(1)
        # 保存确定
        driver.switch_to_alert().accept()
        time.sleep(3)
        output = '打卡成功'
    elif text == '是 Yes':
        output = '已打卡'
    else:
        output = '打卡失败！！！'
    driver.close()
    return output


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def sendMail(from_addr, mail_pwd, to_addr, smtp_server, output):
    msg = MIMEText(output, 'plain', 'utf-8')
    msg['From'] = _format_addr('XMU每日打卡 <%s>' % from_addr)
    msg['To'] = _format_addr('你可真是怠惰呢 <%s>' % to_addr)
    msg['Subject'] = Header('每日打卡结果反馈', 'utf-8').encode()

    server = smtplib.SMTP_SSL(smtp_server, 465)
    server.set_debuglevel(1)
    server.login(from_addr, mail_pwd)
    logger.info("邮箱登录成功")
    server.sendmail(from_addr, [to_addr], msg.as_string())
    logger.info("邮件发送成功")
    server.quit()

def main():
    # XMU统一身份认证用户名密码
    username = os.environ['USERNAME'].split('#')
    passwd = os.environ['PASSWD'].split('#')

    # 邮件设置信息，由于从secrets获取到的是list，这里进一步转string
    from_addr = ""
    from_addr = from_addr.join(os.environ['FROM_ADDR'].split('#'))
    mail_pwd = ""
    mail_pwd = mail_pwd.join(os.environ['MAIL_PWD'].split('#'))
    to_addr = ""
    to_addr = to_addr.join(os.environ['TO_ADDR'].split('#'))
    smtp_server = ""
    smtp_server = smtp_server.join(os.environ['SMTP_SERVER'].split('#'))

    output = checkin(username, passwd)
    logger.info(output)
    sendMail(from_addr, mail_pwd, to_addr, smtp_server, output)


if __name__ == '__main__':
    main()
