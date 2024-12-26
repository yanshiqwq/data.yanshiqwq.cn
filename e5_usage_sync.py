# �����򼰶�Ӧ�������ļ���Ϊ ChatGPT ��д

import sys
import requests
import json
import humanize
import yaml
import logging
import argparse
import datetime

# ���������в���
parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yml', help='ָ�������ļ�·��')
parser.add_argument('--output', default='output.md', help='ָ������ļ�·��')
parser.add_argument('--input', default='template.md', help='ָ�������ļ�·��')
args = parser.parse_args()

# ������־�����ʽ�ͼ���
logging.basicConfig(level=logging.INFO, datefmt='%Y/%m/%d %H:%M:%S',
                    format='[%(asctime)s] [%(levelname)s] %(message)s')

# �������ļ��ж�ȡ�û�����
try:
    with open(args.config, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
except Exception as e:
    logging.error('��ȡ�����ļ�ʧ�ܣ������ļ�·�����ļ���ʽ')
    logging.error(f'������Ϣ��{e}')
    sys.exit(1)

# ��������ļ����Ƿ������Ҫ�Ĳ���
if 'client_id' not in config or 'client_secret' not in config:
    logging.error('�����ļ���ȱ�ٱ�Ҫ�Ĳ���������� client_id �� client_secret')
    sys.exit(1)

if 'refresh_tokens' not in config or not config['refresh_tokens']:
    logging.error('�����ļ���û���ҵ���Ч�� refresh_token�����������һ�� OneDrive �ʻ�����ȨӦ�ó���')
    sys.exit(1)

# ��ȡ�����ļ��еĲ���
client_id = config['client_id']
client_secret = config['client_secret']
refresh_tokens = config['refresh_tokens']
refresh_tokens.append({"name": "total"})

# ���ڴ洢��ͬ�˻���ʹ���������ʽΪ {token����: ռ�ô�С}
usage_dict = {}


# ��ȡaccess_token
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



# ��ȡ OneDrive storage usage
def get_usage(access_token, name):
    url = 'https://graph.microsoft.com/v1.0/me/drive'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        usage = json.loads(response.text)['quota']['used']
        logging.info(f'{name} �� OneDrive ʹ�����Ϊ��{humanize.naturalsize(usage, binary=True, format="%.3f")}')
        return usage
    except Exception as e:
        logging.error(f'��ȡ {name} OneDrive ʹ�����ʧ�ܣ�{e}')


# ���� refresh tokens ����ȡ OneDrive uses
total_usage = 0
try:
    for item in refresh_tokens:
        refresh_token = item['token']
        name = item['name']
        access_token = get_access_token(refresh_token)
        usage = get_usage(access_token, name)
        usage_dict[name] = usage
        total_usage += usage
        logging.info(f'{name} �� OneDrive ʹ�������ȡ�ɹ�')
except Exception as e:
    logging.error(f'��ȡ OneDrive ʹ�����ʧ�ܣ�{e}')
usage_dict["total"] = total_usage
logging.info(usage_dict)

# ��ȡģ���ļ�����
with open(args.input, 'r', encoding='utf-8') as input_file:
    input_content = input_file.read()

# �滻ģ���ļ��е�ռλ��Ϊʵ�ʵ� OneDrive ʹ�����
input_content = input_content.replace(f'[modifydate_e5usagesync]', datetime.datetime.now().strftime("%Y/%m/%d"))
for name in usage_dict:
    usage = usage_dict.get(name)
    usage_str = humanize.naturalsize(usage, binary=True, format="%.3f")
    # ��ģ���ļ��е�ռλ���滻Ϊʵ�ʵ� OneDrive ʹ�����
    input_content = input_content.replace(f'[{name}_odusage]', usage_str)
    input_content = input_content.replace(f'[{name}_odusage_urlenc]', usage_str.replace(" ", "%20"))

# ��������ģ���ļ�����д������ļ�
with open(args.output, 'w', encoding='utf-8') as output_file:
    output_file.write(input_content)
    logging.info('�ļ����³ɹ�')