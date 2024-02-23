# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 09:30:08 2024

@author: cleisonp
"""

import os
import bs4
from sapDocsFiles import SapDocFile
from sapDocsFiles import SapDocsFilesLoader
from parser import Parser
from renderer import Renderer
from functools import reduce
# from lxml import etree
import re

os.chdir(r'C:\Users\cleisonp\OneDrive - Alcast do Brasil SA\Documentos\GitHub\abap-docs')

loader = SapDocsFilesLoader(os.getcwd())


# abentable_exp_chaining não tem tbody para checar tabela
# abencds_f1_cast_expression

version = '7.54'
path = [loader.path, f'abapdocu_{version.replace(".", "")}_index_htm', f'{version}', 'en-US', 'abapappend.html']
path = reduce(lambda a, b: os.path.join(a, b), path)
filename = 'abapappend'
soup = bs4.BeautifulSoup(open(path), 'html.parser')



# variável self: workaround pra usar as funções sem ter q mudar nada
self = SapDocFile(version, path, filename, soup)
allFiles = [self]
allVersions = [version]
parser = Parser(self, Renderer(), allFiles, allVersions)


path = self.soup.find(class_='path')
root = self.soup.find(class_='all')

def preprocess(block: list):
    return [element for element in block.children if element not in ['\n', '\xa0→\xa0\n']]
    # for element in block.findChildren(recursive=True):
    #     print(element)
    #     if element in ['\n', '\xa0→\xa0\n']:
    #         item = element.extract()
    #         del item
    # return block

def isBlock(element: bs4.element.Tag) -> bool:
    if type(element) in [bs4.element.NavigableString, bs4.element.Comment]:
        return False
    if isHeader(element):
        return True
    children = (list(element.children) or []) if element else []
    return any([isHeader(item) for item in children])


def isHeader(element: bs4.element.Tag) -> bool:
    if type(element) in [bs4.element.NavigableString, bs4.element.Comment]:
        return False
    elementHeader = element or {}
    classes = elementHeader.get('class') or ''
    return any([item for item in classes if item in ['h1', 'h2', 'h3', 'h4', 'h5', 'bold']])


for block in root.children:
    if isBlock(block):
        parseBlock(block)

element = list(root.children)[9]
element = root.findChildren()[15]
isHeader(list(root.children)[9])

# %%

blockElements = []
def parseBlock(block):
    
    blockElements.append(block)

    for element in block.next_siblings:
        if isBlock(element):
            break
        blockElements.append(element)
    # self.parseBlockElements(blockElements)
    # if element:
    #     self.parseBlock(element)

parseBlock(block)