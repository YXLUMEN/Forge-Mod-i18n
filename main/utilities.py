import os


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
