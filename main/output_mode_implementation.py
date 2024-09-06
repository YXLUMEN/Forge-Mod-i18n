import json
import os
import shutil
import zipfile
from pathlib import Path

import json5

from file_process import FileProcess
from utilities import scaner_file_gen


def official_translation(target_lang: str, default_lang: str, output_dir: str) -> None:
    helper = FileProcess(target_language=target_lang, default_language=default_lang, output_dir=output_dir)

    for file_path in scaner_file_gen('input/mods'):
        if not helper.verify_mod(file_path):
            continue
        for i in helper.current_zip_object.namelist():
            helper.write_file(i)


def resource_pack_translation(target_lang: str, default_lang: str, output_dir: str) -> None:
    helper = FileProcess(target_language=target_lang, default_language=default_lang, output_dir=output_dir)

    for file_path in scaner_file_gen('input/resources'):
        print(f'当前资源包:{file_path}')
        # 如果资源包为压缩文件,则调用 verify_resource_pack_zip()
        if zipfile.is_zipfile(file_path):
            for i in helper.verify_resource_pack_zip(file_path):
                if i:
                    helper.write_file(i)
        # 如果资源包为文件夹,调用verify_resource_pack_dir(),并在此函数中处理文件
        elif os.path.isdir(file_path):
            if not helper.verify_resource_pack_dir(file_path):
                continue

            for mod_path in scaner_file_gen(f'{file_path}/assets'):
                mod_id: str = mod_path.split('\\')[-1]

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


def replace_official_with_resource_pack(target_lang: str, default_lang: str, output_dir: str) -> None:
    resource_pack_translation(target_lang, default_lang, output_dir)

    temp_dir = Path(f'{output_dir}/temp')
    if temp_dir.is_dir():
        temp_dir.rename(f'{output_dir}/re_temp')

    official_translation(target_lang, default_lang, output_dir)

    for mod_path in temp_dir.iterdir():
        mod_id: str = mod_path.name
        try:
            with open(f'{output_dir}/temp/{mod_id}/{target_lang}.json', 'rb') as f:
                official_file = json.load(f)

            with open(f'{output_dir}/re_temp/{mod_id}/{target_lang}.json', 'rb') as f:
                resource_file = json.load(f)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f'官方翻译替换 \033[31m出现错误:\033[0m {e}')
            continue

        # 存在的资源包翻译将替换官方翻译
        official_file.update(resource_file)
        with open(f'{output_dir}/temp/{mod_id}/{target_lang}.json', 'w', encoding='utf-8') as latest:
            json.dump(official_file, latest, ensure_ascii=False, indent=4)

    shutil.rmtree(f'{output_dir}/re_temp', ignore_errors=True)


def output_mod_id(output_dir) -> None:
    helper = FileProcess()

    with open(f'{output_dir}/ModList.txt', 'w+', encoding='utf-8') as f:
        for file_path in scaner_file_gen('input/mods'):
            f.write(f'{helper.verify_mod(file_path)}\n')


def mix_lang(target_lang: str, default_lang: str, output_dir: str):
    for mod_path in scaner_file_gen(f'{output_dir}/temp'):
        default_lang_dir: str = f'{mod_path}/{default_lang}.json'
        target_lang_dir: str = f'{mod_path}/{target_lang}.json'

        try:
            with (default_lang_dir, 'rb') as f:
                default_lang_file: dict = json.load(f)

            with open(target_lang_dir, 'rb') as f:
                target_lang_file: dict = json.load(f)
        except FileNotFoundError as e:
            print(f'mixLang: 处理的 -> ' + mod_path.split('\\')[-1] + ' 没有: ' + str(e).split('/')[-1])
            continue
        except json.decoder.JSONDecodeError:
            # Json5 似乎处理速度很慢
            print('\033[33m使用json5处理文件\033[0m -> ' + mod_path.split('/')[-1])
            try:
                with (default_lang_dir, 'rb') as f:
                    default_lang_file: dict = json5.load(f)

                with open(target_lang_dir, 'rb') as f:
                    target_lang_file: dict = json5.load(f)
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

        with open(f'{mod_path}/mix.json', 'w', encoding='utf-8') as mix_file:
            json.dump(default_lang_file, mix_file, ensure_ascii=False, indent=4)


def sort_files(target_lang: str, default_lang: str, output_dir: str):
    has = Path(f'{output_dir}/hasTranslation')
    need = Path(f'{output_dir}/needTranslating')
    withoutE = Path(f'{output_dir}/withoutEnglishLang')
    without = Path(f'{output_dir}/withoutLang')

    has.mkdir(parents=True, exist_ok=True)
    need.mkdir(parents=True, exist_ok=True)
    withoutE.mkdir(parents=True, exist_ok=True)
    without.mkdir(parents=True, exist_ok=True)

    all_files = Path(f'{output_dir}/temp/')
    all_files.mkdir(parents=True, exist_ok=True)
    try:
        for each_file in all_files.iterdir():
            default_lang_file: str = f'{each_file}/{default_lang}.json'
            target_lang_file: str = f'{each_file}/{target_lang}.json'

            if os.access(default_lang_file, os.R_OK):
                if os.access(target_lang_file, os.R_OK):
                    shutil.move(each_file, has)
                else:
                    shutil.move(each_file, need)

            elif os.access(target_lang_file, os.R_OK):
                shutil.move(each_file, withoutE)
            else:
                shutil.move(each_file, without)
    except shutil.Error:
        pass
    shutil.rmtree(all_files, ignore_errors=True)
