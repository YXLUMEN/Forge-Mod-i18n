import os
import shutil
from json import decoder

import configuration
import output_mode_implementation
from utilities import selection


def main(select_mode):
    # Load conf
    try:
        conf = configuration.read_conf()
    except FileNotFoundError:
        conf = configuration.reset_conf()
    except KeyError as e:
        print(e)
        if selection('是否重置配置? (y/n) ') == 'n':
            return
        conf = configuration.reset_conf()
    except decoder.JSONDecodeError as e:
        print(e)
        if selection('是否重置配置? (y/n) ') == 'n':
            return
        conf = configuration.reset_conf()
    except Exception as e:
        print(f'出现错误: {e}')
        return
    default_lang = conf['default_lang']
    target_lang = conf['target_lang']
    output_dir = conf['output_dir']

    # 清空输出
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir)

    if select_mode == '4':
        output_mode_implementation.output_mod_id(output_dir)
        return

    print(f'\033[32m当前目标语言: {target_lang}\033[0m')
    try:
        if select_mode == '1':
            output_mode_implementation.output_official_translation(target_lang, default_lang, output_dir)
        elif select_mode == '2':
            output_mode_implementation.output_resource_pack_translation(target_lang, default_lang, output_dir)
        elif select_mode == '3':
            output_mode_implementation.replace_official_with_resource_pack(target_lang, default_lang, output_dir)
    except Exception as e:
        print(e)

    select = selection('\033[1m是否将默认语言与目标语言混合? (y/n):\033[0m ')
    if select == 'y':
        output_mode_implementation.mix_lang(target_lang, default_lang, output_dir)

    output_mode_implementation.sort_files(target_lang, default_lang, output_dir)


if __name__ == '__main__':
    while True:
        # 不在这里创建文件夹会出现怪问题,也许是更新问题
        if not os.path.exists('input/mods'):
            os.makedirs('input/mods')
        if not os.path.exists('input/resources'):
            os.makedirs('input/resources')

        print(
            '-----'
            '\n1.输出官方目标语音和英文语言文件'
            '\n2.输出资源包目标语音和英文语言文件'
            '\n3.使用资源包目标语音替换官方翻译'
            '\n4.输出Mod Id'
            '\nq.退出'
            '\n-----',
            end='')
        selectMode = selection('\n\r\033[1m选择功能:\033[0m ', ('1', '2', '3', '4', 'q'))
        if selectMode.lower() == 'q':
            break

        main(selectMode)
    print('程序退出.')
    os.system('pause')
