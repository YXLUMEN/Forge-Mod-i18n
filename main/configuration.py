import json
import os


def reset_conf():
    default = {
        'output_dir': 'output',
        'default_lang': 'en_us',
        'target_lang': 'zh_cn',
    }
    conf = open('./i18nconf.json', 'w')
    json.dump(default, conf, ensure_ascii=False, indent=4)
    conf.close()

    return default


def read_conf():
    if not os.access('./i18nconf.json', os.R_OK):
        raise FileNotFoundError('无配置文件,或配置文件不存在')
    conf = open('./i18nconf.json', 'r')
    try:
        conf = json.load(conf)
        conf_dic = {
            'output_dir': conf['output_dir'],
            'default_lang': conf['default_lang'],
            'target_lang': conf['target_lang'],
        }
    except KeyError:
        print('\033[31m配置文件缺少键值:\033[0m ', end='')
        raise
    except json.decoder.JSONDecodeError:
        print('\033[31m配置文件格式错误:\033[0m ')
        raise
    return conf_dic
