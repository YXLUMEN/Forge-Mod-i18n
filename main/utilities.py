import os


def scaner_file_gen(url: str | list | tuple):
    if type(url) is str:
        url: list = url.split()

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
        select: str = input(tips)
        if select.lower() in option:
            return select

        print(warning)
        continue
