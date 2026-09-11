from pathlib import Path
import json,threading,queue,tkinter as tk
from tkinter import ttk,filedialog
from .web_engine import WebCrawler,search_web
from .learning_engine import ingest_repository,generate_build_plan
from .neural_engine import NeuralEngine
GROUPS={"Source & Repository":["Open GitHub","Clone Repository","Open Local Source","Open Archive","Deep Recursive Scan","Repository Tree","Dependency Analysis","Application Discovery"],"Toolchains":["Detect Windows Toolchains","Detect MSVC","Detect Clang","Detect GCC/G++","Detect NASM","Bootstrap NASM","Bootstrap GCC/G++","Built-in Spit Fire Assembler"],"Build":["Generate Build Plan","Compile","Link","Debug Build","Release Build","GNU Build","MSVC Build","Build All Projects","Run Tests","Build Journal"],"ISO / Boot":["Build Spit Fire Boot Sector","Build BIOS ISO","Build UEFI ISO","Build BIOS + UEFI ISO","Build ISO Image","Build IMG","Merge Binaries","Merge Libraries","Generate Manifest","Verify Boot Image","Verify ISO"],"Packages / Applications":["Detect Package Managers","Install Dependencies","Application Inventory","Artifact Inventory"],"Diagnostics":["Validate Configuration","Dependency Errors","Runtime Errors","Build Errors","View Logs","Export Diagnostics","Verify Output"],"Knowledge & AI":["Web Search","Crawl Website","Crawl Documentation","Crawl Repository References","Build Knowledge Base","Index Documentation","Train RNN","Train Transformer/LLM","Run AI Build Analysis","Generate Installation Plan","Generate AI Build Plan","Diagnose Build Error","Explain ISO Build","View Sources","View Learning Dataset","View Model Metrics","Offline AI Mode"]}
class UnifiedApp(tk.Tk):
 def __init__(self):
  super().__init__();self.title('ISO-Tool — Source → Build → Spit Fire → Bootable ISO');self.geometry('1400x920');self.repo=tk.StringVar(value='.');self.status=tk.StringVar(value='Ready');self.q=queue.Queue();self.buttons=[];self.ui()
 def ui(self):
  ttk.Label(self,text=self.title(),font=('Segoe UI',20,'bold')).pack(anchor='w',padx=12,pady=10);top=ttk.Frame(self);top.pack(fill='x',padx=12);ttk.Entry(top,textvariable=self.repo).pack(side='left',fill='x',expand=True);ttk.Button(top,text='Browse…',command=self.browse).pack(side='left');c=tk.Canvas(self);s=ttk.Scrollbar(self,command=c.yview);b=ttk.Frame(c);b.bind('<Configure>',lambda e:c.configure(scrollregion=c.bbox('all')));c.create_window((0,0),window=b,anchor='nw');c.configure(yscrollcommand=s.set);c.pack(side='left',fill='both',expand=True);s.pack(side='right',fill='y')
  for g,fs in GROUPS.items():
   box=ttk.LabelFrame(b,text=g);box.pack(fill='x',padx=8,pady=4)
   for f in fs:
    x=ttk.Button(box,text=f,command=lambda z=f:self.run(z));x.pack(side='left',padx=2,pady=2);self.buttons.append(x)
  ttk.Label(self,textvariable=self.status).pack(fill='x',padx=12);self.log=tk.Text(self,height=12);self.log.pack(fill='both',padx=12,pady=8)
 def browse(self):
  p=filedialog.askdirectory();
  if p:self.repo.set(p)
 def run(self,f): threading.Thread(target=self.work,args=(f,),daemon=True).start()
 def work(self,f):
  try:
   root=Path(self.repo.get()).resolve();out=root/'iso-tool-knowledge';out.mkdir(exist_ok=True);self.status.set(f+' — running')
   if f=='Web Search':r=search_web('ISO build installation compiler dependencies')
   elif f=='Crawl Website':r=[x.__dict__ for x in WebCrawler(out/'cache').crawl(self.repo.get())]
   elif f in {'Crawl Documentation','Crawl Repository References','Index Documentation','Build Knowledge Base'}:r=ingest_repository(root,out/'repository.jsonl')
   elif f in {'Train RNN','Train Transformer/LLM'}:r=NeuralEngine().train_from_build_sequences([[1,2,3],[2,3,4]])
   elif f in {'Generate Installation Plan','Generate AI Build Plan','Run AI Build Analysis','Diagnose Build Error','Explain ISO Build'}:r=generate_build_plan(out)
   else:r={'feature':f,'authorization_required':True}
   self.log.insert('end',json.dumps(r,indent=2)+'\n');self.status.set(f+' — complete')
  except Exception as e:self.log.insert('end','[error] '+str(e)+'\n');self.status.set(f+' — failed')
