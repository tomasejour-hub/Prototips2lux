#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compresseur DeLuxe (PDF & Images) - version auto-fermeture
Ferme automatiquement l'application à la fin de la compression sans afficher le message final.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None

class CompresseurDeLuxe:
    def __init__(self):
        self.dossier_courant = os.path.dirname(os.path.abspath(__file__))
        self.niveaux = {
            'Faible (95%)': {'dpi': 300, 'quality': 95},
            'Moyenne (80%)': {'dpi': 200, 'quality': 80},
            'Forte (60%)': {'dpi': 150, 'quality': 60}
        }
        self.seuil_mo_defaut = 1.0
        self.mode = self.demander_mode_lancement()
        self.formats_pdf = ('.pdf', '.PDF')
        self.formats_images = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
        self.creer_interface()

    def demander_mode_lancement(self):
        root = tk.Tk(); root.withdraw()
        mode_var = tk.StringVar(value='pdf')
        dialog = tk.Toplevel(root)
        dialog.title("Choix du mode")
        dialog.resizable(False, False)
        dialog.grab_set()
        frm = ttk.Frame(dialog, padding=20); frm.grid(row=0, column=0)
        ttk.Label(frm, text="Que souhaitez-vous compresser ?", font=('Arial', 12, 'bold')).grid(row=0, column=0, pady=(0, 12))
        ttk.Radiobutton(frm, text="PDF", value='pdf', variable=mode_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(frm, text="Images (JPEG/PNG)", value='images', variable=mode_var).grid(row=2, column=0, sticky=tk.W)
        ttk.Button(frm, text="Valider", command=lambda: dialog.destroy()).grid(row=3, column=0, pady=(12, 0))
        dialog.wait_window(); root.destroy()
        return mode_var.get()

    def creer_interface(self):
        self.root = tk.Tk()
        self.root.title("Compresseur PDF" if self.mode == 'pdf' else "Compresseur Images")
        self.root.geometry("560x520")
        self.root.resizable(False, False)
        style = ttk.Style()
        try: style.theme_use('clam')
        except: pass

        main = ttk.Frame(self.root, padding="20"); main.grid(row=0, column=0)
        titre = "Compresseur de fichiers PDF" if self.mode == 'pdf' else "Compresseur d'images (JPEG/PNG)"
        ttk.Label(main, text=titre, font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0,20))
        count = self.compter_fichiers()
        info = f"Dossier : {os.path.basename(self.dossier_courant)}\n" + (f"PDF trouvés : {count}" if self.mode=='pdf' else f"Images trouvées : {count}")
        ttk.Label(main, text=info, font=('Arial',10)).grid(row=1, column=0, columnspan=2, pady=(0,20))

        ttk.Label(main, text="Niveau de compression :", font=('Arial',12)).grid(row=2, column=0, columnspan=2, pady=(0,10))
        self.niveau_var = tk.StringVar(value='Moyenne (80%)')
        desc = {
            'Faible (95%)': 'Qualité 95%',
            'Moyenne (80%)': 'Qualité 80%',
            'Forte (60%)': 'Qualité 60%'
        }
        r=3
        for n in self.niveaux:
            f = ttk.Frame(main); f.grid(row=r, column=0, columnspan=2, sticky=tk.W)
            ttk.Radiobutton(f, text=n, variable=self.niveau_var, value=n).pack(side=tk.LEFT)
            ttk.Label(f, text=f"  ({desc[n]})", font=('Arial',9), foreground='gray').pack(side=tk.LEFT)
            r+=1

        seuil_frame = ttk.LabelFrame(main, text=("Seuil (PDF uniquement)" if self.mode=='pdf' else "Seuil inactif"), padding="10")
        seuil_frame.grid(row=r, column=0, columnspan=2, pady=10, sticky=tk.EW)
        ttk.Label(seuil_frame, text="Ignorer < ").grid(row=0,column=0,sticky=tk.W)
        self.seuil_var = tk.StringVar(value=("1.0" if self.mode=='pdf' else "0"))
        ttk.Combobox(seuil_frame, textvariable=self.seuil_var, width=6, state=("readonly" if self.mode=='pdf' else "disabled"), values=["0.5","1","2","5","10"]).grid(row=0,column=1,padx=5)
        ttk.Label(seuil_frame, text="Mo").grid(row=0,column=2)

        save_frame = ttk.LabelFrame(main, text="Sauvegarde", padding="5")
        save_frame.grid(row=r+1,column=0,columnspan=2,sticky=tk.EW,pady=10)
        self.mode_sauvegarde = tk.StringVar(value='dossier')
        ttk.Radiobutton(save_frame, text="Créer un dossier avec les fichiers compressés", variable=self.mode_sauvegarde, value='dossier').grid(row=0,column=0,sticky=tk.W)
        ttk.Radiobutton(save_frame, text="⚠️ Remplacer les originaux (pas de sauvegarde)", variable=self.mode_sauvegarde, value='remplacer').grid(row=1,column=0,sticky=tk.W)

        btns = ttk.Frame(main); btns.grid(row=r+2,column=0,columnspan=2,pady=15)
        ttk.Button(btns,text="🗜️ COMPRESSER",command=self.demarrer_compression).pack(side=tk.LEFT,padx=5)
        ttk.Button(btns,text="❌ Quitter",command=self.root.quit).pack(side=tk.LEFT,padx=5)
        self.progress = ttk.Progressbar(main,mode='determinate'); self.progress.grid(row=r+3,column=0,columnspan=2,sticky=tk.EW,pady=10)
        self.status_label = ttk.Label(main,text="Prêt à compresser",font=('Arial',10)); self.status_label.grid(row=r+4,column=0,columnspan=2)

    def compter_fichiers(self):
        try:
            if self.mode=='pdf': return sum(1 for f in os.listdir(self.dossier_courant) if f.lower().endswith(self.formats_pdf))
            else: return sum(1 for f in os.listdir(self.dossier_courant) if f.lower().endswith(self.formats_images))
        except: return 0

    def demarrer_compression(self):
        niveau = self.niveau_var.get(); params = self.niveaux[niveau]; mode_s = self.mode_sauvegarde.get()
        self.btn_compresser = None
        target = self.compresser_pdfs if self.mode=='pdf' else self.compresser_images
        thread = threading.Thread(target=lambda: target(params, mode_s)); thread.daemon=True; thread.start()

    def compresser_pdfs(self, params, mode_s):
        fichiers = [f for f in os.listdir(self.dossier_courant) if f.lower().endswith(self.formats_pdf)]
        dossier_sortie=None
        if mode_s=='dossier':
            dossier_sortie=os.path.join(self.dossier_courant,f"compressed_{params['quality']}q"); os.makedirs(dossier_sortie,exist_ok=True)
        for i,f in enumerate(fichiers):
            chemin=os.path.join(self.dossier_courant,f)
            doc=fitz.open(chemin); imgs=[]
            for p in doc:
                pix=p.get_pixmap(dpi=params['dpi'])
                img=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
                tmp=f"tmp_{i}_{p.number}.jpg"; img.save(tmp,"JPEG",quality=params['quality']); imgs.append(tmp)
            out=os.path.join(dossier_sortie,f) if mode_s=='dossier' else chemin+".tmp.pdf"
            imlist=[Image.open(x).convert('RGB') for x in imgs]
            imlist[0].save(out,save_all=True,append_images=imlist[1:])
            for x in imgs: os.remove(x)
            if mode_s=='remplacer': os.replace(out,chemin)
            self.progress['value']=((i+1)/len(fichiers))*100
        self.root.quit()

    def compresser_images(self, params, mode_s):
        fichiers=[f for f in os.listdir(self.dossier_courant) if f.lower().endswith(self.formats_images)]
        dossier_sortie=None
        if mode_s=='dossier':
            dossier_sortie=os.path.join(self.dossier_courant,f"compressed_images_{params['quality']}q"); os.makedirs(dossier_sortie,exist_ok=True)
        for i,f in enumerate(fichiers):
            src=os.path.join(self.dossier_courant,f)
            dst=os.path.join(dossier_sortie,f) if mode_s=='dossier' else src+".tmp"
            with Image.open(src) as im:
                im=self._safe_exif_transpose(im)
                fmt=(im.format or os.path.splitext(f)[1][1:].upper())
                if fmt.upper() in ("JPEG","JPG"):
                    im.convert("RGB").save(dst,format="JPEG",quality=params['quality'],optimize=True,progressive=True)
                else:
                    lvl=9 if params['quality']<=60 else (6 if params['quality']<=80 else 1)
                    im.save(dst,format="PNG",optimize=True,compress_level=lvl)
            if mode_s=='remplacer': os.replace(dst,src)
            self.progress['value']=((i+1)/len(fichiers))*100
        self.root.quit()

    def _safe_exif_transpose(self, img):
        try:
            if ImageOps: return ImageOps.exif_transpose(img)
        except: pass
        return img

def main():
    CompresseurDeLuxe().root.mainloop()

if __name__=='__main__':
    main()
