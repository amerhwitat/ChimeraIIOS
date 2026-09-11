from pathlib import Path
import json, queue, threading, shutil, tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from iso_tool import dependency_cache_dir, suggested_output_dir, prepare_output_layout
from iso_tool.boot_import import import_boot_sector, inspect_image
from iso_tool.github_source import classify_source, is_source_reference, normalize_github_repository, prepare_source
from iso_tool.build_entrypoint import build
from iso_tool.build_planner import make_plan
from iso_tool.application_discovery import discover_applications, install_authorized_packages
from iso_tool.iso_merger import merge_staging
from iso_tool.image import create_iso
class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('ISO-Tool — Git/GitHub/Archive → scan → compile → ISO/IMG');self.geometry('1240x980');self.repo=tk.StringVar(value='https://github.com/amerhwitat/ChimeraIIOS');self.out=tk.StringVar(value=str(suggested_output_dir()));self.iso_out=tk.StringVar();self.img_out=tk.StringVar();self.boot_out=tk.StringVar();self.bin_out=tk.StringVar();self.target=tk.StringVar(value='Chimera II OS');self.manager=tk.StringVar(value='winget');self.packages=tk.StringVar();self.progress=tk.DoubleVar();self.status=tk.StringVar(value='Ready');self.events=queue.Queue();self.running=False
        ttk.Label(self,text='Git / GitHub / ZIP / TAR / local source').pack(anchor='w',padx=12,pady=(12,2));source=ttk.Frame(self);source.pack(fill='x',padx=12);ttk.Entry(source,textvariable=self.repo).pack(side='left',fill='x',expand=True);ttk.Button(source,text='Browse Source…',command=self.select_source).pack(side='left',padx=8);ttk.Button(source,text='GitHub…',command=self.select_repo).pack(side='left')
        ttk.Label(self,text='Intended system').pack(anchor='w',padx=12,pady=(8,2));ttk.Entry(self,textvariable=self.target).pack(fill='x',padx=12);ttk.Label(self,text='Optional applications/packages (space separated)').pack(anchor='w',padx=12,pady=(6,2));app_row=ttk.Frame(self);app_row.pack(fill='x',padx=12);ttk.Entry(app_row,textvariable=self.packages).pack(side='left',fill='x',expand=True);ttk.Combobox(app_row,textvariable=self.manager,values=('winget','apt','dnf','zypper','pacman','apk','xbps','portage','homebrew','flatpak','snap','chocolatey','scoop'),state='readonly',width=16).pack(side='left',padx=8);ttk.Label(self,text='Package installation is performed only after pressing the explicit install button.').pack(anchor='w',padx=12)
        ttk.Label(self,text='Build/output root').pack(anchor='w',padx=12,pady=(8,2));self._path_row('Build root',self.out,self.choose_output);self._path_row('ISO file',self.iso_out,self.choose_iso);self._path_row('IMG file',self.img_out,self.choose_img);self._path_row('Boot images',self.boot_out,self.choose_boot);self._path_row('Executables/libraries',self.bin_out,self.choose_bins);ttk.Label(self,text=f'Dependency cache: {dependency_cache_dir()}').pack(anchor='w',padx=12,pady=(2,6))
        buttons=ttk.Frame(self);buttons.pack(fill='x',padx=12,pady=10);self.analyze_button=ttk.Button(buttons,text='Analyze Source + Plan',command=self.inventory);self.analyze_button.pack(side='left');self.apps_button=ttk.Button(buttons,text='Discover Applications',command=self.discover_apps);self.apps_button.pack(side='left',padx=8);self.install_button=ttk.Button(buttons,text='Install Selected Packages',command=self.install_apps);self.install_button.pack(side='left');self.import_button=ttk.Button(buttons,text='Import Boot/ISO',command=self.import_image);self.import_button.pack(side='left',padx=8);self.build_images_button=ttk.Button(buttons,text='Compile All Recognized',command=self.build_images);self.build_images_button.pack(side='left',padx=8);self.build_button=ttk.Button(buttons,text='Build ISO + IMG',command=self.build_iso);self.build_button.pack(side='left');ttk.Button(buttons,text='Clear',command=self.clear_log).pack(side='left',padx=8)
        ttk.Label(self,textvariable=self.status).pack(anchor='w',padx=12);ttk.Progressbar(self,variable=self.progress,maximum=100).pack(fill='x',padx=12,pady=8);self.log=tk.Text(self,height=31,state='disabled',font=('Consolas',10));self.log.pack(fill='both',expand=True,padx=12,pady=8);self.after(75,self._drain_events)
    def _path_row(self,label,variable,command):
        ttk.Label(self,text=label).pack(anchor='w',padx=12,pady=(2,0));row=ttk.Frame(self);row.pack(fill='x',padx=12);ttk.Entry(row,textvariable=variable).pack(side='left',fill='x',expand=True);ttk.Button(row,text='Choose…',command=command).pack(side='left',padx=8)
    def select_source(self):
        p=filedialog.askopenfilename(title='Select source archive or repository snapshot',filetypes=[('Source archives','*.zip *.tar *.gz *.tgz *.bz2 *.xz'),('All','*.*')]);
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
        p=filedialog.asksaveasfilename(title='Choose generated ISO file',initialdir=self.out.get(),defaultextension='.iso',filetypes=[('ISO image','*.iso'),('All','*.*')]);
        if p:self.iso_out.set(p)
    def choose_img(self):
        p=filedialog.asksaveasfilename(title='Choose generated IMG file',initialdir=self.out.get(),defaultextension='.img',filetypes=[('Disk image','*.img'),('All','*.*')]);
        if p:self.img_out.set(p)
    def choose_boot(self):
        p=filedialog.askdirectory(title='Choose boot-image directory',initialdir=self.out.get());
        if p:self.boot_out.set(p)
    def choose_bins(self):
        p=filedialog.askdirectory(title='Choose binary/library directory',initialdir=self.out.get());
        if p:self.bin_out.set(p)
    def clear_log(self):self.log.configure(state='normal');self.log.delete('1.0','end');self.log.configure(state='disabled')
    def _append(self,message):self.log.configure(state='normal');self.log.insert('end',message+'\n');self.log.see('end');self.log.configure(state='disabled')
    def _drain_events(self):
        try:
            while True:
                kind,payload=self.events.get_nowait()
                if kind=='progress':self.progress.set(payload[0]);self.status.set(payload[1]);self._append(payload[1])
                elif kind=='log':self._append(payload)
                elif kind=='done':self.running=False;self._set_buttons(True);self.status.set(payload);self._append(payload)
        except queue.Empty:pass
        self.after(75,self._drain_events)
    def _set_buttons(self,enabled):
        for button in (self.analyze_button,self.apps_button,self.install_button,self.import_button,self.build_images_button,self.build_button):button.configure(state='normal' if enabled else 'disabled')
    def _start(self,target):
        if self.running:return
        self.running=True;self._set_buttons(False);self.progress.set(0);threading.Thread(target=target,daemon=True).start()
    def _source(self):
        value=self.repo.get().strip()
        if not is_source_reference(value):raise ValueError('Enter a Git/GitHub URL, source archive, or local source directory.')
        kind=classify_source(value);safe=value.replace('https://','').replace('://','_').replace('/','__').replace('\\','__');destination=Path(self.out.get())/'sources'/safe;self.events.put(('log',f'[{kind}] acquiring source into {destination}'));return prepare_source(value,destination)
    def inventory(self):self._start(self._inventory_worker)
    def _inventory_worker(self):
        try:
            root=self._source();plan=make_plan(root,Path(self.out.get())/'knowledge');self.events.put(('log',f'[scan] source: {root}'));self.events.put(('log','[plan] '+', '.join(step['id'] for step in plan['steps'])));self.events.put(('done','Source analysis and build plan complete.'))
        except Exception as exc:self.events.put(('log',f'[error] {type(exc).__name__}: {exc}'));self.events.put(('done','Analysis stopped.'))
    def discover_apps(self):self._start(self._discover_apps_worker)
    def _discover_apps_worker(self):
        try:
            root=self._source();result=discover_applications(root,self.target.get());self.events.put(('log',f'[applications] discovered {len(result["discovered"])} application/build entries'));self.events.put(('log',json.dumps(result,indent=2)));self.events.put(('done','Application discovery complete.'))
        except Exception as exc:self.events.put(('log',f'[error] {exc}'));self.events.put(('done','Application discovery stopped.'))
    def install_apps(self):self._start(self._install_apps_worker)
    def _install_apps_worker(self):
        try:
            packages=[p for p in self.packages.get().split() if p]
            if not packages:raise ValueError('Enter at least one package/application identifier.')
            root=self._source();result=discover_applications(root,self.target.get());install_authorized_packages(result,self.manager.get(),packages,yes=True,log=lambda m:self.events.put(('log',m)));self.events.put(('done',f'Installed selected packages for {self.target.get()}: '+', '.join(packages)))
        except Exception as exc:self.events.put(('log',f'[package error] {exc}'));self.events.put(('done','Package installation stopped.'))
    def import_image(self):
        source=filedialog.askopenfilename(title='Import boot/ISO image',filetypes=[('Images','*.iso *.img *.bin'),('All','*.*')]);
        if not source:return
        target=filedialog.asksaveasfilename(title='Save boot image',initialdir=self.boot_out.get() or str(Path(self.out.get())/'boot-images'),defaultextension='.bin');
        if target:self._start(lambda:self._import_worker(Path(source),Path(target)))
    def _import_worker(self,source,target):
        try:
            info=inspect_image(source);self.events.put(('log',f'[image] {info.kind} {info.size} bytes bootable={info.bootable}'));import_boot_sector(source,target);self.events.put(('done',f'Imported: {target}'))
        except Exception as exc:self.events.put(('log',f'[error] {exc}'));self.events.put(('done','Import stopped.'))
    def build_images(self):self._start(lambda:self._build_worker(False))
    def build_iso(self):self._start(lambda:self._build_worker(True))
    def _build_worker(self,make_images):
        try:
            layout=prepare_output_layout(Path(self.out.get()));root=self._source();results=[]
            for n,(key,label) in enumerate([('gnu','GNU'),('msvc','MSVC')],1):
                try:self.events.put(('log',f'[{label}] compiling recognized build systems'));results.append(build(root,Path(layout['root']),key,log=lambda m,l=label:self.events.put(('log',f'[{l}] {m}'))))
                except Exception as exc:self.events.put(('log',f'[{label}] unavailable/failed: {exc}'))
                self.events.put(('progress',(n*35,f'{label} stage finished')))
            if not results:raise RuntimeError('No recognized build system produced artifacts.')
            if make_images:
                staging=Path(layout['root'])/'staging';manifest=Path(layout['manifests'])/'staging-manifest.json';merge_staging(root,staging,manifest);iso=Path(self.iso_out.get()) if self.iso_out.get().strip() else Path(layout['iso'])/f'Chimera-II-{root.name}.iso';create_iso(staging,iso,label='CHIMERA_II',profile='data');self.events.put(('log',f'[iso] generated {iso}'));img=Path(self.img_out.get()) if self.img_out.get().strip() else Path(layout['root'])/'img'/f'Chimera-II-{root.name}.img';img.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(iso,img);self.events.put(('log',f'[img] generated ISO9660-compatible image copy {img}'));self.events.put(('log','[outputs] '+json.dumps({'iso':str(iso),'img':str(img),'boot_images':str(self.boot_out.get() or layout['boot_images']),'binaries':str(self.bin_out.get() or layout['executables'])},indent=2)))
            self.events.put(('done','Source acquisition, scan, application discovery/install, compile/link, staging, and image pipeline completed; inspect manifests and logs.'))
        except Exception as exc:self.events.put(('log',f'[fatal] {type(exc).__name__}: {exc}'));self.events.put(('done','Build stopped with an error.'))
if __name__=='__main__':App().mainloop()
