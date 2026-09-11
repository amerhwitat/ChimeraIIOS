from pathlib import Path
import queue,threading,tkinter as tk
from tkinter import filedialog,messagebox,simpledialog,ttk
from iso_tool.github_source import is_github_reference,normalize_github_repository,prepare_source
from iso_tool.build_entrypoint import build
from iso_tool.build_planner import make_plan
from iso_tool.output_paths import dependency_cache_dir,suggested_output_dir,prepare_output_layout
from iso_tool.iso_merger import merge_staging
from iso_tool.image import create_iso
class App(tk.Tk):
 def __init__(self):
  super().__init__();self.title('ISO-Tool — document-aware GitHub → compile/link → ISO');self.geometry('1160x860');self.repo=tk.StringVar(value='https://github.com/amerhwitat/ChimeraIIOS');self.out=tk.StringVar(value=str(suggested_output_dir()));self.q=queue.Queue();self.busy=False
  ttk.Label(self,text='GitHub repository or local source repository').pack(anchor='w',padx=12,pady=(12,2));r=ttk.Frame(self);r.pack(fill='x',padx=12);ttk.Entry(r,textvariable=self.repo).pack(side='left',fill='x',expand=True);ttk.Button(r,text='Select GitHub repo…',command=self.select_repo).pack(side='left',padx=8);ttk.Button(r,text='Browse local…',command=self.select_local).pack(side='left')
  ttk.Label(self,text='Final output directory').pack(anchor='w',padx=12,pady=(8,2));ttk.Entry(self,textvariable=self.out).pack(fill='x',padx=12);ttk.Button(self,text='Choose output…',command=self.choose_output).pack(anchor='e',padx=12);ttk.Label(self,text=f'Dependency cache: {dependency_cache_dir()}').pack(anchor='w',padx=12)
  r=ttk.Frame(self);r.pack(fill='x',padx=12,pady=10);self.analyze=ttk.Button(r,text='Analyze Documents + Plan',command=self.start_analysis);self.analyze.pack(side='left');self.btn=ttk.Button(r,text='AI Plan + Compile + Link + ISO',command=self.start);self.btn.pack(side='left',padx=8);ttk.Button(r,text='Clear',command=lambda:self.log.delete('1.0','end')).pack(side='left');self.status=ttk.Label(self,text='Ready');self.status.pack(anchor='w',padx=12);self.log=tk.Text(self,height=34,font=('Consolas',10));self.log.pack(fill='both',expand=True,padx=12,pady=8);self.after(75,self.drain)
 def select_repo(self):
  v=simpledialog.askstring('Select GitHub repository','Enter GitHub URL or owner/repository:',initialvalue=self.repo.get())
  if v:
   try:self.repo.set('https://github.com/'+normalize_github_repository(v));self.write('[source] '+self.repo.get())
   except ValueError as e:messagebox.showerror('ISO-Tool',str(e))
 def select_local(self):
  v=filedialog.askdirectory(title='Select local repository');
  if v:self.repo.set(v);self.write('[source] '+v)
 def write(self,s):self.log.insert('end',s+'\n');self.log.see('end')
 def drain(self):
  try:
   while True:
    k,v=self.q.get_nowait();self.write(v);self.status.configure(text=v)
    if k=='done':self.busy=False;self.btn.configure(state='normal');self.analyze.configure(state='normal')
  except queue.Empty:pass
  self.after(75,self.drain)
 def source(self):
  out=Path(self.out.get()).expanduser();v=self.repo.get().strip();p=out/'sources'/normalize_github_repository(v).replace('/','__') if is_github_reference(v) else Path(v).expanduser();return prepare_source(v,p) if is_github_reference(v) else p.resolve()
 def start_analysis(self):
  if self.busy:return
  self.busy=True;self.analyze.configure(state='disabled');threading.Thread(target=self.analysis,daemon=True).start()
 def analysis(self):
  try:s=self.source();p=make_plan(s,Path(self.out.get())/'knowledge');self.q.put(('log',f'[documents] {s}'));self.q.put(('log','[plan] '+' → '.join(x['id'] for x in p['steps'])));self.q.put(('done','Analysis and precedence plan complete.'))
  except Exception as e:self.q.put(('done',f'Analysis failed: {e}'))
 def start(self):
  if self.busy:return
  self.busy=True;self.btn.configure(state='disabled');self.analyze.configure(state='disabled');threading.Thread(target=self.worker,daemon=True).start()
 def worker(self):
  try:
   out=Path(self.out.get()).expanduser();layout=prepare_output_layout(out);source=self.source();self.q.put(('log',f'[source] {source}'));results=[]
   for key,label in [('gnu','GNU C++'),('msvc','MSVC')]:
    try:results.append(build(source,out,key,log=lambda m,l=label:self.q.put(('log',f'[{l}] {m}'))))
    except Exception as e:self.q.put(('log',f'[{label}] unavailable or failed: {e}'))
   if not results:raise RuntimeError('No compiler produced artifacts')
   staging=out/'staging';manifest=Path(layout['manifests'])/'staging-manifest.json';merge_staging(source,staging,manifest);iso=Path(layout['iso'])/f'Chimera-II-{source.name}.iso';create_iso(staging,iso,label='CHIMERA_II',profile='data');self.q.put(('done',f'ISO generated: {iso}'))
  except Exception as e:self.q.put(('done',f'Build stopped: {type(e).__name__}: {e}'))
if __name__=='__main__':App().mainloop()
