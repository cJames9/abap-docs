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
    def __init__(self, title: str, link: str, isMainTitle: bool, render: Renderer):
        self.title = title
        self.link = link
        self.isMainTitle = isMainTitle
        self.render = render


class Parser:
    def __init__(self, file: SapDocFile, renderer: Renderer, allFiles: list, allVersions: list):
        self.file = file
        self.renderer = renderer
        self.allFiles = allFiles
        self.allVersions = allVersions
        with open(file.path) as f:
            self.soup = bs4.BeautifulSoup(f, 'html.parser')

    def parse(self) -> str:
        path = self.soup.find(class_='path')
        if path:
            self.parsePath(path)

        root = self.soup.find(class_='all')
        if not root:
            # If there isn't a .all root, it's probably a old page. Just parse everything as is
            self.parseText(self.soup.body)
        else:
            for block in root.children:
                if self.isBlock(block):
                    self.parseBlock(block)

        return self.renderer.getContents()

    def parsePath(self, path):
        pathHTML = path.wrap(self.soup.new_tag('small'))
        self.parseText(pathHTML.text)

    def isBlock(self, element: bs4.element.Tag) -> bool:
        if not isinstance(element, bs4.element.Tag):
            return False
        if self.isHeader(element):
            return True
        children = (list(element.children) or []) if element else []
        return any([self.isHeader(item) for item in children])

    def isHeader(self, element: bs4.element.Tag) -> bool:
        if not isinstance(element, bs4.element.Tag):
            return False
        elementHeader = element or []
        classes = elementHeader.get_attribute_list('class') or ''
        return any([item for item in classes if item in ['h1', 'h2', 'h3', 'h4', 'h5', 'bold']])

    # TIP: parseBlock é o maior ponto de dúvida. talvez aqui algo dê errado
    def parseBlock(self, block):
        blockElements = []
        blockElements.append(block)

        for element in block.next_siblings:
            if element == '\n':
                continue
            if self.isBlock(element):
                break
            blockElements.append(element)
        self.parseBlockElements(blockElements)
        # if isinstance(element, bs4.element.Tag):
        #     self.parseBlock(element)

    def parseBlockElements(self, blockElements: list):
        headerElement = blockElements[0]
        header = self.determineHeader(headerElement)

        match header.title:
            case 'Syntax':
                header.render(header.title)
                self.parseSyntaxBlock(blockElements[1:])
            case ['Note', 'Notes']:
                self.parseAdmonition('note', header.title, blockElements[1:])
            case 'Example':
                self.parseAdmonition('example', header.title, blockElements[1:])
            case ['Catchable Exceptions', 'Non-Catchable Exceptions']:
                self.parseAdmonition('tip', header.title, blockElements[1:])
            case _:
                header.render(header.title)
                self.regularParseBlockElements(blockElements[1:])

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

    def findFile(self, version: str) -> int:
        fileName = self.file.name
        try:
            index = self.allFiles[version].index(fileName)
        except ValueError:
            index = -1
        return index

    def renderVersion(self, version: str, index: int, link: str):
        if version == self.file.version:
            return f'<b>{version}</b>'
        if index == -1:
            return f'<s><i>{version}</i></s>'
        return f'[{version}]({link})'  # TODO: verificar no parseH2

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
            HTML = self.removeDoubleLineBreaks(HTML)
            if HTML == '':
                continue

            parsedElements.append(HTML.decode())
        self.renderer.renderSyntaxBlock(parsedElements)  # TODO: estudar como trazer o fechamento do bloco para cá com o BS4

    def regularParseBlockElements(self, blockElements: list):
        for element in blockElements:
            if isinstance(element, bs4.element.Tag):
                if element.name == 'ul':
                    self.parseList(element)
                elif element.name == 'table':
                    self.parseTable(element)
                elif 'qtext' in element.get_attribute_list('class'):
                    self.parseCodeExample(element)
                elif 'qtext400' in element.get_attribute_list('class'):
                    self.parseCodeExample(element)
                elif 'qtextml1' in element.get_attribute_list('class'):
                    self.parseCodeExample(element)
                elif element.name == 'a':
                    self.parseText(element)
                elif element.name == 'br':
                    self.parseText('\n')
                else:
                    self.parseText(element.text)

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
                if isinstance(cellContent, bs4.element.Tag):
                    cellContent.string = re.sub(r'(\r\n|\n|\r)', '', cellContent.text, flags=re.MULTILINE)
                    markdownRow += cellContent.decode()
                else:
                    cellContent = re.sub(r'(\r\n|\n|\r)', '', cellContent, flags=re.MULTILINE)
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
        # Standard abap documentation doesn't nest UL,
        # so we need to apply the same CSS style to ident

        if isinstance(element, bs4.element.Tag):
            html = self.removeDoubleLineBreaks(element)
        else:
            html = element
        html = html.wrap(self.soup.new_tag('ul'))

        if 'circlem2' in element.get_attribute_list('class'):
            html['class'] = 'circlem2'

        self.parseText(html)

    def parseText(self, text: str):
        if not text:
            return

        # https://regex101.com/r/1mionM/3
        # Show inline code
        if isinstance(text, bs4.element.Tag):
            code = text.findAll('span', class_='qtext')
            for item in code:
                item = item.wrap(self.soup.new_tag('code'))
                item['style'] = 'display: inline;'

            parsedText = self.replaceJavascriptLinks(text)

            parsedText = parsedText.decode()
        else:
            parsedText = text

        parsedText = re.sub(r'\xa0→\xa0', '', parsedText)

        # Remove extra line break
        parsedText = re.sub(r'<br/><br/>', '\n', parsedText, flags=re.MULTILINE)

        self.renderer.renderText(parsedText)

    def determineHeader(self, element: bs4.element.Tag):
        headerElement = element.find(class_=['h1', 'h2', 'h3', 'h4', 'h5', 'bold'])
        if not headerElement:
            headerElement = element if any([class_ in ['h1', 'h2', 'h3', 'h4', 'h5', 'bold'] for class_ in element.get('class')]) else None
        if headerElement:
            match headerElement.get('class')[0]:
                case 'h1':
                    headerTitle = headerElement.text.strip()
                    isMainTitle = True
                    renderer = self.renderer.renderTitle
                case 'h2':
                    headerTitle = headerElement.text.strip().replace(':', '')
                    isMainTitle = False
                    renderer = self.renderer.renderH2
                case 'h3':
                    headerTitle = headerElement.text.strip().replace(':', '')
                    isMainTitle = False
                    renderer = self.renderer.renderH3
                case 'h4':
                    headerTitle = headerElement.text.strip().replace(':', '')
                    isMainTitle = False
                    renderer = self.renderer.renderH3  # TODO: renderH4 não está sendo usado
                case 'h5':
                    headerTitle = headerElement.text.strip().replace(':', '')
                    isMainTitle = False
                    renderer = self.renderer.renderH3  # TODO: repeti o do H4, mas temos isso?
                case 'bold':
                    headerTitle = headerElement.text.strip().replace(':', '')
                    isMainTitle = False
                    renderer = self.renderer.renderH3
                case _:
                    headerTitle = headerElement.text.strip().replace(':', '')
                    isMainTitle = False
                    renderer = self.renderer.renderH3

            if headerElement.a and headerElement.a.has_attr('href'):
                headerLink = headerElement.a.get('href')
            else:
                headerLink = ''

            header = Header(headerTitle, headerLink, isMainTitle, renderer)
            return header
                
                
        #     headerTitle = headerElement.text.strip()
        #     isMainTitle = True if headerElement.get('class') == 'h1' else False
                
        #     header = Header(headerTitle, True, self.renderer.renderTitle)
        #     return header
        
        
        # headerElement = element.find(class_='h1')
        # if headerElement:
        #     headerTitle = headerElement.text.strip()
        #     header = Header(headerTitle, True, self.renderer.renderTitle)
        #     return header

        # # TODO: checar se H2 tem link
        # headerElement = element.find(class_='h2')
        # if headerElement:
        #     headerLink = headerElement.find('a')
        #     # const headerLinkHTML = this.$.html(headerLink);
        #     headerLinkHTML = headerLink.html if headerLink else None
        #     headerTitle = headerElement.text.strip().replace(':', '')
        #     # TODO: original tinha dois render na linha abaixo. o que fazia?
        #     header = Header(headerTitle, False, self.renderer.renderH2)
        #     # header = Header(headerTitle, False, [self.renderer.renderText(headerLinkHTML), self.renderer.renderH2(headerTitle)])
        #     return header

        # headerElement = element.find(class_='h3')
        # if headerElement:
        #     headerTitle = headerElement.text.strip().replace(':', '')
        #     header = Header(headerTitle, False, self.renderer.renderH3)
        #     return header

        # headerElement = element.find(class_='h4')  # TODO: renderH4 não está sendo usado
        # if headerElement:
        #     headerTitle = headerElement.text.strip().replace(':', '')
        #     header = Header(headerTitle, False, self.renderer.renderH3)
        #     return header

        # headerElement = element.find(class_='bold')
        # if headerElement:
        #     headerTitle = headerElement.text.strip().replace(':', '')
        #     header = Header(headerTitle, False, self.renderer.renderH3)
        #     return header

    def parseCodeExample(self, element):
        span = element.find('span', class_='qtext')
        span = span or element if any([class_ in element.get_attribute_list('class') for class_ in ['qtext', 'qtext400', 'qtextml1']]) else None
        code = span.decode()  # TODO: descobrir encodificação que trate os símbolos
        code = re.sub('(\r\n|\n|\r)', '', code, flags=re.MULTILINE)
        code = re.sub('<br/>', '\n', code, flags=re.MULTILINE)  # TODO: criar regex para tirar a tag span
        self.renderer.renderCodeBlock(code)

    def replaceJavascriptLinks(self, text):
        if not text:
            return ''
        if not isinstance(text, bs4.element.Tag):
            return text
        # https://regex101.com/r/rvTc8y/6
        # Replace bad abap docs js links with relative links
        for element in text.findChildren(recursive=True):
            if isinstance(element, bs4.element.Tag):
                link = element.get('href')
                if link:
                    pattern = r'javascript:call_link\((?:&apos;|\')(.*?\.(?:html|htm))(?:&apos;\)\"|\'\))'
                    replacedText = re.sub(pattern, r'../\g<1>', link)
                    element['href'] = replacedText
        return text

    def removeDoubleLineBreaks(self, block):
        lineBreaks = block.findAll('br')
        for element in lineBreaks:
            if element.next_sibling == element:
                item = element.next_sibling.extract()
                item2 = element.extract() # NOQA
                del item, item2
            elif element.next_sibling == '\n' and element.next_sibling.next_sibling == element:
                item = element.next_sibling.next_sibling.extract() # NOQA
                item2 = element.extract() # NOQA
                del item, item2
        return block

    def preprocess(self, block):
        if isinstance(block, list):
            return [element for element in block.children if element not in ['\n', '\xa0→\xa0\n']]
        return block if block not in ['\n', '\xa0→\xa0\n'] else ''
