import argparse
import json
import multiprocessing
import os
import re
import shutil
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor

parsers = argparse.ArgumentParser()
parsers.add_argument('-op', '--output', required=False, help='输出结果目录')
parsers.add_argument('-l', '--lang', required=False, help='目标语言')
parsers.add_argument('-p', '--process', type=int, required=False, help='进程数')
parsers.add_argument(
    '-s', '--save', default=False, action='store_true', required=False,
    help='是否保存配置;当保存配置时,下次运行将依照配置执行,直到输入参数或更改配置')

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


class LangTransHelper:
    langMix = False

    def __int__(self, output_dir: str, trans: str):
        self.output_dir = output_dir
        self.lang = trans

    # read zip and write them into a file
    def _zip_reader(self, target, file, mod_id):
        if file == f'assets/{mod_id}/lang/en_us.json':
            byte = target.read(file)
            with open(f'{self.output_dir}/has_trans/{mod_id}/en_us.json', 'wb') as f:
                f.write(byte)
        elif file == f'assets/{mod_id}/lang/{self.lang}.json':
            byte = target.read(file)
            with open(f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json', 'wb') as f:
                f.write(byte)

    # extract lang files from jar(zip)
    def extract_mod_lang(self, zip_file):
        """
        Extract lang files from the mod jar (compress file)

        zip_file is a string of compress file's name
        """
        # semaphore
        try:
            zip_f = zipfile.ZipFile(zip_file, 'r')
        except Exception as e:
            print(f'\033[31m解压文件错误:\033[0m {e} -> ' + zip_file.split('\\')[-1])
            return
        # get mod id
        try:
            mod_id = zip_f.read('META-INF/mods.toml')
            mod_id = str(mod_id)
            mod_id = re.findall('modId.?=.?"(.*?)"', mod_id)[0]
        except Exception as e:
            print(f'\033[33m未识别的mod:\033[0m {e} -> ' + zip_file.split('\\')[-1])
            return

        if not os.access(f'{self.output_dir}/has_trans/{mod_id}/', os.W_OK):
            os.makedirs(f'{self.output_dir}/has_trans/{mod_id}/')
        # extract target lang json file and en_us.json
        for file in zip_f.namelist():
            self._zip_reader(zip_f, file, mod_id)

        zip_f.close()
        return mod_id

    def read_resource_pack_lang(self, file: str):
        """

        :param file: Resource pack's name
        :return:

        Check if resource pack is valid,if true copy the lang files
        """
        # resource pack usually is a zip file
        if zipfile.is_zipfile(file):
            try:
                target = zipfile.ZipFile(file, 'r')
            except Exception as e:
                print(f'\033[31m解压文件错误:\033[0m {e} -> ' + file.split('\\')[-1])
                return
            # check pack.mcmeta
            try:
                target.read('pack.mcmeta')
            except Exception as e:
                print(f'\033[33m未找到pack.mcmeta:\033[0m {e} -> ' + file.split('\\')[-1])
                return
            for lang_json in target.namelist():
                # get mod id in pack
                # usually it is the name of folder
                if lang_json.split('/')[0] == 'assets' and len(lang_json.split('/')) > 3:
                    mod = lang_json.split('/')[1]
                    if not os.access(f'{self.output_dir}/has_trans/{mod}/', os.W_OK):
                        os.makedirs(f'{self.output_dir}/has_trans/{mod}/')
                    self._zip_reader(target, lang_json, mod)
            target.close()
        # sometime resource pack is a folder
        elif os.path.isdir(file):
            # check pack.mcmeta
            if not os.access(file + '/pack.mcmeta', os.R_OK):
                print('未找到pack.mcmeta -> ' + file.split('\\')[-1])
                return
            # get all mod folder
            mod_folder = self.scaner_file(f'{file}/assets')
            # process each mod to copy lang files if it's existence
            for each_mod in mod_folder:
                # each_mod is path
                self._read_resource_pack_part_one(each_mod)
        # maybe it's nothing
        else:
            print('\033[31m未解析的资源包\033[0m -> ' + file.split('\\')[-1])
            return

    def _read_resource_pack_part_one(self, each_mod):
        """

        :param each_mod:
        :return:

        Read_resource_pack_lang's part. TO make main function more clean
        """
        # split path to get folder name
        mod_id = each_mod.split('\\')[-1]
        try:
            if not os.access(f'{each_mod}/lang/{self.lang}.json', os.R_OK):
                return
            # output path check
            if not os.access(f'{self.output_dir}/has_trans/{mod_id}', os.W_OK):
                os.makedirs(f'{self.output_dir}/has_trans/{mod_id}')
            shutil.copy(
                # abspath() used in here just for a better exception output XD
                os.path.abspath(f'{each_mod}/lang/{self.lang}.json'),
                f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json')
        except Exception as e:
            print(f'{e} -> {mod_id}')

    # func 1
    def replace_authority_lang(self, first_list: list, second_list: list):
        # for resource pack
        for each_pack in second_list:
            self.read_resource_pack_lang(each_pack)
        os.rename(f'{self.output_dir}/has_trans', f'{self.output_dir}/temp')
        # for mods
        for each_pack in first_list:
            mod_id = self.extract_mod_lang(each_pack)
            try:
                # load as json
                origin = open(f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json', 'rb')
                origin = json.load(origin)
                after = open(f'{self.output_dir}/temp/{mod_id}/{self.lang}.json', 'rb')
                after = json.load(after)
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f'官方翻译替换 \033[31m出现错误:\033[0m {e}')
                continue
            origin.update(after)
            latest = open(f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json', 'w', encoding='utf-8')
            json.dump(origin, latest, ensure_ascii=False, indent=4)

    # sort files
    def sort_files(self, dir_name: str):
        if dir_name is None:
            return
        en = False
        zh = False

        # has lang judge
        if os.access(dir_name + '/en_us.json', os.R_OK):
            en = True
        if os.access(dir_name + f'/{self.lang}.json', os.R_OK):
            zh = True
        # create sort path
        if not os.access(f'{self.output_dir}/need_{self.lang}/', os.W_OK):
            os.makedirs(f'{self.output_dir}/need_{self.lang}/')
        if not os.access(f'{self.output_dir}/no_en_us/', os.W_OK):
            os.makedirs(f'{self.output_dir}/no_en_us/')
        if not os.access(f'{self.output_dir}/no_lang_files/', os.W_OK):
            os.makedirs(f'{self.output_dir}/no_lang_files/')
        # sort those files and move
        if not en and not zh:
            shutil.move(dir_name, f'{self.output_dir}/no_lang_files/')
        elif not en:
            shutil.move(dir_name, f'{self.output_dir}/no_en_us/')
        elif not zh:
            shutil.move(dir_name, f'{self.output_dir}/need_{self.lang}/')

    # mix the lang files
    # func2
    def mix_language_files(self, mod_id):
        if not self.langMix:
            return
        # lang files is correct
        if mod_id is None:
            return
        # load in json
        try:
            en_file = open(f'{mod_id}/en_us.json', 'rb')
            en_file = json.load(en_file)
            zh_file = open(f'{mod_id}/{self.lang}.json', 'rb')
            zh_file = json.load(zh_file)
        except FileNotFoundError as e:
            print(f'mixLang: 处理的 -> ' + mod_id.split('/')[-1] + ' 没有: ' + str(e).split('/')[-1])
            return
        # use json5
        except json.decoder.JSONDecodeError:
            print('\033[33m使用json5处理文件\033[0m -> ' + mod_id.split('/')[-1])
            try:
                en_file = open(f'{mod_id}/en_us.json', 'rb')
                en_file = json5.load(en_file)
                zh_file = open(f'{mod_id}/{self.lang}.json', 'rb')
                zh_file = json5.load(zh_file)
            except FileNotFoundError:
                return
            except ImportError:
                print(f'\033[31mJson5 未安装,无法处理\033[0m -> ' + mod_id.split('/')[-1])
                return
            except Exception as e:
                print(f'\033[31mjson5 处理出错: {e}\033[0m -> ' + mod_id.split('/')[-1])
                return
        except Exception as e:
            print(f'Mix Language \033[31m出现错误:\033[0m {e} -> ' + mod_id.split('/')[-1])
            return
        # mix two lang files in to mix.json
        en_file.update(zh_file)
        mix_file = open(f'{mod_id}/mix.json', 'w', encoding='utf-8')
        json.dump(en_file, mix_file, ensure_ascii=False, indent=4)

    @staticmethod
    def scaner_file(url: str | list | tuple) -> list[str]:
        """
        :param url:
        :return:
        返回输入地址下的所以文件名
        """
        if type(url) == str:
            url = url.split()
        result = []
        for each in url:
            files = os.listdir(each)
            if len(files) <= 0:
                print('\033[33m目录为空\033[0m -> ' + each)
            for f in files:
                result.append(os.path.join(each, f))
        return result


# default params
def initialization_params(args):
    # Default
    output_dir = './output'
    lang_target = 'zh_cn'
    max_process = 1
    # read settings
    if os.access('./conf.json', os.R_OK):
        with open('./conf.json', 'r', encoding='utf-8') as F:
            ini = json.load(F)
        output_dir = ini['output'] if ini['output'] is not None else output_dir
        lang_target = ini['lang'] if ini['lang'] is not None else lang_target
        if ini['process'] is not None and ini['process'] >= 1:
            max_process = ini['process']
            # save settings
    if args.save:
        ini = {
            'output': args.output,
            'lang': args.lang,
            'process': args.process if args.process >= 1 else 2
        }
        with open('./conf.json', 'w', encoding='utf-8') as F:
            json.dump(ini, F)

    # params
    if args.output is not None:
        output_dir = args.output
    if args.lang is not None:
        lang_target = args.lang
    if args.process is not None:
        max_process = args.process if args.process >= 1 else 2

    return 'input_dir', output_dir, lang_target, max_process


if __name__ == '__main__':
    multiprocessing.freeze_support()
    arg = parsers.parse_args()
    inputDir, outputDir, langTarget, maxProcess = initialization_params(arg)
    # create path
    if not os.path.exists('input/mods'):
        os.makedirs('input/mods')
    if not os.path.exists('input/resource'):
        os.makedirs('input/resource')
    if not os.access(outputDir, os.R_OK):
        os.mkdir(outputDir)
    # setting
    helper = LangTransHelper()
    helper.__int__(outputDir, langTarget)
    # create process
    # start
    while True:
        # 提示信息
        print(
            '-' * 45 +
            '\n1.仅输出官方中英文语言文件  2.仅输出资源包中文和英文语言文件' +
            '\n3.资源包替换官方中文' +
            '\nq.退出\n' +
            '-' * 45, end='')
        # choose select
        pType = input('\r\n\033[1mInput your select:\033[0m  ')
        if pType == '':
            print('未选择')
            continue
        if pType.lower() == 'q':
            break
        # Does mix the language
        if input('\033[1m是否将语言混合(y/n):\033[0m  ') == 'y':
            helper.langMix = True
        else:
            helper.langMix = False
        print('')
        # clean dir trees
        # input output direction
        shutil.rmtree(outputDir + '/', ignore_errors=True)
        # select
        pool = ProcessPoolExecutor(max_workers=maxProcess)
        start = time.perf_counter()
        if pType == '1':
            for i in helper.scaner_file('input/mods'):
                pool.submit(helper.extract_mod_lang, i)
        elif pType == '2':
            for i in helper.scaner_file('input/resource'):
                pool.submit(helper.read_resource_pack_lang, i)
        elif pType == '3':
            firstList = helper.scaner_file('input/mods')
            secondList = helper.scaner_file('input/resource')
            # helper.replace_authority_lang(firstList, secondList)
            pool.submit(helper.replace_authority_lang, firstList, secondList)
        else:
            print('\033[35m无此选项\033[0m')
            continue

        pool.shutdown(wait=True)
        # select three temp folder remove
        shutil.rmtree(f'{outputDir}/temp', ignore_errors=True)
        # check result all right
        if not os.access(f'{outputDir}/has_trans/', os.W_OK):
            print('\033[31m程序或许未正常运行,请检查输入输出文件夹是否正常\033[0m')
            continue

        count = 0
        # mix and sort
        for i in helper.scaner_file(f'{outputDir}/has_trans/'):
            helper.mix_language_files(i)
            helper.sort_files(i)
            count += 1
        end = time.perf_counter()
        print(
            f'\n\033[1;32m处理完成,共 \033[33m{count} \033[1;32m个项目\033[0m \n'
            f'\033[1;32m共耗时 \033[33m{end - start:.3f} \033[1;32m秒\033[0m')
    print('程序已退出')
    os.system('pause')
