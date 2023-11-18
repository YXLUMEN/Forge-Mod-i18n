import json
import os
import shutil

from file_process import FileProcess
from utilities import scaner_file_gen

count = 2
while count:
    try:
        import json5

        break
    except Exception as E:
        print(E)
        os.system('pip install json5')
        count -= 1
if count <= 0:
    print("Json5 库似乎未成功安装,可能无法处理部分文件")
del count


def output_official_translation(target_lang):
    helper = FileProcess(target_language=target_lang)
    for file_path in scaner_file_gen('input/mods'):
        helper.alter_zip_object(file_path)
        if not helper.verify_mod():
            continue
        for i in helper.current_zip_object.namelist():
            helper.write_file(i)


def output_resource_pack_translation(target_lang):
    helper = FileProcess(target_language=target_lang)
    ...


def replace_official_with_resource_pack(target_lang):
    helper = FileProcess(target_language=target_lang)
    ...


def output_mod_id():
    helper = FileProcess()
    f = open('output/ModList.txt', 'w+', encoding='utf-8')
    for file_path in scaner_file_gen('input/mods'):
        helper.alter_zip_object(file_path)
        f.write(f'{helper.verify_mod()}\n')


def mix_lang(target_lang='zh_cn', default_lang='en_us'):
    for mod_path in scaner_file_gen('output/temp'):
        # mod_id = i.split('\\')[-1]
        try:
            default_lang_file = open(f'{mod_path}/{default_lang}.json', 'rb')
            default_lang_file = json.load(default_lang_file)
            target_lang_file = open(f'{mod_path}/{target_lang}.json', 'rb')
            target_lang_file = json.load(target_lang_file)
        except FileNotFoundError as e:
            print(f'mixLang: 处理的 -> ' + mod_path.split('/')[-1] + ' 没有: ' + str(e).split('/')[-1])
            continue
        except json.decoder.JSONDecodeError:
            print('\033[33m使用json5处理文件\033[0m -> ' + mod_path.split('/')[-1])
            try:
                default_lang_file = open(f'{mod_path}/{default_lang}.json', 'rb')
                default_lang_file = json5.load(default_lang_file)
                target_lang_file = open(f'{mod_path}/{target_lang}.json', 'rb')
                target_lang_file = json5.load(target_lang_file)
            except FileNotFoundError:
                continue
            except ImportError:
                print(f'\033[31mJson5 未安装,无法处理\033[0m -> ' + mod_path.split('/')[-1])
                continue
            except Exception as e:
                print(f'\033[31mjson5 处理出错: {e}\033[0m -> ' + mod_path.split('/')[-1])
                continue
        except Exception as e:
            print(f'Mix Language \033[31m出现错误:\033[0m {e} -> ' + mod_path.split('/')[-1])
            continue

        default_lang_file.update(target_lang_file)
        mix_file = open(f'{mod_path}/mix.json', 'w', encoding='utf-8')
        json.dump(default_lang_file, mix_file, ensure_ascii=False, indent=4)


def sort_files(default='en_us', target='zh_cn'):
    if not os.path.exists('output/hasTranslation'):
        os.makedirs('output/hasTranslation')
    if not os.path.exists('output/needTranslating'):
        os.makedirs('output/needTranslating')
    if not os.path.exists('output/withoutEnglishLang'):
        os.makedirs('output/withoutEnglishLang')
    if not os.path.exists('output/withoutLang'):
        os.makedirs('output/withoutLang')

    for each_file in scaner_file_gen('output/temp/'):
        default_lang = f'{each_file}/{default}.json'
        target_lang = f'{each_file}/{target}.json'
        if os.access(default_lang, os.R_OK):
            if os.access(target_lang, os.R_OK):
                shutil.move(each_file, 'output/hasTranslation/')
            else:
                shutil.move(each_file, 'output/needTranslating/')
        elif os.access(target_lang, os.R_OK):
            shutil.move(each_file, 'output/withoutEnglishLang/')
        else:
            shutil.move(each_file, 'output/withoutLang/')

    if os.access('output/temp', os.W_OK):
        shutil.rmtree('output/temp', ignore_errors=True)
