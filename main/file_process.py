import os
import re
import zipfile


class FileProcess:
    def __init__(self, target_language='zh_cn', default_language='en_us', output_dir='output'):
        self.current_zip_object: zipfile.ZipFile
        self.source = None  # input/mods/*; input/resources/*
        self.mod_id = None

        self.output_dir = output_dir

        self.default_language = default_language  # en_us.json
        self.target_language = target_language  # zh_cn.json
        print(self.target_language)

    def alter_zip_object(self, source):
        try:
            zip_file = zipfile.ZipFile(source, 'r')
        except Exception as e:
            print(f'\033[31m解压文件错误:\033[0m {e} -> ' + source.split('\\')[-1])
            return
        self.source = source
        self.current_zip_object = zip_file

    def write_file(self, file_path: str):
        mod_lang = f'assets/{self.mod_id}/lang'
        output_dir = f'{self.output_dir}/temp/{self.mod_id}'
        if not os.access(output_dir, os.W_OK):
            os.makedirs(output_dir)

        if file_path == f'{mod_lang}/{self.default_language}.json':
            byte = self.current_zip_object.read(file_path)
            with open(f'{output_dir}/{self.default_language}.json', 'wb') as f:
                f.write(byte)
        elif file_path == f'{mod_lang}/{self.target_language}.json':
            byte = self.current_zip_object.read(file_path)
            with open(f'{output_dir}/{self.target_language}.json', 'wb') as f:
                f.write(byte)

    def verify_mod(self):
        """
        判断模组合法性，并返回MOD ID
        :return:
        """
        try:
            mod_id = self.current_zip_object.read('META-INF/mods.toml')
        except KeyError:
            print(f'\033[33m未识别的mod:\033[0m -> ' + self.source.split('\\')[-1])
            return
        except Exception as e:
            print(f'\033[31m出现错误:\033[0m {e} -> ' + self.source.split('\\')[-1])
            self.current_zip_object.close()
            return
        mod_id = str(mod_id)
        mod_id = re.findall('modId.?=.?"(.*?)"', mod_id)[0]

        self.mod_id = mod_id
        return mod_id

    def verify_resource_pack(self):
        """
        判断资源包合法性，输出 0 1 None
        :return:
        """

        if zipfile.is_zipfile(self.source):
            try:
                self.current_zip_object.read('pack.mcmeta')
            except KeyError:
                print(f'\033[33m未找到pack.mcmeta:\033[0m -> ' + self.source.split('\\')[-1])
                return
            except Exception as e:
                print(f'\033[31m出现错误:\033[0m {e} -> ' + self.source.split('\\')[-1])
                self.current_zip_object.close()
                return
            return 1
        elif os.path.isdir(self.source):
            if not os.access(f'{self.source}/pack.mcmeta', os.R_OK):
                print(f'未找到pack.mcmeta -> ' + self.source.split('\\')[-1])
                return
            return 2
        else:
            print('\033[31m未解析的资源包\033[0m -> ' + self.source.split('\\')[-1])
            return
