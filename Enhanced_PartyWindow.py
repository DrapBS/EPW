# Copyright 2026 © — Lovely by Drap & Nizar (・ω・)
# ba_meta require api 9
from __future__ import annotations

import colorsys
import logging
import math
import random
import socket
import textwrap
import threading
import time
import traceback
import weakref
from collections import deque
from typing import Any, Dict, List, Optional, Sequence, Tuple

import babase
import bascenev1 as bs
import bauiv1 as bui
import bauiv1lib.party as bui_party
from bauiv1lib.colorpicker import ColorPickerExact
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.popup import PopupMenuWindow

# Updated: 1.6 > 1.7 (Auto-Updater fixed)
__version__ = 'v1.7'


def _print_exception(msg: str = '') -> None:
    try:
        logging.exception(msg or 'Unhandled exception')
    except Exception:
        traceback.print_exc()


def _get_ping_color(ping_val):
    try:
        if ping_val < 75:
            return (0.0, 1.0, 0.0)
        if ping_val < 150:
            return (0.5, 1.0, 0.0)
        if ping_val < 300:
            return (1.0, 1.0, 0.0)
        if ping_val < 600:
            return (1.0, 0.5, 0.0)
        return (1.0, 0.0, 0.0)
    except Exception:
        return (0.6, 0.6, 0.6)


def _creat_Lstr_list(strings: list) -> list:
    return [babase.Lstr(value=s) for s in strings]


def _popup_scale() -> float:
    ui = bui.app.ui_v1.uiscale
    return (2.3 if ui is bui.UIScale.SMALL else
            1.65 if ui is bui.UIScale.MEDIUM else 1.23)


_FX_T0 = time.time()
_CFG_THEME = 'BetterParty_Theme'
_CFG_FX = 'BetterParty_FX'
_CFG_SPEED = 'BetterParty_Speed'
_CFG_HISTORY = 'BetterParty_ServerHistory'
_CFG_HUB_TAB = 'BetterParty_HubTab'
_CFG_HUB_SORT = 'BetterParty_HubSort'
_CFG_AUTO = 'BetterParty_Auto'

_FX_LEVEL_NAMES = ['Off', 'Low', 'High']
_SPEED_VALUES = [0.5, 1.0, 1.8]
_SPEED_NAMES = ['Slow', 'Normal', 'Fast']

THEMES: Dict[str, Dict[str, Any]] = {
    'Aurora': dict(a=(0.16, 0.38, 0.92), b=(0.16, 0.75, 0.35), mode='wave',
                   tex=('circleSoft', 'star'), dir=1),
    'Neon Pink': dict(a=(1.0, 0.12, 0.62), b=(0.55, 0.15, 1.0), mode='wave',
                      tex=('heart', 'star', 'circleSoft'), dir=1),
    'Lava': dict(a=(1.0, 0.28, 0.05), b=(0.75, 0.05, 0.12), mode='wave',
                 tex=('star', 'circleSoft'), dir=1),
    'Ocean': dict(a=(0.05, 0.40, 0.95), b=(0.02, 0.78, 0.80), mode='wave',
                  tex=('circleOutline', 'circleSoft'), dir=1),
    'Toxic': dict(a=(0.25, 0.95, 0.12), b=(0.75, 0.90, 0.10), mode='wave',
                  tex=('circleSoft', 'star'), dir=1),
    'Galaxy': dict(a=(0.40, 0.10, 0.85), b=(0.08, 0.15, 0.55), mode='wave',
                   tex=('star', 'star', 'circleSoft'), dir=1),
    'Candy': dict(a=(1.0, 0.55, 0.80), b=(0.50, 0.80, 1.0), mode='wave',
                  tex=('heart', 'circleSoft'), dir=1),
    'Gold Rush': dict(a=(1.0, 0.78, 0.12), b=(0.95, 0.45, 0.05), mode='wave',
                      tex=('star', 'circleSoft'), dir=1),
    'Frost': dict(a=(0.55, 0.85, 1.0), b=(0.85, 0.93, 1.0), mode='wave',
                  tex=('circleSoft', 'star'), dir=-1),
    'Sunset': dict(a=(1.0, 0.35, 0.25), b=(0.65, 0.20, 0.90), mode='wave',
                   tex=('circleSoft', 'star'), dir=1),
    'Matrix': dict(a=(0.05, 0.80, 0.25), b=(0.0, 0.45, 0.15), mode='wave',
                   tex=('circleSoft',), dir=-1),
    'Midnight': dict(a=(0.08, 0.10, 0.30), b=(0.22, 0.12, 0.48), mode='wave',
                     tex=('star', 'circleSoft'), dir=1),
    'Rainbow': dict(a=(1.0, 0.2, 0.2), b=(0.2, 0.2, 1.0), mode='rainbow',
                    tex=('star', 'heart', 'circleSoft'), dir=1),
}
THEME_ORDER = list(THEMES.keys())


def _get_theme(name: str) -> Dict[str, Any]:
    th = THEMES.get(name)
    if th is not None:
        return th
    a, b = THEMES['Aurora']['a'], THEMES['Aurora']['b']
    try:
        saved = babase.app.config.get('PartyWindow_Wave_Colors')
        if (isinstance(saved, (list, tuple)) and len(saved) == 2
                and all(isinstance(c, (list, tuple)) and len(c) == 3 for c in saved)):
            a = tuple(float(x) for x in saved[0])
            b = tuple(float(x) for x in saved[1])
    except Exception:
        pass
    return dict(a=a, b=b, mode='wave', tex=('star', 'circleSoft'), dir=1)


def _theme_rgb(theme: Dict[str, Any], elapsed: float, speed: float = 1.0):
    period = 4.0 / max(0.25, speed)
    if theme.get('mode') == 'rainbow':
        h = (elapsed / (period * 2.5)) % 1.0
        s, v = 0.80, 0.95
    else:
        phase = (elapsed % period) / period
        t = (1 - math.cos(phase * 2 * math.pi)) / 2
        h_a, s_a, v_a = colorsys.rgb_to_hsv(*theme['a'])
        h_b, s_b, v_b = colorsys.rgb_to_hsv(*theme['b'])
        dh = h_b - h_a
        if dh > 0.5:
            dh -= 1.0
        elif dh < -0.5:
            dh += 1.0
        h = (h_a + dh * t) % 1.0
        s = s_a + (s_b - s_a) * t
        v = v_a + (v_b - v_a) * t
    v = min(1.0, v * (0.94 + 0.06 * math.sin(elapsed * 2.3)))
    return colorsys.hsv_to_rgb(h, s, v)


def _accent(rgb, sat: float = 0.55, val: float = 0.88):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return colorsys.hsv_to_rgb(h, min(1.0, 0.25 + s * sat), val)


def _light(rgb, k: float = 0.5):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return colorsys.hsv_to_rgb(h, s * k, 1.0)


def _fmt_dur(sec: float) -> str:
    m, s = divmod(int(max(0, sec)), 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'


def _ago(ts: float) -> str:
    if not ts:
        return ''
    d = time.time() - ts
    if d < 45:
        return 'just now'
    if d < 3600:
        return f'{int(d // 60)}m ago'
    if d < 86400:
        return f'{int(d // 3600)}h ago'
    return f'{int(d // 86400)}d ago'


class _FXLayer:

    N_PART = 14
    N_ORB = 5
    N_TWINKLE = 16
    N_RING = 3
    N_BURST = 14
    TAIL = 0.20

    def __init__(self, root: bui.Widget, width: float, height: float,
                 level: int, theme: Dict[str, Any],
                 halos: Optional[List[Any]] = None,
                 rim: Optional[List[Tuple[float, float]]] = None) -> None:
        self._w = float(width)
        self._h = float(height)
        self._level = level
        self._theme = theme
        self._n = 0
        self._rnd = random.Random()
        self._last_pulse = -9.0
        w, h = self._w, self._h
        rnd = random.Random(7)
        soft = bui.gettexture('circleSoft')
        star = bui.gettexture('star')

        def img(tex, size=(10, 10)):
            return bui.imagewidget(parent=root, position=(0, 0), size=size,
                                   texture=tex, color=(1, 1, 1), opacity=0.0)

        self._orbs: List[Dict[str, Any]] = []
        for i in range(self.N_ORB):
            self._orbs.append(dict(
                x=rnd.uniform(0.15, 0.85) * w, y=rnd.uniform(0.2, 0.8) * h,
                r=rnd.uniform(50, 100), fx=rnd.uniform(0.12, 0.3),
                fy=rnd.uniform(0.1, 0.25), ph=rnd.uniform(0, 6.28), w=img(soft)))
        self._twk: List[Dict[str, Any]] = []
        for i in range(self.N_TWINKLE):
            self._twk.append(dict(
                x=rnd.uniform(0.06, 0.94) * w, y=rnd.uniform(0.08, 0.92) * h,
                s=rnd.uniform(5, 10), f=rnd.uniform(0.6, 1.8),
                ph=rnd.uniform(0, 6.28), op=-1.0, w=img(star)))

        self._glow = bui.imagewidget(
            parent=root, position=(w * 0.12, h - 80), size=(w * 0.76, 90),
            texture=soft, color=(1, 1, 1), opacity=0.0)
        self._shine = bui.imagewidget(
            parent=root, position=(-80, 6), size=(46, h - 12),
            texture=bui.gettexture('softRectVertical'), color=(1, 1, 1),
            opacity=0.0)
        self._tshine = bui.imagewidget(
            parent=root, position=(-80, h - 62), size=(30, 46),
            texture=bui.gettexture('softRectVertical'), color=(1, 1, 1),
            opacity=0.0)
        self._tshine_on = False

        self._halos: List[Dict[str, Any]] = []
        for cx, cy, sz in (halos or []):
            self._halos.append(dict(x=cx, y=cy, s=sz, w=img(soft, (sz, sz))))

        self._dots: List[Dict[str, Any]] = []
        for i, (u, v) in enumerate(rim or []):
            x, y = u * w, v * h
            bloom = None
            if i % 2 == 0:
                bloom = bui.imagewidget(
                    parent=root, position=(x - 9, y - 9), size=(18, 18),
                    texture=soft, color=(1, 1, 1), opacity=0.0)
            self._dots.append(dict(x=x, y=y, op=-1.0, bloom=bloom, w=None))
        for d in self._dots:
            d['w'] = bui.imagewidget(
                parent=root, position=(d['x'] - 3, d['y'] - 3), size=(6, 6),
                texture=soft, color=(1, 1, 1), opacity=0.0)

        self._parts: List[Dict[str, Any]] = []
        for i in range(self.N_PART):
            self._parts.append(dict(
                x=rnd.uniform(0.07, 0.93) * w,
                speed=rnd.uniform(0.035, 0.10), off=rnd.random(),
                amp=rnd.uniform(4, 18), freq=rnd.uniform(0.6, 1.8),
                ph=rnd.uniform(0, 6.28), size=rnd.uniform(9, 22),
                maxop=rnd.uniform(0.35, 0.8), tex_i=i, w=img(soft, (12, 12))))

        self._shoot_w = [img(star, (14, 14)), img(soft, (10, 10)),
                         img(soft, (8, 8)), img(soft, (6, 6))]
        self._shoot: Optional[Dict[str, float]] = None
        self._next_shoot = 3.0

        self._rings = [dict(t0=None, x=0.0, y=0.0,
                            w=bui.imagewidget(
                                parent=root, position=(0, 0), size=(20, 20),
                                texture=bui.gettexture('circleOutline'),
                                color=(1, 1, 1), opacity=0.0))
                       for _ in range(self.N_RING)]
        self._bursts = [dict(t0=None, x=0.0, y=0.0, vx=0.0, vy=0.0,
                             col=(1, 1, 1), w=img(star if i % 2 else soft, (12, 12)))
                        for i in range(self.N_BURST)]
        self.set_theme(theme)
        self.set_level(level)

    def set_theme(self, theme: Dict[str, Any]) -> None:
        self._theme = theme
        texs = theme.get('tex') or ('circleSoft',)
        for p in self._parts:
            try:
                bui.imagewidget(edit=p['w'],
                                texture=bui.gettexture(texs[p['tex_i'] % len(texs)]))
            except Exception:
                pass

    def _hi_widgets(self):
        wl = [o['w'] for o in self._orbs] + [t['w'] for t in self._twk]
        wl += [hh['w'] for hh in self._halos] + list(self._shoot_w)
        wl += [d['bloom'] for d in self._dots if d['bloom'] is not None]
        wl.append(self._tshine)
        return wl

    def set_level(self, level: int) -> None:
        self._level = level
        hide = []
        if level <= 0:
            hide += self._hi_widgets() + [self._glow, self._shine]
            hide += [p['w'] for p in self._parts] + [d['w'] for d in self._dots]
            hide += [r['w'] for r in self._rings] + [b['w'] for b in self._bursts]
            self._shoot = None
            for r in self._rings:
                r['t0'] = None
            for b in self._bursts:
                b['t0'] = None
        else:
            if level < 2:
                hide += self._hi_widgets()
                self._shoot = None
                self._tshine_on = False
                for b in self._bursts:
                    b['t0'] = None
                hide += [b['w'] for b in self._bursts]
            hide += [p['w'] for p in self._parts[self._active_count():]]
        for d in self._dots:
            d['op'] = -1.0
        for t in self._twk:
            t['op'] = -1.0
        for wd in hide:
            try:
                bui.imagewidget(edit=wd, opacity=0.0)
            except Exception:
                pass

    def _active_count(self) -> int:
        return 0 if self._level <= 0 else (6 if self._level == 1 else self.N_PART)

    def pulse(self, x: Optional[float] = None, y: Optional[float] = None) -> None:
        if self._level <= 0:
            return
        now = time.time() - _FX_T0
        if now - self._last_pulse < 0.35:
            return
        self._last_pulse = now
        ring = min(self._rings, key=lambda r: -1.0 if r['t0'] is None else r['t0'])
        ring.update(t0=now, x=self._w / 2 if x is None else x,
                    y=self._h / 2 if y is None else y)

    def burst(self, x: Optional[float] = None, y: Optional[float] = None) -> None:
        if self._level < 2:
            return
        now = time.time() - _FX_T0
        cx = self._w / 2 if x is None else x
        cy = self._h * 0.6 if y is None else y
        rnd = self._rnd
        for b in self._bursts:
            a = rnd.uniform(0, 6.283)
            sp = rnd.uniform(70, 200)
            b.update(t0=now, x=cx, y=cy, vx=math.cos(a) * sp, vy=math.sin(a) * sp,
                     col=colorsys.hsv_to_rgb(rnd.random(), 0.55, 1.0))

    def tick(self, elapsed: float, rgb, speed: float) -> None:
        if self._level <= 0:
            return
        self._n += 1
        n = self._n
        w, h = self._w, self._h
        hi = self._level >= 2
        light = _light(rgb, 0.45)
        pulse = (1 + math.sin(elapsed * 1.6 * speed)) / 2
        ih = colorsys.rgb_to_hsv(*light)[0]

        bui.imagewidget(edit=self._glow, color=light, opacity=0.12 + 0.22 * pulse)
        sx = ((elapsed * 0.13 * speed) % 1.6 - 0.3) * w
        bui.imagewidget(edit=self._shine, position=(sx, 6), opacity=0.07)

        if n % (2 if hi else 3) == 0:
            cnt = len(self._dots)
            base = 0.30 + 0.10 * pulse
            h1 = (elapsed * 0.10 * speed) % 1.0
            h2 = (h1 + 0.5) % 1.0
            recolor = (n % 12 == 0)
            for i, d in enumerate(self._dots):
                t = i / cnt
                k = 0.0
                for head in (h1, h2):
                    dist = (head - t) % 1.0
                    if dist < self.TAIL:
                        k = max(k, (1.0 - dist / self.TAIL) ** 1.6)
                op = base + (0.98 - base) * k
                if k > 0.0 or abs(op - d['op']) > 0.02 or recolor:
                    sz = 6.0 + 5.0 * k
                    col = tuple(c + (1.0 - c) * 0.75 * k for c in light)
                    bui.imagewidget(
                        edit=d['w'], position=(d['x'] - sz / 2, d['y'] - sz / 2),
                        size=(sz, sz), color=col, opacity=op)
                    if hi and d['bloom'] is not None:
                        bs_ = 16.0 + 16.0 * k
                        bui.imagewidget(
                            edit=d['bloom'],
                            position=(d['x'] - bs_ / 2, d['y'] - bs_ / 2),
                            size=(bs_, bs_), color=light,
                            opacity=0.05 + 0.30 * k)
                    d['op'] = op

        direction = self._theme.get('dir', 1)
        span = h - 2 * 17 - 20
        for p in self._parts[:self._active_count()]:
            prog = (p['off'] + elapsed * p['speed'] * speed) % 1.0
            if direction < 0:
                prog = 1.0 - prog
            sz = p['size'] * (0.75 + 0.25 * math.sin(elapsed * 2 + p['ph']))
            x = p['x'] + math.sin(elapsed * p['freq'] + p['ph']) * p['amp']
            y = 17 + 10 + prog * span
            op = math.sin(math.pi * min(1.0, max(0.0, prog))) * p['maxop']
            bui.imagewidget(edit=p['w'], position=(x - sz / 2, y - sz / 2),
                            size=(sz, sz), opacity=op, color=light)

        for r in self._rings:
            if r['t0'] is None:
                continue
            age = elapsed - r['t0']
            if age >= 1.2:
                r['t0'] = None
                bui.imagewidget(edit=r['w'], opacity=0.0)
                continue
            f = age / 1.2
            sz = 30 + f * max(w, h) * 0.95
            bui.imagewidget(edit=r['w'], position=(r['x'] - sz / 2, r['y'] - sz / 2),
                            size=(sz, sz), color=light, opacity=0.65 * (1 - f) ** 1.5)

        if not hi:
            return

        if n % 2 == 0:
            for i, o in enumerate(self._orbs):
                x = o['x'] + math.sin(elapsed * o['fx'] + o['ph']) * 45
                y = o['y'] + math.cos(elapsed * o['fy'] + o['ph']) * 30
                sz = o['r'] * (1 + 0.08 * math.sin(elapsed * 0.9 + o['ph']))
                hh, ss, _vv = colorsys.rgb_to_hsv(*light)
                col = colorsys.hsv_to_rgb((hh + 0.07 * i) % 1.0, min(1.0, ss + 0.3), 1.0)
                bui.imagewidget(
                    edit=o['w'], position=(x - sz / 2, y - sz / 2), size=(sz, sz),
                    color=col,
                    opacity=0.05 + 0.05 * (1 + math.sin(elapsed * 0.6 + o['ph'])) / 2)
            for t in self._twk:
                k = max(0.0, math.sin(elapsed * t['f'] + t['ph'])) ** 3
                op = 0.05 + 0.75 * k
                if abs(op - t['op']) > 0.04:
                    sz = t['s'] * (0.7 + 0.5 * k)
                    bui.imagewidget(
                        edit=t['w'], position=(t['x'] - sz / 2, t['y'] - sz / 2),
                        size=(sz, sz), color=light, opacity=op)
                    t['op'] = op

        for i, hl in enumerate(self._halos):
            ph = math.sin(elapsed * 2.2 * speed + i * 1.3)
            sz = hl['s'] * (1 + 0.10 * ph)
            bui.imagewidget(
                edit=hl['w'], position=(hl['x'] - sz / 2, hl['y'] - sz / 2),
                size=(sz, sz), color=light, opacity=0.10 + 0.14 * (1 + ph) / 2)

        cyc = ((elapsed * speed) % 7.0) / 7.0
        if cyc < 0.22:
            f = cyc / 0.22
            bui.imagewidget(edit=self._tshine, position=(w * 0.2 + f * w * 0.6, h - 62),
                            color=(1, 1, 1), opacity=0.30 * math.sin(math.pi * f))
            self._tshine_on = True
        elif self._tshine_on:
            bui.imagewidget(edit=self._tshine, opacity=0.0)
            self._tshine_on = False

        sh = self._shoot
        if sh is None:
            if elapsed >= self._next_shoot:
                rn = self._rnd
                self._shoot = dict(t0=elapsed, x=rn.uniform(0.08, 0.5) * w,
                                   y=rn.uniform(0.7, 0.95) * h,
                                   vx=rn.uniform(260, 340), vy=-rn.uniform(120, 190))
        else:
            age = elapsed - sh['t0']
            if age > 1.0:
                for wd in self._shoot_w:
                    bui.imagewidget(edit=wd, opacity=0.0)
                self._shoot = None
                self._next_shoot = elapsed + self._rnd.uniform(5.0, 10.0)
            else:
                for j, wd in enumerate(self._shoot_w):
                    a = age - 0.05 * j
                    if a < 0:
                        continue
                    x = sh['x'] + sh['vx'] * a
                    y = sh['y'] + sh['vy'] * a
                    sz = (14, 10, 8, 6)[j]
                    bui.imagewidget(
                        edit=wd, position=(x - sz / 2, y - sz / 2), color=light,
                        opacity=(1 - age) * (0.95, 0.55, 0.35, 0.2)[j])

        for b in self._bursts:
            if b['t0'] is None:
                continue
            age = elapsed - b['t0']
            if age >= 1.1:
                b['t0'] = None
                bui.imagewidget(edit=b['w'], opacity=0.0)
                continue
            x = b['x'] + b['vx'] * age
            y = b['y'] + b['vy'] * age - 70.0 * age * age
            sz = 16 * (1 - 0.4 * age / 1.1)
            bui.imagewidget(edit=b['w'], position=(x - sz / 2, y - sz / 2),
                            size=(sz, sz), color=b['col'],
                            opacity=0.9 * (1 - age / 1.1) ** 1.2)


def _srv_key(addr, port) -> str:
    return f'{str(addr).strip()}@{int(port)}'


def _hist() -> Dict[str, Any]:
    cfg = babase.app.config
    h = cfg.get(_CFG_HISTORY)
    if not isinstance(h, dict):
        h = {}
        cfg[_CFG_HISTORY] = h
    return h


def history_record(addr, port, name: Optional[str] = None,
                   joined: bool = True) -> Optional[Dict[str, Any]]:
    try:
        addr = str(addr).strip()
        port = int(port)
        if not addr:
            return None
        h = _hist()
        key = _srv_key(addr, port)
        now = time.time()
        e = h.get(key)
        if not isinstance(e, dict):
            e = dict(addr=addr, port=port, name=(name or addr),
                     first=now, last=now, count=0)
            h[key] = e
        if joined:
            e['count'] = int(e.get('count', 0)) + 1
            e['last'] = now
        if name and name != e.get('name'):
            e['name'] = name
        babase.app.config.commit()
        return e
    except Exception:
        _print_exception('history_record failed')
        return None


def _saved_servers() -> Dict[str, Any]:
    cfg = babase.app.config
    s = cfg.get('Saved Servers')
    if not isinstance(s, dict):
        s = {}
        cfg['Saved Servers'] = s
    return s


def _find_favorite(addr, port) -> Optional[str]:
    addr = str(addr).strip()
    for k, v in _saved_servers().items():
        try:
            if (isinstance(v, dict) and str(v.get('addr', '')).strip() == addr
                    and int(v.get('port', -1)) == int(port)):
                return k
        except Exception:
            continue
    return None


def favorites_save(addr, port, name: str):
    addr = str(addr).strip()
    port = int(port)
    name = (name or '').strip() or addr
    saved = _saved_servers()
    k = _find_favorite(addr, port)
    if k is not None:
        old = str(saved[k].get('name', ''))
        if name != old:
            saved[k]['name'] = name
            babase.app.config.commit()
            return 'renamed', old
        return 'exists', old
    saved[_srv_key(addr, port)] = {'addr': addr, 'port': port, 'name': name}
    babase.app.config.commit()
    return 'added', ''


_PING_CACHE: Dict[str, Dict[str, Any]] = {}
_PING_SEM = threading.BoundedSemaphore(6)


def _ping_once(addr: str, port: int, tries: int = 3,
               timeout: float = 1.0) -> Optional[float]:
    sock = None
    try:
        infos = socket.getaddrinfo(addr, int(port), 0, socket.SOCK_DGRAM)
        fam, _typ, _proto, _cn, sockaddr = infos[0]
        sock = socket.socket(fam, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.connect(sockaddr)
        for _i in range(tries):
            t0 = time.time()
            sock.send(b'\x0b')
            try:
                res = sock.recv(10)
            except Exception:
                res = None
            if res == b'\x0c':
                return (time.time() - t0) * 1000.0
    except Exception:
        pass
    finally:
        try:
            if sock is not None:
                sock.close()
        except Exception:
            pass
    return None


def _ping_worker(addr: str, port: int, key: str) -> None:
    with _PING_SEM:
        ms = _ping_once(addr, port)
    _PING_CACHE[key] = dict(ms=ms, t=time.time(), busy=False)


def _ping_async(addr, port, force: bool = False) -> None:
    try:
        key = _srv_key(addr, port)
        cur = _PING_CACHE.get(key)
        if cur is not None and (cur.get('busy') or
                                (not force and time.time() - cur.get('t', 0) < 20)):
            return
        _PING_CACHE[key] = dict(ms=None, t=time.time(), busy=True)
        threading.Thread(target=_ping_worker, args=(str(addr), int(port), key),
                         daemon=True).start()
    except Exception:
        pass


def _ping_text(key: str):
    c = _PING_CACHE.get(key)
    if c is None:
        return '', None
    if c.get('busy'):
        return '...', None
    if c.get('ms') is None:
        return 'timeout', (1.0, 0.35, 0.35)
    return f"{int(c['ms'])} ms", _get_ping_color(c['ms'])


def _is_ip_literal(s: str) -> bool:
    for fam in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(fam, s)
            return True
        except Exception:
            pass
    return False


def _hsv(h: float, s: float, v: float):
    return colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)),
                               max(0.0, min(1.0, v)))


def _palette(rgb) -> Dict[str, Any]:
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    s = min(1.0, 0.15 + s * 0.8)
    return dict(
        body=_hsv(h, s * 0.9, 0.13), card=_hsv(h, s * 0.8, 0.21),
        head=_hsv(h, s * 0.8, 0.29), field=_hsv(h, s * 0.8, 0.10),
        edge=_hsv(h, s * 0.65, 0.72), edge_dim=_hsv(h, s * 0.65, 0.46),
        accent=_accent(rgb), light=_light(rgb, 0.45), text=_light(rgb, 0.16))


def _kind_colors(pal: Dict[str, Any]) -> Dict[str, Any]:
    return {'body': (pal['body'], pal['edge']),
            'card': (pal['card'], pal['edge_dim']),
            'head': (pal['head'], pal['edge']),
            'field': (pal['field'], pal['edge_dim'])}


class _RRect:

    def __init__(self, parent: bui.Widget, x: float, y: float, w: float,
                 h: float, r: float, color=(1, 1, 1)) -> None:
        r = max(1.0, min(r, w / 2.0, h / 2.0))
        white = bui.gettexture('white')
        disc = bui.gettexture('circle')
        self.parts: List[bui.Widget] = []

        def add(px, py, pw, ph, tex):
            self.parts.append(bui.imagewidget(
                parent=parent, position=(px, py), size=(pw, ph),
                texture=tex, color=color, opacity=1.0))

        add(x + r, y, w - 2 * r, h, white)
        add(x, y + r, r, h - 2 * r, white)
        add(x + w - r, y + r, r, h - 2 * r, white)
        tile = 2 * r / 0.97
        for cx, cy in ((x + r, y + r), (x + w - r, y + r),
                       (x + r, y + h - r), (x + w - r, y + h - r)):
            add(cx - tile / 2, cy - tile / 2, tile, tile, disc)

    def recolor(self, rgb) -> None:
        for p in self.parts:
            bui.imagewidget(edit=p, color=rgb)


class _Card:

    def __init__(self, parent, x, y, w, h, r, bw: float = 1.6) -> None:
        self.edge = _RRect(parent, x, y, w, h, r)
        self.fill = _RRect(parent, x + bw, y + bw, w - 2 * bw, h - 2 * bw,
                           max(1.0, r - bw))

    def recolor(self, edge, fill) -> None:
        self.edge.recolor(edge)
        self.fill.recolor(fill)


def _rounded_rim(w: float, h: float, radius: float, inset: float,
                 spacing: float = 18.0) -> List[Tuple[float, float]]:
    rr = max(2.0, radius - inset)
    x0, x1, y0, y1 = inset, w - inset, inset, h - inset
    lh = (x1 - x0) - 2 * rr
    lv = (y1 - y0) - 2 * rr
    arc = math.pi * rr / 2
    total = 2 * lh + 2 * lv + 4 * arc
    n = max(24, int(round(total / spacing)))
    pts = []
    for k in range(n):
        d = total * k / n
        if d < lh:
            p = (x0 + rr + d, y0)
        else:
            d -= lh
            if d < arc:
                a = -math.pi / 2 + d / rr
                p = (x1 - rr + rr * math.cos(a), y0 + rr + rr * math.sin(a))
            else:
                d -= arc
                if d < lv:
                    p = (x1, y0 + rr + d)
                else:
                    d -= lv
                    if d < arc:
                        a = d / rr
                        p = (x1 - rr + rr * math.cos(a), y1 - rr + rr * math.sin(a))
                    else:
                        d -= arc
                        if d < lh:
                            p = (x1 - rr - d, y1)
                        else:
                            d -= lh
                            if d < arc:
                                a = math.pi / 2 + d / rr
                                p = (x0 + rr + rr * math.cos(a),
                                     y1 - rr + rr * math.sin(a))
                            else:
                                d -= arc
                                if d < lv:
                                    p = (x0, y1 - rr - d)
                                else:
                                    d -= lv
                                    a = math.pi + d / rr
                                    p = (x0 + rr + rr * math.cos(a),
                                         y0 + rr + rr * math.sin(a))
        pts.append((p[0] / w, p[1] / h))
    return pts


class _Skin:

    def __init__(self, root: bui.Widget, w: float, h: float,
                 theme: Dict[str, Any], level: int,
                 cards: List[Tuple[float, float, float, float, float, str]],
                 halos: Optional[List[Any]] = None,
                 radius: float = 18.0) -> None:
        self._items: List[Tuple[_Card, str]] = []
        self._items.append((_Card(root, 0, 0, w, h, radius, bw=2.0), 'body'))
        for x, y, cw, ch, r, kind in cards:
            self._items.append((_Card(root, x, y, cw, ch, r), kind))
        self.fx = _FXLayer(root, w, h, level, theme, halos,
                           rim=_rounded_rim(w, h, radius, 5.0))
        self.pal: Dict[str, Any] = _palette(theme['a'])
        self.recolor(theme['a'])

    def recolor(self, rgb) -> None:
        pal = _palette(rgb)
        self.pal = pal
        kinds = _kind_colors(pal)
        for card, kind in self._items:
            fill, edge = kinds[kind]
            card.recolor(edge, fill)


_CFG_RECONNECT = 'BetterParty_Reconnect'
_CFG_ALERTS = 'BetterParty_Alerts'
_CFG_QUICK = 'BetterParty_Quick'
_CFG_CMDS = 'BetterParty_Cmds'
_DEFAULT_QUICK = ['gg', 'nice one', 'lol', 'wait for me', 'brb', 'ez']
_DEFAULT_CMDS = ['/list', '/help', '/ping', '/stats']


class _Live:

    def __init__(self) -> None:
        self.connected = False
        self.session_start: Optional[float] = None
        self.addr = ''
        self.port = 0
        self.name = ''
        self.target: Optional[Tuple[str, int]] = None
        self.ping_ms: Optional[float] = None
        self.ping_hist: deque = deque(maxlen=24)
        self.user_left = False
        self.reconnect_at: Optional[float] = None
        self.reconnect_tries = 0


_L = _Live()
_tracker_timer: Any = None
_orig_disconnect: Any = None


def _tracker_tick() -> None:
    try:
        info = bs.get_connection_to_host_info_2()
    except Exception:
        info = None
    now = time.time()
    cfg = babase.app.config
    try:
        if info is not None:
            addr = (getattr(info, 'address', '') or '')
            port = int(getattr(info, 'port', 0) or 0)
            name = (getattr(info, 'name', '') or '').strip()
            if not _L.connected:
                _L.connected = True
                _L.session_start = now
                _L.user_left = False
                _L.reconnect_at = None
                _L.reconnect_tries = 0
                _L.ping_hist.clear()
                if addr and port:
                    history_record(addr, port, name or None, joined=True)
            _L.addr, _L.port, _L.name = addr, port, name
            if addr and port:
                _L.target = (addr, port)
                e = _hist().get(_srv_key(addr, port))
                if name and isinstance(e, dict) and e.get('name') != name:
                    e['name'] = name
                    cfg.commit()
            return
        if _L.connected:
            _L.connected = False
            _L.session_start = None
            _L.ping_ms = None
            if cfg.get(_CFG_RECONNECT, False) and not _L.user_left and _L.target:
                _L.reconnect_tries = 0
                _L.reconnect_at = now + 5.0
                bui.screenmessage('Disconnected. Auto-reconnect in 5 s '
                                  '(turn it off in the ... menu)',
                                  color=(1, 0.8, 0.3))
            _L.user_left = False
        if _L.reconnect_at is not None and now >= _L.reconnect_at:
            if not cfg.get(_CFG_RECONNECT, False) or _L.target is None:
                _L.reconnect_at = None
                return
            _L.reconnect_tries += 1
            if _L.reconnect_tries > 3:
                _L.reconnect_at = None
                bui.screenmessage('Auto-reconnect gave up', color=(1, 0.4, 0.4))
                return
            bui.screenmessage(f'Reconnecting ({_L.reconnect_tries}/3) ...',
                              color=(0.5, 1, 0.7))
            _L.reconnect_at = now + 10.0
            join_server(_L.target[0], _L.target[1])
    except Exception:
        _print_exception('tracker tick failed')


def _ping_monitor() -> None:
    while True:
        try:
            t = _L.target
            if t is not None and _L.connected:
                ms = _ping_once(t[0], t[1], tries=2, timeout=0.8)
                _L.ping_ms = ms
                _L.ping_hist.append(ms if ms is not None else 999.0)
            time.sleep(1.2)
        except Exception:
            time.sleep(2.0)


def _migrate_history() -> None:
    cfg = babase.app.config
    try:
        if _CFG_HISTORY in cfg:
            return
        for key in list(cfg.keys()):
            val = cfg.get(key)
            if (key != _CFG_HISTORY and str(key).endswith('_ServerHistory')
                    and isinstance(val, dict) and val
                    and all(isinstance(e, dict) and 'addr' in e and 'port' in e
                            for e in val.values())):
                cfg[_CFG_HISTORY] = val
                cfg.commit()
                return
    except Exception:
        pass


def _install_hooks() -> None:
    global _orig_disconnect, _tracker_timer
    if _orig_disconnect is None:
        _orig_disconnect = bs.disconnect_from_host

        def _wrapped(*args, **kwargs):
            _L.user_left = True
            _L.reconnect_at = None
            return _orig_disconnect(*args, **kwargs)
        bs.disconnect_from_host = _wrapped
        threading.Thread(target=_ping_monitor, daemon=True).start()
    _tracker_timer = babase.AppTimer(1.0, _tracker_tick, repeat=True)


def join_server(addr, port) -> None:
    addr = str(addr).strip()
    port = int(port)

    def _go(ip: str) -> None:
        try:
            if bs.get_connection_to_host_info_2() is not None:
                _L.user_left = True
                bs.disconnect_from_host()
        except Exception:
            pass
        bs.connect_to_party(ip, port=port)

    if _is_ip_literal(addr):
        _go(addr)
        return

    def _work() -> None:
        try:
            res = socket.getaddrinfo(addr, port, 0, socket.SOCK_DGRAM)[0][4][0]
        except Exception:
            res = None

        def _done() -> None:
            if res is None:
                bui.screenmessage(
                    babase.Lstr(resource='internal.unableToResolveHostText'),
                    color=(1, 0, 0))
                bui.getsound('error').play()
            else:
                _go(res)
        bui.pushcall(_done, from_other_thread=True)
    threading.Thread(target=_work, daemon=True).start()


_UI_COLOR: List[Any] = [(0.16, 0.38, 0.92)]
_DISCORD_URL = 'https://discord.gg/V8KnB54fUF'
_CREDITS_BODY = (
    "As you can see, here we are, in a newer and a better version of "
    "PartyWindow. Let's just say it's the same as the regular one, but it "
    "looks way better, it has a lot of features and stuff, go check them out!")
_CREDITS_BY = 'Made by Nizar & Drap'


def _row_left(sx: float, sc: float, pad: float = 5.0) -> float:
    return -(sx * (1.0 - sc) / 2.0 + 9.0 - pad)


def _row_size(shift: float, sc: float) -> float:
    return 2.0 * shift / (1.0 - sc)


def _join_color(rgb):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return _hsv(h, 0.35 + s * 0.7, 1.0)


def _danger_color(rgb):
    h, s, _v = colorsys.rgb_to_hsv(*rgb)
    return _hsv(h, 0.3 + s * 0.5, 0.58)


def _dim(color, k: float = 0.5):
    return tuple(c * k for c in color[:3])


def _open_discord() -> None:
    try:
        bui.open_url(_DISCORD_URL)
        bui.screenmessage('Opening Discord ...', color=(0.55, 0.62, 1.0))
    except Exception:
        try:
            if bui.clipboard_is_supported():
                bui.clipboard_set_text(_DISCORD_URL)
        except Exception:
            pass
        bui.screenmessage('Discord link copied', color=(0.55, 0.62, 1.0))


def _options_items() -> Tuple[List[str], List[str]]:
    cfg = babase.app.config
    muted = cfg.resolve('Chat Muted')
    rc = cfg.get(_CFG_RECONNECT, False)
    al = cfg.get(_CFG_ALERTS, True)
    try:
        ag = _fr_auto_greet_enabled()
    except Exception:
        ag = True
    return (['profile', 'mute', 'clear', 'reconnect', 'alerts',
             'autogreet', 'copyip', 'credits'],
            ['Profile',
             'Unmute chat' if muted else 'Mute chat', 'Clear chat',
             f"Auto-reconnect: {'On' if rc else 'Off'}",
             f"Mention alerts: {'On' if al else 'Off'}",
             f"Auto-greet friends: {'On' if ag else 'Off'}",
             'Copy IP:Port',
             'Credits'])


def _options_choice(choice: str, party: Any = None) -> None:
    cfg = babase.app.config
    if choice == 'profile':
        try:
            _fr_open_profile(None)
        except Exception:
            _print_exception('profile failed')
        return
    if choice == 'mute':
        cfg['Chat Muted'] = not bool(cfg.resolve('Chat Muted'))
        cfg.apply_and_commit()
    elif choice == 'clear':
        if party is not None:
            party._clear_chat()
    elif choice == 'reconnect':
        cfg[_CFG_RECONNECT] = not cfg.get(_CFG_RECONNECT, False)
        cfg.commit()
        if not cfg[_CFG_RECONNECT]:
            _L.reconnect_at = None
        bui.screenmessage(
            f"Auto-reconnect: {'On' if cfg[_CFG_RECONNECT] else 'Off'}",
            color=(0.8, 0.9, 1))
    elif choice == 'alerts':
        cfg[_CFG_ALERTS] = not cfg.get(_CFG_ALERTS, True)
        cfg.commit()
        bui.screenmessage(
            f"Mention alerts: {'On' if cfg[_CFG_ALERTS] else 'Off'}",
            color=(0.8, 0.9, 1))
    elif choice == 'autogreet':
        try:
            new_val = not _fr_auto_greet_enabled()
            cfg[_CFG_AUTO_GREET] = new_val
            cfg.commit()
            bui.screenmessage(
                f"Auto-greet friends: {'On' if new_val else 'Off'}",
                color=(0.8, 0.9, 1))
        except Exception:
            pass
    elif choice == 'copyip':
        if _L.connected and _L.addr and bui.clipboard_is_supported():
            bui.clipboard_set_text(f'{_L.addr}:{_L.port}')
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))
        else:
            bui.screenmessage('Join a server first', color=(1, 1, 0))
            bui.getsound('error').play()
    elif choice == 'credits':
        _open_credits()


class _Overlay:

    def __init__(self, w: float, h: float, cards: List[Any],
                 outside_close: bool = True) -> None:
        ui = bui.app.ui_v1.uiscale
        scale = (1.7 if ui is bui.UIScale.SMALL else
                 1.3 if ui is bui.UIScale.MEDIUM else 1.0)
        self._root = bui.containerwidget(
            size=(w, h), transition='in_scale',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close if outside_close else None,
            scale=scale, background=False)
        self._cards: List[Tuple[_Card, str]] = [
            (_Card(self._root, 0, 0, w, h, 16, bw=2.0), 'body')]
        for x, y, cw, ch, r, kind in cards:
            self._cards.append((_Card(self._root, x, y, cw, ch, r), kind))
        self._pal = _palette(_UI_COLOR[0])
        self._btns: List[bui.Widget] = []
        self._texts: List[Tuple[bui.Widget, str]] = []
        self._paint()
        self._timer: Any = bui.AppTimer(
            0.25, bui.WeakCallStrict(self._tick), repeat=True)

    def _paint(self) -> None:
        kinds = _kind_colors(self._pal)
        for card, kind in self._cards:
            fill, edge = kinds[kind]
            card.recolor(edge, fill)

    def button(self, **kw) -> bui.Widget:
        b = bui.buttonwidget(
            parent=self._root, button_type='square', autoselect=True,
            color=self._pal['accent'], textcolor=self._pal['text'], **kw)
        self._btns.append(b)
        return b

    def text(self, role: str, **kw) -> bui.Widget:
        t = bui.textwidget(parent=self._root, color=self._pal[role], **kw)
        self._texts.append((t, role))
        return t

    def _tick(self) -> None:
        try:
            if not self._root.exists():
                self._timer = None
                return
            self._pal = pal = _palette(_UI_COLOR[0])
            self._paint()
            for b in self._btns:
                bui.buttonwidget(edit=b, color=pal['accent'],
                                 textcolor=pal['text'])
            for t, role in self._texts:
                bui.textwidget(edit=t, color=pal[role])
        except Exception:
            pass

    def close(self) -> None:
        try:
            if self._root and not self._root.transitioning_out:
                bui.containerwidget(edit=self._root, transition='out_scale')
        except Exception:
            pass


class _CreditsCard(_Overlay):
    def __init__(self) -> None:
        lines = textwrap.wrap(_CREDITS_BODY, 42)
        lh = 19.0
        W = 380.0
        content_h = 14 + len(lines) * lh + 14 + 28
        H = content_h + 128
        super().__init__(W, H, [
            (12, H - 58, W - 24, 46, 12, 'head'),
            (12, 62, W - 24, content_h, 12, 'card')])
        self.text('text', position=(W / 2, H - 35), size=(0, 0), scale=1.0,
                  text='Credits', h_align='center', v_align='center')
        top = 62 + content_h
        for i, line in enumerate(lines):
            self.text('text', position=(W / 2, top - 14 - lh * (i + 0.5)),
                      size=(0, 0), scale=0.62, text=line, maxwidth=W - 40,
                      h_align='center', v_align='center')
        self.text('light', position=(W / 2, 62 + 20), size=(0, 0), scale=0.85,
                  text=_CREDITS_BY, maxwidth=W - 40, h_align='center',
                  v_align='center')
        exit_btn = self.button(
            position=(W / 2 - 150, 14), size=(140, 40), label='Exit',
            on_activate_call=self.close)
        self.button(
            position=(W / 2 + 10, 14), size=(140, 40), label='Discord',
            icon=bui.gettexture('discordLogo'), iconscale=0.9,
            on_activate_call=_open_discord)
        bui.containerwidget(edit=self._root, cancel_button=exit_btn)


_credits_card: Any = None


def _open_credits() -> None:
    global _credits_card
    bui.getsound('swish').play()
    _credits_card = _CreditsCard()


class _EditDialog(_Overlay):
    def __init__(self, hub: Any, name: str, addr: str, port: int) -> None:
        self._hub_ref = weakref.ref(hub)
        W, H = 440.0, 316.0
        super().__init__(W, H, [(12, H - 58, W - 24, 46, 12, 'head')] + [
            (118, H - 118 - i * 54, W - 142, 38, 10, 'field')
            for i in range(3)])
        self.text('text', position=(W / 2, H - 35), size=(0, 0), scale=1.0,
                  text='Edit server', h_align='center', v_align='center')
        self._fields = []
        for i, (label, val, mc) in enumerate((
                ('Name', name, 60), ('Address', addr, 100),
                ('Port', str(port), 5))):
            y = H - 118 - i * 54
            self.text('light', position=(106, y + 19), size=(0, 0),
                      scale=0.7, text=label, h_align='right',
                      v_align='center')
            self._fields.append(bui.textwidget(
                parent=self._root, editable=True, size=(W - 156, 38),
                position=(124, y), text=val, max_chars=mc,
                description=label, autoselect=True, h_align='left',
                v_align='center', maxwidth=W - 164, color=(1, 1, 1)))
        cancel = self.button(position=(24, 14), size=(180, 40),
                             label=babase.Lstr(resource='cancelText'),
                             on_activate_call=self.close)
        self._save = self.button(position=(W - 204, 14), size=(180, 40),
                                 label='Save',
                                 on_activate_call=self._on_save)
        bui.widget(edit=cancel, right_widget=self._save)
        bui.widget(edit=self._save, left_widget=cancel)
        bui.containerwidget(edit=self._root, cancel_button=cancel,
                            start_button=self._save)

    def _on_save(self) -> None:
        hub = self._hub_ref()
        if hub is None:
            self.close()
            return
        try:
            name = (bui.textwidget(query=self._fields[0]) or '').strip()
            addr = (bui.textwidget(query=self._fields[1]) or '').strip()
            port = int(bui.textwidget(query=self._fields[2]))
            if not addr or port < 0 or port > 65535:
                raise ValueError
        except Exception:
            bui.screenmessage('Invalid address or port', color=(1, 0, 0))
            bui.getsound('error').play()
            return
        hub._apply_edit(name or addr, addr, port)
        self.close()


_HUB_SORTS = ['recent', 'name', 'joins', 'ping']
_HUB_SORT_NAMES = {'recent': 'Recent', 'name': 'A-Z',
                   'joins': 'Most joined', 'ping': 'Ping'}
_HUB_SHIFT = 100.0


class ServerHubWindow:

    def __init__(self, party: Any = None) -> None:
        cfg = babase.app.config
        ui = bui.app.ui_v1.uiscale
        self.W = 620
        self.H = (360 if ui is bui.UIScale.SMALL else
                  440 if ui is bui.UIScale.MEDIUM else 520)
        self._scale = (1.7 if ui is bui.UIScale.SMALL else
                       1.3 if ui is bui.UIScale.MEDIUM else 1.0)
        self._party_ref = weakref.ref(party) if party is not None else None
        self._restored = False
        tab = cfg.get(_CFG_HUB_TAB, 'history')
        self._tab = tab if tab in ('history', 'favorites') else 'history'
        sort = cfg.get(_CFG_HUB_SORT, 'recent')
        self._sort = sort if sort in _HUB_SORTS else 'recent'
        self._filter = ''
        self._selected: Optional[str] = None
        self._items: List[Dict[str, Any]] = []
        self._rows: Dict[str, Any] = {}
        self._shown: Dict[str, Any] = {}
        self._tick_n = 0
        self._dlg: Any = None
        self._edit_key = ''
        self._theme_name = cfg.get(_CFG_THEME, 'Aurora')
        self._theme = _get_theme(self._theme_name)
        self._speed = float(cfg.get(_CFG_SPEED, 1.0))
        level = cfg.get(_CFG_FX, 2)
        level = level if level in (0, 1, 2) else 2
        self._color = _theme_rgb(self._theme, time.time() - _FX_T0,
                                 self._speed)
        _UI_COLOR[0] = self._color
        w, h, P = self.W, self.H, 10
        hy = h - P - 54
        ty = hy - 6 - 32
        top = ty - 6
        info_h = 32
        list_y = P + info_h + 6
        list_h = top - list_y
        side_w = 168
        list_w = w - 2 * 18 - side_w - 8
        side_x = 18 + list_w + 8
        self._side = (side_x, list_y, side_w, list_h)

        self._root = bui.containerwidget(
            size=(w, h), transition='in_scale',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close_with_sound,
            scale=self._scale, background=False,
            stack_offset=(0, -10) if ui is bui.UIScale.SMALL else (0, 0))
        party_obj = self._party_ref() if self._party_ref else None
        if party_obj is not None:
            try:
                party_obj._fx.set_level(0)
            except Exception:
                pass
        search_x = 366
        self._skin = _Skin(
            self._root, w, h, self._theme, level,
            [(P, hy, w - 2 * P, 54, 14, 'head'),
             (18, list_y, list_w, list_h, 12, 'card'),
             (side_x, list_y, side_w, list_h, 12, 'card'),
             (18, P, w - 36, info_h, 10, 'field'),
             (search_x, ty, w - 18 - search_x, 32, 8, 'field')])
        self._fx = self._skin.fx
        self._skin.recolor(self._color)
        pal = self._skin.pal

        self._cancel = bui.buttonwidget(
            parent=self._root, position=(P + 6, hy + 7), size=(40, 40),
            label=bui.charstr(bui.SpecialChar.CLOSE), button_type='square',
            autoselect=True, color=pal['accent'], textcolor=pal['text'],
            on_activate_call=self.close)
        bui.containerwidget(edit=self._root, cancel_button=self._cancel)
        self._title = bui.textwidget(
            parent=self._root, position=(w / 2, hy + 37), size=(0, 0),
            scale=0.95, text='Servers', maxwidth=300, h_align='center',
            v_align='center', color=pal['text'])
        self._subtitle = bui.textwidget(
            parent=self._root, position=(w / 2, hy + 15), size=(0, 0),
            scale=0.45, text='', h_align='center', v_align='center',
            color=(0.85, 0.93, 1.0), maxwidth=300)
        self._tab_hist = bui.buttonwidget(
            parent=self._root, position=(18, ty), size=(100, 32),
            label='History', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._set_tab, 'history'))
        self._tab_fav = bui.buttonwidget(
            parent=self._root, position=(122, ty), size=(110, 32),
            label='Favorites', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._set_tab, 'favorites'))
        self._sort_btn = bui.buttonwidget(
            parent=self._root, position=(236, ty), size=(124, 32),
            label='', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.8,
            on_activate_call=self._cycle_sort)
        self._search = bui.textwidget(
            parent=self._root, position=(search_x + 8, ty),
            size=(w - 18 - search_x - 16, 32), editable=True, text='',
            maxwidth=w - 18 - search_x - 24, max_chars=40,
            description='Search', h_align='left', v_align='center',
            autoselect=True, shadow=0.3, flatness=1.0, color=(1, 1, 1))
        self._search_hint = bui.textwidget(
            parent=self._root, position=(search_x + 12, ty + 16),
            size=(0, 0), text='search...', scale=0.7,
            color=(0.8, 0.9, 1.0, 0.55), h_align='left', v_align='center')

        self._list_w = list_w - 12
        self._sx_name = _row_size(_HUB_SHIFT, 0.85)
        self._sx_det = _row_size(_HUB_SHIFT, 0.55)
        self._scroll = bui.scrollwidget(
            parent=self._root, position=(24, list_y + 6),
            size=(list_w - 12, list_h - 12), color=(0.4, 0.6, 0.3),
            border_opacity=0.0)
        self._col = bui.columnwidget(
            parent=self._scroll, border=2,
            left_border=_row_left(self._sx_name, 0.85), margin=0)

        bx = side_x + 8
        bw = side_w - 16
        avail = list_h - 12
        join_h, gap = 34, 4
        bh = max(24, min(34, (avail - join_h - 5 * gap) / 5))
        y = list_y + list_h - 6 - join_h
        self._btn_join = bui.buttonwidget(
            parent=self._root, position=(bx, y), size=(bw, join_h),
            label='JOIN', button_type='square', autoselect=True,
            color=_join_color(self._color), textcolor=(1, 1, 1),
            text_scale=1.05, on_activate_call=self._join_selected)

        def side_btn(label, call, **kw):
            nonlocal y
            y -= gap + bh
            return bui.buttonwidget(
                parent=self._root, position=(bx, y), size=(bw, bh),
                label=label, button_type='square', autoselect=True,
                color=pal['accent'], textcolor=pal['text'], text_scale=0.85,
                on_activate_call=call, **kw)
        self._btn_fav = side_btn('Favorite', self._toggle_fav)
        self._btn_edit = side_btn('Edit name/ip/port', self._edit_selected)
        self._btn_copy = side_btn('Copy IP:Port', self._copy_selected)
        self._btn_ping = side_btn('Ping all', self._ping_all)
        self._btn_del = side_btn('Delete', self._delete_selected)
        bui.buttonwidget(edit=self._btn_del, color=_danger_color(self._color))
        self._info = bui.textwidget(
            parent=self._root, position=(w / 2, P + info_h / 2), size=(0, 0),
            scale=0.55, text='', h_align='center', v_align='center',
            maxwidth=w - 60, color=(0.9, 0.95, 1.0))
        self._accent_buttons = [
            self._cancel, self._tab_hist, self._tab_fav, self._sort_btn, self._btn_fav,
            self._btn_edit, self._btn_copy, self._btn_ping]

        self._refresh_tabs(pal)
        self._rebuild_list()
        self._timer: Any = bui.AppTimer(
            0.06, bui.WeakCallStrict(self._tick), repeat=True)

    def close(self) -> None:
        if not self._restored:
            self._restored = True
            party = self._party_ref() if self._party_ref else None
            if party is not None:
                try:
                    party._fx.set_level(party._fx_level)
                except Exception:
                    pass
        try:
            if self._root and not self._root.transitioning_out:
                bui.containerwidget(edit=self._root, transition='out_scale')
        except Exception:
            pass

    def close_with_sound(self) -> None:
        bui.getsound('swish').play()
        self.close()

    def _live_key(self) -> Optional[str]:
        try:
            if _L.connected and _L.addr:
                return _srv_key(_L.addr, _L.port)
        except Exception:
            pass
        return None

    def _load_items(self) -> List[Dict[str, Any]]:
        hist = _hist()
        favs = _saved_servers()
        fav_set = set()
        for v in favs.values():
            try:
                fav_set.add(_srv_key(v['addr'], v['port']))
            except Exception:
                pass
        items: List[Dict[str, Any]] = []
        if self._tab == 'history':
            for k, e in hist.items():
                try:
                    items.append(dict(
                        key=k, addr=str(e['addr']), port=int(e['port']),
                        name=str(e.get('name') or e['addr']),
                        count=int(e.get('count', 0)), last=float(e.get('last', 0)),
                        fav=_srv_key(e['addr'], e['port']) in fav_set))
                except Exception:
                    continue
        else:
            for k, v in favs.items():
                try:
                    pk = _srv_key(v['addr'], v['port'])
                    he = hist.get(pk) or {}
                    items.append(dict(
                        key=k, addr=str(v['addr']), port=int(v['port']),
                        name=str(v.get('name') or v['addr']),
                        count=int(he.get('count', 0)),
                        last=float(he.get('last', 0)), fav=True))
                except Exception:
                    continue
        for it in items:
            it['pkey'] = _srv_key(it['addr'], it['port'])
        q = self._filter.lower()
        if q:
            items = [i for i in items if q in i['name'].lower()
                     or q in i['addr'].lower() or q in str(i['port'])]
        if self._sort == 'name':
            items.sort(key=lambda i: i['name'].lower())
        elif self._sort == 'joins':
            items.sort(key=lambda i: -i['count'])
        elif self._sort == 'ping':
            def pk(i):
                c = _PING_CACHE.get(i['pkey'])
                return c['ms'] if c and c.get('ms') is not None else 1e9
            items.sort(key=pk)
        else:
            items.sort(key=lambda i: -i['last'])
        return items

    def _item(self, key: Optional[str]) -> Optional[Dict[str, Any]]:
        for it in self._items:
            if it['key'] == key:
                return it
        return None

    def _row_texts(self, it: Dict[str, Any]):
        sel = it['key'] == self._selected
        live = it['pkey'] == self._live_key()
        name = ('> ' if sel else '   ') + it['name'] + ('   [LIVE]' if live else '')
        ptxt, pcol = _ping_text(it['pkey'])
        bits = [f"{it['addr']}:{it['port']}"]
        if ptxt:
            bits.append(ptxt)
        if it['count']:
            bits.append(f"x{it['count']}")
        ago = _ago(it['last'])
        if ago:
            bits.append(ago)
        ncol = ((1, 1, 1) if sel else (0.5, 1.0, 0.7) if live
                else (1.0, 0.88, 0.4) if it['fav'] else (0.85, 0.92, 1.0))
        dcol = pcol if pcol else (0.7, 0.8, 0.9)
        return name, '   '.join(bits), ncol, dcol

    def _rebuild_list(self) -> None:
        for c in self._col.get_children():
            c.delete()
        self._rows = {}
        self._shown = {}
        self._items = self._load_items()
        if self._selected is None or self._item(self._selected) is None:
            self._selected = self._items[0]['key'] if self._items else None
        if not self._items:
            sx = _row_size(_HUB_SHIFT, 0.7)
            bui.textwidget(
                parent=self._col, size=(sx, 60), scale=0.7,
                text=('No servers match.' if self._filter else
                      'Nothing here yet. Join a server and it\nappears here automatically.'
                      if self._tab == 'history' else
                      'No favorites yet. Use the star button\nin the party window.'),
                h_align='left', v_align='center', color=(0.8, 0.9, 1.0))
        for idx, it in enumerate(self._items):
            name, det, ncol, dcol = self._row_texts(it)
            sel_call = bui.CallStrict(self._select, it['key'])
            act_call = bui.CallStrict(self._join_key, it['key'])
            n = bui.textwidget(
                parent=self._col, size=(self._sx_name, 22), text=name,
                scale=0.85, h_align='left', v_align='center', selectable=True,
                autoselect=True, color=ncol, maxwidth=self._list_w - 30,
                on_select_call=sel_call, on_activate_call=act_call)
            d = bui.textwidget(
                parent=self._col, size=(self._sx_det, 14), text=det,
                scale=0.55, h_align='left', v_align='center', color=dcol,
                maxwidth=self._list_w - 30, selectable=True,
                on_select_call=sel_call, on_activate_call=act_call)
            self._rows[it['key']] = (n, d)
            self._shown[it['key']] = (name, det)
            if idx < 12:
                _ping_async(it['addr'], it['port'])
        self._refresh_actions()

    def _refresh_rows(self) -> None:
        for it in self._items:
            r = self._rows.get(it['key'])
            if not r:
                continue
            name, det, ncol, dcol = self._row_texts(it)
            try:
                bui.textwidget(edit=r[0], text=name, color=ncol)
                if self._shown.get(it['key']) != (name, det):
                    bui.textwidget(edit=r[1], text=det, color=dcol)
                self._shown[it['key']] = (name, det)
            except Exception:
                pass

    def _select(self, key: str) -> None:
        if key != self._selected:
            self._selected = key
            self._refresh_rows()
            self._refresh_actions()

    def _refresh_actions(self) -> None:
        it = self._item(self._selected)
        try:
            bui.buttonwidget(edit=self._btn_fav,
                             label='Unfavorite' if (it and it['fav']) else 'Favorite')
            bui.buttonwidget(edit=self._sort_btn,
                             label='Sort: ' + _HUB_SORT_NAMES[self._sort])
            if it:
                ptxt, _pcol = _ping_text(it['pkey'])
                info = f"{it['name']}  -  {it['addr']}:{it['port']}"
                if it['count']:
                    info += f"  -  joined {it['count']}x"
                if it['last']:
                    info += f"  -  {_ago(it['last'])}"
                if ptxt:
                    info += f"  -  {ptxt}"
            else:
                info = 'Select a server'
            bui.textwidget(edit=self._info, text=info)
            bui.textwidget(
                edit=self._subtitle,
                text=f'{len(_hist())} in history   |   {len(_saved_servers())} favorites')
        except Exception:
            pass

    def _refresh_tabs(self, pal: Dict[str, Any]) -> None:
        on = pal['text']
        off = _dim(pal['text'], 0.5)
        bui.buttonwidget(edit=self._tab_hist,
                         textcolor=on if self._tab == 'history' else off)
        bui.buttonwidget(edit=self._tab_fav,
                         textcolor=on if self._tab == 'favorites' else off)

    def _apply_style(self, rgb, el: float) -> None:
        pal = self._skin.pal
        for b in self._accent_buttons:
            bui.buttonwidget(edit=b, color=pal['accent'], textcolor=pal['text'])
        bui.buttonwidget(edit=self._btn_join, color=_join_color(rgb),
                         textcolor=(1, 1, 1))
        bui.buttonwidget(edit=self._btn_del, color=_danger_color(rgb),
                         textcolor=pal['text'])
        self._refresh_tabs(pal)
        bui.textwidget(edit=self._title, color=_light(rgb, 0.3),
                       scale=0.95 + 0.03 * math.sin(el * 2.2))

    def _tick(self) -> None:
        try:
            if not self._root.exists():
                self._timer = None
                return
            elapsed = time.time() - _FX_T0
            rgb = _theme_rgb(self._theme, elapsed, self._speed)
            self._color = rgb
            _UI_COLOR[0] = rgb
            self._fx.tick(elapsed, rgb, self._speed)
            self._tick_n += 1
            if self._tick_n % 4 == 0:
                self._skin.recolor(rgb)
            if self._tick_n % 3 == 0:
                self._apply_style(rgb, elapsed)
            if self._tick_n % 8 == 0:
                q = (bui.textwidget(query=self._search) or '').strip()
                bui.textwidget(edit=self._search_hint,
                               text='' if q else 'search...')
                if q != self._filter:
                    self._filter = q
                    self._rebuild_list()
                else:
                    self._refresh_rows()
        except Exception:
            pass

    def _no_selection(self) -> None:
        bui.screenmessage('Select a server first', color=(1, 1, 0))
        bui.getsound('error').play()

    def _set_tab(self, tab: str) -> None:
        self._tab = tab
        babase.app.config[_CFG_HUB_TAB] = tab
        babase.app.config.commit()
        self._selected = None
        bui.getsound('click01').play()
        self._fx.pulse()
        self._refresh_tabs(self._skin.pal)
        self._rebuild_list()

    def _cycle_sort(self) -> None:
        self._sort = _HUB_SORTS[(_HUB_SORTS.index(self._sort) + 1) % len(_HUB_SORTS)]
        babase.app.config[_CFG_HUB_SORT] = self._sort
        babase.app.config.commit()
        bui.getsound('click01').play()
        self._rebuild_list()

    def _join_key(self, key: str) -> None:
        it = self._item(key)
        if it is None:
            return self._no_selection()
        bui.getsound('swish').play()
        bui.screenmessage(f"Joining {it['name']} ...", color=(0.5, 1, 0.7))
        join_server(it['addr'], it['port'])
        self.close()

    def _join_selected(self) -> None:
        self._join_key(self._selected)

    def _toggle_fav(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        if it['fav']:
            k = _find_favorite(it['addr'], it['port'])
            if k is not None:
                _saved_servers().pop(k, None)
                babase.app.config.commit()
            bui.getsound('shieldDown').play()
            bui.screenmessage(f"Removed from favorites: {it['name']}", color=(1, 0.8, 0.3))
        else:
            status, old = favorites_save(it['addr'], it['port'], it['name'])
            bui.getsound('gunCocking').play()
            self._fx.burst(self._side[0] + self._side[2] / 2, self._side[1] + self._side[3] / 2)
            bui.screenmessage(f"Saved to favorites: {it['name']}", color=(0, 1, 0))
        self._rebuild_list()

    def _copy_selected(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(f"{it['addr']}:{it['port']}")
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'), color=(0, 1, 0))
        else:
            bui.screenmessage(f"{it['addr']}:{it['port']}", color=(0.8, 0.9, 1))

    def _ping_all(self) -> None:
        bui.getsound('click01').play()
        for it in self._items[:30]:
            _ping_async(it['addr'], it['port'], force=True)

    def _delete_selected(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        where = 'History' if self._tab == 'history' else 'Favorites'
        ConfirmWindow(
            babase.Lstr(value=f"Delete \"{it['name']}\" from {where}?"),
            bui.CallStrict(self._do_delete, it['key']), width=460, height=150)

    def _do_delete(self, key: str) -> None:
        store = _hist() if self._tab == 'history' else _saved_servers()
        store.pop(key, None)
        babase.app.config.commit()
        bui.getsound('shieldDown').play()
        self._selected = None
        self._rebuild_list()

    def _edit_selected(self) -> None:
        it = self._item(self._selected)
        if it is None:
            return self._no_selection()
        self._edit_key = it['key']
        self._dlg = _EditDialog(self, it['name'], it['addr'], it['port'])

    def _apply_edit(self, name: str, addr: str, port: int) -> None:
        old = self._edit_key
        newkey = _srv_key(addr, port)
        if self._tab == 'history':
            h = _hist()
            e = h.pop(old, None) or {}
            if newkey in h and newkey != old:
                t = h[newkey]
                t['name'] = name
                t['count'] = int(t.get('count', 0)) + int(e.get('count', 0))
                t['last'] = max(float(t.get('last', 0)), float(e.get('last', 0)))
            else:
                e.update(addr=addr, port=port, name=name)
                e.setdefault('count', 0)
                e.setdefault('first', time.time())
                e.setdefault('last', 0)
                h[newkey] = e
        else:
            s = _saved_servers()
            s.pop(old, None)
            s[newkey] = {'addr': addr, 'port': port, 'name': name}
        babase.app.config.commit()
        self._selected = newkey
        bui.getsound('gunCocking').play()
        self._rebuild_list()


_CHAT_LEFT = _row_left(900.0, 0.6)


class _PlayerCard:

    def __init__(self, party: 'BetterPartyWindow', ent: Dict[str, Any],
                 is_host: bool, anchor) -> None:
        self._party_ref = weakref.ref(party)
        self._last_col = party._color
        acc = str(ent.get('display_string') or '').strip()
        cid = ent.get('client_id')
        profs: List[str] = []
        for pl in (ent.get('players') or [])[:3]:
            nm = str(pl.get('name_full') or pl.get('name') or '').strip()
            if nm and nm not in profs:
                profs.append(nm)
        rows: List[Tuple[str, str]] = []
        if acc:
            rows.append(('ACCOUNT NAME', acc))
        rows += [('PROFILE NAME', p) for p in profs]
        if cid is not None:
            rows.append(('CLIENT ID', str(cid)))
        title = profs[0] if profs else (acc or 'Player')
        W = 380
        H = 70 + len(rows) * 42 + 58
        ui = bui.app.ui_v1.uiscale
        scale = (1.7 if ui is bui.UIScale.SMALL else
                 1.3 if ui is bui.UIScale.MEDIUM else 1.0)
        self._root = root = bui.containerwidget(
            size=(W, H), transition='in_scale',
            parent=bui.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close, scale=scale, background=False)
        self._cards: List[Tuple[_Card, str]] = [
            (_Card(root, 0, 0, W, H, 16, bw=2.0), 'body'),
            (_Card(root, 12, H - 62, W - 24, 50, 12), 'head')]
        ys, y = [], H - 62 - 8 - 38
        for _r in rows:
            self._cards.append((_Card(root, 12, y, W - 24, 38, 10), 'card'))
            ys.append(y)
            y -= 42
        pal = _palette(party._color)
        self._paint(pal)

        self._btns: List[bui.Widget] = []
        close = bui.buttonwidget(
            parent=root, position=(18, H - 56), size=(38, 38),
            label=bui.charstr(bui.SpecialChar.CLOSE), button_type='square',
            autoselect=True, color=pal['accent'], textcolor=pal['text'], on_activate_call=self.close)
        bui.containerwidget(edit=root, cancel_button=close)
        self._btns.append(close)
        self._title = bui.textwidget(
            parent=root, position=(W / 2 + 14, H - 30), size=(0, 0),
            scale=0.9, text=bui.Lstr(value=title), maxwidth=W - 130,
            h_align='center', v_align='center', color=pal['text'])
        sub = 'host' if is_host else (f'client {cid}' if cid is not None else '')
        bui.textwidget(
            parent=root, position=(W / 2 + 14, H - 49), size=(0, 0),
            scale=0.45, text=f'tap Add to put a name in your message box   '
            f'{("(" + sub + ")") if sub else ""}', maxwidth=W - 130,
            h_align='center', v_align='center', color=(0.85, 0.93, 1.0))
        self._labels: List[bui.Widget] = []
        for (label, val), yy in zip(rows, ys):
            self._labels.append(bui.textwidget(
                parent=root, position=(22, yy + 29), size=(0, 0), scale=0.42,
                text=label, h_align='left', v_align='center',
                color=pal['light']))
            bui.textwidget(
                parent=root, position=(22, yy + 13), size=(0, 0), scale=0.8,
                text=bui.Lstr(value=val), h_align='left', v_align='center',
                maxwidth=200, color=(1, 1, 1))
            add = bui.buttonwidget(
                parent=root, position=(W - 12 - 8 - 58 * 2 - 6, yy + 4),
                size=(56, 30), label='Add', button_type='square',
                autoselect=True, color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
                on_activate_call=bui.CallStrict(self._add, val))
            cp = bui.buttonwidget(
                parent=root, position=(W - 12 - 8 - 58, yy + 4),
                size=(56, 30), label='Copy', button_type='square',
                autoselect=True, color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
                on_activate_call=bui.CallStrict(self._copy, val))
            self._btns += [add, cp]
        self._actions = bui.buttonwidget(
            parent=root, position=(20, 10), size=(160, 38),
            label='Kick / admin ...', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
            on_activate_call=bui.CallStrict(
                self._open_actions, cid, is_host, title))
        done = bui.buttonwidget(
            parent=root, position=(W - 180, 10), size=(160, 38),
            label='Close', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9, on_activate_call=self.close)
        self._btns += [self._actions, done]
        self._timer: Any = bui.AppTimer(
            0.25, bui.WeakCallStrict(self._tick), repeat=True)

    def _paint(self, pal) -> None:
        kinds = _kind_colors(pal)
        for card, kind in self._cards:
            fill, edge = kinds[kind]
            card.recolor(edge, fill)

    def _tick(self) -> None:
        try:
            if not self._root.exists():
                self._timer = None
                return
            party = self._party_ref()
            if party is not None:
                self._last_col = party._color
            pal = _palette(self._last_col)
            self._paint(pal)
            for b in self._btns:
                bui.buttonwidget(edit=b, color=pal['accent'], textcolor=pal['text'])
            bui.textwidget(edit=self._title, color=pal['text'])
            for lb in self._labels:
                bui.textwidget(edit=lb, color=pal['light'])
        except Exception:
            pass

    def _open_actions(self, cid, is_host: bool, name: str) -> None:
        party = self._party_ref()
        if party is not None:
            party._on_member_press(cid, is_host, self._actions, name)

    def _add(self, value: str) -> None:
        try:
            party = self._party_ref()
            if party is not None:
                party._append_to_field(value)
                party._fx.pulse()
        except Exception:
            pass
        bui.getsound('gunCocking').play()
        bui.screenmessage(f'Added to message: {value}', color=(0, 1, 0))
        self.close()

    def _copy(self, value: str) -> None:
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(value)
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    def close(self) -> None:
        try:
            if self._root and not self._root.transitioning_out:
                bui.containerwidget(edit=self._root, transition='out_scale')
        except Exception:
            pass


class BetterPartyWindow(bui.Window):

    PAD = 10
    HEAD_H = 54
    FOOT_H = 50
    INFO_H = 18
    DOCK_W = 56
    ROSTER_W = 232

    def __init__(self, origin: Sequence[float] = (0, 0)) -> None:
        self._uiopenstate = bui.UIOpenState('classicparty')
        ui = bui.app.ui_v1.uiscale
        self._W = 662
        self._H = (360 if ui is bui.UIScale.SMALL else
                   440 if ui is bui.UIScale.MEDIUM else 520)
        scale = (1.7 if ui is bui.UIScale.SMALL else
                 1.3 if ui is bui.UIScale.MEDIUM else 1.0)

        cfg = babase.app.config
        self._theme_name = cfg.get(_CFG_THEME, 'Aurora')
        if self._theme_name not in THEMES and self._theme_name != 'Custom':
            self._theme_name = 'Aurora'
        self._theme = _get_theme(self._theme_name)
        lvl = cfg.get(_CFG_FX, 2)
        self._fx_level = lvl if lvl in (0, 1, 2) else 2
        self._speed = float(cfg.get(_CFG_SPEED, 1.0))
        self._auto = bool(cfg.get(_CFG_AUTO, False))
        self._auto_t = time.time()
        self._color = _theme_rgb(self._theme, time.time() - _FX_T0,
                                 self._speed)
        _UI_COLOR[0] = self._color
        self._bg_color_a = self._theme['a']
        self._bg_color_b = self._theme['b']
        self._blend_from: Any = None
        self._blend_t0 = 0.0
        self._n = 0
        self._popup_type: Optional[str] = None
        self._menu_popup: Optional[PopupMenuWindow] = None
        self._popup_cid: Optional[int] = None
        self._popup_is_host = False
        self._popup_name = ''
        self._pending_wave_pick: Optional[str] = None
        self._chat_rows: List[bui.Widget] = []
        self._chat_msgs: List[str] = []
        self._recall_i: Optional[int] = None
        self._recall_orig = ''
        self._hl: Optional[Tuple[bui.Widget, str]] = None
        self._roster: Any = None
        self._roster_widgets: List[bui.Widget] = []
        self._ros_tab = 'players'
        self._fr_sig: Any = None
        self._fr_cards: List[Any] = []
        self._fr_tabtxt: Dict[str, Any] = {}
        self._display_old = True
        self._was_connected = False
        self._was_muted = False
        self._last_title: Any = None
        self._toast: Optional[Tuple[str, Any, float]] = None
        self._my_name = ''
        try:
            self._my_name = (bui.app.plus.get_v1_account_name() or '').strip()
        except Exception:
            pass

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._W, self._H),
                transition='in_scale',
                parent=bui.get_special_widget('overlay_stack'),
                on_outside_click_call=self.close_with_sound,
                scale_origin_stack_offset=origin,
                scale=scale,
                stack_offset=((0, -10) if ui is bui.UIScale.SMALL else (0, 0)),
                darken_behind=True,
                background=False),
            prevent_main_window_auto_recreate=False)
        try:
            self._build()
        except Exception:
            try:
                bui.containerwidget(edit=self._root_widget, transition='out_scale')
            except Exception:
                pass
            raise

    def _build(self) -> None:
        W, H, P = self._W, self._H, self.PAD
        root = self._root_widget
        hy = H - P - self.HEAD_H
        cy0 = P + self.FOOT_H + self.INFO_H + 6
        cy1 = hy - 8
        ch = cy1 - cy0
        dock_x = P
        chat_x = P + self.DOCK_W + 8
        ros_x = W - P - self.ROSTER_W
        chat_w = ros_x - 8 - chat_x
        quick_w, send_w = 64, 70
        qx = P + 8
        sx = W - P - 8 - send_w
        aw = 30
        ax_up = qx + quick_w + 6
        ax_dn = ax_up + aw + 4
        fx_ = ax_dn + aw + 8
        fw = sx - 8 - fx_
        self._geo = dict(hy=hy, cy0=cy0, cy1=cy1, ch=ch, chat_x=chat_x,
                         chat_w=chat_w, ros_x=ros_x, sx=sx, send_w=send_w)

        bh, step = 34, 39
        dock_y = [cy1 - 5 - bh - i * step for i in range(5)]
        dbx = dock_x + 7
        menu_x = W - P - 6 - 40
        style_x = menu_x - 8 - 64
        halos = [(dbx + 21, dock_y[2] + 17, 64), (dbx + 21, dock_y[3] + 17, 64),
                 (sx + send_w / 2, P + 25, 92), (style_x + 32, hy + 27, 100)]

        self._skin = _Skin(
            root, W, H, self._theme, self._fx_level,
            [(P, hy, W - 2 * P, self.HEAD_H, 14, 'head'),
             (dock_x, cy0, self.DOCK_W, ch, 12, 'card'),
             (chat_x, cy0, chat_w, ch, 12, 'card'),
             (ros_x, cy0, self.ROSTER_W, ch, 12, 'card'),
             (P, P, W - 2 * P, self.FOOT_H, 14, 'head'),
             (fx_, P + 6, fw, self.FOOT_H - 12, 10, 'field')],
            halos=halos)
        self._fx = self._skin.fx
        self._skin.recolor(self._color)
        pal = self._skin.pal

        self._close_btn = bui.buttonwidget(
            parent=root, position=(P + 6, hy + 7), size=(40, 40),
            label=bui.charstr(bui.SpecialChar.CLOSE), button_type='square',
            autoselect=True, color=pal['accent'], textcolor=pal['text'], on_activate_call=self.close)
        bui.containerwidget(edit=root, cancel_button=self._close_btn)
        self._spark_x0 = P + 6 + 40 + 12
        self._spark_y0 = hy + 11
        self._spark = [bui.imagewidget(
            parent=root, position=(self._spark_x0 + i * 4.4, self._spark_y0),
            size=(3.2, 2), texture=bui.gettexture('white'),
            color=(0.5, 0.5, 0.5), opacity=0.0) for i in range(24)]
        self._title = bui.textwidget(
            parent=root, position=(W / 2, hy + 37), size=(0, 0), scale=0.95,
            text=bui.Lstr(resource='partyWindow.titleText'), maxwidth=230,
            h_align='center', v_align='center', color=pal['text'])
        self._sub = bui.textwidget(
            parent=root, position=(W / 2, hy + 15), size=(0, 0), scale=0.45,
            text='', maxwidth=300, h_align='center', v_align='center',
            color=(0.85, 0.93, 1.0))
        self._menu_btn = bui.buttonwidget(
            parent=root, position=(menu_x, hy + 7), size=(40, 40), label='...',
            button_type='square', autoselect=True, color=pal['accent'], textcolor=pal['text'],
            on_activate_call=self._on_menu_press)
        self._style_btn = bui.buttonwidget(
            parent=root, position=(style_x, hy + 9), size=(64, 36),
            label='Style', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
            on_activate_call=self._on_style_press)

        def dock(i, **kw):
            return bui.buttonwidget(
                parent=root, position=(dbx, dock_y[i]), size=(42, bh),
                button_type='square', autoselect=True, color=pal['accent'], textcolor=pal['text'],
                **kw)
        self._ping_btn = dock(0, label='--', text_scale=0.95,
                              on_activate_call=self._share_ping)
        self._ip_btn = dock(1, label='IP', text_scale=1.05,
                            on_activate_call=self._share_ip)
        self._save_btn = dock(2, label='', icon=bui.gettexture('star'),
                              iconscale=1.0, on_activate_call=self._save_server)
        self._hub_btn = dock(3, label='', icon=bui.gettexture('logIcon'),
                             iconscale=1.0, on_activate_call=self._open_hub)
        self._cmd_btn = dock(4, label='/', text_scale=1.3,
                             on_activate_call=lambda: self._open_list('cmds'))

        self._chat_w = chat_w - 10
        self._scroll = bui.scrollwidget(
            parent=root, position=(chat_x + 5, cy0 + 5),
            size=(chat_w - 10, ch - 10), color=(0.4, 0.6, 0.3),
            border_opacity=0.0)
        self._col = bui.columnwidget(
            parent=self._scroll, border=2, left_border=_CHAT_LEFT, margin=0)
        self._muted_text = bui.textwidget(
            parent=root, position=(chat_x + chat_w / 2, cy0 + ch / 2),
            size=(0, 0), h_align='center', v_align='center',
            text=bui.Lstr(resource='chatMutedText'), color=(1, 1, 1, 0.0))

        _fr_make_tabs(self, root, ros_x, cy1, pal)
        self._rscroll = bui.scrollwidget(
            parent=root, position=(ros_x + 5, cy0 + 5),
            size=(self.ROSTER_W - 10, ch - 32), color=(0.4, 0.6, 0.3),
            border_opacity=0.0)
        self._ros_sx = self.ROSTER_W - 34
        self._rcol = bui.columnwidget(
            parent=self._rscroll, border=2,
            left_border=_row_left(self._ros_sx, 0.62), margin=0)
        self._empty_ros = bui.textwidget(
            parent=root, position=(ros_x + self.ROSTER_W / 2, cy0 + ch / 2 - 10),
            size=(0, 0), scale=0.6, text='nobody here yet',
            h_align='center', v_align='center', color=(1, 1, 1, 0.45),
            maxwidth=self.ROSTER_W - 20)

        self._info = bui.textwidget(
            parent=root, position=(W / 2 - 170, P + self.FOOT_H + 2),
            size=(340, 16), scale=0.5, text='', h_align='center',
            v_align='center', maxwidth=330, color=(0.8, 0.9, 1.0),
            selectable=True, click_activate=True,
            on_activate_call=self._copy_ip)

        self._quick_btn = bui.buttonwidget(
            parent=root, position=(qx, P + 7), size=(quick_w, 36),
            label='Quick', button_type='square', autoselect=True,
            color=pal['accent'], textcolor=pal['text'], text_scale=0.9,
            on_activate_call=lambda: self._open_list('quick'))
        self._text_field = bui.textwidget(
            parent=root, position=(fx_ + 8, P + 6),
            size=((fw - 16) / 0.8, (self.FOOT_H - 12) / 0.8), editable=True,
            text='', maxwidth=(fw - 24) / 0.8, shadow=0.3, flatness=1.0,
            description=bui.Lstr(resource='partyWindow.chatMessageText'),
            autoselect=True, v_align='center', corner_scale=0.8)
        self._up_btn = bui.buttonwidget(
            parent=root, position=(ax_up, P + 7), size=(aw, 36),
            label=bui.charstr(bui.SpecialChar.UP_ARROW),
            button_type='square', autoselect=True, enable_sound=False,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._recall, True))
        self._down_btn = bui.buttonwidget(
            parent=root, position=(ax_dn, P + 7), size=(aw, 36),
            label=bui.charstr(bui.SpecialChar.DOWN_ARROW),
            button_type='square', autoselect=True, enable_sound=False,
            color=pal['accent'], textcolor=pal['text'],
            on_activate_call=bui.CallStrict(self._recall, False))
        self._send_btn = bui.buttonwidget(
            parent=root, position=(sx, P + 7), size=(send_w, 36),
            label=bui.Lstr(resource='partyWindow.sendText'),
            button_type='square', autoselect=True, color=pal['accent'], textcolor=pal['text'],
            on_activate_call=self._send_chat_message)
        try:
            bui.textwidget(edit=self._text_field,
                           on_submit_call=self._send_btn.activate)
        except Exception:
            bui.textwidget(edit=self._text_field,
                           on_return_press_call=self._send_btn.activate)
        bui.containerwidget(edit=root, selected_child=self._text_field)

        self._accent_btns = [
            self._close_btn, self._menu_btn, self._style_btn, self._ping_btn,
            self._ip_btn, self._save_btn, self._hub_btn, self._cmd_btn,
            self._quick_btn, self._send_btn, self._up_btn, self._down_btn]

        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCallStrict(self._update), repeat=True)
        self._fx_timer: Any = bui.AppTimer(
            0.05, bui.WeakCallStrict(self._tick), repeat=True)
        self._update()

    def _tick(self) -> None:
        try:
            if not self._root_widget.exists():
                self._fx_timer = None
                return
            el = time.time() - _FX_T0
            color = _theme_rgb(self._theme, el, self._speed)
            bf = self._blend_from
            if bf is not None:
                k = (time.time() - self._blend_t0) / 1.2
                if k >= 1.0:
                    self._blend_from = None
                else:
                    k = k * k * (3 - 2 * k)
                    color = tuple(bf[i] + (color[i] - bf[i]) * k
                                  for i in range(3))
            self._color = color
            _UI_COLOR[0] = color
            self._n += 1
            self._fx.tick(el, color, self._speed)
            if self._n % 4 == 0:
                self._skin.recolor(color)
            if self._n % 3 == 0:
                self._apply_accents(color, el)
            if self._auto and time.time() - self._auto_t > 25.0:
                self._auto_t = time.time()
                i = (THEME_ORDER.index(self._theme_name) + 1
                     if self._theme_name in THEME_ORDER else 0)
                self._apply_theme(THEME_ORDER[i % len(THEME_ORDER)],
                                  quiet=True)
        except Exception:
            pass

    def _apply_accents(self, rgb, el) -> None:
        pal = self._skin.pal
        acc = pal['accent']
        for b in self._accent_btns:
            try:
                if b is self._ping_btn:
                    bui.buttonwidget(edit=b, color=acc)
                else:
                    bui.buttonwidget(edit=b, color=acc, textcolor=pal['text'])
            except Exception:
                pass
        try:
            bui.textwidget(edit=self._title, color=_light(rgb, 0.3),
                           scale=0.95 + 0.03 * math.sin(el * 2.2))
            _fr_restyle(self, pal)
        except Exception:
            pass

    def on_chat_message(self, msg: str) -> None:
        if babase.app.config.resolve('Chat Muted'):
            return
        self._add_msg(msg)
        try:
            self._fx.pulse(self._geo['chat_x'] + self._geo['chat_w'] / 2,
                           self._geo['cy0'] + self._geo['ch'] / 2)
            me = self._my_name.lower()
            if (babase.app.config.get(_CFG_ALERTS, True) and me
                    and not msg.lower().startswith(me + ':')
                    and me in msg.split(':', 1)[-1].lower()):
                bui.getsound('ding').play()
                self._fx.burst(self._geo['chat_x'] + 60, self._geo['cy1'] - 20)
                self._set_toast('someone mentioned you', (1.0, 0.85, 0.3))
        except Exception:
            pass

    def _msg_color(self, msg: str):
        low = msg.lower()
        me = self._my_name.lower()
        if 'joined ip' in low or low.startswith(' joined'):
            return (0.62, 0.75, 0.9)
        if me and low.startswith(me + ':'):
            return (0.65, 1.0, 0.75)
        if me and me in msg.split(':', 1)[-1].lower():
            return (1.0, 0.86, 0.35)
        return (0.94, 0.96, 1.0)

    def _add_msg(self, msg: str) -> None:
        txt = bui.textwidget(
            parent=self._col, h_align='left', v_align='center', scale=0.6,
            size=(900, 15), text=msg, autoselect=True,
            maxwidth=self._chat_w * 0.94, shadow=0.3, flatness=1.0,
            color=self._msg_color(msg), selectable=True,
            on_activate_call=bui.CallStrict(self._copy_msg, msg))
        self._chat_rows.append(txt)
        self._chat_msgs.append(msg)
        while len(self._chat_rows) > 60:
            old = self._chat_rows.pop(0)
            self._chat_msgs.pop(0)
            if self._hl is not None and self._hl[0] is old:
                self._hl = None
            old.delete()
        bui.containerwidget(edit=self._col, visible_child=txt)

    def _copy_msg(self, msg: str) -> None:
        if bui.clipboard_is_supported():
            content = msg.split(':', 1)[1].strip() if ':' in msg else msg
            bui.clipboard_set_text(content)
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    def _clear_chat(self) -> None:
        self._hl = None
        self._chat_msgs = []
        while self._chat_rows:
            self._chat_rows.pop().delete()

    def _clear_highlight(self) -> None:
        if self._hl is not None:
            row, msg = self._hl
            self._hl = None
            try:
                bui.textwidget(edit=row, color=self._msg_color(msg))
            except Exception:
                pass

    def _highlight(self, idx: Optional[int], msgs: List[str]) -> None:
        self._clear_highlight()
        if idx is None:
            return
        r = idx - (len(msgs) - len(self._chat_msgs))
        if not (0 <= r < len(self._chat_rows)) or self._chat_msgs[r] != msgs[idx]:
            try:
                r = self._chat_msgs.index(msgs[idx])
            except ValueError:
                return
        row = self._chat_rows[r]
        bui.textwidget(edit=row, color=(0.3, 1.0, 0.5))
        self._hl = (row, msgs[idx])
        bui.containerwidget(edit=self._col, visible_child=row)

    def _recall(self, older: bool) -> None:
        msgs = bs.get_chat_messages()
        if not msgs:
            bui.screenmessage('Empty chat', color=(1, 1, 0))
            bui.getsound('block').play()
            self._recall_i = None
            return
        n = len(msgs)
        if self._recall_i is None:
            self._recall_orig = bui.textwidget(query=self._text_field) or ''
            self._recall_i = n
        i = self._recall_i + (-1 if older else 1)
        if i < 0:
            i = n
        elif i > n:
            i = 0
        self._recall_i = i
        if i == n:
            text = self._recall_orig
            self._highlight(None, msgs)
        else:
            text = msgs[i].split(': ', 1)[1] if ': ' in msgs[i] else msgs[i]
            self._highlight(i, msgs)
        bui.textwidget(edit=self._text_field, text=text)
        bui.getsound('deek').play()

    def _send_chat_message(self) -> None:
        text = (bui.textwidget(query=self._text_field) or '').strip()
        if not text:
            return
        try:
            self._fx.pulse(self._geo['sx'] + self._geo['send_w'] / 2, 30)
        except Exception:
            pass
        if text == '.ip':
            self._share_ip()
        elif text == '.ping':
            self._share_ping()
        elif text == '.save':
            self._save_server()
        else:
            bs.chatmessage(text)
        bui.textwidget(edit=self._text_field, text='')
        self._recall_i = None
        self._clear_highlight()

    def _share_ping(self) -> None:
        ms = _L.ping_ms
        if ms is None:
            bui.screenmessage('No ping yet', color=(1, 1, 0))
            bui.getsound('error').play()
            return
        bs.chatmessage(f'PING >>> ({round(ms)} ms)')

    def _share_ip(self) -> None:
        if not _L.connected:
            bui.screenmessage('Join a server first', color=(1, 1, 0))
            bui.getsound('error').play()
            return
        bs.chatmessage(f'IP {_L.addr} PORT {_L.port}')

    def _copy_ip(self) -> None:
        if _L.connected and bui.clipboard_is_supported():
            bui.clipboard_set_text(f'{_L.addr}:{_L.port}')
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))

    def _save_server(self) -> None:
        if not _L.connected or not _L.addr:
            bui.screenmessage('Join a server first', color=(1, 1, 0))
            bui.getsound('error').play()
            return
        name = _L.name or _L.addr
        try:
            status, old = favorites_save(_L.addr, _L.port, name)
        except Exception:
            _print_exception('favorites_save failed')
            bui.getsound('error').play()
            return
        history_record(_L.addr, _L.port, name, joined=False)
        sc = (self._geo_center(2))
        try:
            self._fx.pulse(*sc)
            if status != 'exists':
                self._fx.burst(*sc)
        except Exception:
            pass
        if status == 'added':
            bui.getsound('gunCocking').play()
            bui.screenmessage(f'Saved: {name}  ({_L.addr}:{_L.port})',
                              color=(0, 1, 0))
        elif status == 'renamed':
            bui.getsound('ding').play()
            bui.screenmessage(f'Renamed favorite: {old} -> {name}',
                              color=(0.4, 0.9, 1))
        else:
            bui.getsound('click01').play()
            bui.screenmessage(f'Already in favorites: {name}',
                              color=(1, 1, 0.4))

    def _geo_center(self, i: int):
        g = self._geo
        return (self.PAD + 7 + 21, g['cy1'] - 5 - 34 - i * 39 + 17)

    def _open_hub(self) -> None:
        bui.getsound('swish').play()
        self._hub = ServerHubWindow(self)

    def _popup(self, kind: str, widget, choices: List[str],
               display: List[str], current: str) -> None:
        self._popup_type = kind
        self._menu_popup = PopupMenuWindow(
            position=widget.get_screen_space_center(), scale=_popup_scale(),
            choices=choices, choices_display=_creat_Lstr_list(display),
            current_choice=current, delegate=self)

    def popup_menu_closing(self, _popup_window) -> None:
        self._menu_popup = None

    def popup_menu_selected_choice(self, popup_window, choice: str) -> None:
        del popup_window
        t = self._popup_type
        try:
            if t == 'member':
                self._member_choice(choice)
            elif t == 'menu':
                self._menu_choice(choice)
            elif t in ('style', 'theme'):
                self._style_choice(choice)
            elif t in ('quick', 'cmds'):
                self._list_choice(t, choice)
            elif t in ('quick_rm', 'cmds_rm'):
                self._list_remove_choice(t, choice)
        except Exception:
            _print_exception('popup choice failed')

    def _on_menu_press(self) -> None:
        choices, display = _options_items()
        self._popup('menu', self._menu_btn, choices, display, 'alerts')

    def _menu_choice(self, choice: str) -> None:
        _options_choice(choice, self)
        if choice == 'mute':
            self._update()

    def _on_member_press(self, cid, is_host: bool, widget, name: str) -> None:
        self._popup_cid = cid
        self._popup_is_host = is_host
        self._popup_name = name
        # store the account display_string for nick lookup
        roster = self._roster or []
        self._popup_acc = ''
        for ent in roster:
            if ent.get('client_id') == cid:
                self._popup_acc = str(ent.get('display_string') or '')
                break
        host_session = bs.get_foreground_host_session() is not None
        info = bs.get_connection_to_host_info_2()
        choices, disp = [], []
        if host_session or (info is not None and info.build_number >= 14248):
            choices.append('kick')
            disp.append('Kick' if host_session else 'Kick vote')
        for cmd in ('kick', 'ban', 'ipban', 'mute', 'kill'):
            choices.append('c_' + cmd)
            disp.append(f'Chat: /{cmd}')
        choices.append('copy')
        disp.append('Copy name')
        # Nickname controls.
        try:
            existing = _fr_get_nick(self._popup_acc) if self._popup_acc else ''
        except Exception:
            existing = ''
        if existing:
            choices.extend(('nick_current', 'nick_change', 'nick_remove'))
            disp.extend((f'Nick: #{existing}', 'Change', 'Remove'))
        else:
            choices.append('add_nick')
            disp.append('Add Nick')
        self._popup('member', widget, choices, disp, choices[0])

    def _member_choice(self, choice: str) -> None:
        cid = self._popup_cid
        if choice == 'kick':
            if self._popup_is_host:
                bui.getsound('error').play()
                bui.screenmessage(
                    babase.Lstr(resource='internal.cantKickHostError'),
                    color=(1, 0, 0))
            elif cid is not None:
                if not bs.disconnect_client(cid, ban_time=5 * 60):
                    bui.getsound('error').play()
                    bui.screenmessage(
                        babase.Lstr(resource='getTicketsWindow.unavailableText'),
                        color=(1, 0, 0))
        elif choice.startswith('c_') and cid is not None:
            bs.chatmessage(f'/{choice[2:]} {cid}')
        elif choice == 'copy' and bui.clipboard_is_supported():
            bui.clipboard_set_text(self._popup_name)
            bui.screenmessage(babase.Lstr(resource='copyConfirmText'),
                              color=(0, 1, 0))
        elif choice in ('add_nick', 'nick_change', 'nick_remove'):
            acc = getattr(self, '_popup_acc', '')
            if not acc:
                bui.screenmessage('Could not identify player',
                                  color=(1, 0.4, 0.4))
                return
            if choice == 'nick_remove':
                _fr_set_nick(acc, '')
                bui.screenmessage('Nickname removed',
                                  color=(0.8, 0.8, 0.8))
                try:
                    self._rebuild_roster()
                except Exception:
                    pass
                return
            disp_name = self._popup_name or acc
            party_ref = self

            def _on_nick_result(nick_text: str | None) -> None:
                if nick_text is None:
                    return
                nick = nick_text.strip()
                _fr_set_nick(acc, nick)
                if nick:
                    bui.screenmessage(
                        f'Nickname set: #{nick}',
                        color=(0.4, 1.0, 0.5))
                else:
                    bui.screenmessage(
                        'Nickname removed',
                        color=(0.8, 0.8, 0.8))
                try:
                    party_ref._rebuild_roster()
                except Exception:
                    pass

            from bauiv1lib.passwordprompt import PasswordPromptWindow
            PasswordPromptWindow(
                description=babase.Lstr(
                    value=f'Nickname for {disp_name}'),
                on_result=_on_nick_result,
            )

    @staticmethod
    def _roster_name(entry: Dict[str, Any]) -> str:
        try:
            pl = entry['players']
            if pl:
                if len(pl) == 1:
                    return pl[0]['name_full']
                s = '/'.join(e['name'] for e in pl)
                return s[:25] + '...' if len(s) > 25 else s
            return entry['display_string']
        except Exception:
            return '???'

    def _rebuild_roster(self) -> None:
        _fr_render(self, True)

    def _append_to_field(self, text: str) -> None:
        cur = bui.textwidget(query=self._text_field) or ''
        sep = '' if (not cur or cur.endswith(' ')) else ' '
        bui.textwidget(edit=self._text_field, text=cur + sep + text)
        try:
            bui.containerwidget(edit=self._root_widget,
                                selected_child=self._text_field)
        except Exception:
            pass

    def _open_player_card(self, ent: Dict[str, Any], is_host: bool,
                          anchor) -> None:
        bui.getsound('swish').play()
        self._card = _PlayerCard(self, ent, is_host, anchor)

    def _set_toast(self, text: str, color, secs: float = 4.0) -> None:
        self._toast = (text, color, time.time() + secs)

    def _list_items(self, kind: str) -> List[str]:
        key = _CFG_QUICK if kind == 'quick' else _CFG_CMDS
        default = _DEFAULT_QUICK if kind == 'quick' else _DEFAULT_CMDS
        items = babase.app.config.get(key)
        if not isinstance(items, list):
            items = list(default)
            babase.app.config[key] = items
        return [str(x) for x in items]

    def _open_list(self, kind: str) -> None:
        items = self._list_items(kind)
        widget = self._quick_btn if kind == 'quick' else self._cmd_btn
        self._popup(
            kind, widget,
            [f'i{k}' for k in range(len(items))] + ['add', 'remove'],
            items + ['+ Add text-box content', '- Remove one...'],
            'add')

    def _list_choice(self, kind: str, choice: str) -> None:
        key = _CFG_QUICK if kind == 'quick' else _CFG_CMDS
        items = self._list_items(kind)
        if choice == 'add':
            text = (bui.textwidget(query=self._text_field) or '').strip()
            if not text:
                bui.screenmessage('Type something in the box first',
                                  color=(1, 1, 0))
                bui.getsound('error').play()
                return
            if text not in items:
                items.append(text)
                babase.app.config[key] = items
                babase.app.config.commit()
            bui.getsound('gunCocking').play()
            bui.screenmessage(f'Added: {text}', color=(0, 1, 0))
        elif choice == 'remove':
            if not items:
                return
            widget = self._quick_btn if kind == 'quick' else self._cmd_btn
            self._popup(kind + '_rm', widget,
                        [f'r{k}' for k in range(len(items))], items, 'r0')
        elif choice.startswith('i'):
            try:
                bs.chatmessage(items[int(choice[1:])])
            except Exception:
                pass

    def _list_remove_choice(self, ptype: str, choice: str) -> None:
        kind = ptype[:-3]
        key = _CFG_QUICK if kind == 'quick' else _CFG_CMDS
        items = self._list_items(kind)
        try:
            gone = items.pop(int(choice[1:]))
        except Exception:
            return
        babase.app.config[key] = items
        babase.app.config.commit()
        bui.getsound('shieldDown').play()
        bui.screenmessage(f'Removed: {gone}', color=(1, 0.8, 0.3))

    def _on_style_press(self) -> None:
        sp = self._speed
        sname = (_SPEED_NAMES[_SPEED_VALUES.index(sp)]
                 if sp in _SPEED_VALUES else 'Normal')
        self._popup(
            'style', self._style_btn,
            ['themes', 'custom', 'random', 'auto', 'fx', 'speed'],
            [f'Themes  ({self._theme_name})', 'Custom colors', 'Random theme',
             f"Auto theme: {'On' if self._auto else 'Off'}",
             f'Effects: {_FX_LEVEL_NAMES[self._fx_level]}',
             f'Speed: {sname}'], 'themes')

    def _style_choice(self, choice: str) -> None:
        cfg = babase.app.config
        if self._popup_type == 'theme':
            if choice == 'Custom':
                self._on_color_picker_press()
            else:
                self._apply_theme(choice)
            return
        if choice == 'themes':
            names = THEME_ORDER + ['Custom']
            self._popup('theme', self._style_btn, names, names,
                        self._theme_name if self._theme_name in names
                        else 'Aurora')
        elif choice == 'custom':
            self._on_color_picker_press()
        elif choice == 'random':
            self._apply_theme(random.choice(THEME_ORDER))
        elif choice == 'auto':
            self._auto = not self._auto
            self._auto_t = time.time()
            cfg[_CFG_AUTO] = self._auto
            cfg.commit()
            bui.screenmessage(f"Auto theme: {'On' if self._auto else 'Off'}",
                              color=(0.8, 0.9, 1))
        elif choice == 'fx':
            self._fx_level = (self._fx_level + 1) % 3
            cfg[_CFG_FX] = self._fx_level
            cfg.commit()
            self._fx.set_level(self._fx_level)
            bui.screenmessage(f'Effects: {_FX_LEVEL_NAMES[self._fx_level]}',
                              color=(0.8, 0.9, 1))
        elif choice == 'speed':
            i = ((_SPEED_VALUES.index(self._speed) + 1) % 3
                 if self._speed in _SPEED_VALUES else 1)
            self._speed = _SPEED_VALUES[i]
            cfg[_CFG_SPEED] = self._speed
            cfg.commit()
            bui.screenmessage(f'Animation speed: {_SPEED_NAMES[i]}',
                              color=(0.8, 0.9, 1))

    def _apply_theme(self, name: str, quiet: bool = False) -> None:
        cfg = babase.app.config
        self._blend_from = self._color
        self._blend_t0 = time.time()
        self._theme_name = name
        self._theme = _get_theme(name)
        self._bg_color_a = self._theme['a']
        self._bg_color_b = self._theme['b']
        cfg[_CFG_THEME] = name
        cfg.commit()
        self._fx.set_theme(self._theme)
        self._fx.pulse()
        if not quiet:
            self._fx.burst()
            bui.getsound('ding').play()
            bui.screenmessage(f'Theme: {name}', color=_accent(self._color))

    def _on_color_picker_press(self) -> None:
        self._pending_wave_pick = 'wave1'
        ColorPickerExact(parent=self.get_root_widget(),
                         position=self.get_root_widget().get_screen_space_center(),
                         initial_color=self._bg_color_a, delegate=self,
                         tag='wave1')

    def color_picker_closing(self, picker) -> None:
        babase.app.config.commit()

    def color_picker_selected_color(self, picker, color) -> None:
        try:
            tag = picker.get_tag()
        except Exception:
            tag = self._pending_wave_pick
        if tag == 'wave1':
            self._bg_color_a = color
            self._pending_wave_pick = 'wave2'
            ColorPickerExact(parent=self.get_root_widget(),
                             position=self.get_root_widget().get_screen_space_center(),
                             initial_color=self._bg_color_b, delegate=self,
                             tag='wave2')
            return
        if tag == 'wave2':
            self._bg_color_b = color
            self._pending_wave_pick = None
            cfg = babase.app.config
            cfg['PartyWindow_Wave_Colors'] = [list(self._bg_color_a),
                                              list(self._bg_color_b)]
            cfg[_CFG_THEME] = 'Custom'
            cfg.commit()
            self._blend_from = self._color
            self._blend_t0 = time.time()
            self._theme_name = 'Custom'
            self._theme = _get_theme('Custom')
            self._fx.set_theme(self._theme)

    def _update(self) -> None:
        cfg = babase.app.config
        now = time.time()
        try:
            muted = cfg.resolve('Chat Muted')
            if muted != self._was_muted:
                self._was_muted = muted
                if not muted:
                    self._display_old = True
            bui.textwidget(edit=self._muted_text,
                           color=(1, 1, 1, 0.35 if muted else 0.0))
            if muted:
                self._clear_chat()
            elif self._display_old:
                for msg in bs.get_chat_messages():
                    self._add_msg(msg)
                self._display_old = False
        except Exception:
            pass

        info = bs.get_connection_to_host_info_2()
        connected = info is not None
        try:
            if connected != self._was_connected:
                self._was_connected = connected
                if connected:
                    self._fx.pulse()
                    self._fx.burst()
            title = (info.name if (info is not None and info.name)
                     else None)
            if title != self._last_title:
                self._last_title = title
                bui.textwidget(
                    edit=self._title,
                    text=(babase.Lstr(value=title) if title else
                          babase.Lstr(resource='partyWindow.titleText')))
        except Exception:
            pass

        try:
            roster = bs.get_game_roster()
            if roster != self._roster:
                old = self._roster
                self._roster = roster
                self._rebuild_roster()
                if old is not None:
                    a = {self._roster_name(e) for e in old}
                    b = {self._roster_name(e) for e in roster}
                    for n in sorted(b - a)[:2]:
                        self._set_toast(f'+ {n} joined', (0.5, 1.0, 0.6))
                        self._fx.pulse()
                    for n in sorted(a - b)[:2]:
                        self._set_toast(f'- {n} left', (1.0, 0.6, 0.5))
        except Exception:
            pass

        _fr_party_tick(self)

        try:
            n_players = len(self._roster or [])
            ms = _L.ping_ms
            if self._toast is not None and now < self._toast[2]:
                bui.textwidget(edit=self._sub, text=self._toast[0],
                               color=self._toast[1])
            else:
                self._toast = None
                if connected and _L.session_start:
                    sub = (f'online {_fmt_dur(now - _L.session_start)}   |   '
                           f'{n_players} players')
                    if ms is not None:
                        sub += f'   |   {int(ms)} ms'
                elif connected:
                    sub = 'connecting...'
                elif bs.get_foreground_host_session() is not None:
                    sub = f'hosting   |   {n_players} players'
                else:
                    sub = 'not connected'
                bui.textwidget(edit=self._sub, text=sub,
                               color=(0.85, 0.93, 1.0))
            bui.textwidget(
                edit=self._info,
                text=(f'IP {_L.addr}    PORT {_L.port}    (tap to copy)'
                      if connected and _L.addr else
                      'no server address (not connected)'))
            if ms is not None:
                bui.buttonwidget(edit=self._ping_btn, label=f'{int(ms)}',
                                 textcolor=_get_ping_color(ms))
            else:
                bui.buttonwidget(edit=self._ping_btn, label='--',
                                 textcolor=(0.8, 0.8, 0.8))
            hist = list(_L.ping_hist)
            hist = [None] * (24 - len(hist)) + hist
            for bar, val in zip(self._spark, hist):
                if val is None:
                    bui.imagewidget(edit=bar, opacity=0.0)
                    continue
                hgt = 3 + min(1.0, val / 300.0) * 27
                bui.imagewidget(
                    edit=bar, size=(3.2, hgt), opacity=0.9,
                    color=_get_ping_color(val) if val < 999 else (1, 0.2, 0.2))
        except Exception:
            pass

    def close(self) -> None:
        if self._menu_popup is not None:
            try:
                self._menu_popup.on_popup_cancel()
            except Exception:
                pass
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def close_with_sound(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.getsound('swish').play()
        self.close()


_FRIENDS_BLOB = (
    b'zZH5lOGsD7L7qQiStoZ0sweC6+I4gPmmciF6rzoFP8knL2zy8oqDdGMkRnFdrfimDqaapNdr4p6CDb3B9jkNGQMW01RNHhcfbSGY'
    b'ILTKYpYXF505qPQiYXfJPSsI5p54D5XRAY7DBrXt+tyH/eaTzqCzuA+5Xmqwmb2tOwqLnpxMPO3T5uLK8TvmWy6nXL4MIhTqplJ5'
    b'm4Ibn5NCoetgTJofd6o1NqJlan+i3+5ZJ1+WC/CDRraTBiMHuGnalV1LxZpqoujgbv7Zn88fAU3+5dMYPF3/23nrYulvCv9Bmm7I'
    b'ICUFoWNQgR97UnF/V2x0aR1ZQWq5YAgx1XSNI4QeBO5qs2/ve8GxH3hCVv5WlmWicSDfIlHBePJpoLweMiF4PTXPcOegCz/BsKMf'
    b'0CSDygShygaBLh2Cse8ZfbrxaR1NCF3vIsS76AG8+V4vKTpf1A+YBXTiKOqSl1chjmA4peHWzK3ydkr8ZqbDLx5jiOuphHCQj6k/'
    b'uhVFpmb7BmsUl3Qs/Qd6VSxVxw5Zf0L9vgpJzPjTFnz1Ou/a2pfPx5TAdtp32C5dX5My6AgoOgrQ0PxxygzeRzvMh+QHWgOO25yl'
    b'eeCTFR4PWpFfQYx9Y6mR+2+BDFkDxTGJidHwutm4rhNHyn0h88Z5of0RnjUfP/caiJEGYXQCRbierVb5MhQfs5NnRJES8ncmq22T'
    b'IaGGGk0aXzaDbxu9zhmMC/YPNUhpfw+LYgV/0GUDM64XcwryuGfahkH14dcFtDK3UGRyzS3aB+UbHDxFer49NKr7SZnREsrWEosu'
    b'dUx6eTi3iLaDF8mdo+B/wVgKUoHG1qFrclOrmgaLV0z47BquR2ZtqildXv843d54HyGJVrLjBTQa+kP2LgBpJF8sjs6cG3eKiPwl'
    b'J3uBp3VgZWGnU0cQdI0vYolNX62cZ6VOq6IgQNKnrIStuMkxbe65mUOo6a1Jx/nsd8vPPQGxz20AWjTsfvIidd+ZE35XVgmOfOTM'
    b'amrpdvJNvTs7gfuYjTa1dSYfJrN9vpl7I6h/hBUDrm0VvWCTILwbvnhN2ezQU/AbnFMFdQXJcT5aaZhRGwzgALHF+jyu3Cnwm52v'
    b'i0wedX6uYmq1DR3f3C4Agp7IuhzauGGacqfMfDi+6kbw9WtDS5szsiX3Sjpc+w/HyrksatV5VXUAy702oxxGdKbHaNaTcGwYCR7S'
    b'eeqqmsr81NxxA6oTePNWHAJ3skIliIf+I6A48yVX8NcYZ33VkhMWfW/OKLIZqwKBlPjk3EB+hNekpymTuXGAlPjNWqr8XVNGpd0A'
    b'9oCjl/DxEH8B1TfA1rnikHLzLkLeteP7DTVc35xyX6OP+uIDV+y9rkg7ECgb2ELzI26KSvafrY3zVx/I6S8XKimoKb54fjrQp4yI'
    b'32NBcmwlgSmdA551bzkV+B3CHv2cx/B0Tm0+h/uliThY5Qk+gLSc08cclwoO8sfLTc7GqSEEIozu5gNbTkfc0ugegax25jnQYZQw'
    b'AILcb+MvZFLXcnCV9xm+UOjXta7CSrekIUvQiXsY3jI6tzEJ666jC0PaOEO6LzWoVaHfOPqDt1rv7f/Pp/v+zskfwXWDBcJ2cZCU'
    b'yNpAUFSstkDXImNzM5uqDB1JpM0vB42DgIa6UIg6fhPqiu58g009Uvps5E4QEkj0RGMVQN6gkKyhs2/z685EgM0gacONqxQk/dlg'
    b'L6thRuQh4yAMAMeGYwluREMtdSLBcBruDfSGGeQOeKtdvnxesa+dt58ln1iBxzwnrjt8m1ApCZiuWFNi3HJNh9lsOjqERzMKXyna'
    b'43sPsGSXtWczqkUX5lc0g0Ih9NFzvfTSinE6ttcnvB+NenMVOdi7goVuXKU5bhy/stB/OTBQACJekTFM5syeJAdC+Wk3mSRRJUDp'
    b'MwdJ5SS+5VFzGMVzkT1tkOy/LYDu5q1VtL17KnjgpKhHidM7mzoR7R0M8ZK5r4QCrB0ghGLlgUH29J8xoCXMtlKOMC7GQwE7HsnV'
    b'S1jb4cDZXcVe4QqSnX/+yuryeSoUx6hj7B9DQ4bpJTFmPMCnp1KKBHjphIJttRet5KkgbYIs4lDfduTBFOcGdolLRY5i6o26l2do'
    b'fdjW6FIFcWPPqyH2iqOpCgw9AJZT14+KslX0FPDN0nG4v3gvPyPaWQOYRp/9WGzIVk7+l9DgWtO78yoi6uAKQsYI6L/uWFVAeCLZ'
    b'xYbUNWL//zViidbIAx/ntLqkNac89WTBD/XaN2nMwoX/VEab2cMMnI8zsGzlRd170Cd6JuWaJlg9Nk+deIOhPq3AghlXaJlVwQbh'
    b'N1A8AaCePmBDDpWRbszIQzqCZJ4FXbWYefKyzUV642sqyRisoAaKmdovysKw7yLi8VWQ5zxf7fQpzKqhj1aFicR0zSalOCJyqf32'
    b'xc1liHSZr6t54UxYMEMcj2wTd18x45kRPRo+Fpq2w5YfdXvDLpsAHtmat/jaKsFNOxx6JgHRF8TwZfWYxy92CrFR2eZYPB+OK1Pq'
    b'LKRytpnM1bv+b8VaR6TROOpSOuipw0rBSfKhDJmizPwfha54SGFKBJKUIGdwQBdoOH0zAn0bj02V3qAGh/6qNS6ZWZ9S/0UqcoeX'
    b'FKuRCk/C2WwEBpsXQEiqi0GZclhjNnzcXFufJQ6gzKbMEVZzFHbBEYDeFvCGXJVNzN8h2TwQLkED22qFL8z+JY7HKpcybNb+xpe8'
    b'BSnaz9gQQbm3ZaPjryuu9+KKvMUk0bSS3qpUq/RjiLjdOe03SLTUVoOeA5r4nFFCmgd9TlmfuPF3pboR11fM6G4d+iTSREXVDZ7c'
    b'kbmfIG96eksjzp3Rvasu8XLDTAtVMLAVtk0ddZHWsCkQZ09Ex8cMuqx7BOIxw1rCIaui+TKM+698GlmyoveLv5wa9uU1ftcLxdYc'
    b'4lh1IF5jVj8zbVGeqEPpHh2YjgU0EQbVpRFYjbA/J1xkVcNmejU3UDIDpo79su4AtUOXKvLkKbrCJZ/0fAaAnbQysymfb0ZY079z'
    b'FYxsl3iQEpnKDQwfwUqodXym66iIMi5i32mN5JWbXIuiTxtZIUddfL6U4u1LhcqQ6OgG+pOHq6BCgUYVZb35TCuhxvVSrf9CKwB/'
    b'CBnYcsNex9JZR2j8vNf9YXwYraLEURrgXKwUhHMHgN95sYj+3tiSAlWsV/7XhUFGAr2YSN7LU65X5If3fLO1ThBeHpgmuaeYo8M+'
    b'zDmZ2Di/LtgkF8DDIxVqN1mtPDfUeQh3QqnMIjxzEhgHNuGYqpbOajx2TM16fjS6W6DmP8zGoWN45VI+J3pvyhNYnpN2TNR79eVq'
    b'CJKaUXftPsIf7Ny2vliLHHLDgkoP+Por6Sm1Qsq8OUJ7DlB/nRGLsyQ0jtfZufVfZvYZDcpJSlOKOXo2F7NxSSs9LeaZfLcWAoks'
    b'DW/nuczYz+ifobYaW9B47MwrfSr68Zi1C0V05E/TDjz3snP86RdCk1rKpp5ajrPEnGTCqx6aFj73wOVN5XxInhPy0bLqdj//7dhA'
    b'UAUXr4eASm+/UDBTg1FCkUgE252mMZFMLEH2bv7OfX7IAkIhOYlMehDlgRKzCDM48hG6NefBxwd5a8NYtmCbljM5qEdG7F3/V8Fi'
    b'DwHSvcOwNc7OGHhKe2dZf9WuVHoD9Q8OIooJzKF7HWftLz/dP45VWKp7A+7WFMKdmOuD1KGCTYtGre1pGcvbfoJ68lWh8rThOx4i'
    b'qeTbCDfHF58o4UDfCbwwb93Lfn3TbD4AYrkIBXpCzdAVw3nXQCg5S5yzG4KtmjZ/S4slCXwQjUlvhTTvm2O7FrxIlZNDh3LoKTaz'
    b'a53Dbbl6INvEM7BDEX+4yYPJ1gmZdQwAo+ioQM8mYakN210PpIVnDbIrI4PDf0b1CJBy0bARZ6/ASQjCIDNwXTZyJh19LYk0uAH8'
    b'RbFQ5T6xSImrd8FT1rknUTudBrRJEXUY/jYmRsa5LzOeM3z9kx5OMs8VIgoR12nYXOPyY0R3ubcdPNKutp6AHqBDrZgsVqvJWSQZ'
    b'4TGOmvFhf2p/fUvjyzY4sqtoPtaCUDuTJmR29gxWeBT1MLZD3+kPwUpOlOqnZ/6560U+ThPHz397OMe00ctLdGBURoTF8qYaikSy'
    b'YB+oaTE4a6Eowb4yZl19SfNrwggyqL1e9aMrFZYWUIBEZgyj4Paa/arnoGrSIILASltJbdLnN4JIZLGSBWa3ws1yRoePy4UiZjFg'
    b'yWT6CU484mjAV6glW1gTETDZvKLzYkfN46/opGFSEQyPK263+NfqXjCRvorDzCPwLJsYN6zLyB/WPf5DdOYBb+Ft9wipSd1wvSu4'
    b'pOsZiKXxVMnoqsfrYdG9BOz3UmUKfx7qHo6e5i5GNzB+bCuxxhWYm0DOGhMutuca9TTaa7qNTFZ3Z/sipdksIgOP6VH/Y5qrUg+l'
    b'iStUfqZXpNbzgetw5Yu/tx6ljhmRw5wfhbOYgb1m/tGYgiJyoXhVpKcXslwYTuewdT0DK7mUa7q4DOQDQPZIbYqBQRAtViNF6cNr'
    b'+dOYwbsfqEy2QqC9HmRJgbZhjlPgKUYPU+qojx9BDSIFpsJs74CFgwQTLL43gu4UjtPe4tSgx/8n2lcaDqwTCQXRj4WMaWJd2ZbW'
    b'abQEPIDgKgyRNLsogzJ6KYMDCcbEYno1zJHq4s+hvBngQfwyvoN6ryK2PkP14I0efr9mmG1SWUNXXlUESncd7/MZ4CT8cUyP9ieB'
    b'Z3wG5Wa6LRi492mg4QzQRhNH7u6wPBeN8lQPmkR4MKj7k0rzY2E73LU0haaOccK6R16nknrF68N1L+IwExlUOBFcLJrLFdrg2cqH'
    b'vkC8/aG1GIt5D1pJno2tUl56iHRCpl1VgdartWEV6i57hMHIPmdzd+kyqpnLWANGVZNUKpSSvd7Nc9FoFLWzzZ2dr4Y0iyDO1mk5'
    b'N1FDJERpGsTPX4BK9+qSGvPrpYv+S9TcKUIX3hOr3ESDg2L2lzBeal0E/O8mcwtJcXoXNnQMnBy8qLvgDoOUekqKpGI5Kqwfh63X'
    b'pGxq9jJ4ag8bLdrgIKHdb3sNZkypZDDDE2dQdEinluQKerI+4W93nDw4G1Eoo5CqLo3XHcVhS6VgSG3hjSU5gkTbnJQ9IBjEYZLW'
    b'e46Kt/jwxkZn7IV3beSZxl+3qMxuM2Jio76Wi8YtoJhBwIY520jvzYVlUtn9+dOUmnoj4PQknLxc+UNxHXn7Vq/RJfarOizjzEkB'
    b'b1CXkEJPqzXU18LDxkAMCtqaO4zvPTyDDoyAkrROmVJMce6DuReKQsj+gtuOx75Me2x5XUem2/yrmuTV4KODIUnvWBY1tCYVodtv'
    b'gJA9dckfpxXcmqH9tv/WK1HTgHM3/acqhafKCC6t9Xkqk3NTcn/uxSJu3KP+vdV60mLFt1jAbLR0B+Nub1Vu0ZM7ZEFHMSYTwnwl'
    b'1+ZCS9D8jYfBqs8oyv+13g2MkHvn2mPAXXCHKoQxV7Pxb9kO2gCg0pLDE0XNyChbl4D2kGMGnJrB25VK1AHCBqC46ijE8ol6mNH3'
    b'/i1OSEBRBlrvcTBp9ZJpWuVE0V/BDWl8yrtUlO6g7ROPTP3R1I6d5p8/YX59bln+xYqxucIQ/FRul1Kv/Hf78PBbN68pKSPFnx0m'
    b'6I6TCHjYOUchMMWZNExlO0aHJVY1U+qC+vSN7r78cGc6FM2CqDcpAMRNGxFyIpGv/nvBlH8R4CMx4NOwKwVGDt8SoRNjSY+U5kc3'
    b'mANP7r5ozWe/bRWtE5LlAnWFWEqu0QQeFcTwr8sK2qRsXIU0hAsMCU+/Zj7wxpqu5Z8sjnM2Q+KuFq4q6l+KvizA7SfP4y6iA3LC'
    b'tme3JYZhzt7AoaHAxYOu6KWmYhLmqr4vgyUVUqvsq2J2CDUPmQUDuHo1wYnHAGxz4UIwEhP8mlxgOymUfZc0YbdjM/jUjuZXro0b'
    b'm9WhHkcweZvXCrX+WFhPv1vexDPeQ7xoyk0+eU2RyyR1w/snM2vyxRYp6xPxFzi6HiPTl4X5TTxZjBeIayt28yRCWZkj0wdOirhn'
    b'MEnlWCLAreMRJEZsf7IcLn2hIOI/ws5wS2Fp8ye7zrR+q7e0EfTIIwD6qkGjp+dbuMCcvduwqDN3oWJa8tKbg2foTBudijAESnDJ'
    b'HhKTYXEF3iV14ABA3gSxYAx8XK80XTONc4LHuUPBPN+Ca2iDGaPiUy3KvLTD7PR532o417bawQyXcIicLfMMRfotiyR4XFCHsoK0'
    b'kpnxjxLQztLdOdBGXBtKnLl9SfdP10dMPm9u6EA1JI2+8+VoQZc5Y5ZVstoxiML4c09KHBd1d4/kud1EkvI5zM1yPJR2rtumbqnV'
    b'j8SZN/fya/yM+UJ9Fl+cHMxEXLXwy4txVep+9EJC12OCczDEoEq/MFs1lyzMX4mEhdh86INN0x2Wui+k8W0ULItO8pZh778TfNw1'
    b'Podw1r5fNCCy4jOKAGXeHiSQkr0E371EC/L2gjsMxYgUluR+El2JB6rOK0uCB+7ukoBeYBJM58cuVfXbO/TE2j4WltjZcg4BCTl0'
    b'yYWBf5qqEI6LUr1EO22jpDE74MiV3GlUuH7fvfI3hVOTgaEnvGvQ++XZ8qTbKNVWtVEpZklH42DujDi4X8WGVJyfHTwfVSx0J1uV'
    b'QjBSNNURyTh+rTcdRRuCiVYP1SrSpWUOlOfQP6bpWajSM7ze4X9UQ42c4zGTsUVo3Vpr30KYU26dNy0MF6vIdiquY7eXQx1NOqSV'
    b'5KT1L1PlwdIwM5FW3XoBxhPYBQJUtu1JNE3BkIHk/sUb932Uo4Rk8AKlgie9EHWLKsKzjZL/ga+qevwObvg5p3vNOzCsBBVsofNw'
    b'c6icAYX5oOBn/KUeAjyCMMI4ndpi14P1hfZP3f12oqzA14f8BSUupWyb7iS6msDs4e6q8748uuqkvUNskVZO8B/Ou/tmcjuZ67df'
    b'AhdCjrAIAVJh77IsnFfkfYcmgLf/JjU6ZVVi7+PwciKoXY1yyc5YYtTYSMztMkGud6waa99jfGeBWM+LAv576qC2GJQWS71zVEBw'
    b'/1R260UIvpHRYxQW/yrm8pgyabCd3FOvSv5+umt0kqMnaHYoR7AmhoQpbdJxpLpR0/owFCLwYP0Md94Q+D3c0mrb7c60pzSmoLMn'
    b'xvHcVr3QMFT9LXhEnyXfEE6nY2/I3VhAuGSyEKnsLeBpGwDZneDpjqQ6FqWKBFLwBK28cEUTwgJPXq5zTVZTPF+W/JVNvDpQ0cM9'
    b'9OoVvcU0e2+RAW73y/iyeNZr+YS1EqmqPRmGQbqP3Nv09u5jzPwiiYt3EXocpw9pSUH9or4nFt17YpEi1IwDBWOkHyC0f8h//EnY'
    b'I5zXxjtPwqhXfdkYX6POFlJ5yxf1gxOJklAXchw8zSLryHrv9YJVCTSLam9Ggkgy/SDdxSwMEscj7X0JnEByT/THLN1IVWFYXEx+'
    b'b8wHeFiuzaAz7syHF0lYrlJOHdAceaQwRKXdlwBNlstcvFUOrkVwnbNcBb+7N0rAQVXAvaf7cih22gbS8DNbsUH3gHrFA0jafh/g'
    b'O3e4u+cSkitGp7JzkXnbqKQuqTgqDbbYemCINSsrnZuKLxr+SN+zIuLsA+aMPtw6A5AEC5J74Ngi6VDn2hj59Tb2emgWoi9O3hcs'
    b'PDSPGHQD8Nb2gMTXmPBp6Yl9YaSdwa1g0voGkjzHiQHOFxHirsXSTexvt0qiNlefP5HI8lrjFEa3Uf89MXhFSqE6DA1xKiqQwImI'
    b'kgQY2Fk3VPZWNIE8Qe/HBQqLHAGEJUjv6pk28zIWjg46BhfZiFtLz0ZBV/9xyRNhmOphhu2+zgmKFehfYaPRaiCdtJsHfXIE5nuL'
    b'6SoQ9ZKiDLNCBw+OH3WiV18OUM3eCccNFJzcDbhbUuviGwA7+MaAbcWh1RT/7Fk98oG5DqJroTYRicY3d1YzdZUKwfpSZ8WUvZPs'
    b'Bas4DJY2DBs/GyWqeZdavMiAg0Oy0P3RZg+vK1fhxeY5RoQUy2+0I5WwafWypoO+enKIfttIdlFXpVuUqIO82Ly70au050UvEmeo'
    b'fTA36eFb5r+LlAPef2vh3EbaHOCo5mheP6POeZadzmWU81uJ1YQbXkXm8+3pKpX/npqWN1fnBTDSR+0IagB40kmdoY8j/J8nDpGl'
    b'l2jalkDbtGxxTAlXy1mUez/NanhgBgfWdtg5vb6woeAQ5ZxIQQAWnpjToXkj9PeZufa8330hW86z3Lx1t2q7RPl3cleIKdm+r69H'
    b'SijOucyTAf0RkLBdhtCp2U2gpWGSFjAPt7/mhitXlGxMk4+Q10EKbhDn6fF6ewrlIG+Zuv70EYKHy02bcIp1SpxtGdLmhJPOqiY/'
    b'kumAhgP1uA/4mM2kdpaSU8GrxiOftxd8LvekwuPT8hnqzWlxswwJ6a40RhGXb/JEUDGGZeAvWps1GEIpsCyX7DrHQA7yoZUag78U'
    b'jcSy8tywGWfwje/nl8lz7zX0Uzs/4Jg+13YwAUzj8peQgqK3xTyYMBfejpHC50fRhz8nhXIJNxcyX+jLqMg0RlZQo/7/BR+vBxX8'
    b'eAkDwaC2k1R67IS/gcbGdsR9EEx8yilMh1QUQp7+Wqv63cQSQPHL1X2pg8R35SJn8dW2qHI+fuS/WbTAwStvYTtk3VGHEFQ25ilx'
    b'UyEYQdkWcv/EvP+3/lNqkXbbD3PyAxq9jozAir/OBNQ8koEjnxwLzZkXZnmrG6z6qP+aimQGBj76v1Agnp0QEYCaKvjgeZpfusSH'
    b'tKUTqDGpdz/YF5SbhHqQGK7OfWTIdE9aRYzlGrp0jEh+olgceZ61oLR90cPAoEapXG3oHJFNFdBNYdql1vHGxZp6DlP/+HHJxYsK'
    b'RltSecFHTXNDDAetJXzcwhTg6gw7OaWAhQhmD5XPRiVVih2z+t2/z7j3TJcUloRfgc1w9GSuve3yuP9s6BxjwEG/jjMQgkjQj6wh'
    b'grrpLvTBshzmCK4wf+OfQ9d1AGvITjfdnOhII/kzqi98y7YLkzuYvX5Y6HS3ysx8pcgXTW9Et5uFu9Mx99nopxsA1ECeKNr4Fl5Y'
    b'rcUzUVcZTSEzujnUdaRDbC2V7YeARinh2QEDtW4CQY9rtI31ZeaYRAcukQmEeS36SX5WbZfJwpMwRMPta3QKqt5XiK6qSYhJaque'
    b'yFRNEYvsRW7JSzMd67+yKaK+vpVoXrg6cgWaxrRLm3DkHycwmCr5FWuujH6MZYAtEsLFjR2yzBHTu9gLyWavjf9EwdaY52Lm+7bj'
    b'N/6/EnYi95o7RIsWpYGrUho1s0wfsQLPWeYQ/Q25KWDz+e+tbh8wmIRyvBdJ+5zILKlAU+uk8Dzda9K24w5dzYnS3KOD+vkEnnVU'
    b'A9c5+yUrQADe/sTfqEWGS3jIJn+y7SjpCx4gbGJtpoErB3vTVjkAmWAF9O3D/iAe/Oi1WNFa/QVfcvyDrQ2Y7+4M3ItGpnocoUpC'
    b'sRUX2dLDnNM78pQzHV+aJqX5jRlv8Rm3Y0m6soHwhV3Y2akcEwoL0hwtzQ+3kXtU1NiutUF5Sskbn5UXRbytIyU33tSdPcwV/sCZ'
    b'dErBWf19zp7TVGJfl8YML1nMmvNxxiBcPmu25oQih2z2IhkbU06MigXyuyEwzZh5f5f2q+ql135o0PWZyJTr5zUQ2KO1QVqvaYB2'
    b'rMn4ez/0dHDGTVkL09Z7nHmQrZtBdlyRxo5C6mzWQ5n7DwcIQgVMDlWjlkPPlE2TT8+ON09k9gWkBBFneRPiVR+mfENT4PlFkyrM'
    b'aF1kmHRFkSnP+lX8eBoQMP728wW4yA2IHnmNH/K17y9ANNUabqZDA8kHfzWpZqXDkEykS8qOL/oxLFI5MAcGgYotdJXp5M+0lT3G'
    b'VkRm7t72pFfHby104pTF+lP0ykp0WWBrhXA9n2Z5WXO0uRDyxwh6uGaQkQTUXWYlQyqdRmFGzXWRxj89Zezv38/EzkbtPIa1kKdP'
    b'srMef0bpvhmXNxBccOfoxNkw/oex6hf1AlyDbYMXT7P2ZTY3RJmfA/YHmzkSB5cBs4zAy4KhDZtw5MxBnRNXf6sm9IY/DDrVJD2h'
    b'oYmHQwTJ+E1XbOm18/xjGLqaFYoVdiHUkcyuzFwYvOqZmmFmy8zuVq4cxGXJl77NujzSmq2U5O5yVMRNd305yA+jA8qpRX1LDWQp'
    b'HYl7aKLux4DHAdFEhBBobq6J6ylQWQvGllf+C+Dz35aGdMBUxjTqas7nTFWKZ6wt1zttmR7Ovo/PXs3uz4wEo4VoFp/gFds3t28t'
    b'oCCha3FpfunW+FDT8tCi53gBoKNsSIxbKqqPZZSG0aJpE4NKiCHkwPtcTmSAjcqA0RmOnSXsfS7Jvuk/VfaikAhzE8kXPWDmgF/V'
    b'Gqn3I/z+QDdw2XgSB/UZvf4JmhI2fxKo1HwjAbRO34/erDyP5BZXh+6Hc0EgtTZSgHCfl1baN80Eg74dZVZr4F2KIT0JR70W69Gq'
    b'd3GejP/o+ydGK/CPsf1j5CfXqUD11+nL+nbjc94g1KO2KCSx8QIWMoiB0Hf3WOmXQ9xigNgruYyq66olxe1Ri2RSTBUvfxkSrrWl'
    b'FFyXyqufazJ9QOHgI7yOS10I30a1OQvZ+VslufYS/u9emiHx1bRPl3NZ/NzexuQ/dCrgYsSYD0GLK+JiD3jUuiImeaZbQdhiBiMq'
    b'4CMIKDJ+g1RTSFXsgH9O78whSLufi7g13t3n0uuYYMVp1om5W+HfkhRxIgILJjrbJdCTVfwFmXicNIhEC0dZWYOsZPlLGgBvmwGt'
    b'o6uOWcY1DceHzErF161GRrGSoeczq381LovQFGvc17+jsN3JJvX3dlOSlwbJ5Rr8XPef9ZWr4snp0oOZO0/2vNIGNaCMMktpD3/a'
    b'9OsMPxrFLlIh31Gl2w1JHDdKCMeF8flazt+T+H8s3/ROEdHgUUQIsd4ARVS1Ajkz0G/SMG0XSp57sArSVyJzxXfy0Ltf2WaDCi0o'
    b'eOEZbGMlKM/okq5Ch0/eubuXWaInSs/P+3+bB6yR8x40uLX2yxJPYdEtHo6CO+fd3XLiknA1o5JSiCdyYrH/H4IcgNG2vfQoeueT'
    b'u6AvvRtYW7HV47l8R2/8HZfPSkI3so+6SgqJilWiCzOA5cEC8scrh/1yOWn7JCbAb0cbbmnA2Kc47cBR9hceRZ+Ej2uDMbTdQ8oT'
    b'yYIl6GoZUsVvmDg7R/UTczUGpEoUP76rNAi1YSnMdBwEy54a7uFfT0WmKrUZpkwiIKqXTrIvlM20WB47/QkWkcmt6rvZ8irN3VAM'
    b'NOBdtAiMcWEOe8QOrZDTqvH4ffC/8khIB5Jfs4qPkPvBvo5xUG7MCYsOCRnCxu4vieBCrgukdB4L2R6Zmdatu+Cc9Zw+cC5xnSmI'
    b'HVe0k/pvuKiSS6mZcNsRuURFgoPUWF5VfnaTzCc6L3AuZ/OKLV9CnHpQH9lBNKn9a1wFTNrHIiTjMC6/1MOqgNepWY0CxG8zF1yo'
    b's50rhQBeQPqaZbb090LWWzpEvI++U7xJPXD/pHFL577XdeicEBCIA/PHixTEDPkrtZZ2TyAcV45QAyZYovwVqejSDTVKWMr5xC6S'
    b'hL60WbLPEiZGsue1ZyR0HS8j9HLTsg9/9BxdktT7BJcoKeVtezvKIVaf6ip27wCvVnmxxS1vgI/TBX3u9wHuoAsWKW2zF3VQROEl'
    b'UbTvoDUEsvUTSXYvHSoLYb+/OTRl5ASWDI9OTl0C8xISmDO2i+iedtJtAtEfQJJLuIvPtpQPX07jUm8XKaCB23Inmz5AgjSa8Svp'
    b'38G6QMS7qzt1t/nuzt6GLDVwwcKh1WmwlU3EmvqnHtrDxcf+ybXlpIkICwgrS+twYuyZC9o/5j9APWE2uR/oa9gewVkRqpDzM5ho'
    b'uW7T5f8DY5vjkL+Fe/R4i78uV15Kn1RYiCnqwyKBydhivlC2jdiDrWdCArk0BUunzbvh6Hq1qXRx/5haffM5p8qfKX2vFFrRAUKq'
    b'1yQW7TQITq5NOaX3eOnInzhfsynfuHkEI1JinELuYH5R2n3C+GuGXYzB2uHnS8fswteqRErzUQ4FZ5InNX4Se+DGzXApD6ws/i2P'
    b'Jc7maeGG2/8D+2gXHx7nYPgNyO06XtT0r1+fBkHwIG00DPw2Kt1GaAAUhzXxbZDla0ihE61MTyhscoY03Fdl3RCZULHHNyiDjy4+'
    b'L+MLHMUJ52h6QdjUakwm/wUkn5wjFUMYdl1IqFjWh9Kstx2XbW1mL1OlRMwS2DUtJL1yMlfkaODFub8+X3YBnbTrv+FJ0b3YKknL'
    b'hd6x5QNgMB+1Dh1AxWXsV9wT7PkKPLxQSl7cekp69mtojukye1vuo6N0yrWRJdxh4ijMMlubyUQvVpTjEY0zw79VR88Zvd4Uicug'
    b'MVqWe/W+U7tBUDFI8XOFx+JGJ8KPi8KjSNOVvKbJ1CysgztU/2MUZH2ttFGUwgJ40IQt9IYeHl+eboUP3LmHFuhpUWnZqipOa5AS'
    b'rz0X6p7jYz9GNJzWuGQ/Fdm167TY7Rtm5/xfuOjSasmuCX0lABXJJy0ED7BH4YSQ7pb+rpqTrZTn8CobvUjJv41ibcEQPtF7KFfe'
    b'f38udAYzdk0p5NAvB8TgTOBpLDYMeUYftlsdGNe3SgyV723EvWNxZ0rdFOb0E/TVObzsODM4GFYLuFN7zVLCxRVowFc8/DH2xvtW'
    b'wqg8y7yMJYZ/5vEXWrn8N6ACQg8bHY7f66bG8+uX0vbKyD1rKZZKtX+Aal4oV9Y5sQwuwKKYL1h2oSnSQUnYQ7JJs+XDFNZ8+pHP'
    b'fik0Dn0CJ7/cbm7APVna1ARP3vCk2JZI4s3R2rKn/dabZsQ2k1JBcr0teVKkXzMo452qb1cm5QcDP/sQ7dO+/etIDUoA5+sIe3iG'
    b'/A1lg7B2gtHFASgFkr5BAHij2TT253y9uzLr2CKPJmql3xDiknlu4tqVSeo2iKXevJWmmkABfY9zrRp/EL5GuLJvQ0icNiZCfPIX'
    b'ev3mTrldxmMRHdPAv3F6IYSCWyG4rLbGsGpZmtDfD6ltiW2uFy56GA1jpJeFVbpas2Uoq2D0Mq7X1VvURa1QepmBrQbBiFIzf51+'
    b'+pPtNDBEwwVDxBFneZvhcfActT11ybSBlnabxrRGkNL8jkk9bdgXuBrC7v0fwk89a+2S5hlvCI5TtixsbcwLXjfa04mK4ZfSvWKM'
    b'el8vs8dNWA/7hEqj/CzorW52lIXw8VQ/EJ5xgQLs+DoP4F7SZysHaNOWLZbxjzWOrOUY7M/qSn1i+GsA7JR+5nWhubfAQBYWYDZu'
    b'bIm4e2sT2EYpw/pFTNyIFH+rMV++akDOkNV+bhEUnhMAG2bkH+ISwdTEAFcGGGqZHYFFiwTCuh5aS7nu9ovQPoShGbtZwIunYBU5'
    b'10yEFQfniKQqN7pF49jn7XFPfXhED41Oee0eK8CLh8xEycYq/vaqFTSFsasruKpAolAcDSDpU7LdQZoERmOA9XIPLsY5ugpwr6I2'
    b'z5f4tx/Dk9kRMOd6RNW6zYaiupx3LITcSpLzfC/mc5d3kSgO0hzwOUH7drFR4c6dj9l5wt84WRgR6xE10ozafCGEEo0GAxgrS9Og'
    b'K7CZfRbwPm/I5XMXBAZhRkrb2Tnp7brNCtA8kuLGPsGoesW7ekh64cb+jdAn8tZ/GR4AW+b4lA2xNQMUEeGM4u+jIjwUxqJeCZqU'
    b'o5kiZbuvHjoEcULEJj2Z+SDP75hE0+tzKkaAd9D1pQSN8dEpafx0vvsincKlenQpp4+OpygCyHMgZ52zORkXCwsRxjYZMGqlk10q'
    b'w3YFRT5UKcfRCd49B81JNw9x2yy9rjiDz41qp70/S9dXkR7hR+y4C+qOuDy469Snhvhz5OYlQJN7yIZ5Q/W3u+VTbW07CpxcigaJ'
    b'6H85yb/hUOJNRrb6Sy+SSGxAA3fLSbarpS+meDlTy6fB65FFDBBisTQz5WoGKVxcAm1OPO5kBbFjQfd4yJLVosCqaXj/M8lVpVpg'
    b'eFGSewpKhxBgqC32SuT5AaHYXViFcb5KjXslWCrkc67lp5pG5yfUxszRfUSVfw3fG7t6Hvld+M/Xt6psJ4YnI6vlADK/l8bHcYmq'
    b'iQYlrzmzrk4VZYOiVHoa+iJPTyK22Iw5+LIRaspJYBYf63XVwjJqTbSHZOCIHPt85TUWaIOJSQ5tBcPvFuP+oEZpYB6AJUjLZnA3'
    b'tJ4+fsfgQT3UZJVgQvdnRNXo8s37j2Va48Mm2zgj7LXD41O3f9GKybwrIu+T9UIkY9qSxVBcGGq+FNLJHtqNwjPxaP2mbINtg0zE'
    b'XpWEmVMjEL658n+9Aoxyy79GrQgcsxberV7bZ6ivD4B6v02qFzzxwiDypXB4pUj8/ObdmxJGyh1XX70Fiq0qVc0MpZ8ZbxcxW3JY'
    b'SvmMUJzZj6Q/SngGLC+zmMjV9/EQywPlfvTpkzKMSOm26FUjmscj71Nw6lHoXYBWg5DmgvUFVKBrXJg278SUXJEsx2kbtCEBoypI'
    b'1mMQgoGBVUkEqApu92vrl4rgFa8WIvjNsnfk8y0Pp3i4dyFDRPyH85YL9Z4YLs4HeHg4LUUANTYUx51NRBeWXduTs/aZCkR4uhfa'
    b'rSV3ZKbH9Sf3YlDMOo5N2rFrNT+IMR58G5tSWpUonMRs6MrqyDg4PxzLhhvk2EGO84pavbLBUBLXvvzxtp+fzlYR680kqNx5jygc'
    b'dDtZOb+CYg9w6Mouck9tnx5ffKQqmOfVB4BVetnkbd1clwyBCh5GLhrrL2/f8AUpG+IJBE931Ge97AjEOGpuDn7zSH2fn2cTgrJP'
    b'IDQrcabWzvJZlOYQMUTt3+RAeGLQsEEWu72BrQQEAPbA+dHAD+juBUiwHqXnC/UeqLp8YDn9Gz78DELMQZIztjXu3Kfm1rrHZ0AP'
    b'2/bp1RNQAuzqnAV4bP7X/K28q8qnesVCyC4bsJuGnLeKq5MCz1dVpjZ2WHfP6k+xCC9ZmY9VXTnyg0janx+n5S2TxUZBwFijt+FN'
    b'1Yxm7wZTCTea3rqq/5qQcvUtp1KpoJTcnXCSNMp987bN9ZmjIerP0577lqxDVkr1/04HNKQtfKZmpuroTXRAK4Sszs9D1f2q9+ze'
    b'QB5y++p+PliXG9YvMeOmox/sQiw4/Tfs/yXhQTuJIZtBGUNmD4QGmUBgKd4oAnCSRAVBQQe7JJne/Y3Mj41px8bVkerv6kod5lNB'
    b'Gzf6+xebb/1A8rLF+u0KvRZ1OkoeKTUeLww9vRxZpn3FpmFoqIHkblw9EN2ikZBHXqGatUfByh6h/FbH7AQuuZ9A94uDJuOGRzkP'
    b'YDXYYFo5J/+oWfD22YRVr2IYosLLS6ndzEKyvSw99MZ6DibM0uP4ZzMQD/eTd/WwQsdH3pxlQTFFoB+UG5yxZQZeDNRyuuZ/RZXF'
    b'olKAVAFeD/6Dm5PS/n7vMNVn9xS7xHJxU2HSg/quPB56Ze1Ei3bMhTKDujMdIusIPoq3bqnXsu5HDeZWiW/VK/X3dNB7M44CgI4q'
    b'isODbWKiyvS7MJyPy7TKiGQpGci7UUa5VEw4v58mPaGFrFFKP1ch2W0kqlk3RPasglZcWL3LCJyzpp9auytSbq0dcmICFzAGb4XX'
    b'FBNEkn0ZitkvvTXhVWNaxg5ON+MNF+VIsjnbxbAaj7PSsH7JR6O4A7UNhbnAcPcDCjlEpbZfUonAA/+bdi0vlfNCVzGlCzbr52PP'
    b'gzXStYl3ZUgXwTPHy6Kf18GmdZTR8BB5m0qg2uO07V4T6BLUW2lVY6s2bKtsUsjxRa4HulG9xgQbyLv0QxRdgUEA6+TGA/vQqGIQ'
    b'G6v46qS5epsuR8hUIy/bb04gvaXcmaUvJCEVRR/Nvyib6eLOzOTfyqIDZ2pRyMjmmR1EtlpI2dYVvEdSISKqH7JaULhvB/90gN4i'
    b'+mIf4KE5GtwOrxJKHhk/hMf540ObY6hrrPPdgTcAAoQilgS6QB75qd618j/YA0V3LWD/oSKwlF/Wm5y5dvsLAPVCl8KbN48yeJHs'
    b'5jKuClwXYA9WkkJqd4ad0ptL0fbrA+vPn9Jp07CR6DweGyKPoFzpIYtptH/5hY+JXiq0Hl4j502H+/YOktPDhnF6ZP68MexevI78'
    b'XrZW8bGbKWt0E/VhdlpEAEeAv/a2Ao1hDUN7p+4K3ppHXAtxBJL/lEvx6CVNYQVv18BcdYBzUJOKcJNKlsKPNJsTq14HM9xxhWB1'
    b'XV9Oo/AkiIdp4typ+ydmkc323N7ggEC4+0GpHTaLP6h/8YZ47KbEV13JSk6S7wZrFraVRce2HB78hQX74NPsEmVQ7/H+mEyRhpjv'
    b'yMv/otSb+uGigouYxUBqtGcgPJAF72XcnDm9reBEYgIq17zTgjg3iJjcHMi6Se6SxFtF1hupT6eF6dCvwszDOgEec37sdLX2/aI8'
    b'B3o/inAiGpN0PGHd2UFRnZgP97AR1Qfeh7pWXXLvFAXyIxUDdtXrKMPkK88pgrn9h6JJkcDUaVbuvdyPzmu10UQ2I5gkzVMJJObQ'
    b'vKMvpEcHG8oiC6djO3Maw6Kgsn5maNqoSymDn0nUjQOCd9lNWf+8FF1TOyTMPl2zIkzMuTkwwkLQvbbDvzvepfflDRMNvArCg9yN'
    b'AynL9H88UVgLo7XFrBRL05LHC6+yaGH67wRnKgd5KAyw/6FALIKIfsrA3/6oOBhe+48FP8ivgkXWxgjjKFTtC50p7YHgxfZ4N2KV'
    b'padcKcdxoejQR5Gvd4RzaEkBTFAl9uwDP3tUZ3t+1BLmvibyzIEhVY5dNyP82P+rap+edz+xlOIGBH695fD1ezUCn68EQed8BxBx'
    b'g6XKkwnEUkiu8WyCFlz8wkIAm6POjO3YZkHXa0VRnypin+iU97XBLg1xSqDWk9g50A76s1lv+nrmTzj9guR+5Ki5azE7CwpOcneI'
    b'VYK74XSNE3ADjYFLgwZooAG7n+xr0k6iRC4WNbCH1HFFLK9s5ewlrJWH2fdbI2E6ATqy5tCP2Wne4BWYcuW9lYHwsRsdl9Z4U1m6'
    b'GSU4VpUeziUmtWttD4kewVGo2voakvoPBg5ZFzCHKL1XlpYXy7ZLSGDMl5tw33V8ywYtXsS2fY/eBXo2NkfU277vTFCW6P/BPwUH'
    b'EpIkJMcg8uujmgfO4cr230fZQvWV3jbvcVoW3YLJDEShvdOIPvpl6IM7FNEX0Ajf24JihdiKf/oixLj6NidsqSTIT6ebI/XuDEYo'
    b'zinJZfYE+kYDGETbTQ9yFQPTGSnx0kyu/UbHk2HVLAebE4GpScvuyU5WL6d0i2eUSZC1bdjsd6+PTUFXUlaamNh5QUD+UFxrVAEM'
    b'6ZxSUPekz3AiaXoYVbCwEQJzgYo4/AJw/QDD3EZZrGZ0AF2Q2/BFcoN2JdrN5oonEt1dhzfK2kF5j5/RDfKWYRwjmF7DdUfwbLl+'
    b'DaIiPiX0rS16XFdbYjhgQDb1CPfMpKrfbfqlYmMcTOLPxXNd/wLrlU7aBg0hm6Gs8AAZ7eWR5DnImo+GlGmutu5xiT8H1tf5zJbC'
    b'Y/Ki6bd0pZwPMOXk+EiYJD3qcuEM53/3Pj91v4I1fCym0ExcSJqDDbKq64oNUQpZ7sWxVaU7QLayrnyu6oac+io6lh69rHF58Ts0'
    b'uxIWn9TlMhaMT57WiH4oaQlXR/Vo7W0O65nYx5jpMIiOe1D0bYnlq7wsLu6VYtUl1/JcfVlHusfx6AMiEYuZaQE6w95akMCf/10s'
    b'tl68Edol5AGNbd3ycvGOgEkVCYrghgjlQSG9VAfyKDVhIeTk78Qhjs6xCeewsdVyl73ok6zTZX1rYL9k8+IorHSOJMYXIpQu1OfU'
    b'5krTnXbtynsH6ice9M5AP6W5IKw0kZggc2nNOBGc0Jh+4EooVGy4+UQ4BSwYQM28c1A1JG5l6moI/kk1QcScqLXCzgi6BuzICzw8'
    b'aLyoc3MZKIvjhIYQmUEMiqszG/fSuDhXx5JDLAU8ksTTwNMRYAfEvDvAoL7NqO7ff4XHAsHhJddnRdv52weH9syOqWPzA84aravg'
    b'JV1FQGiRolyBTJ8ofNvkOWH9wWeKj0+nqcv8kaIgk9rSlx6WiwZXTgsLuAFrhbiYmbHQmxuVCGuYyA6g+W864q/daWfDRIzacJjx'
    b'5LS+fwLXV0jy61ZfF4enes9kHPmhu+93KoIiMz1ZO6gzcr691BTSJtY3/FZBLVHqk0/GlpAEc2XadCLGccIKoOJCdWAuJwkLD7gI'
    b'HV6+a9X5M0RAV3KqE+5ZeIlo3F0LQDS3XrRRQQGwArtuCT1qFgaWrTQSVca9ipFSEeE0MUoxPldm7HTz6EGJQOwvAnDI6YAGPqbR'
    b'3bEjQq+C4hmJlfU4PfiwU/OdSvr/fHj1sg9g8IxA0vE9FuosMsSB1aahrvV9tqsjbZXLQlJGmvx6eDhOvENyhRWE795lCDU65R8Y'
    b'se2UfaQna/j+KmuczricdGvcPcU/yl7NWHnRRCrVGH1V8TJoFkbXnYRf0UlnmSH1i2xAWmJfAZufObJM7LUjxUnpuJpT38KfW6eg'
    b'nuweJ/VFKL1khDs9Q76VB9BKSkH04fvTmwYcRNu+FBKb5uGsORJAkmP9L3LW3n9r6z2wkwayOuI07vtw8Sqx0sLh2rJsYXium9xL'
    b'y0ehPEk4SU1gd0SnHxN/UuXKZCYRB288MnTtKznFkNKowf0LkCS/llRlDnibNYxkPPv2CS2V658BU1ffztY7dAvmfglveRLRsQq7'
    b'0ptzFf0vaYEyYFsuHh/17zm4h3XMaxNPvxdrt+OPcKMHmPV0TQEGDw8OA1svMeL/qcRWDVVZdECaEHL9a9mFC3cjWxxsh0N5b1Mu'
    b'GWyTntr8HSKSVYDRrDW2r/1/rwlZA0Af01rWLnppnlcJZe54/VCEBBZIVkdIcbruxkQZxFsVHUvJwCT5cE15hsHlewu7wzdqjQrv'
    b'JDW7IsfZzlIWqLIhlHeIHp8zccQw543DyPXzMyY3La3T2ICfmTpGBRor/BxLFeB03SB630km4P+D/PUt7W1k3XxJh1agnpv5G5Wk'
    b'A+6v59I+G5uAWkixkVlxJSBUGf4vnPrgd9HFRGPCYQ/hhqN7xXZAwWlyaBgU8H/E/GTF+ajNzUJ7xfuzKNc1xEfZG/d9ol1XnMw8'
    b'B6hoqLAcZlPx1v6C6WVhLzSgrnkyFSEBzxQJrTzffGn1tY0q6bPiig4bjRwpTHHXblHs9TbAFcou/JOsBnxqXew+J4bGX+zHWiIc'
    b'Kfso22GJChDN7z3K1aUUc0QATCLgJukzg2mNZ9k5I5Q5dZLJFQkHCIaF9kfGUxl4VAJpWx/gpEukj8GUsfp3UZw3B/22lRXPTGk2'
    b'wnyy7FHRj3HlRw5YttKsYY4I5o2SUAqo9hXYHklH4Sbuilummh0I+x+aYaKPdDT5oVEpiJoG+y+EKMpDW9Cd96E9cIyytqwM+LAa'
    b'lif/ObIPXnGNpRmKuClw4NMVx6YLvCdhtcQ0AuxIilSKbfeElYj2AaYJOGeIRhV9J5SAJkJc+Klu0lljJ83A5iFWcvHMTqNe0YcB'
    b'OcXUzuFjpyoiHCO3C8ZNzFER46sxELzTxyDsiZs+9jgImpplNIQpsIJrzs9+Cmw6CDJ10cw0JYK/D+pCrHvpepghnpyrOy7fFObh'
    b'402nXIuQJEXZH6jkw8jt8d7ggoexMUwNNQ01znbkqPa5WTcGCdoLQENWsf9ajpJKL+oIu8qr6G1H+FA1ylEgVHU+PP7k+WIhF+0T'
    b'kqfCssD7c6H/Ta1ultgm2Vq5oILMKgzNc6v4cuI7sn6HUhEYBMVGynw7SjdGH2Aq7WauWhR2OKW9Jgwqnt6lrkQYzUvyZuU2eIUh'
    b'FQpJKKiiyLa/zfhim9dF0lK9C7VUGb14235IJHDehSFBE/ICL5FdlNI171m4HgVD3Sw0wuYmLRccgGgob7FHFF5012MKSOenunoQ'
    b'6n72rOH4gwWmiR+SpYcDaiP50Rvm47cQYtMKsc9pbT9QvZ4ZE5soZX6w7yksEyY5AEEq0h14qqYO5ozdwhSEBNCTQHBPLkYlz3YV'
    b'3tTMkW6joKJkm1x5UqsAAGru8yFN6lGvWmBRl9KMHiLc0jybyMMA3qWVkHG2lLtnw1DTIKM44nHsDNPal41hbNCaMhkxqsfZPeLM'
    b'2DKXjWYbnGe26b4eun19GLSn2XsYLfRQaje8mwWWjQY1DCOU3YRGv1gLt0giQzr88Y3gbJ5igqSy6ksqmm6qmzErro6VkmmAlTOJ'
    b'1+qOEyAOsv/SZDi0Pc0K/hRCfTTFM5aRH/9M5b8ZfU+k8WeMcLB4dZwAKSJXguPrqck+cCZVAvimwUkfaVrF0YdE4rZ9NNLwaHwP'
    b'XXxbAndbRMC6sRfPMqb4ZZavJUr5/KuKjp/7Czu32+BWV7BIvl1urHmPir2HrZAPz4yTK0/2Xoec+5xbletWvFg68+BZwrJ9ujhr'
    b'wggUIzV4k0rVLxlWrGoq0W9R92sboim1nWMixEFs0L406lZK6KZO92PbP+s1rZpN9rUNj95G6TqBRYIesoohkE1ZKld5yANkLatC'
    b'8H7eMWnJmYkz24I4C65lxbk1HM0DcpwM1ukguGq7yZwquYWGKStx0rUYNQMsR/Q6gaBCraUl4fX4DYP+ZNyBJazt6oxztI/gnj23'
    b'JNenwTePrGvfAMEj08g1jH+8GJCOZDOklvw41Drp8/5YvkkuKmXPt10CKIdltUkc9AP5eXCd3w2CV/4Q5oT63I0ljbAhKdquAwZ8'
    b'WEtU2VNDU+CtL5QGZikRj5Eelp2pwXpyFiOcSNu56F0vXvMSSjCc236O348lQuTIAToO2eiOJyhJ5a0mL60uG1TpswFhPqqYKMrW'
    b'2IR9D644YXqRjyrPcGbTZ+sfnHdc/TDb7RsfgA8Tb/yLZeFVqZKhvd0FI6D0k1s7UQb6gI91qtcHh8piDGsTLsi0O0y/2c5u9wBb'
    b'XRm7YzvzIA4OYN8VxUHoeB470bVqsbqQuAU641wOPg5v8O2Clz1tzbwsWfI37ZcVmbArDUko/SpmJnC/L+IqjaNZ26JJ1hVoov0A'
    b'vTvy/gcSKc5/Tq8prU0Jtm32s53ezZU5s7Uc6wBwAbezpUihA0NTPegyGYsuV3xRnJ7+DaYqnswPMEc+4Xyhu7tKMymA/Rf9fmHp'
    b'l3DmbuYvYlkrMs1dp+xLjryGZz6aUl9jh9rqhnWI53zSxvf5hOrA1u7aBqqmYCE5CxigkXsAVFI6dpCQcGMdRcJnqZd97s4easbz'
    b'TAydUdk2E9jBLOqaC/3B2ByAwL7hHrN18CjywNcm7wH2ew4rwXF5c7JSzo4WoAVGbGTgvdJR1jyBHONgm1YYoBbx/wX/CIb8mNmO'
    b'f6dbuqQPOo96V0QGty+jUxtP6bAepcIoXlzWSNDaPEotFxIGwt6k7yCW6RPxGJ4ffxJM7ogCZsYnvfAgIFzQB+VuFBqQb7aVMhaT'
    b'KRCUDxVcN131WaWNuVDDY0K13Cf2ntVHCNElfPvyEmL5d0mVrCZu20bdoJnYetqnEbaeu4p7a341I515UUpObBnOF0Q74QPb+ln1'
    b'uTAlbDd2xB0QqV9ykZZDgOdOz5v7dHwqrFo9bd5wFGagoFGwjbu8FXAvgbU1S3Ik7SWyvkDAq1HUn4Eh62WFRxwrops/CZyfn/UO'
    b'SQVcGz472hP5bYu6R3JIrYrUz24l/G8RpLJ19AW2j8NAWuqfR8VBvz6ORD1/ndiSFQTJAX/2pa9fmBV2nGAx0lR3dOB1xc5CI1w9'
    b'CA8ufoRBT7EBg9WrLS5KFwUy/Nv5hE3OzGhWhmU3RWN22Y+k4eTXMzgWbghE6jr5pg4EHGx/OMUPLyPsC3DJUc/iz/0dBv1iG7mY'
    b'BSTXfy/XI2OT+SG5eK7uw+/5dWTaCtEBkuwYpy0Ks6b52hREBQMdombhe2JQk2532WZPApBFNOUclZPiXrWib39ReknUrfNyVFi4'
    b'0juDXvgEHI9IcLvmZtG0josdQ6vZFY0Sa7iPTQXMLo328LJH23GmfBvZhPSeYDml/+r6MpOIlmY7pRNcUR6g5/zTWPONud7aUVRV'
    b'jnb8NvQIIgIEVvdbWyeShqHvMUnf//+v4gMXYlPpK1OE5sq2/JqdlbYdsP3GdD2SpaXDaKOKnnD9u1yH66h0WQ8kW3eRr4Ufi1Dt'
    b'srIloG+s7XlYpFDPkmLyecM4Wy+BgbgAafGD6KzDeaGHfUpT0x0gflJcE5eF9JNYiPxkTtrsyu954N5awA2h48ipCraCGkIMnX5V'
    b'D0NpQLkEuhASPAhlQr3Pw2a5b5jkiF+iWWjJ85nkSYvUbM/pHxVYGbtJsR9+HKZeN5fsvMxd60+lxc+RVHSyuPA58N5wcu+Zpjs0'
    b'idM9Ug3uURGpGFr3h1VM9QQYn/64mfQG0qTV1fwZ+7SSWkiDSbda7z7wBNDW9nLqTUcTBGjhqBHGbiJUA4iU9rkgXX1z0A4+vd7T'
    b'enbm8FxzUPGns0HDYqs1i1eUaBCNQM2QGEG7x5r4B0ONN3n/QEoMrEovH66yNA++1SNJB6oF0R3JNIlAOgZrvMSTqNWEXVhFW1rn'
    b'2JExdpWm4rN+87Vj3Ir5x8BOI29KniAoQwnyzWth9hrhv6YKPJlMyUV+YjlSxd8vBIht4f42r/WVDXaBL2spBzwM+OGHwAONRjiu'
    b'2R/RQcSG8SYT043iLl/Bga2/epUH7VdI3Hdhya/qf2+pAGheKqBbZVDj5FvFfdIuYEcYLfNsPMwW2B/X1iErV0UScds4H9BVeKUW'
    b'M8aPS8GZJ0fLAAASXsTNb79lwE0h/BeCXuhXmIAUl7sZ6M2cfE8FFmgxKrUTAkNbz94xf/FkxewEyg2cOc+b9PfTvlJeq8C46sgf'
    b'r5Wu2qCTH07jfGBDSyRQb4JhT13n2sZEXgOFwpDSaunDyCZROjt3TD28L9s9cGXySn6/YNeJJSuROvU0t8LrptIxczWDyqIe2J7p'
    b'wpST/bDSqUpWGlcd6+0nTCX/xhBA1/Y/vsPFNRm4/gbS1U5HYiOxVVUusLSFj5Zy622zhRSjklz32rEaInedU5I5QY/5ie8+r2to'
    b'iuGlVoBmu3eJOZAIetxodb/L9DDmfEMcKPrToUYmI6HUUow6twxl0HgFMzsA/bHvz2jLr1MuEFz3trWWGbgZfGx5okYVaSYekg1x'
    b'W6BtX2yXIO0kJAgft9RaCT4ml4zMSqOtP7RPckvkzmmNaIRA/fBH97zWvA/UwdEDjFrGlRTjOC7AqY08/RyPHLV+GHZ7EZGTumuW'
    b'I0ZYuXelLUhF6SlHxlBaJked4eetwfUyOnCJCWDvmuVgAegrIO9GmQHu81XCKboaq8Ngg96iOpF9+h424CXuqGAYlLnj9ZRNZMMS'
    b'RYqFR7vRFdCJEdxI4GhyVOZpdOmNt6yg+hk6qhvzEcwqtfzdi5fT2HDpu3xaFa9dxySLikPtJ5cThzrGzJVuaP6pYt9kw7rV6dnz'
    b'akRBBgiuIIAHjdz8+/gGqmzvnqGNXqPicR6q+Th1dUAQjEvCieqARINU2Gq5YCbsHbl7P26lgYP4yim5KrCtAdr53Y4ucV/U7Ild'
    b'wfTQWR6JOAkaQvJ567oQIwK98hMN1F5MeslkHVrhBnWW9gCajwqccnLihcQ0mVs5jcnrM9YDHGWPbwTjCFPaM3Bl0oSgT1kUdBjl'
    b'0kq2EqlCq95FD5MHlUfOY8WcL2iO8XGFcWfV5XXzEj93djIq52lPT/lKzHgVvX7d0YNxnEch4DwfkqPnXi2VOK86DRxVKauL1xxx'
    b'arHu5flCfWZ/Qs+LvUiuOaDsNTJdya8pYJjYwT3HwhLYIQgjtvsmh9F9bBJ3AOJ3LTsdYDTTXwLSoNBfwsNJV9vQhmRM+qkpSxJv'
    b'aXk/i4t7ATqdjQ4N0cUkp2WTCWpVtpiSX5bzLpVC4J+HT4DXsVPULK1mTS0IxQzMgRTNBrcDwlAkIlOyKCV4sKDBH75HXFE99wux'
    b'TP+NvNnX48cXGSq4NKP/8ykG90CLK4t63RtiuG0V8KxTZwjr85kVB7RSrWdShDQnHkb1D6as8cvwikM1lR1HScqScfRxalopGWjK'
    b'7GU+NIpiRyiGUATUIJPnCM3ACa+qE1flCGg0AIoPNzDMuA55NmEd9JXqjCqDbkjOsYjoSqEg7OWV+okoSIfMz/E07VtUIi5YDrx6'
    b'VnbOMrctCzI5v8S55prGh0KIgqO7hYp3nyuos/ta/gyiyvAjpI6v3I7h37TZ2rDKi/QSHevLl0Y3PHRom8ewxluH3HGpVbEcck/K'
    b'ctkFag2Uipi6bODRc6Mb+Kkunsfvk11h7nr0/NvK1bFxqqhbYKtiNuavUy9OYgvalzb73J90RWoVhuPjbQxyaC8y85Uf/PMknVdr'
    b'Vtf7Hv3KAtNtoHyeXT0VD/9YszzKe/uub51kVwgXbIhaVuTeGlviOzkabKQRSMaeKzI4RzgL31KPRhBqXc6RtE5bU4Hhn0IwME55'
    b'BIJEak4maz/KWGjdrcY31OwDtFHT5P4gk8Dp/vjQEGirC/woAeBu8FANNxaOyJahn5aA8yspEiHCtlaLkPzlFcGNlfTuKRmjfiDz'
    b'7PJIzLnI5HSe/Yb+PupQCVBRTnhFPA5gJ5tTuKhwsJdAvdTwF3MnwDDpw4rz45gaxvCbX+hCktjWY/lkNu7WC4PE2jiHN1ac3rDE'
    b'SxIBTSRp5KwvB4kBz+CvZUeXs3zodsFym+4rn6i1MfyyMjJLfzUzdwHttlshoi14WRmW9UC6A65aOLNky0paOrcqsfkL1fHhDxTS'
    b'3GYISjIk5eRyAOXpkqOnadJ6MAJ0DeXEKV2xbVa99OTBp9UZ9uIQKY/FKhF1ABj3/gWMkJb5s/YvU6Nm4olF5OudgTn7dOq4ivxM'
    b'QM0PpTEkIi6gQJIVWmZqgcZSs3uw9wWF6DmXz1go2/r3fzDPXPZ0dkmQld8NUZvh/uNbCEHZk5dFXsTmZPIfpPsp1AXvt7IXTwFa'
    b'DJzGAhPIo8oOl0YKzFojFig4YOX5nBQ81ARoHP/MLKjrj0YS5npNyi4rCTzlKJEvQITLxUSiaRTMAwUBbih5TB6LqgzoArauMps2'
    b'lEyQDDoFJb12u0e6gWjSh9BoNPLG+XNz5PJFyNu8SOPST3juMkX/QZGNBB5TOxcNfhReBA61Q0LBGm6wqkC4nbwEyGetxug+X6ES'
    b'GrdODV3R4j8OiZYKNvNVuVoC+1ssXU2bSFMmpEN57qWhFPJjizcut5fOP8VIOw8VmGMjv+r0Z40edUiwx+9t8aqfGZWPx7mc1yiN'
    b'zCt0ktiSUtEdGzQjN6t9hWXoYaioRxnXQV3SjHFZEJkasQgJXUzioVn/T9x5mbY3Nbq3z2QVPJvTuar0RMgasxHkXeDke6JoHvIe'
    b'2mVofY2p9DPOi8WEaybCETw3/Owk81x2R/QJb/GO0yKOvjijBcRfCE0nE7gamssCh5h1rTe/7c3YbruaCK1KJx0wqVIqn3tx4grv'
    b'1eQodQ1rYtLv1hrSbbjnF7aI0PtiAf+tbjsjpWlm2L4wc+uULIH8GVrstm3wff4o73ZzdXT9GMWUx4l+15GipHK+0rMKzGQmFJLb'
    b'sNZiMgryyfjQjgWLCltDM7UjXH+FPhpfkbE09+FLfK63LHi80WhPssqW7b2d/Q4fYY7z9I2ZuHwEO/V0gwb5+6ILMIWh3/zKKjQb'
    b'e9/aCUAlEPxEkafb4NaA4f1UoJ14vAkvihQNmvoeW3SdIU/RwCbf+soVg/g+URjL0ucKzyw8EI483F34mzZ1nDkM7YoiN3hw698S'
    b'88IcQiakHbzVviIXSFSlLtSeP63skhWYBeG9Lwk3wuX/rqnoojhVqn00NnVfalEK/iS/Qw+ufE/J690drgaJWWeQRH8R+2luD0BA'
    b'2lhd6to8XoiY7dGE1HP9Zg2kXOZ45qeJjqXGsLkw4Me8d6IBE2GWFxa4aAd2N/eXCd8Yf7I8QYU45aiP18t2Q4d23+s1dwx1cSNR'
    b'tqzyB+DL4lZXzXj1XVoiUoAepBkZs+Jg0kp0aMpHdyf+NTHIZg7Yw9H7R6cPvWzI8uT0qMSbylonEpaA4g1BOcGUDpnwtZyfR5Q4'
    b'FLpDJSZDW4qUH5tghCee4ePZFUJW8/y85QcxCpSZxeCswZY3Brz9XrGnKvkCb/V7MAY5v0P8wQ3cM3pUcrtUOTyZxd+NckwNOgf5'
    b'hVw4vUNhY5ouV9dWhnAxyvntRreRmwe8KJnAqKWiHU+uuJXr+NrUv1N6g/knLitUh/QlP6KgWoHC1IQsgHhpIywkcMj4wltkjHf3'
    b'e5F7jDhNuN4LMK4Dv7XiEnyVDrMIkgF+Hl1raBumpFlaRbDHww7QCpMtpNpdl90Ryc9eqhtLIxeuie7EuhNAa7ApSxq1/UifAyHc'
    b'+7YDyZrzwvqvIZIbLA5uPx3gRCQk4ZRRdrzE/6I12rJiYeUx3/Wg4BvQwLuneNZiglQtnnZw68r7yly+FkHTbTMs84//oYCxxd7v'
    b'5zL0dSCAlPmG3RB7DxsB51TiIYhS8sC8TdY792EkGz7YvgOtuOH1dls3j/sPRCUipsRi8v8QYRt5fPdEIre0SAib3EyvDDHuE+4u'
    b'Rz3lv/fV4t7S55/nGIq4S1/nNJwsmWugLLRpSyMynwTpSzC4jFSVZAiBYk+/2u+T+9bKrgsCex/h3EJjLD2Z7yUNbQ0aO0Eh43o5'
    b'Fmd81eAWObSyJDrFfKXFTL6lAFvhqGyKBAtYLMjPIZP3LJ09D/VemdAe1794D2haeNbtmh+gBQHMJS2981prdZIcMfPw6wRRhXli'
    b'4aL8ENxGL+8K8lvMegwjyVeEMiVK5Ns7gusaz8pJjYxqldUPq3MvB7IozooVb5Rd62BgoQGUOg3BBPuod5UWacRynnm00fhfASay'
    b'n567kH1TaFK3cmv8l6BulpV6zjVVF9efN/nXcU2/C8yWwuPRrGVg1frmQMSvY2cTSZgL6Zytvf0yJco3QRnieh39A9THW5IsCHET'
    b'Z4OF41zQO7RBO5JqSNaoCd/hkFiQmo1HvdlUp5uw9qah6IM7OUxklFDcZmdMaBZeIbD0Csqmhr3xQd51Lbise0wcyfHK/1M/u3sT'
    b'jeddFuiWIFclqDPWiNaypbpQqBuvs+vU9hd57IbR5OscmxzT7f/ptsA3eP+VY3NFo/359BvNJCSbtlkN/8IshUeUeOFb2REPLLUy'
    b'yoKbTeKkXh1aQjfMwyg5UJLnJYGE+4TuGodXaxVbG/D6dOY8wZF1inCFF6wTlI62wRZTCdqRBcOaS0X7TStkNbhZCJ6VMU3bKgeE'
    b'EmM9+y2M78URuM8Z77we9njKpS/7LwporUk7FpIObNDcZmTwp9Zw9waCRr2AlWn3NvpBLCZTc9ACYVIwHnXF+tgmFpqlLcd/2eVZ'
    b'guuogCXZOhux6sMcxy3E3WI+bko0CPJ6XteMpU8y0nCUb+6ko05ZzSrQHq6+vLlwYRYy556JEvQk55ZjBCjsNStvn3tHf+syvWRU'
    b'icrP7V4tSUwFQx7e2yDzJkYkUhvwmDoOpLK4uc4tpfsY/FHXU6r4O5clOw103vB4FYzMKiZiMJSV99WdIx6RWk8eWl7IOt398fj4'
    b'bgxRlZd5EjJkfF/lJMimgNtBWwCLD8P0FVGjKKV/9MD2+a8VaMf+zO0590K+myweQeWuw+0Dkw6uun4Aw6VSdv837N/URO1yPOR8'
    b'KhzIGARpty+V/TPL2JhzOuENMf0W2I7o2VZed9l54mIinQccpK+uiIZysjywn+x4RHVEbwAwbuEyamus+cJMFNNHxC2DPqpefPnT'
    b'iZU0A3imbTnG5ebLRJUyfWHgsv4EbozEaVPPs9MZcr/qtQdp2b6j32jZDfxJDfFPI968SdrZbCAWYKA1GED5HNVsCIPhRbNeY7u/'
    b'abtC875T2KY3vZzD2SAWPxxnMErjVf+l+I47dMWqur6hnKOL3lZ312vqNPpw7ROoEnMz22aeTJlxf0h4ZdGQTbg13LlcLrpZsMsi'
    b'Fw1WpZlp5cDH0pzrhClNXmMpiuWNNLmf+7v8P5hDAT0ETgXd2fs+7jR1KcGt1u5aqO+hpKI4+EGhlabsQz29fDhv51W2V0siSknZ'
    b'IEhiYYNIMpjWDs/hCS30I2FmDC/1ObMNdOJ5F8TqkaW8wiZpAccbuLIxVQj9UqwQxc05q+5fY3p5h813JJwhIve9UejpPwElxzjM'
    b'Zhq+AxbRWd5dkB/ZNhgoprFfyK897Shn7B32/PKSPGykjD+3ZQYERa/gGjYB8FR38k86eyIN7PSqUUGLI3B3RWzcuJKQuj8LLbaM'
    b'nQTSN1Oh3HFKkRd21EoAUrSlc9YLhhQcV1urkALIPun7Se6YQUJeIWx92xweUSgRKQUyvALi6UXa5Xl+ULZ1ArENR+7AqwrjGcPT'
    b'7m3WJyazs74+RkUbmUtEhu4n9H+4XvECPgUH0ddSKbhBIads4LukNDFY+VwY+aAWvK+qqXcjd7dVlNrbp+6cUVUhj0ob1kGVdh11'
    b'6Lhm82RuUR43DYfSnC10HOuec8v85EeyHGXkljl5MzIOlwQHupGZo2sMPEbrQGMZF6bskAmnugNOjjoAN90n2CPhAW826KWi9l4l'
    b'n1onJ1pBJmYR7smiuYKWw2TkN3X3hk3uOHvhMKY+cOwzw9x4ANjN8JR00MwuycZajXnvuXXfLzpoCEYZyMsIzwUmNTw7V9TjrmQ9'
    b'ZngP6phcTXGd5bt1bmHZDx4TCdzRtOG94fUIyKAQlw1V+445BokPDy/r7eRCKllIeoEh+ti8wFVq/7Aa9nia3Yrspeo/iuCQ0Wsf'
    b'fgi6Kd1TcqOxsPVcSdyIzC7x7wSMfVVgfj45HbSha4HAJfb7q+XL9uPb5iZxKa2FD5ucJCclzzscziWcFJ0ai7aH9RP7+yb4F2ZT'
    b'7JdSHK1TUyuLV2q+nmpbNbl4Wr1UeENKVKC3oGRNXmC5rtFaWeom6FTAp0wRJYxgAXs9nKWSgDA6TLiodmyzPMAb4//UndhyCg9+'
    b'aE+Yt1foCx1lO9BxxMpg3RbKObsp7UUv2sT1rpsyL1F7ks+rGemdGjkhpJUzXhY5IX3IJTYf0BM3Gkokel48oji4/YDxneb1S0AH'
    b't9uMThib9rAmMLazz1GZ9BxV/JeAIvuKjzucJ09D8Bz6rs7PihR92sbiRj3bTW4+ub1Rl15iK324Coo+nizPXfMqTvtOA3ba+tez'
    b'wV7ou6YPeq7jIOXp40FnwUVgGBQf3mzg+rdqybYyWQnIWYjGkaX2C6ZHYGqUsiIr2NKqFiWEgL3MCsfw8oBStAETmak1pE0BjkKL'
    b'dbEk+mzFRqT+5PhEgprLTcxvOtf3VK7gNtMuLos1v/K32YVjaTs7FQeTNpHw2fOW2iGM0H0/TCMRbLBm3tQ9NV93iwf9YhPpMxMh'
    b'gNKGudA9bd0h7DBsMDzlMcNgsxTAlmDTpkVuZdhKfrItkwfvJQWeeJy443v5uqkEIkZtvKNKmo/Lqe8BtbwtAJj8ipMJAPS2eyN6'
    b'AKxdM1+E3eXIkfh/XT6hlnXYfrAtkzHqAq0uhp2X5DauxnGId00FyPvJsBDmCGxE+B818ZCtzMRYO7A4BKQTnEYRiJgkzb48Y9v+'
    b'/gNxCOWIbI6yNSpwA/+gS//x4JCM+F8O7lU77VwXF1SYqR1MmrClS9IgiruhP8u1huQ9Xl+6t0LqeF4sQivZeTeSIRsH7yEW4Smb'
    b'zvHA6wMsHcguk3FVUAC9IwRxjCX6jzPr53nOINAIWPumngvUgGrmoCp2LO134qFgPZ+UJe1A9uh5wgwj6VYEhXiloVA3mRp3WfYc'
    b'6Q27LNWqa9xdl5I1mTtykpZZAby6CHiMtzwoGUoWnqzW9hPJONAutJmZqN6yT/nWXfNu36Ia3CBw9mUQyIYo/ZhCUg/JdSJjY8sU'
    b'j2LN+FCPj3kXwbEmh4RD/P/fLzcRxpyX63zyQDhreC74W6zCgoY7I5k2LvhFvvdyCwspP4+FQP2clEyoE1O+0K55CFSk3VHk+qVw'
    b'Y3PTX30MD7T4Uu0ltmVzD0vmttyTFRtVMV5ov0ZMJL6OM6CraEIPbQO8bnjB9uVjQGsSsmafdkNS7tcHNf/6Sc2Fz+PfoaAbJNqW'
    b'ipE3IlPg9I9j2bPojUPI/HoWRqzu4o9IEFg/ipbiie7FbvNFuy/LvQDqLiisFhAJCruARjBNv82gLwwdC7zAVx46riJv94qdBr+s'
    b'sFb8W+sFESOl7MHU1oWDBMjjSNhFHVNRpjJVfjyVfnxORtRAokhHwiEVxxVTp5k9lB7MlTuRzTfamd9+WlUSRdgDjxpZbnkpBnpG'
    b'UB+PjjhyT+h52JWFWjSeLIey8Baw0q0NG9lo5pYOXlb+H/JlmeRbtpaXP69uzr+rtP8cMRBpUZBpE09mZXsBHxUcbkfLxObDhP92'
    b'OcA3drENoQH1rYq5hYejxUbp6Uoct6lzteR15sEsRlAK8HAJfMc2XcFYSL8UIJx2pCSNOVLSIKfH4SFEWcnfzzKm6uo+pcM+wWV/'
    b'lPW7Zlr7xyiZnJIyL5I0Nx2s4evGmsVY0tXUJO/6N54+jHn8dupnWIYhblV2IdWjYOfKZWCDB4MmRJy9qTSP7tVeqYjoMtPtLKw6'
    b'A42vhw/yJ4LmHkq9+xwfc4ELgTYUXgWMLBYH9/K7U29ppCHKwDHIwoqtYM8rXCeYPTH5grreL8W64YkY/9Ms9qMVD4uKd9DNzjYy'
    b'RIEjIXUq6UW+1kvIO6Rs49q2aE/v4X6YSxOmhdBFrLIAeF9rNCRQpWvFsZ7mvuIkAX2yhOR9SPCcqWzNZvy1DTZnB3oCOmlvYeGX'
    b'b0b+J9YTZhwl2SU7ZHymfiqCqJ5dSAEOp7/vzyou5GXiR4QDOihG5USL7YbUz+3HEr+kJCJjFDtljWHQeTs8vwgmHlRi08FRu0q2'
    b'CD1xdVHndhyzDob2Ua4MpwBosOwfMkL41KkUar5ScHlpd5qc7rSdZ+ZC51qDl3Elj+GyBXAfQvH32XSqyA0rycdixh9yJpT+14R9'
    b'jdFKf68AMV1DEWjBG602C50KHJHdzqSFNKnud1V7hE3beFLXZtiUPbZk/goQO7Sb45yshdl0z+Z0PcZOUgd/1glu8jyew/7G1U0g'
    b'oDzCzBaRuRa0docgGc4btrspFmI4YehKCqzsfp5C1oiouWl1vg4DbTI0GFRJDI2ksY0SzREKtEVTCAwpI3PYeDr8slON8Q4JEYvE'
    b'S1mhoXW/2gHze7ChKdLifTVv11NHRqfeUKYjeMKTbasXrYzrw0u1JY7eCcqDyPFivVgBXTptJBNXPTFtL7/5Kko1midJ6a/gk44R'
    b'CAwDmuP3q12xjQiCSJws0LzfIX3AmMPTBLeUnPD/UL5lvekjzbAUP+jR3+5U5lcnp/itCtjPAuVU1oarxfrvbV6a9rdltikejzxH'
    b'3bE4rdjNFiyb+zHayF+pViDIEyHUQ8wp1INnfYt3YgBvWLPeReOwbyXp/SuZ//odOM3SltecAn2HoIjReSurkz468z6VvI2niGud'
    b'fp47QzN9+JjNOIxotpnIU8FkRfwfK4AKSD/bENNnDWaikgYDqt5Seb0P3wGeel0VDkh8xRMj+pDzXEgyNK8qmi/LB2C2G87hMxFN'
    b'mpghEmGYEMQwNeiDEm1qh+AKvjRnFmG7pTNPZwA+sWo3/X27ezxAY/e6PFaI1JCsUa9EeRah7YxcIV/SEuHykwiwFg1mak7WVMoi'
    b'aNHBVMowK0F/fbm6OuWob1oWKCiBNuAH3xdwWhnuUP7VAfCYwUbEB5GZKNa+uS6CCS9TJHob7PtZ5ZHv/Or/BxMXzWHM/vEoCuqy'
    b'xxWDDA47eFkB8Bu+ht4/Behm28pHmQXTfttaqWuVaZXO+KXQUwL7OGGkBVSPhk8fcu1P3Pv28NaL3t9FKbMDPCFDZNCYVeRC2b2C'
    b'tvFECPsbedioeyI/Vms9SEXBsyXT2MLQ3VNMn1wcrwx8fFl/4+oIi0mobkgKZcyFNYs0Yj17TWopCf2FeonTzilx3ofY7xNtIqtE'
    b'NEfKhj7vQsSIh4HRSC7nHReqdxMYInw37fyFw+MXTm2ICAXwtKrrdPHd8M9vOelkoEfoeRKUZ8uMYdQDSQsexNqKex4pIFVjyGnt'
    b'GDco8nBL0lTSWQvid7DQTi86T7K3nazJo+GkDpN8Q3VnLa6HwliAhM5tWkkeoYIA00KMKycQOE3UvuClPxvN+6X27nQ9uZLxPi+o'
    b'J4OB2kupe9r+7njVR/cRCfD9YY0T1gpGpOxC+M/cXRGpyJRHZ6a/XsMep7EegUkn4t9JdKNl0C/nB6eHS0uHlvJSi0xcNXUteGbu'
    b'Gm/Y3NYw0d5s+qEl78hKFpFY8lXxRWF3/7g5Kw/8XQcsOMLCqgAr7C8qgf7LDAPYr8i+bwSLe+H3Q8PCmlLO6kP/tsPUTBBnIAmo'
    b'yP6Uk+7w0xm0BKdSN+KXT9DMtM3nyji4rxyiMjYVRrJtFN92rq1OgpJS/t8C7v+oTdf07LNvDZx4htvWqQVPgN1B584OAcwYagJD'
    b'PVEphMo/t7AV3lPHYAIwIz7QlJzN1cVy/Q7BPN10NPKOzo8NZhBZX028FwoSEBpYJFt2BHGECfyrXykUrnJU9cYWlnPLIaLzXtYY'
    b'TM8VAnnduKGs0qP0Xn29U7zzyrsYUoNsAygQWHJX91PMkxwpKzyxGc6rJinYx5RnubkAdkjzpnCy23sE1DxAzuSnK7ASyGcu7+Iu'
    b't40XD/l6C/h8bmGTdteRf5x6d0slQh6xP8Wdnpyp9bTsUd4R8EH6RYKm45Vubh19a9DkEXcmqzwQh7vB6hZl9G/+J6o7w1ckQKYM'
    b'KxhqdEEFVDnTnja+vwxxNfrtdeboCG6yyflz+qocyDG/LDJ2OhPY3he3uTc84eI7Xj4o8iB+XXvHK805Xrjx7nLAzCOk8O0nw/FJ'
    b'PoIVD8MXebtXOj9L9dEZh/Bk78ze6fB/+BNR86o5fnjR5jH4LdeAYIM0R/ALy/HaGleNIPrAPtSjGNQdnB7hiA+oPJjuPyshH5lA'
    b'9b5bizPT6RnsnRRf6ippGt5fsbo/tXntBvjzRf1w8qvgeiEPZLC3j/WB2c22HJd0pjFxWGq80iKCbeTLiSUATEqrQHF4XtwMOrnM'
    b'XV8NKgubcLL32noKuWI98i7WRl9eTnIuZu+1tU07dAa/tNQ3w63JvkLvZtZn+AZ+e+VH4mFh++K9GrsMaN0VgkjWuVdMMwYvoF3c'
    b'XpgXDjnTR1xKWjdQWkLqrGLA0wRFW9jkHMCCugOJgN5d/t+G9WzK+DAC3iXrEdKdvV9rwXc0wnJ7jGHt/1soIdMfqKQVEFQyv3Uj'
    b'df17JCNCMsncT9WfgUYraTtYmnBfjyZKxL6VAhaT0EXpyCmQRc6NoLVfKUQHuNEfKBpN+CN3pubOyAWuggJ/1E/S/Asrqtpc0S3a'
    b'F3kgxcyjyqrma+6Uedx0/cbSX+IXVJuzwI5k1/Q2pzVp36C/fIUuy+AnBrQGHJDuutxxkP/luEAReKZVZt6LGjdHa52TEDoF2JpX'
    b'QpOhAlJEqYOXEGf4Yj/Ik4u3jpzZbpuDgVkNa4c0CWrqOto51IxG3Eaa7jNvSSI0mDk7MBXJEgQcd/peNcFC0SOhvn7rEtg3ue7b'
    b'wUmpse3xhE8+D4ZdW+3c1m6NQwRG0fZkcuE7NspuhYDQfaQaHlUAufCRxryy/JEv/cHDxHd35IZW+0ot46YzHgHynnBRsCs0DrUs'
    b'JOcoaQ2aHpSfdIiNp5c5ZNFFT8aIPjB0ZKMBqbgqaLftrV+CpAAPYOvOCSiAOO5MlmdYxEIrY/HGdnqvamdVlAQfPnxPchXjC6nC'
    b'G77Wg2q0yk3/Bkc3aJTdbtzTzolnjp8D+uRdYaFseAPsa7KkCnvURjem0MrEWWvkdKptJqdjXE1UNvkaQGMMKAdno9+UjK9jqGCt'
    b'bf4B+H5IMMZVu0MOo6StGUu+BikK1NpkwXyhaOwJpKDxe8WQb1TjNP7gwcMTN4ajbHx0ckAsvt2q2yqmUrnmiAZxJEPW803++e+F'
    b'ceQuoZSfJxuCk6OCm0iJLR51WMjjcWI9dYa5ZZHDpfCLN9CY/mjjeWcEsHwk5UjKWwZBHd5MXPCHaSjQJYtwslHfnH5zuWtOv+eS'
    b'HY3Y/muPHnGRLEuNhkVOg7DhMZi7rI2VCuLM84a0QXxKbxs/ho5Wk/15m7Os2EpSg6YCBn/DUJrFaDJl1YTc2co2iqkjeIGwCbv4'
    b'ngFzzQPjuYK0vUMwiq7vebKY68sddfJl7yIbqVmqicNvaZQTqlQ9+G3IAYyRXwjvNficnB9KBc+SFpJYxSzKkrJYBYC+P39m7Idc'
    b'bvysrj0YRCfxdemMhMFwTVZPGRBZnCHKcUFcHrSTmej4srjC6KuGg/Ypvcm+j5yD3GSe8RZnM+lBvArlSgBj+LYpfrj9uDuc35yg'
    b'4YcEl+vN2hFXmTsH5CBFHbDi/o0GEqwonQDdB+dahko1YiDjFRGN9oS+7Fse0edXXr7PP6jTClySj9lLUuo2DIHbM4orr4qDaatH'
    b'Wspr0+YbWFusg/LUyvIPoWzaxAtDOdRdp47uzfK+zM9b0xbWMntsQ0gXSfnOyzDOY8pCnJUsKihx35QLBlgetSvekcjX885QsLbU'
    b'k3OP3PTKmKrCAGZdfkXM09+Po9guMMPXNlKl+LwM9qjdpA6SpgXuLR2LN8myHJsChd+k833IThWDv7dsbu+flBO0bkBCiXzvDaL3'
    b'DsUgqqNtnCVfpTmGRdeItB3Joofw/lzFRwiW11eWz7BTEhaw4OBlGvKhi8W5q77Z8R/nxDAR3qcBH3exiAKebS/0EFhVO7hLyyTL'
    b'UNZZWnVKSdnBh8n5N9crffxIl+RiOPgvp/RCGWU9yA6FKJvVUyPY49SC2r/pkGRCttl2vl0bjd07KEF3mtGv3SwEZwJph5dIp/xs'
    b'S/87fv1pifKK3Orwo1LlntPccmbqIOgJp+uXgVTtSa9sg/3y0mtsMGcflmKOhEsPII0OrnYd9aVvcHnkcg48W9u/Q7BMtc4wdxuF'
    b's7kTJNYMJDU+VMsgn975g+8yqiUrBB2OFJn27EuYIO52AMhTPjCWan57wJHrDZgCjS/Sl8UEGWfrcqw9+44/gKANZfGP7XddWi+r'
    b'Dimp9kWaXLupAdHAgFUOaVJCAfWbf7uJVvln8AZfEeyJTmwXAiwU4QyCUB7d6u6VkIzVm5U1eiC3mVDSNJS48vM/gVNR374kN5HN'
    b'cI7+qjq3bwqv9NQ7R8sQYRF011R7wuXxjc0ZpJiR4uqfkbv256EucxxrUJ3Yizwo9iSB49dypUXf5defocBC9rHvPn1M4OKqZ/hs'
    b'aBidex5LaolhdXgQ1Wbi3ouObhNp/KiJBu907ZGGIQjMwrDeSQk8QP0WgVPwbPokuvMrvc4wp0u7RjhlxNnnxAO/sThJJSdZUpF+'
    b'Uq7Qu3Vra8oyI0nJ70u6f7Jkq3OUv+gr/Hey7qcan3y6hPSixjcE2nIQXbWq+QaOZZl8Bhx5nX9v3+XKNeBvSHThrrkB53N5c+4q'
    b'+CT9Ea0SSu9U3I5MSh0MCq+AsMhC+NQ+z0hDt0Ixg35IMJVh1gvX2gF4s2DIltEQWLMQJLoF/5r6RzOZiX0JW+UJeBFFFs+1HJHe'
    b'pibNAIQHzeLkhea/CA9bn6gK74Tymv4ff6Ga/+1jSaEbu7RbRROlnGKE1wH7TJ4To2F78TJd2P2Iif2IQkfNuebphFostAROJNTE'
    b'+CWGAL1FA60l8ZU0xdQ8Jwr+ZZXDZqt17uGKt85rtt9uL08UwVVsdmixbHUVb2ys6kKDT2RF0vM0kYl3ZLkVClWEMIK1+lxUDn0L'
    b'k3XRReAjKS9LZRwR/UOttbBc9o6MEx4jMlGvsOzhCtu2owTkY79U2jsxYI4aCD9pwbqANAMmTWHPB1tuyfx10B2yVFU9Fien+phj'
    b'bql9Z5YUOceeABxjdvZNdbiNRuD4raS8k1+iUs0KJMn5TPQCN28wvXT851cLdDHMdBmuKbzyZ5dbM2in6+Yrp0kv3PfJHTKc6HHS'
    b'SSGosoYnRIoUJ8KWPSVgIiOUPjA2Jy3zVXYXqM5rhVltgSUEn2PSO3XPBwKpHh1oE2T3TUXAzUBFqDwlU7k3xe59i+JbpT/vqexj'
    b'm/LAj6Nro+vdEC2U0dks1/6GDwyUlQJ/LqP+tdcrSl5+UQRcP+E9ODJ+hGsExT8th4zj6abF61bgfLjr4PYfIqEREti0NYxoRksc'
    b'Zhy+qXJflX+eEVMepfxReybE34bRmwBd3G8ND5xZXCQQ/LjJayQ6Y94SuzhXE2hIXmepg1lvX33WKW2BIO1UudODvUYB5PfbpsyK'
    b'34tpKnFAjJF8fWuhsMRDgDfLtfjZNNvAMqfOKp9uMGfqMvnbbEEVdGEyBEjRy+I9JunVHj3Cf4yhJ+BXmcL+mQxKvdqw4FohkKJj'
    b'JwNuADN3wuJxLdpEswxwSPkziXbcZuPyRFI+fR2uwYVYbV/HTx+buuMeT9+gGUF8WpRO3ZJ/Qm122CNQAbzRwvoTk6/WRDAttAoO'
    b'89KgOTpOHtcZVj2SdHN+at5G/4Zam8AKrFxSyg5jupnPsJDXFAf08OTtPNeCGaUaiTKhWOUaeFL2Y3gn+r3TQ9jvzpmi76nBkke/'
    b'RirFg/LkUo9aLsYiLMj+C8OBP0dcdhhSzKuSB7Dpq5qKWkr3QmwM83m5nSNUOhJF6H9mBTyhbemWeB4eekg2G+jcwhROMBJdQRel'
    b'oCosRmc2wrG8H1VdtPWHzYpyDHVWjH74DYNurMemkMahl05hIUcgdBNG4ISIsScWF36izyWtZwkDLNpSPfo2yaxizuHgh/at6G74'
    b'qNw/d6db9NB9/39GgVC4tjEXxMaxIsalhH8SZvLoUpJqxZdFZf6RbOUXFuts4f1OO78m1R1lUJcsoeVGZ5lhXmruLaJ7XIalku8r'
    b'9a3X0H8GuycoH08BzRFwdn974OnNbdpX0buOz6vjCVqZU76gUCrCo3UFP1jPlgIofj5f+QKF1AcGsZxY3KBWdDxnPa4e7OMvHk0R'
    b'CygE4GZHTt2TlLzh+Qj7wNk7NjC2w19GFO6JcGd6qqhpvb4SqbscG8f51h3pwp05C/WWYShofihy87qGxQfaNc/ATJ3ExayzsjxS'
    b'DSyTBzGHju1yOlNsL25NRfY5KmDzy54eU45v8hlOFH2vWso5Bat/Ztwgs1ZyZAg00+5PGUypCa9i6HQeuzRIJ/vgS8gZSsy+oeFC'
    b'pkj5zLtQgNXd8gHtSSw+rGnbkKFcUZtgzAxzurPh+qjKtLUptkbraDnFWNexb0ULu5xCyTpwElW/WuO14yAkfMZx6PofUC+bSFAu'
    b'11j4XT+4g0x846pCWrcUw1pAJzPmbfJX8H6q2sti13oz4ftAlJuKgt6jmxY78nfEzY2m9g02drmZPeEcbCWOaRUzQ2OMSqnONpNg'
    b'GPYarKfmP2BzAZ24GBmk49maxyu5SsK1GMX+1PJ7VRuO+2g2nm6OIAB+yY84ZMz17xM+HBtA/9XClr5+CEqMrAUu/oybX7lhKx2i'
    b'MtPvVmaruKpaxu4RYi8FcXo8YrSvg0+98lekwWvHMcuQJOYOeiyOcGkYCmjsaH5GhZ12DXh/nz9IbqoYb3mKXEr9UbAXi7c2E3xM'
    b'WbnpvTJDcHKFHlMaL4vbjK0lK0ka7gz6BBvIq3iOC+FbQp/frByVCRaBqbaGqmUT+YcOVZZr+X/fNeeZMi1QdooTcdih4ueIby3O'
    b'3lYiazqZQajD21FIodENKP+VlcAy1GICxlYVW/Rqna9X+w/ZaW3NUisWmZSD+gsV6mPEmJUm9U7XrDifJPczuIoQP9yEXrkrotds'
    b'08NfIMOa4nLABUqhU+aunJ7KmKesHx6TWumaejWNb/P7EPur3kzqobykR7VayzQBBllRHJxQw7+lBfogNqnivRBzqOfAgJToh4SF'
    b'AFcc8gJTWiCaartofrPEhgymxrqTMm5N1HQjfmVzqwOUHv1ZjQ/kxMkB8NeB6oLglS1NxJSjZVjEZkvvH0ohQ36+BydC9OyjxYeu'
    b'DT77AGr/ZZXoXESLUvWTZpgdfoXbD8BJo2a5DYEiywTpxg9Tjb430NR3/KAaXc3Hw6//O60BKoHz04D57EobXrASxOer9OzuhMWB'
    b'nS4jSSnrsIiHqiRFILVFtucbZAM7ZOK6RFQGotbH7bJBkSGaX9u3w3RTxVpnOTefwXGe5KULDqEuMYFivVK7VQsO6cFNPYtojRAs'
    b'DCL/Saw1KLFDpLg4swHrL2jP4r3Vpn0WUf+kfrllCpGVZbVcXXd1yxVaGMzarn2Xt+h8kUz4o3+ZFxYC7is/tdRAG5yYafZKAfgM'
    b'75jcBKBEMWL1Pbjv5OJO/KdSg6cOBLtpVvA+wgEBHWARbZzgcGA6FW+02IRFqiyccMQOAqB8BuAvqxLVVrtXvcMurndkqLBbQucO'
    b'8sX8Gm6VXXwT0hDdFOhCNgMCrUskwtGiwmSlsvXk7893iU3s10CoEQpf57PRKaUwwFbQrywQjvPFKw6nxAXsiY+ag36VcAnZdGpZ'
    b'b0VGGeF69Wqv40/C2GXjfVimAAL/iGAeqtALubjmpAvToadzdU/FGaViSQjd0Gy5BtWRfUtVkWz1OwakV6OVyWbPy3uf6Li8QH3Y'
    b'ZIcEhTvPseZvo0PAvlmL9YVThy0RJRbpXGDVghbzWO2sY+Qr2dgykEj0v2rpsOBQYnx3baVew21z8s8aKu86j8Zd78vpr0gaNlg8'
    b'TFCQK5CpG4QPwzAk3AuFybGoEUuf1T2OOohpFRGz/XXDt/vWYr9DKPY9qYF3kGvVzUXHU9gI5cnsAMjxBc6hodJYHgeQvjiLrbaw'
    b'RRJJ6CeQ4OssHgaFq0PecUE+yX4DKOLAarD40IzLmN+AEKSn7Lcb/yO5I7KMqINS6m74nS1TExOHXV59bOgSMmNRtjkSSYG5zQZL'
    b'KuEcXyp8fSc1+oN6lp4aVxDcQRXphmw4Q7mUVfd4CDwRrd7tZCwK01DYpud3iSQr8Y0kOKbmA3XAAVAjBadBxD9JJ/J57xs7/j4R'
    b'5w8P6pl/0O8lZGsLpTSdZo3pU1qma2wAm7l97G2U6oaj8gzuFtuwQBOWH6+Ztxqe5nqT3xA7eJ/rFVkdlfUcPz89W9F/UIeTF0V0'
    b'mWX8l/OBcWZ4+yvUf3V8rB5ceSVCZOg9VazU4f71pnpcoE1DNVN+HYXLFnaJH11u4qpvrosPchcGjhZ2iIkUa/0joq3p9Npxqag3'
    b'4CNzYtLWnhhgu+1evVsz79Fjjq7Qd36TzITY3IktIJJpMqggP/SW9X6PASe5E2snuefAoyL0NM6//wtb844cpD2hp/p08HOC1jna'
    b'yx/wVtQUB7iA0ZNcyhH537jZkYR2j3drQogVTP0gul68H3zH91q6ZOPr4RRsuISzzRqo6602dOuMLRXhQ7SSe/ND8/tc7o9g9taB'
    b'wrXTnry7uz+gtFOC/m/NHeu6TciCuFC7ipcPjsY41Jj7W+OvBc6TJm5wtNJ0AXUUcnAvsPWU45anAkAzNpeoPBS1nSSBgXIs0vii'
    b'HVAmwLNKqtkFDrkapHNCV38sTxX+4YuYuw3URvLhV06MLTZyPYBKHhpjKg5RTV1VWyGzKWSr3WGqZVZOlPuJqBwfkY7U9+wlj/fI'
    b'Zpxp/FSL0p3ebPz/q4rdutZqFnl4AiEL68rEK8q3I7exNQFFNap+4smGndxnEJsLzjvYGi9SNu1sk1zbm1NZcMlP+AUrGBpPVLbS'
    b'/ZwzHllYBqzOvVjdyv7THphBa9Fw6HEtwlW6ASezxCE5qtJYbOAqVw3Rekj4Oqw/7tDezLVZRVb+Nzie4DhcJoHX0YmZ3XmH1q+z'
    b'HC9bvlsEZvN0ietER0lafJ7muRiKXuE8G5RdLt0HNap/bMsw302RkAPWCu+ZB89bKzNHXZeP5T8+HXQHw9b/4ocS9fppjcz9ZyeO'
    b'4EIeHAkczxeDu8DzTE4rjrvxnTMabrRMxWq8ml7EXYHhw+1OBcjM9ZzV0GsMn3+T3f9uMSI08hBvSmYXA8xXEJfpzKb0tAWV5gGT'
    b'JzSxCOEp4Y6LoHAcSV8gNCeYIjzd+ZMeAl0hnRZfHLSBTuG0rVKOR7XONedjp+/8qGV4y/sv2E7PeGQiziIToGM2DkLSBcLn7lel'
    b'eTUBJUFUifMF650FuGTZO3vUEziNzx8/OreZHelVusKzCPjVcGcZzK2w0DQiRsHwkPM2gNZCWdI2NP1mWE8AiKOIf/IvQadpGhRS'
    b'RP5xT+49ymlxXh2ytdSJ0b+nyJ/fGGK8ZI/qqArGki/gTYRh6HsyqmJ0Hg/fKTenhgHVIyYeaLtA2l4sx2GS83vwYNZk99JNJkUD'
    b'1cEkpxUr4fICtBmo9uKJwCwsLl1Es0XwOGMUZI12jQh68dp67IO2Q63m7/wdTqmERUhosCRqd7utDXt7BBqDD1aVK5na8OIZcida'
    b'30JdbzNYsSkd+qdDe22JEHhWXcBEmDkXACFoBevUgBmM9GbScZAxPscLUuwRvebYVNjocjvIx7Kax/mO+KMMm7+Wdnu458upS8K/'
    b'8bSe9R0PhobVOg03G6rtHhU1ryNGwfbUjwR9/ID9X0NSfnevEfRmCPNTeNEubrqH/mpd6RSNhWrIUEpAxeRCyk8C1PfzB03Vcruo'
    b'5SIcCwlPysN1uZWj2uZvqShzj+nZN4GMTVaAC16AsjrF/cCTc3YQEAjm4Je+CM94YBZOs70SChqDDeI6e7IlWoRPpDT9FfIQ3h/J'
    b'6pPPv5aCbHZwZKbP8wIP/nqKvuPac2CIjqtnc5/4wormnLl84vi1hVt8zDO7x8LVFOybXp51NjNJb0nY4vuUL08viekcHc4zO4er'
    b'GHnprrOhdI8J5BdPbT0S5x97T1hQjvv9i+2Ii1Ka/s0ujbV8z0mJ2uLVCVJao/BGG6CKDKSlJ/9pnQAmwM+zfGVZe8cA1YM4VAM4'
    b'4r3Aa9XfcB2Slkin1SYeJ5uffh0YkLIu6i6bNXFpw+aQ3S8e50V4F0yuLn1eWQ93gI17VRYXiZuK0Ij13mUeQZU5Twfsxu7U7zOg'
    b'9VbosMFx4Rve3TpV0nWLiC2VknfnTn9JbMjHO6X+np5KEM/d2pOvcKCJdR66+49rNVoC5X/g5G5Ad504+BTJrpfJd3DF4bNai8rD'
    b'8hRSJZTqOQEmIC60o2yNIfvT/GCqRHOkgk+UhXBVY69HCpb5dVH6ISfwLjuKh6WCBToSrfAvghgd5dV4xCuIEcix9kMxy9gC3zcE'
    b'XSRw81OJe03wLAbZb+4q3QmDAH9iVneSv0Brm8ZMVqX5RSaRxvQ/cQStgEvY5x6tl8QHaZ60lEaj/bqysT98XraOXDQB4x1kRymm'
    b'mvMd5dU7Mh2tzuKp8yOT335kCqey1eh3v/cCD1qOaxXdllEGrPD5h9/joKELqzqIEbyOPy99TPhh1a2xL1ZUOUyiCRCI4XKyabcf'
    b'AMXUy4pErRxA8aOV36fOOdMvkNHsLYdfrzlFrH+sBY95ILrZkO+X8E3+F2PM+p4s0KiWItSfJFD9Ub3qtsmYJH1Wu0ifyXaTvDEo'
    b'lXUFFlvoTx95iDukd3hp+AW3Y1SXViV2TSMV/J6ydK/VEOEmM7+GN0zUchhcM2gLNcFU7JvoVqah7qWZkZWzePxqcqIWn37GY39e'
    b'tGaqan0zMfYM7nLmn12Er9kVYQz/IF50IBghSxhT8rFA+EiSluwIxCCkorIt1EHf92BZ2Ldkfc2tWQAvt+asoQfW/TIwEU7y3mjW'
    b'diJ8YINnczma20cSdqUKCLJR2g9CllVOpLtyLGub2ng2KXcMHpxgNBTkZM3bN8o7lEBAV/OLy7DUgBi6pWemuEbjBGd9Krh2Vvpz'
    b'1nFB6ZXm8uGs5ZWNVwT7HeM84D/85HVp29ATrtkCKJK81MCN+F/+eTXekF2rORTb14KrzkpYlwqQK+PnKj84JKqDCp2sBF19DXhj'
    b'vbfZzyg6f/VNH1HO29cvdlFF7ACX/TtcmgbrE7TGoFFwKpQqiCyeUDHN7MJ87aN/0ou87iqdo2hWTjxae5lVVwWdvxhIrs1LqlOx'
    b'yNcz2Qhev/ecNp8RqqBUSjCcr/dZ/MRVGVyzQnKGMt1AjuhIWqGDlSOuRnnS6hn0dyRdLdBN3nwETxan2Oct1hx0a1FGusO0LtQK'
    b'vfp8vwRrMmVC9AQ4WvqNBhV3lInviDo8nn4vcEcYNPK7duV3jpvivH2eJry8WjfNeuZyaOUpN1pAGXNkZ3l6X+a+nTe1K4VcKt+z'
    b'DI79//o8kAJUTNGefzntAiK9H4TczwtSmI3fe5kMb71YN6oOMYp7KTyKMSnANKovoJFl8O2BU/XaLRAGbXfXs1p/d0cMTegs6eTe'
    b'cliLGZwNqJVEeNJ8xcWKZSXrQ3LVpg7K3BFSlEPzjZK1t7oI0bn3eVkOZ6Q1N6scYaodpTmD9Ugh2ObYa6oRGldifLuXS6ZfPsxX'
    b'4VmmKvNsRKe/Qomry0UbsHnFFv2QN6uKPo0EeVV7HZW9KAcJbIUvnlrAEGMR9+u0qDYGQ5emXkQ8WxqBO8iwa9ZljIt5ek0pf8jB'
    b'26TUqWr84Rg2N6FdJO5bGFLfgFnbnWoB441eZZbe+llemvt+V0OjrtggZUDEpl4cYsdk5dAnIxmJ5cG71QbBflJAleQOq9Vh7JUk'
    b'oDZFbveHW2qDtk2ihaioUNnxsOzRDkvoSlSi36sJL0f9C66NxvNVMNs25ORku1TYJiOppjlVnHrvMZIMvmWcUvxguFcnvy8WTHaI'
    b'faIMQ8sKD2r4a7i8EWbWoq6vsVe6Q/NiDNokK4VQxROGY5HF9beUtJyfdFeFLxoj18x7ROnHIfohKTrw7fsB3fkNfWFwOlb6ZsDe'
    b'Mon5/lwAfZtJxIDymmn5KKbujiuR5IwrXdiz2/nlvKqmA4z2bWBiAY+X3LjHrmEXKfL4lWkvKuJDXxg4G1LM/cEdu44OhhfFgPHY'
    b'zCCs0qyPlIWlbgnFxxrgitcCl/y+J+/MGnwP7qaXKnVgm6hnAZ4NhG/PPfP1easHrD9/uBB/TbY1eEHf1g/FaQ9EizvTTg9w8PQc'
    b'aLEVL++MXiunJJ+Sh3oOOSJasACLxYITScKU+tZKfk+qa7HEtPfXopp4rBkcrOYqJtvdXN0PL1Ol45kFyjFIZ1JyEwftXYFedqT4'
    b'trAnXiaO+e1ZpiBcOodEkrG67tjuMlpa4yDRzO3XQ0HB6QLxns46ukRkhH/Q/unlB+ZoHg37uGWH37Exds8nJ6QojUec8O56eakt'
    b'IZ+iKM7BFnD+Dy75eB/BaYKnsjdxz2Bd8W+HEFdIz7aDm5K39RNVMwJlu77oQHbi9OkO+xd+ujdU3ZHUG4DyyO/hVXJysQb/23NY'
    b'7y0RykI5sMBbjbMj0ee1oxuVQHzKmAmucdqzYdvkZVFKe0Sp+NJn/2SJFFoYmTx23CBR3blqhIEwnA137sRaZjIRm404mKoUwv5E'
    b'o3F23tuBJRsVRDml9EveOq/CDrLHACzpJ2+uHYnrV55RAOUwmph7ZgHGJ7WHvN0Ox1xIdB7m5yJ3Ds/+609xVJ8pWVQlZhoJnyzf'
    b'3+KDPJQeUr9pVDY7ren6EXsZrO1EAeFAzVosbFzOQJKoFVMQYi1B5YtjI2Vx8DUl1g1FqOPUm1UNH2pWz2uPP6+Tp5niFahuFI/V'
    b'BE5p71TXDGRuRh//R7LKHygfRzjIklepeGWPlTI0C8ccMCdPCsC+8AR30HtWKmoezg+H+eGrnn+RKxNmIW5EpamkTTENHDu7f2eg'
    b'bIQ6tKJScVRetVdlw1cWIBz35A/gDtXkCa++k4jyDBUGsop7lC38jzQdcqNG9kmkFtaU53zejJeQgYQe2H/Ee7aKvRYit1yxFqLP'
    b'wm8KkdFY0NEtYn6lQMZwJzi+ftFhP2zRtV8TJMKoWC3OZ49M8BZNsepP1bvb3/jFCiZHUpyKjSuS+d7WA1NrFjujZROBBCGaM4P0'
    b'iNgpDcJ9uJhCPKD+ql2If+2jN3s6h9vOsJh92eucg4FQcCo8rwwIaPPnfmbAJTLfHaHbbWvSHeCMjeT1i6VP+r7w2S1G52pK5fcj'
    b'8KsSJGqmnFfMX4SFN6PvYWv2tNKGlkIgPyL+b3kxgyQLD7bEz9FRtYIlDbabT+d4z7EpmIajyuVjpBSf4VkSrNViUx6uiKR6ag7V'
    b'TvBTesEwb0brbStlrQfIyJEDQEcrDVRPRwfK9r2UGuE6RThdlYJ6mh7XfDxuQGPUAmWMFtHjrdjfd01xUKCX/r/7HGCqLta5pkR6'
    b'eW7Zf+/KoBUgVAFe6cGtIeeTXi3Sq/22HjhgJFXxpGF5I1tUfdYrOve0HOR3Tw48Jhk6GaIhmiSQpIzjWQYQya/eAxsSbY5MjEf2'
    b'HgatU9ORcoeFO4AfNP/KSSlALE0rR4PNjTjSkLjz1cySeIHSwLMlGBies0NX9qV5wwi4dZn18+TZx/XnXGoLytSRPXtRjhA7T+FQ'
    b'dMfJTSjSu3Teh5GTFpOcAb4rzHhGmLvWKRCcY6Ryw57RnsXf0DT7TMzi7EM5MgrdWJiO6eQz6lKZ56k7VT0VRrgZFGlscxpWih2v'
    b'P2eEZTgNOmcZpbJB0qb2z+b3Ex8GDJHcyXoXI6iTEAbwHR7iTE2+IXL97eSFMYhRcnImfTU3YFp1fLVOsW3l/vaAORBZ2b2KlAEO'
    b'zPuMmxEDamPLmklFDSZAzppYv5Sr7EuWqZ6CNCndT2W2qfkkhum3oRq+VncMj7KUmvBWkt3EgWIxpDgamJXTuehRYwPrsXeWksOi'
    b'YsB79Gf9LzePHnP0HDmDtzzhMpDpHCZvbAFqBeyANYLUBAiFHcr8zVmwTV2oP9eDx5YAQdhgb0ThQ4hAcLT3ZoZyi6TNho76n73c'
    b'Quu5PmK1Tp77DBAWdF26UTCl7iqFhs9w4EGPMOBxZWcZaKfHflbYBmazyqo+zXrL2tJb5O6Ku5IgoTBb3ZS4a4yPxkFbnRY63tHY'
    b'YoRIZNBXTNhQ06+OlmZVP9f7MAcuZZQYuPrxtWqHdB88WVNSA6UMvfsYlnDq/S5KKOI1/VIn3Su02+7R31BOUE4wPm89SL2kMpVk'
    b'rFWY5or/sPbCCIjbn70eXLScyhY3/qD/BLFDO+8WesqjA6vB7Blbg8Lhiqh2Bj0VE5ezTiM3niHSj4gSMlLn5DOy2w9NrJQhdgkM'
    b'HrpBw1dCic3KTidRdvhK/Tv6NCnZdxQcr8jHim4TEPmwX6wBRCu7bK9rdwni0Zze6PbLhIs5i+b22i3KMUTCiR3XNsjr6Kwpowee'
    b't7N29G1/mdMTwXUE/vC0feYvzQWxO4mrHgIHynjsG6cHvBnHZlFqXTigqZIiVNI41Wk/AU+WD086Zabnri6zKDi8zrjjFrAT4tpy'
    b'cvF7Lif0c6upSz/7XDSlYGRcwLWUNHjrLmTY4ubpFI6/bD4+Y65eSpxTZ5625Ze9LhqaJlrXI8gbhFr2HUtaxmmXfp3EZ3mkvidW'
    b'lxPfQla3YMsCMgW/6ATIb1iEXZ79dO58Fk7ANPCrDvxhyVcAoRItFhAVpfT1pZD+JXj3NcUEUg4731yddF57aX4mkxw8qO1SYSgQ'
    b'ay5CrKy6nZwNPp1dOAMumyqykLcQLncX5XUWFiOVGeauiohQ9LRToDmH6zwjYeJU/y7Mhv/8nB1nCObpNfqnKpZdv+6q+9b7xm5e'
    b'IDxHEA1yV2Gz7gTV6bYlRJi1nWmwhf7YQtGo8Nyx+HgpKnIgb/NdoPzMDmMHj459+4w2udaKC8XpY3lVQ5ZKdlbO+kQQJIVPyHbZ'
    b'vywN0d4doPUawEaamf2tsX9fRfFm2D5/C2r3HguFiZSuKRdxP/P3kZKFPnrBSvSUWhJxLzc0PkTD2vzFzOJnlksXFy27Osf47VtE'
    b'w/NsJWtpzrHOUFp159xE92BMikZ1tULMmbwdPFouen+2dinMQ0ZiovEjubB0yvfFDIUvE5bvoYr3OSkXq4q4Gsnh1Yjk0f6LypcU'
    b'61x5fJTF7J8zj/qa+4PzmopP+MM4ILUdZHXv0X8GwPYbpmrg+tXUe73NnL/BEbinmrZalNROe4CoiDLnnfOdo+vYi5erknIwPgTr'
    b'O9iwUWtVOYKJ9VMJX1wYoZxTVlxDGzeBGVQYGm4Y6Z2xmUu/6zSwn3ys74hmABisldGQAiRbXQXMh6EFxNjqljmbg8fJd6ABfjJM'
    b'3F8OtDNLH0n7u/5O4V7g5uFwW+JKkVZ/MtBW11Eyp14eBdrVzT1okohEWoqBWvXDg7FONousl4iCfKkuw1y0zLMZyL3klNQTXTI5'
    b'ZkKIR7LX2Sjl6vpXPHuqMmjFGViD6qKlsCXTxblDRi6v0PnMHbHVYhk23QHvWaH9eCf2swD6qpq2yQS15Lm1JmFHaJa+Js8PM1ts'
    b'j51yBRK+LNGhszKonZ7+qL278CDYDvxN1XVSWWhTHQ9c0wtJk9gxXNzN6pAGFWwHsbTLDoylOExgOzPsVuMGgRMAw8dmvS9Ebjky'
    b'qMNWjp2CDKaq8LnHpAdo3M2Btna8cZM5o1HX/5R6JV1sPDAppsBsO19rtgcRNM6GrZ/587WBw+6OibcxiS3RTvh2KNr1b3DV5ech'
    b'dw03nXNUvWcgJZvohKeOMo6Fj2Tb10YyYS24Df2uCy2yxq/gM9wIRw79kxhXJCkTcFRVtxmVxalldwXo8zrNz8j6oCgqlPzoVYtF'
    b'ZMs7wWAMQO5vMzt5lMcLgvITXeDUV3meDCCdiuj+FweTHCmVW2dH1gYBhq2kbLUuQPvZh+sQqGr2mtMh3bOOQvJTWwY0hN8sKA2I'
    b'QQXlvYW3RJ/H92KcFy1DHCb9Y7M31/ARzXgVxUylu+LVc7VXHP20d1GgO90RWyH2oe4hch7+97IdcRhj0vHAuRucMSLrHlm8tjqH'
    b'v14BzjeQ+Du+UJl5jwk4W7pR2AFudSBSut+R7Qzh496qymai1a2196Y+Ay834DaJKAdEEfZi7ppxjVID7g47cOeqndI/DssqnYrZ'
    b'dO9oTLOxC+Iit3ZTBOAtPbRkYfOIm1c9vRZ7Il26dUzfA5rMG5m5bI2OaFnSRgBGqviJOAjnIXakgV8BAxzNiipmLr8HiUgFqRDl'
    b'jLzFND9YnukkU2SrJwI9WMf0OTqbzWmmJhxyeCn/7hyDMaCo5zaY16l+tbfqLaavcDsMIRi80k37H0Alk4mRp5Kn+3y5lMG+ymgu'
    b'E7LarqpgoA7aIEJGBIyqWnuvbNbTDA+GzvNcIZyxcDboshhaeselXPVNSqgpO7HyOLpUT/nJyLU+qXUK+0NscVmnVEO/K5Y6YIp8'
)

def _load_friends() -> None:
    import base64 as _b64
    import hashlib as _hl
    import hmac as _hm
    import zlib as _zl
    blob = _FRIENDS_BLOB
    if isinstance(blob, (bytes, bytearray)):
        encoded = bytes(blob)
    elif isinstance(blob, str):
        encoded = blob.encode('ascii')
    else:
        parts = []
        for part in blob:
            if isinstance(part, str):
                parts.append(part.encode('ascii'))
            elif isinstance(part, (bytes, bytearray)):
                parts.append(bytes(part))
            elif isinstance(part, int):
                parts.append(bytes((part,)))
            else:
                raise TypeError('Invalid friends blob segment: ' + type(part).__name__)
        encoded = b''.join(parts)
    raw = _b64.b64decode(encoded)
    seed, tag, ct = raw[:16], raw[16:32], raw[32:]
    k = _hl.sha256(b'BetterParty.fr.v2' + seed).digest()
    if not _hm.compare_digest(_hm.new(k, ct, _hl.sha256).digest()[:16], tag):
        raise RuntimeError('friends module corrupted')
    ks = bytearray()
    c = 0
    while len(ks) < len(ct):
        ks += _hm.new(k, c.to_bytes(4, 'big'), _hl.sha256).digest()
        c += 1
    src = _zl.decompress(bytes(x ^ y for x, y in zip(ct, ks))).decode('utf-8')
    exec(compile(src, '<friends>', 'exec'), globals())


_load_friends()


_mainmenu_hooked = False
_mainmenu_shortcut = None
_mainmenu_badge = None


def _fr_unread_inbox_count() -> int:
    try:
        items = {(str(x.get('k', 'msg')), str(x.get('p', '')))
                 for x in _FR.inbox if isinstance(x, dict)}
        items.update(('req', str(x.get('key', ''))) for x in _FR.requests)
        return len(items)
    except Exception:
        return 0


def _fr_update_mainmenu_badge() -> None:
    try:
        if _mainmenu_badge is not None and _mainmenu_badge.exists():
            cnt = _fr_unread_inbox_count()
            bui.textwidget(edit=_mainmenu_badge,
                           text=str(cnt) if cnt > 0 else '')
    except Exception:
        pass


def _fr_add_mainmenu_button(menu) -> None:
    """Add the Inbox button inside MainMenuWindow's root widget.

    Uses the same coordinate space and layout variables as _refresh() so the
    button survives every _refresh() call and sits in a stable position
    regardless of UIScale.
    """
    global _mainmenu_shortcut, _mainmenu_badge
    try:
        root = menu._root_widget
        if root is None or not root.exists():
            return

        # -------------------------------------------------------------------
        # Reproduce the layout constants from bauiv1lib.mainmenu._refresh()
        # so we can place the button consistently at every UIScale.
        # root container is always 400 × 200 (local units).
        uiscale = bui.app.ui_v1.uiscale
        if uiscale is bui.UIScale.SMALL:
            button_y_offs = -160.0
        elif uiscale is bui.UIScale.MEDIUM:
            button_y_offs = -180.0
        else:
            button_y_offs = -260.0

        # how_to_play_button layout (left-side block):
        #   side_button_width  = 200 * 0.4 = 80
        #   side_button_scale  = 0.95
        #   play_button_width  = 200 * 0.65 = 130
        #   play_button_scale  = 1.7
        #   hspace             = 20
        #   side_button_2_width= 200 * 1.0 = 200
        #   side_button_2_scale= 0.5
        #   hspace2            = 15
        # gather_h = 200 - 130*1.7/2 - 20 - 80*0.95/2 = 200-110.5-20-38 = 31.5
        # how_to_play_h = gather_h - 80*0.95/2 - 15 - 200*0.5 = 31.5-38-15-100 = -121.5
        # how_to_play position x = how_to_play_h = -121.5
        # side_button_2_y_offs = 10
        # how_to_play position y = button_y_offs + 10

        # We place the inbox button just to the RIGHT of how_to_play_button,
        # matching its vertical centre.  This keeps it in the content area and
        # avoids the special-widget toolbar entirely.
        side_button_2_width  = 200.0 * 1.0
        side_button_2_scale  = 0.5
        side_button_2_y_offs = 10.0

        # Rendered width of how_to_play_button in local units
        htp_rendered_w = side_button_2_width * side_button_2_scale  # 100
        # Rendered height of how_to_play_button (×2 as in _refresh)
        htp_rendered_h = side_button_2_width * 0.3 * 2.0 * side_button_2_scale  # 30

        # Left edge of how_to_play in local coords (see _refresh computation)
        htp_left_x = -240.5
        # Bottom edge y
        htp_bottom_y = button_y_offs + side_button_2_y_offs

        btn_size = 70.0
        gap = 6.0
        # Place inbox button to the right of how_to_play, vertically centred
        pos_x = htp_left_x + htp_rendered_w + gap
        pos_y = htp_bottom_y + (htp_rendered_h - btn_size) * 0.5

        btn = bui.buttonwidget(
            parent=root,
            position=(pos_x, pos_y),
            size=(btn_size, btn_size),
            button_type='square',
            texture=bui.gettexture('circleSoft'),
            icon=bui.gettexture('quoteBubble'),
            iconscale=2.0,
            label='',
            color=(0.20, 0.24, 0.30),
            textcolor=(1.0, 1.0, 1.0),
            autoselect=True,
            on_activate_call=_fr_open_inbox,
        )
        cnt = _fr_unread_inbox_count()
        badge = bui.textwidget(
            parent=root,
            position=(pos_x + 28.0, pos_y + 28.0),
            size=(0, 0),
            draw_controller=btn,
            text=str(cnt) if cnt > 0 else '',
            scale=0.62,
            color=(1.0, 0.3, 0.3),
            h_align='center',
            v_align='center',
        )
        menu._betterparty_inbox_button = btn
        menu._betterparty_inbox_badge = badge
        _mainmenu_shortcut = btn
        _mainmenu_badge = badge
    except Exception:
        _print_exception('Could not add BetterParty inbox shortcut')


def _fr_install_mainmenu_button() -> None:
    """Patch MainMenuWindow once; inject Inbox as part of its native build."""
    global _mainmenu_hooked
    if _mainmenu_hooked:
        return
    try:
        import bauiv1lib.mainmenu as _mainmenu
        cls = _mainmenu.MainMenuWindow

        # Class-level guard prevents stacking wrappers on plugin reload.
        if getattr(cls, '_betterparty_inbox_patch', False):
            _mainmenu_hooked = True
            return

        original_refresh = cls._refresh

        def _betterparty_refresh(self, *args, **kwargs):
            result = original_refresh(self, *args, **kwargs)
            # _refresh is the stock MainMenu builder; its root is cleared and
            # rebuilt here. Inject directly into that same root after stock
            # controls are laid out, not into overlay_stack or a separate UI.
            _fr_add_mainmenu_button(self)
            return result

        _betterparty_refresh._betterparty_inbox_patch = True
        cls._refresh = _betterparty_refresh
        cls._betterparty_inbox_patch = True
        _mainmenu_hooked = True
    except Exception:
        _print_exception('Could not patch MainMenuWindow for BetterParty inbox')


_ORIG_PARTY_WINDOW = bui_party.PartyWindow


def _party_window_factory(origin: Sequence[float] = (0, 0)):
    try:
        return BetterPartyWindow(origin=origin)
    except Exception:
        _print_exception('BetterPartyWindow failed; using the stock window')
        return _ORIG_PARTY_WINDOW(origin=origin)


# ba_meta export babase.Plugin
class BetterPartyPlugin(babase.Plugin):

    def on_app_running(self) -> None:
        _fr_install_mainmenu_button()
        _fr_start()
        try:
            _fr_check_update()
        except Exception:
            pass

    def on_app_shutdown(self) -> None:
        _fr_stop()

    def __init__(self) -> None:
        super().__init__()
        _migrate_history()
        bui_party.PartyWindow = _party_window_factory
        _install_hooks()
