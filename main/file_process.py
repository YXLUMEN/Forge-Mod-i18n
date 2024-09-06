import os
import re
import zipfile


class FileProcess:
    __slots__ = 'current_zip_object', 'source', 'mod_id', 'output_dir', 'default_language', 'target_language'

    def __init__(self, target_language: str = 'zh_cn', default_language: str = 'en_us', output_dir: str = 'output'):
        self.current_zip_object: zipfile.ZipFile
        self.source: str = ''  # input/mods/*; input/resources/*
        self.mod_id: str = ''

        self.output_dir: str = output_dir

        self.default_language: str = default_language  # en_us.json
        self.target_language: str = target_language  # zh_cn.json

    def __del__(self):
        try:
            self.current_zip_object.close()
        except AttributeError:
            pass
        except Exception as e:
            print(f'\033[31m出现错误:\033[0m {e}')

    def _set_zip_object(self, source: str):
        try:
            zip_file = zipfile.ZipFile(source, 'r')
        except Exception as e:
            print(f'\033[31m解压文件错误:\033[0m {e} -> ' + source.split('\\')[-1])
            return

        self.source = source
        self.current_zip_object = zip_file

    def write_file(self, file_path: str) -> None:
        mod_lang_path: str = f'assets/{self.mod_id}/lang'
        output_dir: str = f'{self.output_dir}/temp/{self.mod_id}'

        if not os.access(output_dir, os.W_OK):
            os.makedirs(output_dir)

        if file_path == f'{mod_lang_path}/{self.default_language}.json':
            file_bytes: bytes = self.current_zip_object.read(file_path)

            with open(f'{output_dir}/{self.default_language}.json', 'wb') as f:
                f.write(file_bytes)
        elif file_path == f'{mod_lang_path}/{self.target_language}.json':
            file_bytes: bytes = self.current_zip_object.read(file_path)

            with open(f'{output_dir}/{self.target_language}.json', 'wb') as f:
                f.write(file_bytes)

    def verify_mod(self, source: str) -> str:
        self._set_zip_object(source)
        try:
            mod_id: str = self.current_zip_object.read('META-INF/mods.toml').decode('utf-8')
        except KeyError:
            print(f'\033[33m未识别的mod:\033[0m -> ' + self.source.split('\\')[-1])
            return ''
        except Exception as e:
            print(f'\033[31m出现错误:\033[0m {e} -> ' + self.source.split('\\')[-1])
            self.current_zip_object.close()
            return ''

        mod_id = re.findall('modId.?=.?"(.*?)"', mod_id)[0]

        self.mod_id = mod_id
        return mod_id

    def verify_resource_pack_zip(self, source: str):
        # 返回压缩包文件路径，并且获取Mod ID
        self._set_zip_object(source)

        try:
            self.current_zip_object.read('pack.mcmeta')
        except KeyError:
            print(f'\033[33m未找到pack.mcmeta:\033[0m -> ' + self.source.split('\\')[-1])
            return
        except Exception as e:
            print(f'\033[31m出现错误:\033[0m {e} -> ' + self.source.split('\\')[-1])
            self.current_zip_object.close()
            return

        for each_mod in self.current_zip_object.namelist():
            # 暂时如此
            if each_mod.split('/')[0] == 'assets' and len(each_mod.split('/')) > 3:
                mod_id: str = each_mod.split('/')[1]
                self.mod_id = mod_id
                yield each_mod

    def verify_resource_pack_dir(self, source: str) -> bool:
        # 仅仅判断资源包合法性
        self.source = source

        if os.access(f'{self.source}/pack.mcmeta', os.R_OK):
            return True
        print(f'未找到pack.mcmeta -> ' + self.source.split('\\')[-1])
        return False
