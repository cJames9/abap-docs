# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 21:53:33 2024

@author: Cleison
"""

import bs4
from src.sapDocsFiles import SapDocFile
from src.renderer import Renderer
import re


class Header:
    def __init__(self, title: str, isMainTitle: bool, render: Renderer):
        self.title = title
        self.isMainTitle = isMainTitle
        self.render = render


class Parser:
    def __init__(self, file: SapDocFile, renderer: Renderer, allFiles: list, allVersions: list):
        self.file = file
        self.renderer = renderer
        self.allFiles = allFiles
        self.allVersions = allVersions
        self.soup = file.soup

    def parse(self) -> str:
        path = self.soup.find(class_='path')
        if path:
            self.parsePath(path)

        root = self.soup.find(class_='all')
        if not root:
            # If there isn't a .all root, it's probably a old page. Just parse everything as is
            self.parseText(self.soup.body)
        else:
            for block in root.findChildren(recursive=True):
                print(block)
                if self.isBlock(block):
                    self.parseBlock(block)

        return self.renderer.getContents()

    def parsePath(self, path):
        # Remove last arrow
        pathHTML = re.sub(r'\xa0→\xa0', '', path.decode())
        self.parseText(f'<small>{pathHTML}</small>')

    def isBlock(self, element: bs4.element.Tag) -> bool:
        if not element.name:
            return False
        if self.isHeader(element):
            return True
        children = (list(element.children) or []) if element else []
        return any([self.isHeader(item) for item in children])

    def isHeader(self, element: bs4.element.Tag) -> bool:
        if not element.name:
            return False
        elementHeader = element or []
        classes = elementHeader.get_attribute_list('class') or ''
        return any([item for item in classes if item in ['h1', 'h2', 'h3', 'h4', 'h5', 'bold']])

    # TIP: parseBlock é o maior ponto de dúvida. talvez aqui algo dê errado
    def parseBlock(self, block):
        blockElements = []
        blockElements.append(block)

        # # generator = element.children
        # generator = iter(lista)
        # while True:
        #     element = next(generator, 'stop')
        #     blockElements.append(element)
        #     if element == 'stop':
        #         break
        #     if self.isBlock(element):
        #         break
        # self.parseBlockElements(blockElements)
        # if element:
        #     self.parseBlock(element)

        for element in block.next_siblings:
            if self.isBlock(element):
                break
            blockElements.append(element)
        self.parseBlockElements(blockElements)
        if element:
            self.parseBlock(element)

    def parseBlockElements(self, blockElements: list):
        headerElement = blockElements[0]
        header = self.determineHeader(headerElement)

        match header.title:
            case 'Syntax':
                header.render(header.title)
                self.parseSyntaxBlock(blockElements)
            case ['Note', 'Notes']:
                self.parseAdmonition('note', header.title, blockElements)
            case 'Example':
                self.parseAdmonition('example', header.title, blockElements)
            case ['Catchable Exceptions', 'Non-Catchable Exceptions']:
                self.parseAdmonition('tip', header.title, blockElements)
            case _:
                header.render(header.title)
                self.regularParseBlockElements(blockElements)

        if header.isMainTitle:
            self.parseVersioning()

    def parseVersioning(self):
        # Example:
        # Versions: <u>7.31</u> [7.40](../cds) [7.54](../cds)
        versioning = "Other versions: \n "
        for version in self.allVersions:
            text = self.renderVersion(version, self.findFile(version), f'../../{version}/{self.file.name}')
            versioning = versioning + text + " | "
        versioning = versioning[:-1]
        self.renderer.renderText(versioning)

    # TODO: ajustar classe para carregar versões e todos os arquivos (independente de estar em processamento ou não)
    def findFile(self, version: str) -> int:
        fileName = self.file.name
        try:
            index = self.allFiles.index(version)
        except ValueError:
            index = -1
        return index

    def renderVersion(self, version: str, index: int, link: str):
        if version == self.file.version:
            return f'<b>{version}</b>'
        if index == -1:
            return f'<s><i>{version}</i></s>'
        return f'[{version}]({link})'

    def parseAdmonition(self, type: str, title: str, contents):
        # This break line before an admonition is necessary, otherwise they get
        # wrongly merged by mkdocs. display: block is to reduce its size
        self.parseText('<br style="display: block">'),
        self.parseText(f'<div markdown="span" class="admonition {type}">')
        self.parseText(f'<p class="admonition-title">{title}</p>')
        self.regularParseBlockElements(contents)
        self.parseText('</div>')

    def parseSyntaxBlock(self, blockElements: list):
        parsedElements = []
        for idx, item in enumerate(blockElements):
            HTML = self.replaceJavascriptLinks(item)
            HTML = re.sub(r'<br/><br/>', '', HTML, flags=re.MULTILINE)
            if idx == 0 and HTML == '':
                continue
            if blockElements[-1] == blockElements[idx]:
                continue

            parsedElements.append(HTML)
        self.renderer.renderSyntaxBlock(parsedElements)

    def regularParseBlockElements(self, blockElements: list):
        for element in blockElements:
            if element.name == 'ul':
                self.parseList(element)
            elif element.name == 'table':
                self.parseTable(element)
            elif 'qtext' in element.get_attribute_list('class'):
                self.parseCodeExample(element)
            elif 'qtext400' in element.get_attribute_list('class'):
                self.parseCodeExample(element)
            elif element.name == 'a':
                # parse outer HTML
                # TIP: o que isto quer dizer? preciso pegar o elemento pai ou os demais preciso passar somente texto?
                outerHTML = element.parent
                self.parseText(outerHTML)
            elif element.name == 'br':
                self.parseText('\n')
            else:
                self.parseText(element)

    def parseTable(self, element):  # TODO: checar se não tem mais tipos
        tableBody = element.find('tbody') or element
        tableHeaderParsed = False

        for row in tableBody.findChildren(recursive=False):
            tableRow = row
            tableWidth = tableRow.findChildren(recursive=False)

            markdownRow = ''

            for tableCell in tableWidth:
                markdownRow += '|'
                # Don't use HTML in the header, so that we have pure text (e.g. sy-subrc is in a span)
                cellContent = tableCell if tableHeaderParsed else tableCell.text
                cellContent = cellContent or ''

                # Remove new lines so that markdown tables do not break
                cellContent = re.sub('(\r\n|\n|\r)', '', flags=re.MULTILINE)
                markdownRow += cellContent

            # Closes row
            markdownRow += '|'
            self.parseText(markdownRow)

            if not tableHeaderParsed:
                markdownRow = ''
                for idx, col in enumerate(tableWidth):
                    markdownRow += '|'
                    markdownRow += '----'
                markdownRow += '|'
                tableHeaderParsed = True
                self.parseText(markdownRow)

    def parseList(self, element):
        ulTag = '<ul>'

        # Standard abap documentation doesn't nest UL,
        # so we need to apply the same CSS style to ident
        if 'circlem2' in element.get_attribute_list('class'):
            ulTag = '<ul class="circlem2">'

        self.parseText(ulTag)
        html = element if element.name else None  # TIP: se o item tiver nome, não é string
        if html:
            # Remove extra line break
            html = re.sub('<br/>\n<br/>', '\n', html, flags=re.MULTILINE)
            html = re.sub('<br/><br/></li>', '</li>', html, flags=re.MULTILINE)

        self.parseText(html)
        self.parseText('</ul>')

    def parseText(self, text: str):
        if not text:
            return

        # https://regex101.com/r/1mionM/3
        # Show inline code
        parsedText = re.sub(r'(<span class="qtext">.*?<\/span>)', '<code style="display: inline;">\0</code>', text)

        # Remove extra line break
        parsedText = re.sub(r'<br/><br/>', '\n', parsedText, flags=re.MULTILINE)

        parsedText = self.replaceJavascriptLinks(parsedText)
        self.renderer.renderText(parsedText)

    def determineHeader(self, element: bs4.element.Tag):
        headerElement = element.find(class_='h1')
        headerTitle = headerElement.text.strip()
        if headerTitle:
            header = Header(headerTitle, True, self.renderer.renderTitle)
            return header

        # TODO: checar se H2 tem link
        headerElement = element.find(class_='h2')
        headerLink = headerElement.find('a')
        # const headerLinkHTML = this.$.html(headerLink);
        headerLinkHTML = headerLink.html if headerLink.name else None
        headerTitle = headerElement.text.strip().replace(':', '')
        if headerTitle:  # TODO: original tinha dois render na linha abaixo. o que fazia?
            header = Header(headerTitle, False, self.renderer.renderH2)
            # header = Header(headerTitle, False, [self.renderer.renderText(headerLinkHTML), self.renderer.renderH2(headerTitle)])
            return header

        headerElement = element.find(class_='h3')
        headerTitle = headerElement.text.strip().replace(':', '')
        if headerTitle:
            header = Header(headerTitle, False, self.renderer.renderH3)
            return header

        headerElement = element.find(class_='h4')  # TODO: renderH4 não está sendo usado
        headerTitle = headerElement.text.strip().replace(':', '')
        if headerTitle:
            header = Header(headerTitle, False, self.renderer.renderH3)
            return header

        headerElement = element.find(class_='bold')
        headerTitle = headerElement.text.strip().replace(':', '')
        if headerTitle:
            header = Header(headerTitle, False, self.renderer.renderH3)
            return header

    def parseH2(self, element):  # TODO: não está sendo usado
        text = element.find(class_='bold')
        self.renderer.renderH2(text.text)
        self.parseBlock(element)

    def parseCodeExample(self, element):
        if 'qtext' in element.get_attribute_list('class') or 'qtext400' in element.get_attribute_list('class'):
            span = element
        span = span or element.find(class_='qtext')
        code = span.decode()
        code = re.sub('(\r\n|\n|\r)', '', code, flags=re.MULTILINE)
        code = re.sub('<br/>', '\n', code, flags=re.MULTILINE)  # TODO: verificar se o BS4 trocou as tags por <br/>

        self.renderer.renderCodeBlock(code)

    def replaceJavascriptLinks(self, text):
        if not text:
            return ''
        # https://regex101.com/r/rvTc8y/6
        # Replace bad abap docs js links with relative links
        # HTML
        pattern = r'(href=")(javascript:call_link\((?:&apos;|\'))(.*?\.(?:html|htm))(?:&apos;\)\"|\'\)("))'
        replacedText = re.sub(pattern, '\g<1>../\g<3>\g<4>', text)
        return replacedText
