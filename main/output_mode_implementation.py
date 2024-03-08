import json
import os
import shutil
import zipfile

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


# MAX_THREAD = 2


def output_official_translation(target_lang: str, default_lang: str, output_dir: str):
    helper = FileProcess(target_language=target_lang, default_language=default_lang, output_dir=output_dir)
    for file_path in scaner_file_gen('input/mods'):
        if not helper.verify_mod(file_path):
            continue
        for i in helper.current_zip_object.namelist():
            helper.write_file(i)


def output_resource_pack_translation(target_lang: str, default_lang: str, output_dir: str):
    helper = FileProcess(target_language=target_lang, default_language=default_lang, output_dir=output_dir)
    for file_path in scaner_file_gen('input/resources'):
        print(f'当前资源包:{file_path}')
        # 如果资源包为压缩文件,则调用 verify_resource_pack_zip()
        if zipfile.is_zipfile(file_path):
            for i in helper.verify_resource_pack_zip(file_path):
                helper.write_file(i)
        # 如果资源包为文件夹,调用verify_resource_pack_dir(),并在此函数中处理文件
        elif os.path.isdir(file_path):
            if not helper.verify_resource_pack_dir(file_path):
                continue
            for mod_path in scaner_file_gen(f'{file_path}/assets'):
                mod_id = mod_path.split('\\')[-1]
                if not os.access(f'{mod_path}/lang/{target_lang}.json', os.R_OK):
                    continue
                    # create the output path
                if not os.access(f'{output_dir}/temp/{mod_id}', os.W_OK):
                    os.makedirs(f'{output_dir}/temp/{mod_id}')
                shutil.copy(
                    # abspath() used in here just for a better exception output XD
                    os.path.abspath(f'{mod_path}/lang/{target_lang}.json'),
                    f'{output_dir}/temp/{mod_id}/{target_lang}.json')

        else:
            print('\033[31m未解析的资源包\033[0m -> ' + file_path.split('\\')[-1])


def replace_official_with_resource_pack(target_lang: str, default_lang: str, output_dir: str):
    output_resource_pack_translation(target_lang, default_lang, output_dir)
    if os.path.exists(f'{output_dir}/temp'):
        os.rename(f'{output_dir}/temp', f'{output_dir}/re_temp')
    output_official_translation(target_lang, default_lang, output_dir)
    for mod_path in scaner_file_gen(f'{output_dir}/temp'):
        mod_id = mod_path.split('\\')[-1]
        try:
            official_file = open(f'{output_dir}/temp/{mod_id}/{target_lang}.json', 'rb')
            official_file = json.load(official_file)
            resource_file = open(f'{output_dir}/re_temp/{mod_id}/{target_lang}.json', 'rb')
            resource_file = json.load(resource_file)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f'官方翻译替换 \033[31m出现错误:\033[0m {e}')
            continue
        # 存在的资源包翻译将替换官方翻译
        official_file.update(resource_file)
        latest = open(f'{output_dir}/temp/{mod_id}/{target_lang}.json', 'w', encoding='utf-8')
        json.dump(official_file, latest, ensure_ascii=False, indent=4)
    shutil.rmtree(f'{output_dir}/re_temp', ignore_errors=True)


def output_mod_id(output_dir):
    helper = FileProcess()
    f = open(f'{output_dir}/ModList.txt', 'w+', encoding='utf-8')
    for file_path in scaner_file_gen('input/mods'):
        f.write(f'{helper.verify_mod(file_path)}\n')
    f.close()


def mix_lang(target_lang: str, default_lang: str, output_dir: str):
    for mod_path in scaner_file_gen(f'{output_dir}/temp'):
        # mod_id = i.split('\\')[-1]
        try:
            default_lang_file = open(f'{mod_path}/{default_lang}.json', 'rb')
            default_lang_file = json.load(default_lang_file)
            target_lang_file = open(f'{mod_path}/{target_lang}.json', 'rb')
            target_lang_file = json.load(target_lang_file)
        except FileNotFoundError as e:
            print(f'mixLang: 处理的 -> ' + mod_path.split('\\')[-1] + ' 没有: ' + str(e).split('/')[-1])
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
        mix_file.close()


def sort_files(target_lang: str, default_lang: str, output_dir: str):
    # Translated
    if not os.path.exists(f'{output_dir}/hasTranslation'):
        os.makedirs(f'{output_dir}/hasTranslation')
    # Need translate
    if not os.path.exists(f'{output_dir}/needTranslating'):
        os.makedirs(f'{output_dir}/needTranslating')
    # Without default lang files
    if not os.path.exists(f'{output_dir}/withoutEnglishLang'):
        os.makedirs(f'{output_dir}/withoutEnglishLang')
    # Without any lang files
    if not os.path.exists(f'{output_dir}/withoutLang'):
        os.makedirs(f'{output_dir}/withoutLang')

    for each_file in scaner_file_gen(f'{output_dir}/temp/'):
        default_lang_file = f'{each_file}/{default_lang}.json'
        target_lang_file = f'{each_file}/{target_lang}.json'
        if os.access(default_lang_file, os.R_OK):
            if os.access(target_lang_file, os.R_OK):
                shutil.move(each_file, f'{output_dir}/hasTranslation/')
            else:
                shutil.move(each_file, f'{output_dir}/needTranslating/')
        elif os.access(target_lang_file, os.R_OK):
            shutil.move(each_file, f'{output_dir}/withoutEnglishLang/')
        else:
            shutil.move(each_file, f'{output_dir}/withoutLang/')

    shutil.rmtree(f'{output_dir}/temp', ignore_errors=True)
