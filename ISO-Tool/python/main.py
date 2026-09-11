from pathlib import Path
import json,queue,threading,shutil,tkinter as tk
from tkinter import filedialog,messagebox,simpledialog,ttk
from iso_tool import dependency_cache_dir,suggested_output_dir,prepare_output_layout
from iso_tool.boot_import import import_boot_sector,inspect_image
from iso_tool.github_source import classify_source,is_source_reference,normalize_github_repository,prepare_source
from iso_tool.build_entrypoint import build
from iso_tool.build_planner import make_plan
from iso_tool.application_discovery import discover_applications,install_authorized_packages
from iso_tool.iso_merger import merge_staging
from iso_tool.image import create_iso
from iso_tool.tree_scanner import scan_tree
from iso_tool.toolchain_bootstrap import scan_windows,write_plan
from iso_tool.boot_builder import build_spit_fire
class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('ISO-Tool — Deep scan → toolchains → Spit Fire bootable ISO');self.geometry('1240x1040');self.repo=tk.StringVar(value='https://github.com/amerhwitat/ChimeraIIOS');self.out=tk.StringVar(value=str(suggested_output_dir()));self.iso_out=tk.StringVar();self.img_out=tk.StringVar();self.boot_out=tk.StringVar();self.bin_out=tk.StringVar();self.target=tk.StringVar(value='Chimera II OS');self.manager=tk.StringVar(value='winget');self.packages=tk.StringVar();self.progress=tk.DoubleVar();self.status=tk.StringVar(value='Ready');self.events=queue.Queue();self.running=False
        ttk.Label(self,text='Git / GitHub / ZIP / TAR / local source').pack(anchor='w',padx=12,pady=(12,2));r=ttk.Frame(self);r.pack(fill='x',padx=12);ttk.Entry(r,textvariable=self.repo).pack(side='left',fill='x',expand=True);ttk.Button(r,text='Browse Source…',command=self.select_source).pack(side='left',padx=8);ttk.Button(r,text='GitHub…',command=self.select_repo).pack(side='left')
        ttk.Label(self,text='Intended system').pack(anchor='w',padx=12,pady=(8,2));ttk.Entry(self,textvariable=self.target).pack(fill='x',padx=12)
        ttk.Label(self,text='Optional applications/packages').pack(anchor='w',padx=12,pady=(6,2));r=ttk.Frame(self);r.pack(fill='x',padx=12);ttk.Entry(r,textvariable=self.packages).pack(side='left',fill='x',expand=True);ttk.Combobox(r,textvariable=self.manager,values=('winget','apt','dnf','zypper','pacman','apk','xbps','portage','homebrew','flatpak','snap','chocolatey','scoop'),state='readonly',width=16).pack(side='left',padx=8);ttk.Label(self,text='Package installation occurs only after the explicit install action.').pack(anchor='w',padx=12)
        ttk.Label(self,text='Output locations').pack(anchor='w',padx=12,pady=(8,2));self._path_row('Build root',self.out,self.choose_output);self._path_row('ISO file',self.iso_out,self.choose_iso);self._path_row('IMG file',self.img_out,self.choose_img);self._path_row('Boot images',self.boot_out,self.choose_boot);self._path_row('Executables/libraries',self.bin_out,self.choose_bins)
        ttk.Label(self,text=f'Dependency cache: {dependency_cache_dir()}').pack(anchor='w',padx=12,pady=(2,6));b=ttk.Frame(self);b.pack(fill='x',padx=12,pady=10)
        self.analyze_button=ttk.Button(b,text='Deep Scan + Plan',command=self.inventory);self.analyze_button.pack(side='left');self.apps_button=ttk.Button(b,text='Discover Applications',command=self.discover_apps);self.apps_button.pack(side='left',padx=6);self.install_button=ttk.Button(b,text='Install Selected Packages',command=self.install_apps);self.install_button.pack(side='left');self.import_button=ttk.Button(b,text='Import Boot/ISO',command=self.import_image);self.import_button.pack(side='left',padx=6);self.build_images_button=ttk.Button(b,text='Scan Windows Toolchains',command=self.scan_toolchains);self.build_images_button.pack(side='left');self.build_button=ttk.Button(b,text='Compile + Bootable ISO/IMG',command=self.build_iso);self.build_button.pack(side='left',padx=6);ttk.Button(b,text='Clear',command=self.clear_log).pack(side='left')
        ttk.Label(self,textvariable=self.status).pack(anchor='w',padx=12);ttk.Progressbar(self,variable=self.progress,maximum=100).pack(fill='x',padx=12,pady=8);self.log=tk.Text(self,height=34,state='disabled',font=('Consolas',10));self.log.pack(fill='both',expand=True,padx=12,pady=8);self.after(75,self._drain_events)
    def _path_row(self,label,var,command):
        ttk.Label(self,text=label).pack(anchor='w',padx=12,pady=(2,0));r=ttk.Frame(self);r.pack(fill='x',padx=12);ttk.Entry(r,textvariable=var).pack(side='left',fill='x',expand=True);ttk.Button(r,text='Choose…',command=command).pack(side='left',padx=8)
    def select_source(self):
        p=filedialog.askopenfilename(title='Select source archive',filetypes=[('Source archives','*.zip *.tar *.gz *.tgz *.bz2 *.xz'),('All','*.*')]);
        if p:self.repo.set(p);self._append('[source] '+p)
    def select_repo(self):
        v=simpledialog.askstring('Source repository','Enter GitHub URL or owner/repository:',initialvalue=self.repo.get())
        if v:
            try:self.repo.set('https://github.com/'+normalize_github_repository(v));self._append('[source] '+self.repo.get())
            except ValueError as exc:messagebox.showerror('ISO-Tool',str(exc))
    def choose_output(self):
        p=filedialog.askdirectory(title='Choose build/output root',initialdir=self.out.get());
        if p:self.out.set(p)
    def choose_iso(self):
        p=filedialog.asksaveasfilename(title='Choose generated ISO',initialdir=self.out.get(),defaultextension='.iso',filetypes=[('ISO image','*.iso')]);
        if p:self.iso_out.set(p)
    def choose_img(self):
        p=filedialog.asksaveasfilename(title='Choose generated IMG',initialdir=self.out.get(),defaultextension='.img',filetypes=[('Disk image','*.img')]);
        if p:self.img_out.set(p)
    def choose_boot(self):
        p=filedialog.askdirectory(title='Choose boot-image directory',initialdir=self.out.get());
        if p:self.boot_out.set(p)
    def choose_bins(self):
        p=filedialog.askdirectory(title='Choose executable/library directory',initialdir=self.out.get());
        if p:self.bin_out.set(p)
    def clear_log(self):self.log.configure(state='normal');self.log.delete('1.0','end');self.log.configure(state='disabled')
    def _append(self,m):self.log.configure(state='normal');self.log.insert('end',m+'\n');self.log.see('end');self.log.configure(state='disabled')
    def _drain_events(self):
        try:
            while True:
                k,p=self.events.get_nowait()
                if k=='progress':self.progress.set(p[0]);self.status.set(p[1]);self._append(p[1])
                elif k=='log':self._append(p)
                elif k=='done':self.running=False;self._set_buttons(True);self.status.set(p);self._append(p)
        except queue.Empty:pass
        self.after(75,self._drain_events)
    def _set_buttons(self,e):
        for x in (self.analyze_button,self.apps_button,self.install_button,self.import_button,self.build_images_button,self.build_button):x.configure(state='normal' if e else 'disabled')
    def _start(self,fn):
        if self.running:return
        self.running=True;self._set_buttons(False);self.progress.set(0);threading.Thread(target=fn,daemon=True).start()
    def _source(self):
        v=self.repo.get().strip()
        if not is_source_reference(v):raise ValueError('Enter a Git/GitHub URL, archive, or local source directory.')
        safe=v.replace('https://','').replace('://','_').replace('/','__').replace('\\','__');return prepare_source(v,Path(self.out.get())/'sources'/safe)
    def inventory(self):self._start(self._inventory_worker)
    def _inventory_worker(self):
        try:
            root=self._source();result=scan_tree(root,Path(self.out.get())/'knowledge'/'repository-tree.json');plan=make_plan(root,Path(self.out.get())/'knowledge');self.events.put(('log',f'[deep scan] {result["summary"]["files"]} files; languages={result["summary"]["languages"]}'));self.events.put(('log','[tree] '+str(Path(self.out.get())/'knowledge'/'repository-tree.json')));self.events.put(('log','[plan] '+', '.join(s['id'] for s in plan['steps'])));self.events.put(('done','Deep recursive hierarchical source scan complete.'))
        except Exception as exc:self.events.put(('log',f'[error] {type(exc).__name__}: {exc}'));self.events.put(('done','Analysis stopped.'))
    def scan_toolchains(self):self._start(self._toolchain_worker)
    def _toolchain_worker(self):
        try:
            layout=prepare_output_layout(Path(self.out.get()));report=scan_windows(Path(layout['manifests'])/'windows-toolchains.json');plan=write_plan(Path(layout['manifests'])/'toolchain-bootstrap-plan.json',report);self.events.put(('log',json.dumps(report,indent=2)));self.events.put(('log',json.dumps(plan,indent=2)));self.events.put(('done','Windows compiler/assembler scan and bootstrap plan complete.'))
        except Exception as exc:self.events.put(('log',f'[toolchain error] {exc}'));self.events.put(('done','Toolchain scan stopped.'))
    def discover_apps(self):self._start(lambda:self._apps_worker(False))
    def install_apps(self):self._start(lambda:self._apps_worker(True))
    def _apps_worker(self,install):
        try:
            root=self._source();result=discover_applications(root,self.target.get());self.events.put(('log',json.dumps(result,indent=2)))
            if install:
                packages=[p for p in self.packages.get().split() if p]
                if not packages:raise ValueError('Enter at least one package/application identifier.')
                install_authorized_packages(result,self.manager.get(),packages,yes=True,log=lambda m:self.events.put(('log',m)));self.events.put(('done','Selected packages installed.'))
            else:self.events.put(('done',f'Discovered {len(result["discovered"])} application/build entries.'))
        except Exception as exc:self.events.put(('log',f'[error] {exc}'));self.events.put(('done','Application operation stopped.'))
    def import_image(self):
        source=filedialog.askopenfilename(title='Import boot/ISO image',filetypes=[('Images','*.iso *.img *.bin'),('All','*.*')]);
        if not source:return
        target=filedialog.asksaveasfilename(title='Save boot image',initialdir=self.boot_out.get() or str(Path(self.out.get())/'boot-images'),defaultextension='.bin');
        if target:self._start(lambda:self._import_worker(Path(source),Path(target)))
    def _import_worker(self,source,target):
        try:info=inspect_image(source);self.events.put(('log',f'[image] {info.kind} {info.size} bytes bootable={info.bootable}'));import_boot_sector(source,target);self.events.put(('done',f'Imported: {target}'))
        except Exception as exc:self.events.put(('log',f'[error] {exc}'));self.events.put(('done','Import stopped.'))
    def build_iso(self):self._start(self._build_worker)
    def _build_worker(self):
        try:
            layout=prepare_output_layout(Path(self.out.get()));root=self._source();self.events.put(('progress',(10,'Recursively scanning repository and planning builds…')))
            for n,key in enumerate(('gnu','msvc'),1):
                try:build(root,Path(layout['root']),key,log=lambda m,l=key:self.events.put(('log',f'[{l}] {m}')))
                except Exception as exc:self.events.put(('log',f'[{key}] unavailable/failed: {exc}'))
                self.events.put(('progress',(20+n*20,f'{key} recursive build stage finished')))
            boot=Path(self.boot_out.get()) if self.boot_out.get().strip() else Path(layout['boot_images']);boot.mkdir(parents=True,exist_ok=True);boot_bin=boot/'first_stage.bin';boot_source=Path(__file__).resolve().parents[1]/'boot'/'bios'/'first_stage.asm';build_spit_fire(boot_source,boot_bin,log=lambda m:self.events.put(('log',m)))
            staging=Path(layout['root'])/'staging';manifest=Path(layout['manifests'])/'staging-manifest.json';merge_staging(root,staging,manifest);dst=staging/'boot'/'bios'/'first_stage.bin';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(boot_bin,dst);self.events.put(('log',f'[boot] validated Spit Fire BIOS sector: {boot_bin}'))
            iso=Path(self.iso_out.get()) if self.iso_out.get().strip() else Path(layout['iso'])/f'Chimera-II-{root.name}.iso';create_iso(staging,iso,label='CHIMERA_II',profile='bios-only');img=Path(self.img_out.get()) if self.img_out.get().strip() else Path(layout['root'])/'img'/f'Chimera-II-{root.name}.img';img.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(iso,img);self.events.put(('progress',(100,'Bootable ISO/IMG generation complete')));self.events.put(('log',json.dumps({'iso':str(iso),'img':str(img),'spit_fire':str(boot_bin),'bootable_profile':'bios-only'},indent=2)));self.events.put(('done','Recursive scan, compiler/toolchain integration, Spit Fire boot-sector validation, compile/link, staging, and bootable ISO/IMG pipeline completed; inspect manifests and logs.'))
        except Exception as exc:self.events.put(('log',f'[fatal] {type(exc).__name__}: {exc}'));self.events.put(('done','Build stopped with an error.'))
if __name__=='__main__':App().mainloop()
