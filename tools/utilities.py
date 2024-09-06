import os
import sys
import time
from collections import ChainMap


def scaner_file(url: str | list | tuple) -> list[str]:
    if type(url) is str:
        url = url.split()
    result = []
    for each in url:
        files = os.listdir(each)
        if len(files) <= 0:
            print('\033[33m目录为空\033[0m -> ' + each)
        for f in files:
            result.append(os.path.join(each, f))
    return result


def scaner_file_gen(url: str | list | tuple):
    if type(url) is str:
        url = url.split()
    for each in url:
        if not os.path.exists(each):
            continue
        files = os.listdir(each)
        if len(files) <= 0:
            print('\033[33m目录为空\033[0m -> ' + each)
        for f in files:
            yield os.path.join(each, f)


def scaner_file_next(url: str | list | tuple):
    if type(url) is str:
        url = url.split()
    for each_dir in url:
        if not os.path.exists(each_dir):
            continue
        scandir_item = os.scandir(each_dir)
        try:
            scandir_item.__next__()
        except StopIteration:
            print('\033[33m目录为空\033[0m -> ' + each_dir)
            continue
        for f in scandir_item:
            yield f.path


def selection(tips: str, option=('y', 'n'), warning='\033[33m无此选项\033[0m'):
    while True:
        select = input(tips)
        if select.lower() in option:
            return select
        print(warning)
        continue
