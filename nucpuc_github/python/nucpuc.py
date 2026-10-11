#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NuCPuC - Python/Tkinter translation of nucpuc.prg
(Dr. R. Beunis, Visual FoxPro 9.0, version 19/09/2019)

Simulates the formation of 'privileged partner connections' (PPC) between
Purkinje cells (PuC) and nuclear cells (NuC) in the cerebellar nuclei, as
described in Beunis R. (2021) "Olivo-Cerebello-Nucleo-Olivary Loops
Connectivity might be refined during the juvenile multi-innervation Phase of
Climbing Fibers onto Purkinje Cells", Zenodo, doi:10.5281/zenodo.17575573.

The translation follows nucpuc.prg procedure by procedure (same names: FIBERS,
DORUN, PICKGROUPMEMBERS, ABORT, PAUSE, PAUSE12, PAUSE34, SLOW, CFRETRACT,
ENABLECTRLS, SCRAMBLE, RSTRING, RASORT, DEMO).  The VFP form is emulated with
a raster image (Pillow) on which drawing uses the same 'form graphics' state
as VFP (ForeColor, FillColor, FillStyle, DrawWidth, FontSize, Line, Circle,
Box, Print, Cls), with Tk controls at the same pixel positions as the VFP
objects.

Deliberate differences from VFP:
  * RAND() -> Python random.  Reproducing the exact random sequence of a VFP
    run is impossible; with --seed a run is reproducible.
  * VFP compares numbers with a small tolerance; therefore SSP/SSD are rounded
    to 10 decimals after each step and comparisons use a tolerance of 1e-9
    (otherwise e.g. 'nSum = 19' would never be reached exactly).
  * The empty DOEVENTS wait loops take the time measured in VFP 9
    (100000 x DOEVENTS = 0.002 s, 1000000 x DOEVENTS = 0.017 s).
  * The VFP text box TXT (right half of the screen), which the program never
    fills, is not shown; a demo panel and a playback speed control were added.

Usage:
  python nucpuc.py                 normal interactive mode
  python nucpuc.py --demo 7        demo mode (pcCMD = "1".."9")
  python nucpuc.py --speed 0.5     half speed
  python nucpuc.py --seed 123      reproducible run
  python nucpuc.py --maximize      maximized window, like the VFP form
"""

import argparse
import random
import sys
import time
import tkinter as tk
import tkinter.font as tkfont

from PIL import Image, ImageDraw, ImageFont, ImageTk

# ----------------------------------------------------------------------------
# Colours (PROCEDURE INITCOLOR)
# ----------------------------------------------------------------------------
pnZwart = (0, 0, 0)
pnLichtGrijs = (192, 192, 192)
pnGrijs = (128, 128, 128)
pnWit = (255, 255, 255)
pnRood = (255, 0, 0)
pnGroen = (0, 255, 0)
pnBlauw = (0, 0, 255)
pnGeel = (255, 255, 0)

LABEL_BACK = (240, 240, 240)   # default BackColor of a VFP label
pcLF = "\n"                     # CHR(13)+CHR(10)


def hexc(c):
    return "#%02x%02x%02x" % c


# ----------------------------------------------------------------------------
# VFP helper functions
# ----------------------------------------------------------------------------
EPS = 1e-9


def ge(a, b):
    return a > b - EPS


def lt(a, b):
    return a < b - EPS


def eq(a, b):
    return abs(a - b) < EPS


def INT(x):
    return int(x + EPS) if x >= 0 else -int(-x + EPS)


def r10(x):
    return round(x, 10)


def AT(s, t):
    return t.find(s) + 1 if s else 0


def SUBSTR(s, start, n=None):
    i = int(start) - 1
    if i < 0:
        i = 0
    return s[i:] if n is None else s[i:i + n]


def STUFF(s, pos, n, rep):
    return s[:pos - 1] + rep + s[pos - 1 + n:]


def VAL(s):
    """VFP VAL() for the integers used here ('0'..'9', '10'); otherwise 0."""
    num = ""
    for ch in s.strip():
        if not ch.isdigit():
            break
        num += ch
    return int(num) if num else 0


def STR(n, length=10, dec=0):
    """VFP STR(): right-aligned, decimals dropped when the number does not fit.
    Decimal separator ',' (SET POINT as on the screenshots in the article)."""
    for d in range(dec, -1, -1):
        s = "%.*f" % (d, n)
        if len(s) <= length:
            return s.rjust(length).replace(".", ",")
    return "*" * length


def LTSTR(n):
    """LTRIM(STR(n))"""
    return str(int(round(n)))


def STREXTRACT(s, delim, n):
    parts = s.split(delim)
    return parts[n] if n < len(parts) else ""


# ----------------------------------------------------------------------------
# Form graphics (VFP Form.Line/Circle/Box/Print/Cls on a raster image)
# ----------------------------------------------------------------------------
class FormGraphics:
    FONTFILES = {("Arial", True): "arialbd.ttf", ("Arial", False): "arial.ttf",
                 ("Courier New", True): "courbd.ttf", ("Courier New", False): "cour.ttf"}

    def __init__(self, w, h, back):
        self.W, self.H = int(w), int(h)
        self.BackColor = back
        self.img = Image.new("RGB", (self.W, self.H), back)
        self.d = ImageDraw.Draw(self.img)
        self.ForeColor = pnZwart
        self.FillColor = pnZwart
        self.FillStyle = 1
        self.DrawWidth = 1
        self.FontSize = 8
        self.FontName = "Arial"
        self.FontBold = True
        self._fonts = {}
        self._textcache = {}
        self.dirty = True

    def font(self, size=None):
        size = size or self.FontSize
        key = (self.FontName, self.FontBold, size)
        if key not in self._fonts:
            fn = self.FONTFILES.get((self.FontName, self.FontBold), "arialbd.ttf")
            px = int(size * 96 / 72 + 0.5)      # MulDiv(pt, 96, 72)
            try:
                self._fonts[key] = ImageFont.truetype(fn, px)
            except OSError:
                try:
                    self._fonts[key] = ImageFont.truetype("C:/Windows/Fonts/" + fn, px)
                except OSError:
                    self._fonts[key] = ImageFont.load_default()
        return self._fonts[key]

    def Cls(self):
        self.d.rectangle([0, 0, self.W, self.H], fill=self.BackColor)
        self.dirty = True

    def Line(self, x1, y1, x2, y2):
        w = max(1, int(self.DrawWidth))
        p1 = (int(round(x1)), int(round(y1)))
        p2 = (int(round(x2)), int(round(y2)))
        self.d.line([p1, p2], fill=self.ForeColor, width=w)
        if w > 2:   # GDI pens have round end caps
            r = (w - 1) / 2
            for (x, y) in (p1, p2):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.ForeColor)
        self.dirty = True

    def Circle(self, r, x, y):
        w = max(1, int(self.DrawWidth))
        e = w // 2
        box = [x - r - e, y - r - e, x + r + e, y + r + e]
        fill = self.FillColor if self.FillStyle == 0 else None
        self.d.ellipse(box, fill=fill, outline=self.ForeColor, width=w)
        self.dirty = True

    def Box(self, x1, y1, x2, y2):
        w = max(1, int(self.DrawWidth))
        e = w // 2
        fill = self.FillColor if self.FillStyle == 0 else None
        self.d.rectangle([x1 - e, y1 - e, x2 + e, y2 + e], fill=fill,
                         outline=self.ForeColor, width=w)
        self.dirty = True

    def TextWidth(self, t):
        return self.font().getlength(t)

    def Print(self, t, x, y):
        # Opaque text: background in BackColor (as on the screenshots).
        # Rendered text snippets are cached and simply pasted afterwards (much faster).
        key = (t, self.FontName, self.FontBold, self.FontSize, self.ForeColor, self.BackColor)
        tile = self._textcache.get(key)
        if tile is None:
            f = self.font()
            asc, desc = f.getmetrics()
            tile = Image.new("RGB", (int(f.getlength(t)) + 1, asc + desc), self.BackColor)
            ImageDraw.Draw(tile).text((0, 0), t, font=f, fill=self.ForeColor, anchor="la")
            if len(self._textcache) > 20000:
                self._textcache.clear()
            self._textcache[key] = tile
        self.img.paste(tile, (int(round(x)), int(round(y))))
        self.dirty = True


# ----------------------------------------------------------------------------
# Controls
# ----------------------------------------------------------------------------
class ToolTip:
    def __init__(self, ctl):
        self.ctl = ctl
        self.tip = None
        self.job = None
        for w in ctl.all_widgets():
            w.bind("<Enter>", self.enter, add="+")
            w.bind("<Leave>", self.leave, add="+")
            w.bind("<ButtonPress>", self.leave, add="+")

    def enter(self, _e=None):
        self.cancel()
        self.job = self.ctl.app.root.after(500, self.show)

    def cancel(self):
        if self.job:
            try:
                self.ctl.app.root.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None

    def show(self):
        self.job = None
        text = self.ctl.ToolTipText
        if not text or not self.ctl.app.ShowTips:
            return
        root = self.ctl.app.root
        x, y = root.winfo_pointerx() + 12, root.winfo_pointery() + 18
        self.tip = tk.Toplevel(root)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=text, justify="left", bg="#ffffe1", relief="solid",
                 bd=1, font=self.ctl.app.tkfont("Arial", 8, False),
                 wraplength=500).pack()
        self.tip.wm_geometry("+%d+%d" % (x, y))

    def leave(self, _e=None):
        self.cancel()
        if self.tip:
            self.tip.destroy()
            self.tip = None


class Ctl:
    """Common VFP properties: Name, Visible, Enabled, ToolTipText, position."""
    cls = ""

    def __init__(self, app, name, widget):
        self.app = app
        self.Name = name
        self.w = widget
        self._visible = True
        self._enabled = True
        self.ToolTipText = ""
        self.geom = (0, 0, 0, 0)
        ToolTip(self)

    def all_widgets(self):
        return [self.w]

    def place(self, left, top, width, height):
        self.geom = (left, top, width, height)
        self._place()

    def _place(self):
        S = self.app.S
        l, t, w, h = self.geom
        if self._visible and l > -500:
            self.w.place(x=int(round(l * S)), y=int(round(t * S)),
                         width=int(round(w * S)), height=int(round(h * S)))
        else:
            self.w.place_forget()

    @property
    def Left(self):
        return self.geom[0]

    @property
    def Width(self):
        return self.geom[2]

    @property
    def Visible(self):
        return self._visible

    @Visible.setter
    def Visible(self, v):
        self._visible = bool(v)
        self._place()

    @property
    def Enabled(self):
        return self._enabled

    @Enabled.setter
    def Enabled(self, v):
        self._enabled = bool(v)
        self._apply()

    def _apply(self):
        pass

    def SetFocus(self):
        pass


class VLabel(Ctl):
    def _flush(self):
        self.w.config(text=self._caption)

    def __init__(self, app, name, cls, caption="", fontname="Arial", fontsize=8,
                 border=True, wrap=False, backcolor=LABEL_BACK, anchor="n"):
        lbl = tk.Label(app.root, bd=0, anchor=anchor, justify="center", padx=0, pady=1)
        self.cls = cls
        self._caption = caption
        self._fore = pnZwart
        self._back = backcolor
        self._fontname = fontname
        self._fontsize = fontsize
        self._border = border
        self._wrap = wrap
        super().__init__(app, name, lbl)
        self._apply()

    @property
    def Caption(self):
        return self._caption

    @Caption.setter
    def Caption(self, v):
        # As in VFP: a new caption only appears at the next repaint.
        if v != self._caption:
            self._caption = v
            self.app._dirty_labels.add(self)

    @property
    def ForeColor(self):
        return self._fore

    @ForeColor.setter
    def ForeColor(self, v):
        self._fore = v
        self._apply()

    @property
    def BackColor(self):
        return self._back

    @BackColor.setter
    def BackColor(self, v):
        self._back = v
        self._apply()

    @property
    def FontSize(self):
        return self._fontsize

    @FontSize.setter
    def FontSize(self, v):
        self._fontsize = v
        self._apply()

    def _apply(self):
        if self._enabled:
            fg, bg = self._fore, self._back
        else:
            fg, bg = (160, 160, 160), (248, 248, 248)
        S = self.app.S
        self.w.config(text=self._caption, fg=hexc(fg), bg=hexc(bg),
                      font=self.app.tkfont(self._fontname, self._fontsize, True),
                      highlightthickness=1 if self._border else 0,
                      highlightbackground=hexc(fg), highlightcolor=hexc(fg),
                      wraplength=int((self.geom[2] - 4) * S) if self._wrap and self.geom[2] else 0)

    def place(self, left, top, width, height):
        super().place(left, top, width, height)
        self._apply()


class VButton(Ctl):
    def _flush(self):
        self.w.config(text=self._caption)

    def __init__(self, app, name, cls, caption="", fontsize=8, wrap=False, command=None):
        b = tk.Button(app.root, text=caption, takefocus=0, padx=0, pady=0,
                      command=command, font=app.tkfont("Arial", fontsize, True))
        self.cls = cls
        self._caption = caption
        self._fontsize = fontsize
        self._wrap = wrap
        super().__init__(app, name, b)

    @property
    def Caption(self):
        return self._caption

    @Caption.setter
    def Caption(self, v):
        # As in VFP: a new caption only appears at the next repaint.
        if v != self._caption:
            self._caption = v
            self.app._dirty_labels.add(self)

    def _apply(self):
        self.w.config(state="normal" if self._enabled else "disabled")

    def place(self, left, top, width, height):
        super().place(left, top, width, height)
        if self._wrap:
            self.w.config(wraplength=int((width - 2) * self.app.S))


class VSpinner(Ctl):
    """VFP SPINNER: text box with arrows, value shown with a decimal comma."""

    def __init__(self, app, name, fontsize=7, low=0.0, high=2147483647, inc=0.1, value=0.1):
        f = tk.Frame(app.root, bd=1, relief="sunken", bg="white")
        self.cls = "SP"
        self.SpinnerLowValue = low
        self.SpinnerHighValue = high
        self.Increment = inc
        self._value = value
        fnt = app.tkfont("Arial", fontsize, True)
        self.entry = tk.Entry(f, justify="right", bd=0, font=fnt,
                              disabledbackground="#f0f0f0", disabledforeground="#a0a0a0")
        bf = tk.Frame(f, bg="white")
        afont = app.tkfont("Arial", 5, True)
        self.up = tk.Button(bf, text="\u25b2", font=afont, padx=0, pady=0, bd=1,
                            takefocus=0, command=lambda: self.spin(+1))
        self.dn = tk.Button(bf, text="\u25bc", font=afont, padx=0, pady=0, bd=1,
                            takefocus=0, command=lambda: self.spin(-1))
        self.up.place(relx=0, rely=0, relwidth=1, relheight=0.5)
        self.dn.place(relx=0, rely=0.5, relwidth=1, relheight=0.5)
        self.entry.place(x=0, y=0, relwidth=1, width=-int(17 * app.S), relheight=1)
        bf.place(relx=1, x=-int(16 * app.S), y=0, width=int(16 * app.S), relheight=1)
        self.bf = bf
        self.entry.bind("<FocusOut>", self._parse)
        self.entry.bind("<Return>", self._parse)
        super().__init__(app, name, f)
        self._show()

    def all_widgets(self):
        return [self.w, self.entry, self.up, self.dn]

    def _fmt(self, v):
        if float(self.Increment).is_integer() and float(v).is_integer():
            return str(int(v))
        s = ("%.4f" % v).rstrip("0")
        if s.endswith("."):
            s += "0"
        return s.replace(".", ",")

    def _show(self):
        st = self.entry.cget("state")
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, self._fmt(self._value))
        self.entry.config(state=st)

    def _parse(self, _e=None):
        try:
            v = float(self.entry.get().replace(",", "."))
            self.Value = v
        except ValueError:
            self._show()

    def spin(self, d):
        if self._enabled:
            self._parse()
            self.Value = r10(self._value + d * self.Increment)

    @property
    def Value(self):
        return self._value

    @Value.setter
    def Value(self, v):
        v = min(max(v, self.SpinnerLowValue), self.SpinnerHighValue)
        if float(self.Increment).is_integer() and float(v).is_integer():
            v = int(v)
        self._value = v
        self._show()

    def _apply(self):
        st = "normal" if self._enabled else "disabled"
        self.entry.config(state=st)
        self.up.config(state=st)
        self.dn.config(state=st)


class VEditBox(Ctl):
    def __init__(self, app, name):
        t = tk.Text(app.root, font=app.tkfont("Courier New", 7, True), bd=1, relief="sunken",
                    wrap="none")
        self.cls = "EDITBOX"
        super().__init__(app, name, t)
        self.Value = ""

    @property
    def Value(self):
        return self.w.get("1.0", "end-1c")

    @Value.setter
    def Value(self, v):
        self.w.config(state="normal")
        self.w.delete("1.0", "end")
        self.w.insert("1.0", v)
        self.w.config(state="disabled")    # ReadOnly=.T.


class Dummy:
    """CBU5: invisible button (Left=-1000) that only receives the focus."""
    cls = "CBU"

    def __init__(self, name, app=None):
        self.app = app
        self.Name = name
        self.Caption = ""
        self.Enabled = True
        self.Visible = True
        self.ToolTipText = ""
        self.ForeColor = pnZwart

    def SetFocus(self):
        # In VFP, moving the focus commits a typed spinner value (Valid/LostFocus).
        if self.app:
            self.app.commit_spinners()
            self.app.root.focus_set()

    def Click(self):
        pass


# ----------------------------------------------------------------------------
# The NUCPUC form
# ----------------------------------------------------------------------------
class NucPuc:

    def __init__(self, root, S, pnW, pnH, plCalled=False, pcCMD="", seed=None, view_w=None):
        self.root = root
        self.view_w = view_w or pnW   # visible width (pnW remains the VFP form width used for the buttons)
        self.S = S
        self.ShowTips = True
        self.closed = False
        self.running = False
        self.busy = 0           # >0 while activate/DEMO/a click is still on the call stack
        self._last_ev = 0.0
        self._keys = 0
        self.pausing = False
        self._tkfonts = {}
        self._dirty_labels = set()
        self.speed = 1.0          # playback speed (set in the demo panel)
        self._pace_t = time.perf_counter()
        self._debt = 0.0

        if seed is not None:
            self.rng = random.Random(seed)
            self.reseed = False
        else:
            self.rng = random.Random()
            self.reseed = True

        # PUBLIC variables
        self.plCalled = plCalled
        self.pcCMD = pcCMD
        self.plStop = self.plRun = self.plAbort = self.plSlow = self.plDemo = self.plClustered = False
        self.pnGroupSize = 1
        self.pcClF = self.pcNuC = self.pcPuC = ""
        self.pcClF_NxtG = self.pcClF_ActG1 = self.pcLIM = ""

        self.pnH, self.pnW = pnH, pnW
        self.pnDist = 40          # Distance between NuCs
        self.pnHOffSet = 140      # Horizontal offset
        self.pnVOffSet = 50       # Vertical offset
        self.pnHPosNuC = self.pnHOffSet + self.pnDist * 1    # NuC column
        self.pnHPosPuC = self.pnHOffSet + self.pnDist * 10   # PuC axon branching column
        self.pnRad = 10           # circle radius

        self.CNP = [None] + [chr(nX - 1 + 48) * 3 for nX in range(1, 11)]
        self.SSP = [[0.5] * 11 for _ in range(11)]
        self.SSD = [[0.0] * 11 for _ in range(11)]
        self.SUMSSP = [0.0] * 11
        self.SUMSSD = [0.0] * 11
        self.NUCPUC = [""] * 12

        # Background (the 'form' itself)
        self.g = FormGraphics(self.view_w, pnH, pnGrijs)
        self.bg_label = tk.Label(root, bd=0, highlightthickness=0, bg=hexc(pnGrijs))
        self.bg_label.place(x=0, y=0)
        self.tkimg = None
        self.dead = False
        self.refresh()
        self._autorefresh()

        root.bind_all("<Key>", self._key)
        self.controls = {}
        self.build()

    # -- infrastructure ------------------------------------------------------
    def tkfont(self, name, pt, bold):
        key = (name, pt, bold)
        if key not in self._tkfonts:
            self._tkfonts[key] = tkfont.Font(
                root=self.root, family=name,
                size=-int(pt * 96 / 72 * self.S + 0.5),
                weight="bold" if bold else "normal")
        return self._tkfonts[key]

    def rand(self):
        return self.rng.random()

    def _key(self, e):
        if e.keysym not in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            self._keys += 1

    def INKEY(self):
        if self._keys > 0:
            self._keys -= 1
            return 1
        return 0

    def refresh(self):
        img = self.g.img
        if self.S != 1:
            img = img.resize((int(img.width * self.S), int(img.height * self.S)), Image.BILINEAR)
        if self.tkimg is None or self.tkimg.width() != img.width or self.tkimg.height() != img.height:
            self.tkimg = ImageTk.PhotoImage(img)
            self.bg_label.config(image=self.tkimg)
        else:
            self.tkimg.paste(img)
        self.g.dirty = False

    def _autorefresh(self):
        # Also refreshes the image when no further DOEVENTS follows (e.g. RETURN after plStop).
        if self.dead or self.closed:
            return
        try:
            self.flush_labels()
            if self.g.dirty:
                self.refresh()
            self._after_id = self.root.after(40, self._autorefresh)
        except tk.TclError:
            pass

    def stop(self):
        """Stop the refresh loop (form is replaced or window closes)."""
        self.dead = True
        try:
            if getattr(self, "_after_id", None):
                self.root.after_cancel(self._after_id)
        except tk.TclError:
            pass

    def flush_labels(self):
        while self._dirty_labels:
            self._dirty_labels.pop()._flush()

    def DOEVENTS(self, force=False):
        now = time.perf_counter()
        if force or now - self._last_ev > 0.03:
            self._last_ev = now
            self.flush_labels()
            if self.g.dirty:
                self.refresh()
            self.root.update()
            if self.closed:
                raise SystemExit

    def wait(self, secs):
        # Playback speed: 0.5x = all pauses twice as long (see also pace()).
        self._raw_wait(secs / self.speed)
        self._pace_t = time.perf_counter()

    def pace(self):
        """Called at every step: at a speed < 1 the elapsed computing time is
        stretched proportionally, like a video played back more slowly."""
        now = time.perf_counter()
        if self.speed < 1:
            self._debt += (now - self._pace_t) * (1 / self.speed - 1)
            if self._debt > 0.01:
                d, self._debt = self._debt, 0.0
                self._raw_wait(d)
                now = time.perf_counter()
        self._pace_t = now

    def _raw_wait(self, secs):
        # Repaint at most every 30 ms (DOEVENTS without force), as during a run.
        t0 = time.perf_counter()
        while True:
            self.DOEVENTS()
            rest = secs - (time.perf_counter() - t0)
            if rest <= 0:
                break
            if rest > 0.005:
                time.sleep(0.001)     # otherwise busy-wait, like VFP's SLEEP loop

    def commit_spinners(self):
        for c in self.controls.values():
            if isinstance(c, VSpinner):
                c._parse()

    def SetAll(self, prop, value, cls=None):
        for c in self.controls.values():
            if cls is None or c.cls == cls:
                setattr(c, prop, value)

    def add(self, ctl):
        self.controls[ctl.Name] = ctl
        setattr(self, ctl.Name, ctl)
        return ctl

    # -- building the form (ADD OBJECT / Activate) --------------------------
    def build(self):
        pnW, pnH = self.pnW, self.pnH

        # TXT: in VFP a text box in the right half of the screen that the program itself never fills
        # (SHOWTXT is never called); it only kept half the screen free in the VFP article environment.
        # Not needed here: not shown, only its Value remains for DORUN.
        self.TXT = type("TXT", (), {"Value": ""})()

        # SS (label)
        ss = self.add(VLabel(self, "SS", "LABEL", "", "Courier New", 7, True, True, pnGrijs))
        ss.ToolTipText = "For display only."
        ss.place(0, 250, 100, 150)

        # CBU1..5 : toggle switches at the top
        cT = "|Toggle switch :" + pcLF
        cTTT = (cT + "for CF scrambling." + cT + "to choose between the following starting conditions :" + pcLF +
                "Groups of CFs each activating their only target PuC ('one-to-one') - or -" + pcLF +
                "Each CF capable of activating all ten PuCs ('one-to-many', the early development situation)." + pcLF +
                "This last setting also automatically sets the next setting to 'Group size at start=10'.")
        cTTT += (cT + "Setting the group size to one is just for use with the initial demo showing the 'partnership' formation," + pcLF +
                 "Setting the group size to ten is for the synchronous group activations." + pcLF +
                 "Each setting also resets the preprogrammed choices for LTP and LTD.")
        cTTT += cT + "for PuC axon scrambling.|"
        caps = ",CFs (+ cols) not scrambled,CF hand over : one to one,Group size at start = 1,PuC axons not scrambled,,"
        for nX in range(1, 5):
            nW = (pnW / 2) / (5 - 1)
            b = self.add(VButton(self, "CBU%d" % nX, "CBU", STREXTRACT(caps, ",", nX), 8))
            b.w.config(command=lambda b=b: self.CBU_Click(b))
            b.ToolTipText = STREXTRACT(cTTT, "|", nX)
            b.place((nX - 1) * nW, 5, nW, 20)
        self.CBU5 = Dummy("CBU5", self)

        # CBLU1..2 : Red / Fast
        cTTT = ("|Toggle switch : 'Red' shows PuC terminals in red when activated, 'No red' doesn't (making the display quieter)."
                "|Toggle switch : 'Fast' executes the program at top speed, 'Slow' inserts a small pause when a line width changes. "
                "You can however use the different interrupt options of the buttons below.|")
        for nX in range(1, 3):
            l = self.add(VLabel(self, "CBLU%d" % nX, "CBLU", STREXTRACT(",Red,Fast,", ",", nX), "Arial", 8, True, True))
            l.ToolTipText = STREXTRACT(cTTT, "|", nX)
            l.place(0, 210 + (nX - 1) * 20, 100, 20)
            l.w.bind("<Button-1>", lambda e, l=l: self.CBLU_Click(l))

        # CBLD1..5 : interrupt buttons at the bottom
        cTTT = ("|Click to interrupt program execution after each PuC terminal branch firing (the elementary program step)."
                "|Click to interrupt program execution after each PuC having fired all it's terminal branches."
                "|Click to interrupt program execution after the processing of each PuC group "
                "(which is the equivalent of what is considered to have happened synchronously in vivo)."
                "|Click to interrupt program execution when the conditions are ready to decrement the used PuC group size."
                "|Click to clear your above interrupt setting, and to continue the program without interruption (when it is executing).|")
        caps = ",Single PuC axon branch,Single PuC,PuC group,PuC group size,Clear interrupts,"
        for nX in range(1, 6):
            l = self.add(VLabel(self, "CBLD%d" % nX, "CBLD", STREXTRACT(caps, ",", nX), "Arial", 7, True, True))
            l.ToolTipText = STREXTRACT(cTTT, "|", nX)
            l.place(0, pnH - (6 - nX) * 28, 100, 28)
            l.w.bind("<Button-1>", lambda e, l=l: self.CBLD_Click(l))

        # CBD1..3 : Run / status / Abort
        cTTT = "|Starts execution|For status display only|Aborts execution|"
        nW = (self.pnHPosPuC + 42) - (self.pnHPosNuC - 42)
        for nX in range(1, 4):
            l = self.add(VLabel(self, "CBD%d" % nX, "CBD", STREXTRACT(",Run,,Abort,", ",", nX), "Arial", 8, True, False, pnGrijs))
            l.ToolTipText = STREXTRACT(cTTT, "|", nX)
            left = self.pnHPosNuC - 42 + {1: 0, 2: 1, 3: 4}[nX] * nW / 5
            l.place(left, self.pnVOffSet + self.pnDist * 10 + 55, nW / 5 * (3 if nX == 2 else 1) + 2, 20)
            l.w.bind("<ButtonPress-1>", lambda e, l=l: self.CBD_MouseDown(l))

        # CBR1..10 : '?' next to the PuC numbers
        for nX in range(1, 11):
            l = self.add(VLabel(self, "CBR%d" % nX, "CBR", "?", "Arial", 6, True, False, LABEL_BACK, "center"))
            l.ToolTipText = "Click to see (in the left side table) the actual SSs of all terminals of this PuC."
            l.place(self.pnHPosPuC + 23, self.pnVOffSet + self.pnDist * nX + 2, self.pnRad, self.pnRad)
            l.w.bind("<Button-1>", lambda e, l=l: self.CBR_Click(l))

        # SPLB1..5 + SP1..5 : parameters
        cTTT = ("|When the sum of SSs of FIRING PuC terminals (see figures underneath the NuCs while executing) converging on an ACTIVATED NuC (red circle)"
                " exceeds this threshold, LTP occurs (at these firing PuC-NuC synapses only) - and the NuC will show in yellow."
                "|Sets the step by which LTP increases the SSs."
                "|When the sum of SSs of FIRING PuC terminals (see figures underneath the NuCs while executing) converging on a NON-ACTIVATED NuC (NO red circle)"
                " exceeds this threshold, LTD occurs (at these firing synapses only) - and in this case the NuC will show in dark blue, "
                "otherwise it will show in it's 'basic' green (no LTD nor LTP occurring). LTD not applicable when group size=1."
                "|Sets the step by which LTD decreases the SSs. LTD not applicable when group size=1."
                "|When one CF activates many PuCs :" + pcLF +
                "Repeated activation of the same PuC-group before the group size is allowed to decrement"
                " will help to avoid LTP lagging behind and stopping or even reverting"
                " when specific CFs have not been activated enough due to asymmetric random activation.|")
        caps = ",LTP threshold,LTP step,LTD threshold,LTD step,Repeating factor,"
        for nX in range(1, 6):
            b = self.add(VButton(self, "SPLB%d" % nX, "SPLB", STREXTRACT(caps, ",", nX), 7, wrap=True))
            b.ToolTipText = STREXTRACT(cTTT, "|", nX)
            b.place(0, 60 + (nX - 1) * 30, 50, 30)
            if nX == 5:
                b.Enabled = False
            if nX == 3:
                sp = VSpinner(self, "SP3", low=1.1)
            elif nX == 5:
                sp = VSpinner(self, "SP5", low=1, high=30, inc=1, value=5)
                sp.Enabled = False
            else:
                sp = VSpinner(self, "SP%d" % nX)
            self.add(sp)
            sp.place(50, 60 + (nX - 1) * 30, 50, 30)

    def activate(self):
        self.busy += 1
        try:
            self._activate()
        finally:
            self.busy -= 1

    def _activate(self):
        # Clicking twice sets LTP and LTD values and dims appropriate buttons for groupsize=1
        self.CBU3.w.invoke()
        self.CBU3.w.invoke()
        try:
            if self.plCalled:
                self.DEMO()
            else:
                self.DORUN(10)
        except SystemExit:
            self.root.quit()

    # -- PROCEDURE FIBERS ----------------------------------------------------
    def FIBERS(self, nClF, nClF_Act, nC, nG, nB):
        g = self.g
        pnHPosNuC, pnHPosPuC, pnVOffSet, pnDist, pnRad = \
            self.pnHPosNuC, self.pnHPosPuC, self.pnVOffSet, self.pnDist, self.pnRad
        self.DOEVENTS()
        nVSV = pnVOffSet + pnDist - 30
        nHMidLine = (pnHPosNuC + pnHPosPuC) / 2
        nW = 90   # (Half) width of PuC scrambling sector

        if nClF == 1:
            # One-time drawing of the CN box and permanent texts
            g.DrawWidth = 5
            g.ForeColor = pnGroen
            g.FillStyle = 1
            g.Box(pnHPosNuC - 42, pnVOffSet + pnDist / 2, pnHPosPuC + 42, pnVOffSet + pnDist * 11)
            g.ForeColor = pnZwart
            g.FontSize = 8
            cT = "Cerebellar (sub)nucleus"
            g.Print(cT, nHMidLine - g.TextWidth(cT) / 2, pnVOffSet + pnDist * .5 - 6)
            cT = "NuCs"
            g.Print("NuCs", pnHPosNuC - pnRad - g.TextWidth(cT) / 2, pnVOffSet + pnDist * 10 + 20)
            cT = "Branching PuC axon terminals"
            g.Print(cT, pnHPosPuC - g.TextWidth(cT), pnVOffSet + pnDist * 10 + 17)
            g.FontSize = 6
            cT = "Line width represents PuC-NuC synapse strength (evolving)"
            g.Print(cT, nHMidLine - g.TextWidth(cT) / 2, pnVOffSet + pnDist * 10 + 5)

        nNuCPos = AT(LTSTR(nClF - 1), self.pcNuC)
        nVODNuC = pnVOffSet + pnDist * nNuCPos
        if nClF_Act > 0:
            nNuCPos_Act = AT(LTSTR(nClF_Act - 1), self.pcNuC)
            nVODNuC_Act = pnVOffSet + pnDist * nNuCPos_Act
            nVNuC_Act = nVSV - nNuCPos_Act * 3
            nVClF_Act = nVSV - nClF_Act * 3
        nPuCPos = AT(LTSTR(nClF - 1), self.pcPuC)
        nVODPuC = pnVOffSet + pnDist * nPuCPos

        nVClF = nVSV - nClF * 3
        nVNuC = nVSV - nNuCPos * 3
        nVPuC = nVSV - nPuCPos * 3
        yc = nVODNuC if nClF_Act == 0 else nVODNuC_Act

        # Circles and numbers
        g.FillStyle = 0
        g.DrawWidth = 1
        g.FillColor = nC
        g.Circle(pnRad, pnHPosNuC - pnRad, yc)

        g.ForeColor = nC
        g.FillStyle = 1
        g.DrawWidth = 2
        if nC == pnRood:
            g.FillColor = pnGroen
            g.Circle(pnRad + 2, pnHPosNuC - pnRad, yc)      # ring around the circle
        else:
            g.ForeColor = g.BackColor
            g.Circle(pnRad + 2, pnHPosNuC - pnRad, yc)      # wipes the ring away
        g.DrawWidth = 1
        g.FillStyle = 0

        g.ForeColor = pnZwart
        g.FontSize = 8
        g.Print(STR(abs(nClF), 2), pnHPosNuC - 32, nVODNuC - 14)   # the NuC numbers
        g.Print(STR(abs(nClF), 2), pnHPosPuC + 22, nVODPuC - 14)   # the PuC numbers

        # CF lines (yellow)
        g.ForeColor = nG
        if nClF_Act == 0:
            xc = pnHPosNuC - 80 + (11 - nNuCPos) * 3
            g.Line(0, nVClF, 10, nVClF)
            g.Line(10, nVClF, pnHPosNuC - pnRad * 9, nVNuC)
            g.Line(pnHPosNuC - pnRad * 9, nVNuC, nHMidLine - nW, nVNuC)
            g.Line(xc, nVNuC, xc, nVODNuC)
            g.Line(xc, nVODNuC, pnHPosNuC - pnRad * 2, nVODNuC)
        else:
            xc = pnHPosNuC - 80 + (11 - nNuCPos_Act) * 3
            g.Line(0, nVClF_Act, 10, nVClF_Act)
            g.Line(10, nVClF_Act, pnHPosNuC - pnRad * 9, nVNuC_Act)
            g.Line(pnHPosNuC - pnRad * 9, nVNuC_Act, nHMidLine - nW, nVNuC_Act)
            g.Line(xc, nVNuC_Act, xc, nVODNuC_Act)
            g.Line(xc, nVODNuC_Act, pnHPosNuC - pnRad * 2, nVODNuC_Act)

        # Transition lines and further PuC lines (blue)
        g.ForeColor = nB
        g.Line(nHMidLine - nW, nVNuC, nHMidLine + nW + 1, nVPuC)
        xp = pnHPosPuC + 80 - (11 - nPuCPos) * 3
        g.Line(nHMidLine + nW + 1, nVPuC, xp, nVPuC)
        g.Line(xp, nVPuC, xp, nVODPuC)
        g.Line(xp, nVODPuC, pnHPosPuC, nVODPuC)

    # -- PROCEDURE DEMO ------------------------------------------------------
    def DEMO(self):
        self.plDemo = True
        self.SetAll("Visible", False)
        self.plRun = False
        c = self.pcCMD
        if c == "1":
            self.DORUN(1, 1)
        elif c == "2":
            self.CBU4.w.invoke(); self.CBU4.Visible = True
            self.DORUN(1, 1)
        elif c == "3":
            self.CBU4.w.invoke(); self.CBU4.Visible = True
            self.CBU1.w.invoke(); self.CBU1.Visible = True
            self.DORUN(1, 1)
        elif c == "4":
            self.CBU4.w.invoke(); self.CBU4.Visible = True
            self.CBU1.w.invoke(); self.CBU1.Visible = True
            self.plStop = True
            self.CBD_MouseDown(self.CBD1)
        elif c == "5":
            self.CBU4.w.invoke(); self.CBU4.Visible = True
            self.CBU1.w.invoke(); self.CBU1.Visible = True
            self.plSlow = True
            self.SetAll("Visible", True, "CBD")
            self.CBD_MouseDown(self.CBD1)
        elif c == "6":
            self.CBU4.w.invoke(); self.CBU4.Visible = True
            self.CBU1.w.invoke(); self.CBU1.Visible = True
            self.CBU3.Visible = True
            self.CBU3.w.invoke()
            self.plSlow = True
            self.SetAll("Visible", True, "CBD")
            self.CBD_MouseDown(self.CBD1)
        elif c == "7":
            self.SetAll("Visible", True, "CBU")
            self.CBU4.w.invoke(); self.CBU1.w.invoke(); self.CBU2.w.invoke()
            self.SetAll("Visible", True, "CBD")
            self.CBD_MouseDown(self.CBD1)
        elif c == "8":
            self.SetAll("Visible", True)
            self.DORUN(1, 1)
        elif c == "9":
            self.SetAll("Visible", True)
            self.CBU4.w.invoke(); self.CBU1.w.invoke(); self.CBU2.w.invoke()
            self.SP2.Value = .5
            self.SP5.Value = 1
            self.CBD_MouseDown(self.CBD1)

    # -- PROCEDURE DORUN -----------------------------------------------------
    def DORUN(self, nClF_ActGLen, nTH=None):
        g = self.g
        SSP, SSD, SUMSSP, SUMSSD = self.SSP, self.SSD, self.SUMSSP, self.SUMSSD
        pnHPosNuC, pnHPosPuC, pnVOffSet, pnDist, pnRad = \
            self.pnHPosNuC, self.pnHPosPuC, self.pnVOffSet, self.pnDist, self.pnRad
        nSteps = nTimes = 0
        self._pace_t = time.perf_counter()
        self._debt = 0.0
        nClF_Act = 0
        nClF_ActPos = 0
        lGroupChange = False
        for a in range(11):
            for b in range(11):
                SSP[a][b] = 0.5
                SSD[a][b] = 0.0
        self.SCRAMBLE(0)
        self.pcLIM = "0" * 10
        self.TXT.Value = ""
        self.SS.Caption = ""
        nTHLTP = self.SP1.Value
        nTHLTD = self.SP3.Value
        nSum = 0
        # First simply draw the 'network'
        for nX in range(1, 11):
            self.FIBERS(nX, 0, pnGroen, pnGeel, pnBlauw)
        g.ForeColor = pnZwart
        for nX in range(1, 11):
            for nY in range(1, 11):
                g.Line(pnHPosNuC, pnVOffSet + pnDist * nX, pnHPosPuC, pnVOffSet + pnDist * nY)
        self.DOEVENTS(True)
        if not self.plRun:
            return   # was only for display

        self.running = True
        try:
            self.ENABLECTRLS(False)
            self.CBD3.Enabled = True
            self.CBD2.FontSize = 8
            self.CBD2.ToolTipText = ""
            while nSteps < 100000:
                # each cycle represents a synchronous activation of a CF group
                nAvgSSP = 0
                while nSteps < 100000:
                    if nTH == 1:
                        if self.pcLIM == ":" * 10:    # ALL NuC-PuC pairs connected by lines of width 10
                            break
                    else:
                        if ge(nAvgSSP * (nClF_ActGLen - 1) / nClF_ActGLen, nTHLTP * 3):
                            break
                        if (self.pcLIM == ":" * 10 and eq(nSum, 10 + (self.SP3.Value - self.SP4.Value) * 9)
                                and nTimes >= 500):
                            break
                    nRep = int(self.SP5.Value)
                    many = "many" in self.CBU2.Caption
                    for nT in range(nRep, (nRep * 11 - 1 if many else nRep) + 1):
                        self.pcClF_NxtG = "0123456789"
                        if many:
                            cClF_ActG = self.NUCPUC[int(nT / nRep)]
                        else:
                            cClF_ActG = self.PICKGROUPMEMBERS(nClF_ActGLen)

                        # Conversion to show the groups in the caption of CBLD3
                        self.pcClF_ActG1 = ""
                        for nX in range(1, nClF_ActGLen + 1):
                            ch = SUBSTR(cClF_ActG, nX, 1)
                            self.pcClF_ActG1 += chr((ord(ch) if ch else 0) + 1) + ("," if nX < nClF_ActGLen else "")
                            self.pcClF_ActG1 = self.pcClF_ActG1.replace(":", "10")

                        # 1) SS sums of the CF-activated NuCs
                        for nY in range(11):
                            SUMSSP[nY] = 0.0
                            SUMSSD[nY] = 0.0
                        for ch in cClF_ActG:
                            nNuCID = VAL(ch) + 1
                            nPuCPos = AT(LTSTR(nNuCID - 1), self.pcPuC)
                            for nY in range(1, 11):
                                SUMSSP[nY] = SUMSSP[nY] + SSP[nPuCPos][nY]
                                SUMSSD[nY] = SUMSSD[nY] + SSD[nPuCPos][nY]

                        g.FontSize = 6
                        g.ForeColor = pnZwart
                        for nY in range(1, 11):
                            g.Print(STR(SUMSSP[nY] + SUMSSD[nY], 5, 2), pnHPosNuC - 19, pnVOffSet + pnDist * nY + 12)

                        if many:
                            nAvgSSP = 9999   # minimum SUMSSP
                            for nY in range(1, 11):
                                if LTSTR(VAL(self.pcNuC[nY - 1])) in cClF_ActG:
                                    nAvgSSP = min(nAvgSSP, SUMSSP[nY])
                        else:
                            nAvgSSP = 0      # average SUMSSP
                            nX = 0
                            for nY in range(1, 11):
                                if LTSTR(VAL(self.pcNuC[nY - 1])) in cClF_ActG:
                                    nX += 1
                                    nAvgSSP += SUMSSP[nY]
                            nAvgSSP = nAvgSSP / nX if nX else 0

                        # 2) Drawing the red activated lines
                        if many:
                            nClF_Act = VAL(SUBSTR(cClF_ActG, int(self.rand() * len(cClF_ActG)) + 1, 1)) + 1
                            nClF_ActPos = AT(LTSTR(nClF_Act - 1), self.pcNuC)

                        for nMember in range(1, len(cClF_ActG) + 1):
                            nNuCID = VAL(cClF_ActG[nMember - 1]) + 1
                            nPuCPos = AT(LTSTR(nNuCID - 1), self.pcPuC)
                            self.FIBERS(nNuCID, nClF_Act if many else 0, pnRood, pnRood, pnRood)
                            for nY in range(1, 11):
                                if self.plAbort:
                                    self.ABORT(nY)
                                    return
                                if self.CBLU1.Caption == "Red":
                                    g.ForeColor = pnRood
                                    g.DrawWidth = 1
                                    g.Line(pnHPosPuC, pnVOffSet + pnDist * nPuCPos, pnHPosNuC, pnVOffSet + pnDist * nY)
                                g.DrawWidth = 1
                                g.FillColor = pnGroen
                                if many:
                                    lActif = LTSTR(VAL(self.pcNuC[nY - 1])) in cClF_ActG and nClF_ActPos == nY
                                else:
                                    lActif = LTSTR(VAL(self.pcNuC[nY - 1])) in cClF_ActG
                                if lActif:
                                    if ge(SUMSSP[nY] + SUMSSD[nY], nTHLTP):
                                        g.FillColor = pnGeel
                                else:
                                    if ge(SUMSSP[nY] + SUMSSD[nY], nTHLTD):
                                        g.FillColor = pnBlauw
                                g.Circle(pnRad, pnHPosNuC - pnRad, pnVOffSet + pnDist * nY)
                                nSteps += 1
                                self.pace()
                                self.CBD1.Caption = str(nSteps)
                                if self.plStop and nY == 10:
                                    self.ENABLECTRLS(True)
                                    return
                                if self.plDemo and not self.plStop and nSteps <= 10:
                                    self.SLEEP(.2)
                                self.PAUSE12(nNuCID, nY)
                            if self.plDemo and nClF_ActGLen < 3:
                                self.wait(0.002)   # FOR 1 TO 100000 DOEVENTS: measured in VFP 9 = 0.002 s
                            self.PAUSE(0)
                            # (In VFP the demo message below cleared lGroupChange before PAUSE34 was reached, so the
                            #  'PuC group size' interrupt never fired in demo mode; here it does when the button is visible.)
                            lGroupChangeBefore = lGroupChange
                            if self.plDemo and lGroupChange and nMember == nClF_ActGLen:
                                lGroupChange = False
                                self.CBD2.Caption = "Group size decrement : %d > %d" % (nClF_ActGLen + 1, nClF_ActGLen)
                                self.SLEEP(1)
                                if self.pnGroupSize == 10 and nClF_ActGLen == 2:
                                    self.plSlow = False
                            lGroupChange = self.PAUSE34(nMember, nClF_ActGLen, lGroupChangeBefore) and lGroupChange
                            if self.plDemo and not self.plStop and nSteps <= 100:
                                self.SLEEP(.4)
                            if self.plDemo and nSteps > 100:
                                self.CBLU1.Caption = "No red"
                            if self.plSlow:
                                self.SLEEP(.05)

                        # Registering the line thickening and adapting the synapses
                        for nMember in range(1, len(cClF_ActG) + 1):
                            nNuCID = VAL(cClF_ActG[nMember - 1]) + 1
                            nNuCPos = AT(LTSTR(nNuCID - 1), self.pcNuC)
                            nPuCPos = AT(LTSTR(nNuCID - 1), self.pcPuC)
                            for nY in range(1, 11):
                                nDW = INT(SSP[nPuCPos][nY] + SSD[nPuCPos][nY])   # current line width
                                if nY == nNuCPos:
                                    if ord(self.pcLIM[nNuCPos - 1]) - 48 < nDW:
                                        self.pcLIM = STUFF(self.pcLIM, nNuCPos, 1, chr(nDW + 48))
                                        self.CBD2.Caption = self.pcLIM
                                if many:
                                    lActif = LTSTR(VAL(self.pcNuC[nY - 1])) in cClF_ActG and nClF_ActPos == nY
                                else:
                                    lActif = LTSTR(VAL(self.pcNuC[nY - 1])) in cClF_ActG
                                ss = SSP[nPuCPos][nY] + SSD[nPuCPos][nY]
                                if lActif:
                                    if ge(SUMSSP[nY] + SUMSSD[nY], nTHLTP):      # hyperpolarization and activated -> LTP
                                        if lt(ss, 10):
                                            SSP[nPuCPos][nY] = r10(SSP[nPuCPos][nY] + min(self.SP2.Value, 10 - ss))
                                else:
                                    if ge(SUMSSP[nY] + SUMSSD[nY], nTHLTD):      # hyperpolarization only -> LTD
                                        if ge(ss, nTHLTD):
                                            SSD[nPuCPos][nY] = r10(SSD[nPuCPos][nY] - self.SP4.Value)

                                g.ForeColor = g.BackColor
                                g.DrawWidth = nDW     # erase with the width it had in red
                                g.Line(pnHPosPuC, pnVOffSet + pnDist * nPuCPos, pnHPosNuC, pnVOffSet + pnDist * nY)
                                g.ForeColor = pnZwart
                                g.DrawWidth = INT(SSP[nPuCPos][nY] + SSD[nPuCPos][nY])   # black with the new width
                                self.SLOW(nDW)
                                g.Line(pnHPosPuC, pnVOffSet + pnDist * nPuCPos, pnHPosNuC, pnVOffSet + pnDist * nY)
                            self.FIBERS(nNuCID, 0, pnGroen, pnGeel, pnBlauw)   # fibers back in their original colour

                        nSum = 0
                        for nY in range(1, 11):
                            nSum += max(self.SP3.Value - self.SP4.Value, SUMSSP[nY] + SUMSSD[nY])
                        if eq(nSum, 10 + (self.SP3.Value - self.SP4.Value) * 9):
                            nTimes += 1     # 500 extra loops

                if many and nClF_ActGLen > 1:
                    self.CFRETRACT(nClF_ActGLen)
                nClF_ActGLen = max(0, nClF_ActGLen - 1)
                lGroupChange = True
                if nClF_ActGLen == 0:
                    break

            self.SetAll("ForeColor", pnZwart, "CBD")
            self.CBD1.Caption = "Run"
            if nSteps >= 100000:
                self.CBD2.FontSize = 7
                self.CBD2.Caption = "FAILED (get the cursor over here to see the tooltiptext)"
                self.CBD2.ToolTipText = ("FAILED RUN" + pcLF + "LTP to weak in comparison to LTD - or - "
                                         "the repetition has to be increased to avoid trailing behind and falling off of CFs "
                                         "when random activation is too asymmetric.")
            else:
                self.CBD2.Caption = "RUN COMPLETED in %d steps" % nSteps
            self.ENABLECTRLS(True)
            self.CBD3.Enabled = False
            if self.plDemo:
                self.CBLU1.Caption = "Red"
            self.DOEVENTS(True)
        finally:
            self.running = False

    def SLEEP(self, nDur):
        self.wait(nDur)

    # -- PROCEDURE PICKGROUPMEMBERS -----------------------------------------
    def PICKGROUPMEMBERS(self, nLen):
        cX = ""
        if not self.plClustered:     # Random
            cGroup = self.pcClF
            for _ in range(nLen):
                cX += SUBSTR(cGroup, self.rand() * len(cGroup) + 1, 1)
                cGroup = STUFF(cGroup, AT(cX[-1], cGroup), 1, "")
        if self.plClustered:
            cX = self.pcClF_NxtG[:nLen]
            self.pcClF_NxtG = self.pcClF_NxtG[nLen:]
            if len(self.pcClF_NxtG) < nLen:
                self.pcClF_NxtG = ""
        return cX

    # -- PROCEDURE ABORT -----------------------------------------------------
    def ABORT(self, nY):
        g = self.g
        self.ENABLECTRLS(True)
        self.CBD3.ForeColor = pnZwart
        g.Cls()
        for nMember in range(1, 11):
            nPuCPos = AT(LTSTR(nMember - 1), self.pcPuC)
            g.ForeColor = pnZwart
            for y in range(1, 11):
                g.DrawWidth = INT(self.SSP[nPuCPos][y] + self.SSD[nPuCPos][y])
                g.Line(self.pnHPosPuC, self.pnVOffSet + self.pnDist * nPuCPos,
                       self.pnHPosNuC, self.pnVOffSet + self.pnDist * y)
            self.FIBERS(nMember, 0, pnGroen, pnGeel, pnBlauw)
        self.CBR_Click(self.controls["CBR%d" % nY])
        self.CBD1.Caption = "Run"
        if self.plDemo:
            self.CBLU1.Caption = "Red"
        self.DOEVENTS(True)

    # -- PROCEDURE PAUSE12 / PAUSE34 / PAUSE ---------------------------------
    def isOn(self, c):
        """An interrupt button only acts when it is visible (in demos 1-7 these buttons are hidden)."""
        return c.ForeColor == pnRood and c.Visible

    def PAUSE12(self, nNuCID, nY):
        if self.isOn(self.CBLD1):
            self.PAUSE(1, nNuCID)
        if self.isOn(self.CBLD2):
            if nY == 10:
                self.PAUSE(2, nNuCID)

    def PAUSE34(self, nMember, nClF_ActGLen, lGroupChange):
        if self.isOn(self.CBLD3):
            if nMember == nClF_ActGLen:
                self.PAUSE(3)
        if self.isOn(self.CBLD4) and lGroupChange:
            if nMember == nClF_ActGLen:
                self.PAUSE(4)
                lGroupChange = False
        return lGroupChange

    def PAUSE(self, nStep, nX=0):
        self.CBLD2.Caption = "Single PuC" + ("" if not nX else pcLF + LTSTR(nX))
        self.CBLD3.Caption = "PuC group" + pcLF + self.pcClF_ActG1
        self.CBLD4.Caption = "PuC group size" + pcLF + LTSTR(self.pcClF_ActG1.count(",") + 1)
        if nStep == 0:
            return
        if not nX:
            nX = VAL(self.pcClF_ActG1[self.pcClF_ActG1.rfind(",") + 1:])
        nPos = AT(LTSTR(nX - 1), self.pcPuC)
        if 1 <= nPos <= 10:
            self.CBR_Click(self.controls["CBR%d" % nPos])
        cbld = self.controls["CBLD%d" % nStep]
        self._keys = 0
        # (Unlike VFP) the pause message blinks red on yellow/white, and a click on it also continues.
        c2 = self.CBD2
        fg0, bg0, tip0 = c2.ForeColor, c2.BackColor, c2.ToolTipText
        self.pausing = True
        c2.ToolTipText = "Press any key, or click here, to continue"
        c2.w.config(cursor="hand2")
        try:
            while cbld.ForeColor == pnRood:
                c2.Caption = "Press any key to continue " + self.pcLIM
                c2.ForeColor = pnRood
                c2.BackColor = pnGeel if int(time.perf_counter() * 2) % 2 else pnWit
                if self.plAbort or self.INKEY() > 0:
                    break
                self.DOEVENTS(True)
                time.sleep(0.01)
        finally:
            self.pausing = False
            if not self.closed:
                c2.ForeColor, c2.BackColor, c2.ToolTipText = fg0, bg0, tip0
                c2.w.config(cursor="")
        self.CBD2.Caption = ""
        if self.plAbort:
            self.CBD2.Caption = "Execution aborted " + self.pcLIM

    def SLOW(self, nDW):
        if self.CBLU2.Caption == "Slow":
            if nDW != self.g.DrawWidth:
                self.wait(0.017)   # FOR 1 TO 1000000 DOEVENTS: measured in VFP 9 = 0.017 s

    # -- PROCEDURE CFRETRACT -------------------------------------------------
    def CFRETRACT(self, nLen):
        cap = "Used PuC-groups" + pcLF + "for each CF"
        for nX in range(1, 11):
            cCF = self.NUCPUC[11][:1]
            self.NUCPUC[11] = self.NUCPUC[11][1:]
            self.NUCPUC[nX] = self.NUCPUC[nX].replace(cCF, "") if cCF else self.NUCPUC[nX]
            cap += pcLF + "CF " + LTSTR(nX) + " > " + self.NUCPUC[nX]
        self.SS.Caption = cap
        self.NUCPUC[11] = self.NUCPUC[11][1:]

    # -- PROCEDURE ENABLECTRLS -----------------------------------------------
    def ENABLECTRLS(self, lEnable):
        self.SetAll("Enabled", lEnable, "CBU")
        self.SetAll("Enabled", lEnable, "SP")
        self.SetAll("Enabled", lEnable, "SPLB")
        self.SPLB5.Enabled = self.plClustered
        self.SP5.Enabled = self.plClustered

    # -- PROCEDURE SCRAMBLE / RSTRING / RASORT -------------------------------
    def SCRAMBLE(self, nNP):
        if self.reseed:
            self.rng.seed()      # =RAND(-1)
        CNP = self.CNP
        if nNP == 0:
            self.pcClF = self.pcNuC = self.pcPuC = ""
            for nX in range(1, 11):
                self.NUCPUC[nX] = self.RSTRING("1234567890", 1)
                self.pcClF += CNP[nX][0]
                self.pcNuC += CNP[nX][1]
                self.pcPuC += CNP[nX][2]
            self.NUCPUC[11] = self.RSTRING("1234567890", 1) * 11
            return
        nP = abs(nNP)
        cX = "".join(CNP[nX][-nP:] for nX in range(1, 11))
        if nNP > 0:
            cX = self.RSTRING(cX, nP)
        else:
            cX = self.RASORT(cX, nP)
        self.pcClF = self.pcNuC = self.pcPuC = ""
        for nX in range(1, 11):
            CNP[nX] = CNP[nX][:2 if nP == 1 else 1] + cX[:nP]
            cX = cX[nP:]
            self.pcClF += CNP[nX][0]
            self.pcNuC += CNP[nX][1]
            self.pcPuC += CNP[nX][-1]

    def RSTRING(self, cPreScramble, nP):
        cPostScramble = ""
        for _ in range(0, len(cPreScramble), nP):
            nAT = int(self.rand() * len(cPreScramble) / nP) * nP + 1
            cPostScramble += cPreScramble[nAT - 1:nAT - 1 + nP]
            cPreScramble = STUFF(cPreScramble, nAT, nP, "")
        return cPostScramble

    def RASORT(self, cPreScramble, nP):
        RAS = [cPreScramble[i * nP:(i + 1) * nP] for i in range(10)]
        if nP == 2:
            RAS.sort()
        else:
            RAS = [self.CNP[nX][1] for nX in range(1, 11)]
        return "".join(RAS)

    # -- Click events --------------------------------------------------------
    def CBU_Click(self, ctl):
        self.busy += 1
        try:
            self._CBU_Click(ctl)
        finally:
            self.busy -= 1

    def _CBU_Click(self, ctl):
        if not ctl.Enabled:
            return
        cCap = ctl.Caption
        self.plRun = False
        if "CFs" in cCap:
            ctl.Caption = cCap.replace("not ", "") if "not" in cCap else cCap.replace("scrambled", "not scrambled")
            self.SCRAMBLE(-2 if "not" in ctl.Caption else 2)
            self.g.Cls()
            self.DORUN(1, self.pnGroupSize)
        elif "hand" in cCap:
            cT = cCap[:AT("to", cCap) + 2]
            ctl.Caption = cT + "one" if "many" in cCap else cT + "many"
            self.pnGroupSize = 10
            if "many" in ctl.Caption and "10" not in self.CBU3.Caption:
                self.CBU3.w.invoke()       # set group size to 10
            if "many" in ctl.Caption and not self.plClustered:
                self.plClustered = True
            else:
                self.plClustered = False
            self.SPLB5.Enabled = self.plClustered
            self.SP5.Enabled = self.plClustered
        elif "size" in cCap:
            cT = cCap[:AT("1", cCap)]
            ctl.Caption = cT if "10" in cCap else cT + "0"
            ten = "10" in ctl.Caption
            self.pnGroupSize = 10 if ten else 1
            self.SP1.Value = 5.0 if ten else .5     # LTP threshold
            self.SP2.Value = 1.0 if ten else .5     # LTP step
            self.SP3.Value = 1.1                    # LTD threshold
            self.SP4.Value = .1                     # LTD step
            if not ten and "many" in self.CBU2.Caption:
                self.CBU2.w.invoke()
            self.SPLB3.Enabled = ten
            self.SP3.Enabled = ten
            self.SPLB4.Enabled = ten
            self.SP4.Enabled = ten
        elif "PuC" in cCap:
            ctl.Caption = cCap.replace("not ", "") if "not" in cCap else cCap.replace("scrambled", "not scrambled")
            self.SCRAMBLE(-1 if "not" in ctl.Caption else 1)
            self.g.Cls()
            self.DORUN(1, self.pnGroupSize)
        self.CBU5.SetFocus()

    def CBLU_Click(self, ctl):
        if ctl.Name == "CBLU1":
            ctl.Caption = "No red" if ctl.Caption == "Red" else "Red"
        else:
            ctl.Caption = "Slow" if ctl.Caption == "Fast" else "Fast"

    def CBLD_Click(self, ctl):
        # (Unlike VFP) clicking a red interrupt button again switches it off.
        on = "Clear" not in ctl.Caption and ctl.ForeColor != pnRood
        self.SetAll("ForeColor", pnZwart, "CBLD")
        if on:
            ctl.ForeColor = pnRood
        if getattr(self, "on_interrupt", None):     # remembered across demos
            self.on_interrupt(ctl.Name if on else None)

    def CBD_MouseDown(self, ctl):
        if ctl is self.CBD2 and self.pausing:     # click on the pause message = continue
            self._keys += 1
            return
        self.busy += 1
        try:
            self._CBD_MouseDown(ctl)
        finally:
            self.busy -= 1

    def _CBD_MouseDown(self, ctl):
        if not ctl.Enabled:
            return
        self.commit_spinners()
        self.plRun = self.plAbort = False
        self.SetAll("ForeColor", pnZwart, "CBD")
        cCap = ctl.Caption
        if cCap == "Run" and not self.running:
            self.CBD2.Caption = ""
            ctl.ForeColor = pnGeel
            self.CBU1.w.invoke()
            self.CBU1.w.invoke()
            self.CBU4.w.invoke()
            self.CBU4.w.invoke()
            self.plRun = True
            self.g.Cls()
            self.DORUN(self.pnGroupSize, self.pnGroupSize)
        elif cCap == "Abort":
            self.CBD2.Caption = "Execution aborted"
            self.plAbort = True

    def CBR_Click(self, ctl):
        nPos = int(ctl.Name[3:])
        nPuCID = VAL(self.pcPuC[nPos - 1]) + 1
        cX = ""
        for nY in range(1, 11):
            nDW = self.SSP[nPos][nY] + self.SSD[nPos][nY]
            cX += "br " + STR(nY, 2) + " = " + STR(nDW, 5, 2) + pcLF
        self.SS.Caption = pcLF + "PuC " + LTSTR(nPuCID) + " SSs" + pcLF + cX


# ----------------------------------------------------------------------------
# Demo panel: one button per pcCMD demo (as with 'DO nucpuc WITH .T.,"n"')
# ----------------------------------------------------------------------------
DEMO_PANEL_W = 160
VIEW_W = 800        # visible window width: the network extends to x = ±620, the demo panel is next to it

# Figures and page numbers according to the Zenodo version of the article
# (doi:10.5281/zenodo.17575573): page number = the number printed at the bottom of the page.
DEMOS = [
    ("1", "Demo 1\nInitial network\nFig. 1A  -  p. 4",
     "Draws the unscrambled network: CFs (yellow), NuCs (green), PuC axons (blue), "
     "all PuC terminals fanning out to all NuCs.\nArticle: Fig. 1A, page 4."),
    ("2", "Demo 2\nPuC axons scrambled\n(no figure)",
     "Same network, with the PuC axon tract scrambled.\nNo corresponding figure in the article."),
    ("3", "Demo 3\nCFs + PuC axons scrambled\nFig. 2A  -  p. 5",
     "Both the CF tract (with its collaterals) and the PuC axon tract scrambled.\nArticle: Fig. 2A, page 5."),
    ("4", "Demo 4\nOne CF activated\nFig. 3  -  p. 5",
     "One CF fires: the activated circuit is shown in red, and the run stops after this single PuC.\n"
     "Article: Fig. 3, page 5."),
    ("5", "Demo 5\nPartner formation, size 1\nFig. 4  -  p. 7",
     "Single CFs fire one at a time (no interference): the PuC-NuC partner connections thicken by LTP.\n"
     "Article: Fig. 4, page 7."),
    ("6", "Demo 6\nGroup size 10: LTP + LTD\nFig. 5  -  p. 9",
     "Groups of 10 CFs fire in synchrony; the group size decrements as LTP grows, "
     "and LTD prunes the false partnerships.\n"
     "Article: Fig. 5, page 9."),
    ("7", "Demo 7\nCF hand over one to many\nFig. 6  -  p. 10",
     "Juvenile multi-innervation: each CF starts by activating ten PuCs, "
     "and the number of PuCs under its control dwindles to one.\n"
     "Article: Fig. 6, page 10."),
    ("8", "Demo 8\nFull program, all controls\n(no figure)",
     "Shows the network with all controls visible (in demo pacing).\nNo corresponding figure in the article."),
    ("9", "Demo 9\nFailing run, LTP step 0,5\nFig. 7  -  p. 11",
     "One to many with LTP step 0,5 and repeating factor 1: LTP is too weak against LTD "
     "and the run fails after 100000 steps (the first example of Fig. 7).\n"
     "Article: Fig. 7, page 11."),
    ("", "Normal mode\n(restart)",
     "Restarts the program in its normal interactive mode (not called with a demo parameter)."),
]


class Shell:
    """Manages (re)starting the NUCPUC form with or without a demo parameter."""

    SPEEDS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]

    def __init__(self, root, S, pnW, pnH, seed, speed=1.0, view_w=None):
        self.root, self.S, self.pnW, self.pnH, self.seed = root, S, pnW, pnH, seed
        self.view_w = view_w or pnW
        self.speed = speed
        self.speed_buttons = {}
        self.app = None
        self.pending = None
        self.current = None

    def start(self, demo):
        if self.app:
            self.app.stop()
        for w in self.root.winfo_children():
            w.destroy()
        self.current = demo
        self.app = NucPuc(self.root, self.S, self.pnW, self.pnH,
                          plCalled=bool(demo), pcCMD=demo, seed=self.seed, view_w=self.view_w)
        self.app.speed = self.speed
        # keep the chosen interrupt button (red) when switching to another demo
        self.app.on_interrupt = lambda name: setattr(self, "interrupt", name)
        if getattr(self, "interrupt", None):
            self.app.controls[self.interrupt].ForeColor = pnRood
        self.build_panel()
        self.root.after(50, self.app.activate)

    def build_panel(self):
        S, app = self.S, self.app
        left = self.view_w - DEMO_PANEL_W
        n = len(DEMOS)
        top0, gap = 10, 4
        speed_h = 52             # room at the bottom for the speed buttons
        h = (self.pnH - top0 - 10 - speed_h - gap * (n - 1)) / n
        h = min(h, 48)
        for i, (cmd, cap, tip) in enumerate(DEMOS):
            active = (cmd == self.current)
            b = tk.Button(self.root, text=cap, takefocus=0, padx=1, pady=0,
                          font=app.tkfont("Arial", 7, True), wraplength=int((DEMO_PANEL_W - 14) * S),
                          bg=hexc(pnGeel) if active else hexc(LABEL_BACK),
                          relief="sunken" if active else "raised",
                          command=lambda c=cmd: self.request(c))
            b.place(x=int(left * S), y=int((top0 + i * (h + gap)) * S),
                    width=int((DEMO_PANEL_W - 10) * S), height=int(h * S))
            self._tip(b, tip)

        # Playback speed, as with a video player
        y0 = top0 + n * (h + gap) + 2
        lbl = tk.Label(self.root, text="Speed", bg=hexc(pnGrijs), fg="white",
                       font=app.tkfont("Arial", 7, True), anchor="w")
        lbl.place(x=int(left * S), y=int(y0 * S), width=int((DEMO_PANEL_W - 10) * S), height=int(14 * S))
        self._tip(lbl, "Playback speed of runs and demos, as with a video player.\n"
                       "Below 1x all pauses and the computation itself are stretched; "
                       "above 1x only the pauses get shorter.\n"
                       "Can be changed while a run is executing.")
        bw = (DEMO_PANEL_W - 10) / 3
        self.speed_buttons = {}
        for k, sp in enumerate(self.SPEEDS):
            txt = ("%g" % sp).replace(".", ",") + "×"
            b = tk.Button(self.root, text=txt, takefocus=0, padx=0, pady=0,
                          font=app.tkfont("Arial", 7, True),
                          command=lambda sp=sp: self.set_speed(sp))
            b.place(x=int((left + (k % 3) * bw) * S), y=int((y0 + 15 + (k // 3) * 18) * S),
                    width=int((bw - 2) * S), height=int(17 * S))
            self.speed_buttons[sp] = b
        self._mark_speed()

    def _tip(self, widget, tip):
        holder = type("H", (), {})()
        holder.app, holder.ToolTipText, holder.all_widgets = self.app, tip, (lambda w=widget: [w])
        ToolTip(holder)

    def set_speed(self, sp):
        self.speed = sp
        self.app.speed = sp       # takes effect immediately, also during a run
        self._mark_speed()

    def _mark_speed(self):
        for sp, b in self.speed_buttons.items():
            on = (sp == self.speed)
            b.config(bg=hexc(pnGeel) if on else hexc(LABEL_BACK), relief="sunken" if on else "raised")

    def request(self, demo):
        self.pending = demo
        if self.app.busy:
            self.app.plAbort = True      # let a running run/demo abort first
        self.root.after(20, self._poll)

    def _poll(self):
        if self.pending is None:
            return
        if self.app.busy:
            self.app.plAbort = True
            self.root.after(50, self._poll)
            return
        demo, self.pending = self.pending, None
        self.start(demo)


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="NuCPuC - Python version of nucpuc.prg")
    ap.add_argument("--maximize", action="store_true",
                    help="maximized window (WindowState=2), layout follows the window size")
    ap.add_argument("--size", default="1264x540",
                    help="logical VFP form size WxH (default 1264x540 = the screenshots in the article)")
    ap.add_argument("--scale", type=float, default=None,
                    help="scale factor (default: automatic, following the Windows DPI)")
    ap.add_argument("--seed", type=int, default=None, help="fixed seed for reproducible runs")
    ap.add_argument("--demo", default="", help="demo mode 1..9 (pcCMD)")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="playback speed, e.g. 0.5 = half speed (as with a video player)")
    args = ap.parse_args()

    root = tk.Tk()
    root.title("NuCPuC")
    root.configure(bg=hexc(pnGrijs))
    S = args.scale if args.scale else max(1.0, round(root.winfo_fpixels("1i") / 96.0 * 4) / 4)

    if args.maximize:
        root.state("zoomed")
        root.update()
        pnW, pnH = root.winfo_width() / S, root.winfo_height() / S
        view_w = pnW
    else:
        pnW, pnH = (int(v) for v in args.size.lower().split("x"))
        view_w = min(pnW, VIEW_W)     # without the (unneeded) TXT box: network + demo panel
        root.geometry("%dx%d" % (int(view_w * S), int(pnH * S)))
        root.resizable(False, False)

    shell = Shell(root, S, pnW, pnH, args.seed, max(0.05, args.speed), view_w=view_w)
    shell.start(args.demo)

    def on_close():
        shell.app.closed = True
        shell.app.plAbort = True
        shell.app.stop()
        try:
            root.destroy()
        except tk.TclError:
            pass

    root.protocol("WM_DELETE_WINDOW", on_close)
    try:
        root.mainloop()
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
