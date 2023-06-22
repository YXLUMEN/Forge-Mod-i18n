import os
import re
import shutil
import zipfile
import json
import argparse
from concurrent.futures import ProcessPoolExecutor

parsers = argparse.ArgumentParser()
parsers.add_argument('-output', required=False, help='输出结果目录')
parsers.add_argument('-lang', required=False, help='目标语言')
parsers.add_argument('-process', default=2, type=int, required=False, help='进程数')
parsers.add_argument(
    '-save', default=0, type=bool, required=False,
    help='是否保存配置;当保存配置时,下次运行将依照配置执行,直到输入参数或更改配置')


class LangTransHelper:
    langMix = False
    count = 0

    def __int__(self, output_dir: str, trans: str):
        self.output_dir = output_dir
        self.lang = trans

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

    def read_resource_pack_lang(self, file: str):
        mod = None
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
                # mod id in pack
                if lang_json.split('/')[0] == 'assets' and len(lang_json.split('/')) == 2:
                    mod = lang_json.split('/')[-1]
                self._zip_reader(target, lang_json, mod)
        # sometime resource pack is a folder
        elif os.path.isdir(file):
            if not os.access(file + '/pack.mcmeta', os.R_OK):
                print('未找到pack.mcmeta -> ' + file.split('\\')[-1])
                return
            # get all mod folder
            mod_folder = self.scaner_file(f'{file}/assets')
            # process each mod to copy lang files if it's existence
            for each_mod in mod_folder:
                self._read_resource_pack_part_one(each_mod)
        # maybe it's nothing
        else:
            print('\033[31m未解析的资源包\033[0m -> ' + file.split('\\')[-1])
            return

    # read_resource_pack_lang's part TO make main function more beautiful
    def _read_resource_pack_part_one(self, each_mod):
        mod_id = each_mod.split('\\')[-1]
        try:
            if not os.access(f'{each_mod}/lang/{self.lang}.json', os.R_OK):
                return
            if not os.access(f'{self.output_dir}/has_trans/{mod_id}', os.W_OK):
                os.makedirs(f'{self.output_dir}/has_trans/{mod_id}')
            shutil.copy(
                os.path.abspath(f'{each_mod}/lang/{self.lang}.json'),
                f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json')
        except Exception as e:
            print(f'{e} -> {mod_id}')

    # TODO
    def replace_authority_lang(self):

        ...

    # sort files
    def sort_files(self, dir_name: str):
        if dir_name is None:
            return
        en = False
        zh = False

        # has lang
        if os.access(dir_name + '/en_us.json', os.R_OK):
            en = True
        if os.access(dir_name + f'/{self.lang}.json', os.R_OK):
            zh = True
        # create path
        if not os.access(f'{self.output_dir}/need_{self.lang}/', os.W_OK):
            os.makedirs(f'{self.output_dir}/need_{self.lang}/')
        if not os.access(f'{self.output_dir}/no_en_us/', os.W_OK):
            os.makedirs(f'{self.output_dir}/no_en_us/')
        if not os.access(f'{self.output_dir}/no_lang_files/', os.W_OK):
            os.makedirs(f'{self.output_dir}/no_lang_files/')
        # sort those files
        if not en and not zh:
            shutil.move(dir_name, f'{self.output_dir}/no_lang_files/')
        elif not en:
            shutil.move(dir_name, f'{self.output_dir}/no_en_us/')
        elif not zh:
            shutil.move(dir_name, f'{self.output_dir}/need_{self.lang}/')

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
            print(f'mixLang: 处理的 -> {mod_id} 没有: ' + str(e).split('/')[-1])
            return
        # mix two lang files in to mix.json
        for key, value in en_file.items():
            if key in zh_file.keys():
                en_file[key] = zh_file[key]
        mix_file = open(f'{mod_id}/mix.json', 'w', encoding='utf-8')
        json.dump(en_file, mix_file, ensure_ascii=False, indent=4)

    def scaner_file(self, url: str | list | tuple) -> list[str]:
        """
        :param url:
        :return:
        返回输入地址下的所以文件名
        """
        if type(url) == str:
            url = url.split()
        self.count = 0
        result = []
        for each in url:
            files = os.listdir(each)
            if len(files) <= 0:
                print('目录为空 -> ' + each)
            for f in files:
                result.append(os.path.join(each, f))
                self.count += 1
        return result


# default params
def initialization_params(args):
    # Default
    output_dir = './output'
    lang_target = 'zh_cn'
    # read settings
    if os.access('./conf.json', os.R_OK):
        with open('./conf.json', 'r', encoding='utf-8') as F:
            ini = json.load(F)
        output_dir = ini['output'] if ini['output'] is not None else output_dir
        lang_target = ini['lang'] if ini['lang'] is not None else lang_target
    # save settings
    if args.save:
        ini = {
            'output': args.output,
            'lang': args.helper,
            'process': args.process
        }
        with open('./conf.json', 'w', encoding='utf-8') as F:
            json.dump(ini, F)

    # params
    if args.output is not None:
        output_dir = args.output
    if args.lang is not None:
        lang_target = args.lang

    return 'input_dir', output_dir, lang_target


if __name__ == '__main__':
    arg = parsers.parse_args()
    inputDir, outputDir, langTarget = initialization_params(arg)
    # create path
    if not os.path.exists('input'):
        os.mkdir('input')
    if not os.access(outputDir, os.R_OK):
        os.mkdir(outputDir)
    # setting
    helper = LangTransHelper()
    helper.__int__(outputDir, langTarget)

    # start
    while True:
        pool = ProcessPoolExecutor(max_workers=arg.process)
        # 提示信息
        print(
            '-' * 45 +
            '\n1.仅输出官方中英文语言文件  2.仅输出资源包中文和英文语言文件' +
            '\n3.资源包替换官方中文' +
            '\nq.退出\n' +
            '-' * 45)
        pType = input('\r\n\033[1mInput your select:\033[0m  ')
        if pType == 'q':
            break
        if pType.lower() not in ('1', '2', 'q'):
            print('\033[35m无此选项\033[0m')
            continue
        if input('\033[1m是否将语言混合(y/n):\033[0m  ') == 'y':
            helper.langMix = True
        else:
            helper.langMix = False
        # clean dir trees
        shutil.rmtree(outputDir + '/', ignore_errors=True)
        if pType == '1':
            for i in helper.scaner_file('input/mods'):
                extractProcess = pool.submit(helper.extract_mod_lang, i)
        elif pType == '2':
            for i in helper.scaner_file('input/resource'):
                folderProcess = pool.submit(helper.read_resource_pack_lang, i)
        elif pType == '3':
            for i in helper.scaner_file(('input/mods', 'input/resource')):
                ...

        pool.shutdown(wait=True)
        if not os.access(f'{outputDir}/has_trans/', os.W_OK):
            exit('程序或许未正常运行,请检查输入输出文件夹是否正常')
        for i in helper.scaner_file(f'{outputDir}/has_trans/'):
            helper.mix_language_files(i)
            helper.sort_files(i)
