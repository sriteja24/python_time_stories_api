import http.server
import urllib.request
from html.parser import HTMLParser
import json

class TimeHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_latest_stories = False
        self.in_story = False
        self.current_title = ''
        self.current_link = ''
        self.stories = []
        self.story_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'div' and 'partial latest-stories' in attrs_dict.get('class', ''):
            self.in_latest_stories = True
        elif tag == 'a' and self.in_latest_stories:
            if 'href' in attrs_dict:
                self.current_link = 'https://time.com' + attrs_dict['href']
                self.in_story = True
        elif tag == 'h3' and self.in_story:
            self.current_title = ''
            self.in_story = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_link:
            if self.current_title:
                self.stories.append({
                    'title': self.current_title,
                    'link': self.current_link
                })
                self.story_count += 1
                if self.story_count >= 6:
                    self.in_latest_stories = False
            self.current_link = ''
            self.in_story = False
        elif tag == 'h3':
            self.current_title = self.current_title.strip()
        elif tag == 'div' and 'partial latest-stories' in self.get_starttag_text():
            self.in_latest_stories = False

    def handle_data(self, data):
        if self.in_story:
            self.current_title += data.strip()

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/getTimeStories':
            try:
                url = 'https://time.com'
                response = urllib.request.urlopen(url)
                html = response.read().decode('utf-8')

                parser = TimeHTMLParser()
                parser.feed(html)

                stories = parser.stories[:6]
                stories_json = json.dumps(stories, indent=4)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(stories_json.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=http.server.HTTPServer, handler_class=RequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('Starting server on port 8000...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
