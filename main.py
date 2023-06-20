import multiprocessing
import os
import re
import shutil
import zipfile
import json
import argparse
import multiprocessing.pool
import queue

parsers = argparse.ArgumentParser()
parsers.add_argument('-input', required=False, help='输入模组目录')
parsers.add_argument('-output', required=False, help='输出结果目录')
parsers.add_argument('-lang', required=False, help='目标语言')
parsers.add_argument('-process', default=2, type=int, required=False, help='进程数')
parsers.add_argument(
    '-save', default=0, type=bool, required=False,
    help='是否保存配置;当保存配置时,下次运行将依照配置执行,直到输入参数或更改配置')


class LangTransHelper:
    langMix = False
    count = 0
    _pType = 1
    _modsQueue = queue.Queue(maxsize=6)

    # _modsFile = queue.Queue(maxsize=6)

    def __int__(self, input_dir: str, output_dir: str, trans: str, max_process: int):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.lang = trans
        self._pool = multiprocessing.Pool(processes=max_process)

    def main(self, p_type: str):
        self._pType = p_type

        for i in self.scaner_file(self.input_dir):
            self.__deploy(i)
        self._modsQueue.join()

    def __deploy(self, in_object: str):
        if not zipfile.is_zipfile(in_object):
            self._pool.apply_async(func=self.get_mod_id, args=(in_object,))
            self._pool.apply_async(func=self.__extract_lang_files)
        elif os.path.isdir(in_object) and self._pType == '2':
            self._pool.apply_async(self.__read_lang_file_from_folder, args=(in_object,))
        # self.__mix_language_files(mod_id)

    # get mod id from jar(zip)
    def get_mod_id(self, zip_file: str):
        """

        :param zip_file:
        :return:
        """
        # create zip object
        try:
            zip_f = zipfile.ZipFile(zip_file, 'r')
        except Exception as e:
            print(f'解压文件错误: {e} -> ' + zip_file.split('\\')[1])
            return
        # get mod id
        try:
            mod_id = zip_f.read('META-INF/mods.toml')
            mod_id = str(mod_id)
            mod_id = re.findall('modId.?=.?"(.*?)"', mod_id)[0]
        except KeyError:
            return
        except Exception as e:
            print(f'未识别的mod或资源包: {e} -> ' + zip_file.split('\\')[1])
            return

        mod = mod_id, zip_f
        self._modsQueue.put(mod, block=True)
        zip_f.close()
        return mod_id

    # extract lang files from jar(zip)
    def __extract_lang_files(self):
        # semaphore
        en = False
        zh = False
        mod_id, zip_f = self._modsQueue.get(block=True)

        if not os.access(f'{self.output_dir}/has_trans/{mod_id}/', os.W_OK):
            os.makedirs(f'{self.output_dir}/has_trans/{mod_id}/')
        # extract target lang json file and en_us.json
        for file in zip_f.namelist():
            if file == f'assets/{mod_id}/lang/en_us.json':
                byte = zip_f.read(file)
                with open(f'{self.output_dir}/has_trans/{mod_id}/en_us.json', 'wb') as f:
                    f.write(byte)
                en = True
            elif file == f'assets/{mod_id}/lang/{self.lang}.json':
                byte = zip_f.read(file)
                with open(f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json', 'wb') as f:
                    f.write(byte)
                zh = True
        zip_f.close()

        self.__sort_files(mod_id, en, zh)

    def __read_lang_file_from_folder(self, folder: str):
        try:
            print('111')
        except Exception as e:
            print(e)

    # sort files
    def __sort_files(self, dir_name: str, en: bool, zh: bool):
        if dir_name is None:
            return
        # create path
        if not os.access(f'{self.output_dir}/need_{self.lang}/', os.W_OK):
            os.makedirs(f'{self.output_dir}/need_{self.lang}/')
        if not os.access(f'{self.output_dir}/no_en_us/', os.W_OK):
            os.makedirs(f'{self.output_dir}/no_en_us/')
        if not os.access(f'{self.output_dir}/no_lang_files/', os.W_OK):
            os.makedirs(f'{self.output_dir}/no_lang_files/')
        # sort those files
        origin_file_dir = f'{self.output_dir}/has_trans/{dir_name}/'
        if not en and not zh:
            shutil.rmtree(f'{self.output_dir}/no_lang_files/{dir_name}', ignore_errors=True)
            shutil.move(origin_file_dir, f'{self.output_dir}/no_lang_files/')
        elif not en:
            shutil.rmtree(f'{self.output_dir}/no_en_us/', ignore_errors=True)
            shutil.move(origin_file_dir, f'{self.output_dir}/no_en_us/')
        elif not zh:
            shutil.rmtree(f'{self.output_dir}/need_{self.lang}/{dir_name}', ignore_errors=True)
            shutil.move(origin_file_dir, f'{self.output_dir}/need_{self.lang}/')

    def scaner_file(self, url: str):
        """
        :param url:
        :return:
        返回输入地址下的所以文件名
        """

        self.count = 0
        files = os.listdir(url)
        if len(files) <= 0:
            print('目录为空')
        result = []
        for f in files:
            result.append(os.path.join(url, f))
            self.count += 1
        return result

    def __mix_language_files(self, mod_id):
        if not self.langMix:
            return
        # lang files is correct
        if mod_id is None:
            return
        if not os.access(f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json', os.R_OK):
            print(f'无中文语言文件或文件不可读 -> {mod_id}')
            return
        # load in json
        en_file = open(f'{self.output_dir}/has_trans/{mod_id}/en_us.json', 'rb')
        en_file = json.load(en_file)
        zh_file = open(f'{self.output_dir}/has_trans/{mod_id}/{self.lang}.json', 'rb')
        zh_file = json.load(zh_file)
        # mix two lang files in to mix.json
        for key, value in en_file.items():
            if key in zh_file.keys():
                en_file[key] = zh_file[key]
        mix_file = open(f'{self.output_dir}/has_trans/{mod_id}/mix.json', 'w', encoding='utf-8')
        json.dump(en_file, mix_file, ensure_ascii=False, indent=4)


def initialization_params(args):
    # Default
    input_dir = './input'
    output_dir = './output'
    lang_target = 'zh_cn'
    # read settings
    if os.access('./conf.json', os.R_OK):
        with open('./conf.json', 'r', encoding='utf-8') as F:
            ini = json.load(F)
        input_dir = ini['input'] if ini['input'] is not None else input_dir
        output_dir = ini['output'] if ini['output'] is not None else output_dir
        lang_target = ini['lang'] if ini['lang'] is not None else lang_target
    # save settings
    if args.save:
        ini = {
            'input': args.input,
            'output': args.output,
            'lang': args.lang,
            'process': args.process
        }
        with open('./conf.json', 'w', encoding='utf-8') as F:
            json.dump(ini, F)

    # params
    if args.input is not None:
        input_dir = args.input
    if args.output is not None:
        output_dir = args.output
    if args.lang is not None:
        lang_target = args.lang
    # create path
    if not os.path.exists(input_dir):
        os.mkdir(input_dir)
    if not os.access(output_dir, os.R_OK):
        os.mkdir(output_dir)

    return input_dir, output_dir, lang_target


if __name__ == '__main__':
    arg = parsers.parse_args()
    inputDir, outputDir, langTarget = initialization_params(arg)
    # pool = Pool(processes=arg.process)
    # setting
    lang = LangTransHelper()
    lang.__int__(inputDir, outputDir, langTarget, arg.process)

    # start
    while True:
        # 提示信息
        print(
            '-' * 40 +
            '\n1.仅输出官方中英文语言文件  2.仅输出资源包中文和英文语言文件' +
            '\n3.资源包替换官方中文  4.官方与资源包互补' +
            '\nq.退出\n' +
            '-' * 40)
        pType = input('\r\nInput your select:  ')
        if pType == 'q':
            break
        if input('是否将语言混合(y/n):  ') == 'y':
            lang.langMix = True
        lang.main(pType)
        print(f'\r\n分析完成,共{lang.count}个模组')
