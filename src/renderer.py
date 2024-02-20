# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 21:01:25 2024

@author: Cleison
"""

class Renderer:
    def __init__(self, contents: list):
        self.contents = []
    
    def renderSyntaxBlock(self, elements: list):
        block = []
        block.append('<pre><code class="hljs abap abap-docs-syntax-block">')
        
        # index starts at 1 so we skip header
        for element in elements[1:]:
            block.append(element)
        
        block.append('</code></pre>')
        
        self.contents.append(block.join(''))

    def renderTitle(self, text: str):
        self.contents.append(f'# {text}')
        self.contents.append()    

    def renderH2(self, text: str):
        self.contents.append(f'## {text}')
    
    def renderH3(self, text: str):
        self.contents.append(f'### {text}')
      
    def renderH4(self, text: str):
        self.contents.append(f'#### {text}')
            
    def getContents(self) -> str:
        return self.contents.join('\n')

    def renderCodeBlock(self, code: str):
        self.contents.append(f'```abap\n{code}\n```')

    def renderText(self, text: str):
        self.contents.append(text)
