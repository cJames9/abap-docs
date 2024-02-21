# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 17:34:22 2024

@author: cleisonp
"""

import os
import bs4
from functools import reduce
from builtins import FileNotFoundError


class SapDocFile:
    def __init__(self, version: str, path: str, name: str, soup: bs4.BeautifulSoup):
        self.version = version
        self.path = path
        self.name = name
        self.soup = soup


class SapDocsFilesLoader:
    def __init__(self, path: str):
        self.files = []
        self.path = path
        self.path = [self.path, 'sapdocs', 'help.sap.com', 'doc']
        self.path = reduce(lambda a, b: os.path.join(a, b), self.path)
        if not os.path.exists(self.path):
            raise FileNotFoundError('sapdocs folder not found')

    def loadFile(self, version: str) -> list:
        versionPath = [self.path, f'abapdocu_{version.replace(".", "")}_index_htm', f'{version}', 'en-US']
        versionPath = reduce(lambda a, b: os.path.join(a, b), versionPath)
        for root, folder, file in os.walk(versionPath):
            filename = file.split('.')
            extension = filename.pop()
            if extension == 'html':
                path = os.path.join(versionPath, file)
                name = filename.pop()
                soup = bs4.BeautifulSoup(open(path), 'lxml')
                sapfile = SapDocFile(version, path, name, soup)
                self.files.append(sapfile)

        return self.files
