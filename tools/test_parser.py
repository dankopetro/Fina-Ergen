from html.parser import HTMLParser
class P(HTMLParser):
    def handle_starttag(self, tag, attrs): print(f"Start {tag}")
    def handle_endtag(self, tag): print(f"End {tag}")

p = P()
p.feed('<input /> <div></div> <br/>')
