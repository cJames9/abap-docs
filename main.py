# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 13:39:39 2024

@author: cleisonp
"""

import sys
import os
import shutil
from functools import reduce
from src.renderer import Renderer
from src.sapDocsFiles import SapDocsFilesLoader
from src.parser import Parser


def parseFiles(version: str, allFiles: list, allVersions: list):
    # For debugging purposes, just change this to true
    current_files = allFiles[version]
    for file in current_files:
        if DEBUG:
            # print(file.name)
            if file.name not in ['abapread_table_key', 'abapmethods_general', 'abapappend', 'abapdata_options', 'abapread_table']:
                continue

        if file.version != version:
            continue

        print(f'processing {file.path}')
        parser = Parser(file, Renderer(), allFiles, allVersions)
        contents = parser.parse()

        filePath = [os.getcwd(), 'docs', f'{version}', f'{file.name}.md']
        with open(reduce(lambda a, b: os.path.join(a, b), filePath), 'w', encoding='utf-8') as f:
            f.write(contents)


if __name__ == '__main__':
    args = sys.argv
    # DEBUG = False
    DEBUG = True
    if '--debug' in args:
        DEBUG = True

    # versions = [item for item in args if item != '--debug']
    versions = ['7.54']

    loader = SapDocsFilesLoader(os.getcwd())
    files = {}
    for version in versions:
        # carregar todos os arquivos antes de passar para o parser
        files[version] = loader.loadFile(version)
    for version in versions:
        versionPath = [os.getcwd(), 'docs', f'{version}']
        versionPath = reduce(lambda a, b: os.path.join(a, b), versionPath)
        if not os.path.exists(versionPath):
            os.mkdir(versionPath)
        elif not os.listdir(versionPath):
            shutil.rmtree(versionPath)
            os.mkdir(versionPath)
        parseFiles(version, files, versions)

    shutil.copyfile('base-mkdocs.yml', 'mkdocs.yml')
    print('Copied mkdocs.yml')

    # for version in versions:
    #     shutil.copyfile('base-pages.yml', f'.docs/{version}/.pages')
    # print('Copied .pages')

    print('Success!')
