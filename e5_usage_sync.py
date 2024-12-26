# 本程序及对应的配置文件均为 ChatGPT 编写

import sys
import requests
import json
import humanize
import yaml
import logging
import argparse
import datetime

# 设置命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yml', help='指定配置文件路径')
parser.add_argument('--output', default='output.md', help='指定输出文件路径')
parser.add_argument('--input', default='template.md', help='指定输入文件路径')
args = parser.parse_args()

# 设置日志输出格式和级别
logging.basicConfig(level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S',
                    format='[%(asctime)s] [%(levelname)s] %(message)s')

# 从配置文件中读取用户配置
try:
    with open(args.config, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
except Exception as e:
    logging.error('读取配置文件失败，请检查文件路径和文件格式')
    logging.error(f'错误信息：{e}')
    sys.exit(1)

# 检查配置文件中是否包含必要的参数
if 'client_id' not in config or 'client_secret' not in config:
    logging.error('配置文件中缺少必要的参数，请添加 client_id 和 client_secret')
    sys.exit(1)

if 'refresh_tokens' not in config or not config['refresh_tokens']:
    logging.error('配置文件中没有找到有效的 refresh_token，请添加至少一个 OneDrive 帐户并授权应用程序')
    sys.exit(1)

# 读取配置文件中的参数
client_id = config['client_id']
client_secret = config['client_secret']
refresh_tokens = config['refresh_tokens']
refresh_tokens.append({"name": "total"})

# 用于存储不同账户的使用情况，格式为 {token名称: 占用大小}
usage_dict = {}


# 获取access_token
def get_access_token(refresh_token):
    url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default',
        'refresh_token': refresh_token
    }
    response = requests.post(url, headers=headers, data=data)
    access_token = json.loads(response.text)['access_token']
    return access_token



# 获取 OneDrive storage usage
def get_usage(access_token, name):
    url = 'https://graph.microsoft.com/v1.0/me/drive'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        usage = json.loads(response.text)['quota']['used']
        logging.info(f'{name} 的 OneDrive 使用情况为：{humanize.naturalsize(usage, binary=True, format="%.3f")}')
        return usage
    except Exception as e:
        logging.error(f'获取 {name} OneDrive 使用情况失败：{e}')


# 处理 refresh tokens 并获取 OneDrive uses
total_usage = 0
try:
    for item in refresh_tokens:
        refresh_token = item['token']
        name = item['name']
        access_token = get_access_token(refresh_token)
        usage = get_usage(access_token, name)
        usage_dict[name] = usage
        total_usage += usage
        logging.info(f'{name} 的 OneDrive 使用情况获取成功')
except Exception as e:
    logging.error(f'获取 OneDrive 使用情况失败：{e}')
usage_dict["total"] = total_usage
logging.info(usage_dict)

# 读取模板文件内容
with open(args.input, 'r', encoding='utf-8') as input_file:
    input_content = input_file.read()

# 替换模板文件中的占位符为实际的 OneDrive 使用情况
input_content = input_content.replace(f'[modifydate_e5usagesync]', datetime.datetime.now().strftime("%Y/%m/%d"))
for name in usage_dict:
    usage = usage_dict.get(name)
    usage_str = humanize.naturalsize(usage, binary=True, format="%.3f")
    # 将模板文件中的占位符替换为实际的 OneDrive 使用情况
    input_content = input_content.replace(f'[{name}_odusage]', usage_str)
    input_content = input_content.replace(f'[{name}_odusage_urlenc]', usage_str.replace(" ", "%20"))

# 将处理后的模板文件内容写入输出文件
with open(args.output, 'w', encoding='utf-8') as output_file:
    output_file.write(input_content)
    logging.info('文件更新成功')