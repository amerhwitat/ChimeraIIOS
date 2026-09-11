from pathlib import Path
import queue, threading, tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from iso_tool.github_source import is_github_reference, normalize_github_repository, prepare_source
from iso_tool.build_entrypoint import build
from iso_tool.output_paths import dependency_cache_dir, suggested_output_dir, prepare_output_layout

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('ISO-Tool — GitHub repository → compile/link → ISO/IMG'); self.geometry('1120x840'); self.repo=tk.StringVar(value='https://github.com/amerhwitat/ChimeraIIOS'); self.out=tk.StringVar(value=str(suggested_output_dir())); self.q=queue.Queue(); self.busy=False
        ttk.Label(self,text='GitHub repository or local source repository').pack(anchor='w',padx=12,pady=(12,2)); r=ttk.Frame(self); r.pack(fill='x',padx=12); ttk.Entry(r,textvariable=self.repo).pack(side='left',fill='x',expand=True); ttk.Button(r,text='Select GitHub repo…',command=self.select_repo).pack(side='left',padx=8); ttk.Button(r,text='Browse local…',command=self.select_local).pack(side='left')
        ttk.Label(self,text='Final output directory').pack(anchor='w',padx=12,pady=(8,2)); r=ttk.Frame(self); r.pack(fill='x',padx=12); ttk.Entry(r,textvariable=self.out).pack(side='left',fill='x',expand=True); ttk.Button(r,text='Choose…',command=self.choose_output).pack(side='left',padx=8); ttk.Label(self,text=f'Dependency cache: {dependency_cache_dir()}').pack(anchor='w',padx=12)
        r=ttk.Frame(self); r.pack(fill='x',padx=12,pady=10); self.btn=ttk.Button(r,text='Compile + Link (GNU + MSVC)',command=self.start); self.btn.pack(side='left'); ttk.Button(r,text='Clear',command=lambda:self.log.delete('1.0','end')).pack(side='left',padx=8); self.status=ttk.Label(self,text='Ready'); self.status.pack(anchor='w',padx=12); self.log=tk.Text(self,height=34,font=('Consolas',10)); self.log.pack(fill='both',expand=True,padx=12,pady=8); self.after(75,self.drain)
    def select_repo(self):
        v=simpledialog.askstring('Select GitHub repository','Enter GitHub URL or owner/repository:',initialvalue=self.repo.get())
        if v:
            try:self.repo.set('https://github.com/'+normalize_github_repository(v)); self.write('[source] '+self.repo.get())
            except ValueError as e: messagebox.showerror('ISO-Tool',str(e))
    def select_local(self):
        v=filedialog.askdirectory(title='Select local repository');
        if v:self.repo.set(v); self.write('[source] '+v)
    def choose_output(self):
        v=filedialog.askdirectory(title='Choose final output directory',initialdir=self.out.get(),mustexist=False)
        if v:self.out.set(v); self.write('[output] '+v)
    def write(self,s): self.log.insert('end',s+'\n'); self.log.see('end')
    def drain(self):
        try:
            while True:
                k,v=self.q.get_nowait(); self.write(v); self.status.configure(text=v)
                if k=='done': self.busy=False; self.btn.configure(state='normal')
        except queue.Empty: pass
        self.after(75,self.drain)
    def start(self):
        if self.busy:return
        self.busy=True; self.btn.configure(state='disabled'); threading.Thread(target=self.worker,daemon=True).start()
    def worker(self):
        try:
            out=Path(self.out.get()).expanduser(); layout=prepare_output_layout(out); value=self.repo.get().strip(); checkout=out/'sources'/normalize_github_repository(value).replace('/','__') if is_github_reference(value) else Path(value).expanduser(); source=prepare_source(value,checkout) if is_github_reference(value) else checkout.resolve(); self.q.put(('log',f'[source] {source}'))
            for key,label in [('gnu','GNU C++'),('msvc','Microsoft Visual C++')]:
                try: build(source,out,key,log=lambda m,l=label:self.q.put(('log',f'[{l}] {m}')))
                except Exception as e:self.q.put(('log',f'[{label}] unavailable or failed: {type(e).__name__}: {e}'))
            self.q.put(('done',f'Build entry point finished. Artifacts: {layout["executables"]} and {layout["libraries"]}'))
        except Exception as e:self.q.put(('done',f'Build stopped: {type(e).__name__}: {e}'))
if __name__=='__main__': App().mainloop()
