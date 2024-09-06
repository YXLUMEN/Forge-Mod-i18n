import json
import os
from typing import TextIO


def reset_conf() -> dict:
    default: dict = {
        'output_dir': 'output',
        'default_lang': 'en_us',
        'target_lang': 'zh_cn',
    }
    with open('./i18nconf.json', 'w', encoding='utf-8') as f:
        json.dump(default, f, ensure_ascii=False, indent=4)

    return default


def read_conf() -> dict:
    if not os.access('./i18nconf.json', os.R_OK):
        raise FileNotFoundError('无配置文件,或配置文件不存在')

    conf: TextIO = open('./i18nconf.json', 'r', encoding='utf-8')
    try:
        conf_json: dict = json.load(conf)
        conf_dic: dict = {
            'output_dir': conf_json['output_dir'],
            'default_lang': conf_json['default_lang'],
            'target_lang': conf_json['target_lang'],
        }
    except KeyError:
        print('\033[31m配置文件缺少键值:\033[0m ', end='')
        raise
    except json.decoder.JSONDecodeError:
        print('\033[31m配置文件格式错误:\033[0m ')
        raise
    finally:
        conf.close()
    return conf_dic
