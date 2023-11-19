import os
import shutil

import output_mode_implementation
from utilities import selection

if __name__ == '__main__':
    while True:
        if not os.path.exists('input/mods'):
            os.makedirs('input/mods')
        if not os.path.exists('input/resources'):
            os.makedirs('input/resources')
        shutil.rmtree('output/', ignore_errors=True)
        os.makedirs('output')

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
        if selectMode == '4':
            output_mode_implementation.output_mod_id()
            continue

        selectTargetLang = input('\033[34m选择目标语言,例如 zh_cn:\033[0m ')
        if selectTargetLang == '':
            selectTargetLang = 'zh_cn'
        print(f'\033[32m当前目标语言: {selectTargetLang}\033[0m')
        try:
            if selectMode == '1':
                output_mode_implementation.output_official_translation(selectTargetLang)
            elif selectMode == '2':
                output_mode_implementation.output_resource_pack_translation(selectTargetLang)
            elif selectMode == '3':
                output_mode_implementation.replace_official_with_resource_pack(selectTargetLang)
        except Exception as e:
            print(e)

        select = selection('\033[1m是否将默认语言与目标语言混合? (y/n):\033[0m ')
        if select == 'y':
            output_mode_implementation.mix_lang()

        output_mode_implementation.sort_files()
    os.system('pause')
    print('程序退出.')
