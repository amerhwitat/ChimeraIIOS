from html.parser import HTMLParser
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse,quote_plus
from urllib.robotparser import RobotFileParser
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,time
USER_AGENT='ISO-Tool-Crawler/1.0'
@dataclass
class WebRecord: url:str; title:str; text:str; retrieved_at:str; sha256:str; source_type:str='web'; status:int=200
class P(HTMLParser):
 def __init__(self): super().__init__();self.links=[];self.text=[];self.title=[];self.t=False
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.links.append(d['href'])
  if t=='title':self.t=True
 def handle_endtag(self,t):
  if t=='title':self.t=False
 def handle_data(self,d): (self.title if self.t else self.text).append(d)
class WebCrawler:
 def __init__(self,cache_dir,max_pages=20,max_depth=2,delay=.2):self.max_pages=max_pages;self.max_depth=max_depth;self.delay=delay;self.r={};self.s=set();Path(cache_dir).mkdir(parents=True,exist_ok=True)
 def crawl(self,start):
  if urlparse(start).scheme not in ('http','https'):raise ValueError('HTTP(S) only')
  q=[(start,0)];out=[];host=urlparse(start).netloc
  while q and len(out)<self.max_pages:
   u,d=q.pop(0)
   if u in self.s or d>self.max_depth:continue
   self.s.add(u)
   rp=RobotFileParser(urlparse(u)._replace(path='/robots.txt',params='',query='',fragment='').geturl())
   try:rp.read()
   except Exception:continue
   if not rp.can_fetch(USER_AGENT,u):continue
   try:
    with urlopen(Request(u,headers={'User-Agent':USER_AGENT}),timeout=15) as x:raw=x.read(1500000);html=raw.decode('utf-8','replace');status=getattr(x,'status',200)
   except Exception:continue
   p=P();p.feed(html);text=' '.join(' '.join(p.text).split());title=' '.join(' '.join(p.title).split());h=hashlib.sha256(raw).hexdigest();out.append(WebRecord(u,title,text,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),h,status=status))
   if d<self.max_depth:
    for hrf in p.links:
     n=urljoin(u,hrf).split('#')[0]
     if urlparse(n).netloc==host:q.append((n,d+1))
   time.sleep(self.delay)
  return out
def search_web(q,endpoint='https://html.duckduckgo.com/html/?q=',limit=10):
 p=P();
 with urlopen(Request(endpoint+quote_plus(q),headers={'User-Agent':USER_AGENT}),timeout=15) as x:p.feed(x.read().decode('utf-8','replace'))
 return [{'url':u,'query':q,'source_type':'search'} for u in p.links if u.startswith('http')][:limit]
def write_records(path,records):
 Path(path).write_text('\n'.join(json.dumps(asdict(r) if hasattr(r,'__dataclass_fields__') else r) for r in records),encoding='utf-8')
