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


def parseFiles(version: str):
    # For debugging purposes, just change this to true
    for file in files:
        if DEBUG:
            if file.name not in ['abapread_table_key', 'abapmethods_general', 'abapappend', 'abapdata_options', 'abapread_table']:
                return

        if file.version != version:
            return

        print(f'processing {file.path}')
        parser = Parser(file, Renderer(), files)
        contents = parser.parse()

        filePath = [os.getcwd(), 'docs', f'{version}', f'{file.name}.md']
        with open(reduce(lambda a, b: os.path.join(a, b), filePath), 'w') as f:
            f.write(contents)


if __name__ == '__main__':
    args = sys.argv.split(' ')
    DEBUG = False
    if '--debug' in args:
        DEBUG = True

    versions = [item for item in args if item != '--debug']

    loader = SapDocsFilesLoader(os.getcwd())
    files = []
    for version in versions:
        files.append(loader.loadFile(version))
        versionPath = [os.getcwd(), 'docs', f'{version}']
        versionPath = reduce(lambda a, b: os.path.join(a, b), versionPath)
        if not os.path.exists(versionPath):
            os.mkdir(versionPath)
        elif not os.listdir(versionPath):
            shutil.rmtree(versionPath)
            os.mkdir(versionPath)
        else:
            parseFiles(version)

    shutil.copyfile('base-mkdocs.yml', 'mkdocs.yml')
    print('Copied mkdocs.yml')

    for version in versions:
        shutil.copyfile('base-pages.yml', f'.docs/{version}/.pages')
    print('Copied .pages')

    print('Success!')
