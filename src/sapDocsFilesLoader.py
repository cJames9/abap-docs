# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 17:34:22 2024

@author: cleisonp
"""

import os
from builtins import FileNotFoundError

import * as cheerio from 'cheerio';
import SapDocFile from './sapDocFile';

const fs = require('fs');
const fse = require('fs-extra');
const pathLib = require('path');
const chalk = require('chalk');


def loadFile(version: str):
    path = os.path.join(os.getcwd(), 'sapdocs\\help.sap.com\\doc')
    if not os.path.exists(path):
        raise FileNotFoundError('sapdocs folder not found')

    versionPath = f'\\abapdocu_{version.replace(".", "")}_index_htm\\{version}\\en-US'
    versionPath = os.path.join(path, versionPath)
    
    for root, dirs, files in os.walk(versionPath):
        filename = file.split('.')
        extension = filename.pop()
        if extension == 'html':
            

  loadFiles(version: string): Array<SapDocFile> {
    

    versionPath = pathLib.join(this.path, versionPath);

    fse.readdirSync(versionPath).forEach((file: string) => {
      const filename = file.split('.');
      const extension = filename.pop();
      if (extension === 'html') {
        const path: string = pathLib.join(versionPath, file);
        const name = filename.pop()!;
        files.push({
          version,
          path,
          name,
          cheerio: cheerio.load(fs.readFileSync(path)),
        });
      }
    });

    return files;
  }
}
