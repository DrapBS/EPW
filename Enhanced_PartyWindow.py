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

__version__ = 'v1.6'


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
    b'BhjyEjucsCtYD6WycruYFeI2IEFKMvryZUUZu8SyClDavuhHMY+zm5CJ7+XnnGsPOhg5sTh0+LEi9Fjp6wk7DplgEqeldAWpIN6l'
    b'yJwQMOOHWEDhx+EzDVCIUORuwpFscytIRrZ4yD9p+B4j8Vv+RLVfPx2sp75EYZChEIHxzPhSIztThQrL+Wz2NxKspieBku+KWp9W'
    b'scmvejCoWlicDRXNnucB7GBQz2Y/a6hpbSQHCMboueeuZMCLh0Ghic/SouawYGS5F5VKfYqrc7vjueVSvBU5rC0t5QSWlULZkZaj'
    b'PpZux8fZMBViIrW3qvJJ+/j2/XEzm/vgts7xsjoY6nfnLOTPzk7elDpTQnJYmq7WuN8wpMlQe/vLPF2q3CE6uvuQAl0cz7YEopTQ'
    b'wRuPmQ7jhKaj3gU1dh2mH1ZQC+n11Au+WWjCQH2QqkL/B/1bXnNc2WQRoc9rtaP8zjwPtpqGuuauAhSTpz+oJvV1lJ24mwWoOTcs'
    b'hPdb4gKZ8joaacW5pqKapczvdBhPMgxD8q+dXmWdkuU/LoSwbY7ChSU3ICvUeSCE73UaT8MtDi4P75mWT04JL0fVWmbJkuTcTUkP'
    b'MTekrrchPXhWJCNTbQ6p4R/BHkyyP2PE6LK9j//05EZqjES4GoJw3pP5oKOSZF3IsCvps0nyXld9x7JF/IdX7OLyHDJDW6uPAxcI'
    b'SdoDrdfZsaBTtX6DZ0QVkmfphRVuBQskPhsONDUJLuaCGN1DMVn+NxpwBQ/EpLU+Nu59lL5VoeosDZ+MBLLOvMG5QvTsJbuGvRl+'
    b'rfZl7NGbbiiqakYmUl1KHFWMWQEZyUEimIw0QR+NgvrEWR0oJf+IiX2F3f3e/NF/ooHNqxKFmw0/LwY5ByhLzD11jVfy0aGyiNK9'
    b'slWY0FAV9od49JBJKcQIOOMVqwNHICWyZbaB/aJ1+gUb7xRj0SBLxWMBKUEtxET4HX+82YAw1+C6qfm6GQKYsOMhbWe2I5WiX+fq'
    b'8QbB+Kng/pZdGQ0nbp/b9HliS2WrfFy7b5kLZCmAIYYXEHv42BxZJttla0OTnz6YHc/EFWO9xwHqCnSi7sgu41ILaG9xhqFRTOLO'
    b'WApxDOBZ8x9ENi5YfbwRIffNgqVisdaZJUf7x2S7rf/DQPoJunC5dQBbi6t4XASi3jj4BBo0zBQvKq/Nc+n9jI3H1C1nd1ZYOaqy'
    b'7dTDRXh21B3Rmb/w/2Ff5uIsAtjtKEOyCarNkCGKR0JzXQ0mKFEg7BQbfJ5RFoZtlYVAEPmVzkmrelNF5eKt6GpklZryPHQvcU0F'
    b'75gwSj5IQNYKGHMurvXrGO+zMLM8NztKSqMMJH7Pf6+uvRu01Z4N5NdZ6g5gjQqwxAEOIl+gEbqg8JGOtbHGYJ/vRmNttdJnFqQC'
    b'++lZs5nFyTKgi1WHVtq+MSd16AUCiOgt3Ahnvhn1C5xdJ/OlGFfZLBYL05kP4n/oQqIqV3FiG4qm0rutMiFEi3Qz8lBaRFM5mI9p'
    b'h7cWgDYhrxlt0ht6Ua1uqJPhTMqKFvmkegeLzbure813zR0l1TnWggJjzEyD774VNLwyq5NYDfJzuRsHQxGL56fNGkEhWw+a2X+U'
    b'htR6f5iVDZOF/XSCKdek8HTMdnt9lm/PPu75rvror0O3KoZJ1smTbQcoXnYkg1/mfBN/zxr5EKtDLGttm2NH1kxfYfpEVRSsIZyE'
    b'0WEXq7CCFPbjgOUcxTil65K8+2WOAstvn13E+C6MFxxpY7s/yb/nJz0zkk2h8/p4nRxVgfcUyMrr4laBwNJd7GJmUD8Ukd/bmRBj'
    b'ObPozfgO8ose/6GjFUnzfx+8phDYKyRMo5tmzRDh4IYPNT9kl5jBRSlXGmloJvYL1RS0sXkytzfieB1QwwNhqwzC5qN6p0UjA+Rm'
    b'/fzYr5WAAwfxhKHYtdw8lDZZNA52As60LDsDyg2hjy7wY2WQ46ORxbrLZmT4jxWJquEAPumGFjGj7KEYUT7Q9G1wfFYI1tQ0vmQv'
    b'vsUu/kro7BVu3XF0Pus1faKj9NDs34LDKOqmDM98pGbvnfmOWthcRMX1RpsYz25ytWY/exv/ikZqKOUFYPRUnXNoNWCW/h0kaUFJ'
    b'UzBzaCP26s7KOlmiSwTG4VVHz2xuzRxSK+ZtKvXLOfIm+ePw9DUQoxC8nRW63Ts0iIEqO5QObMLpAsJdkdCiYMGbLzPEGxchFqhF'
    b'looW2QpOqWt4FztLWVm4DTo3JaOws439UWbM/Q67z0vm5RfldtFRdngkbps9Ryd4+XeRLUbqjYbAgr000cLOYIWSkFlGVBWgj5T9'
    b'Y5TBVPbYgNlTfWuOC5Q9IwJOh3L3KXN7GNCLlucXgwlTYJzgGpjLB0tqkd6qP8iFhFjZFeVlQfj8UEBuMCMMPADT+IPgguXEdb9u'
    b'AjWqZrvB4ZcGuNY5VPALOLza8O2RSfpMCgX7wCx8hbiAxD42gCjgvjYjG9xI627T3hP9/VjWPbDI1zGBg4jBJ60HFW6a14b15qdo'
    b'kbuwDkKOFN8qJmvKS9R4PCdHih4yJCyZVNxvFJNguRaZTXqLRuA4onXMhGcmX9YO+LzlH+vYdwHeTQysDVr++Z5ngxaFapMk5/iu'
    b'4MQGTEg24htuWDaK6WZCuc/VLYrDQM/REYv5YmjyvxosnwwqM1JZRtxbntEKDZfMY5KdkmJh8MkJSR9xmVapJDShJ9aI9rlDKiqN'
    b'R1IKCmOOp0pnWWKEcAIVrBADYj0NI9JPhT3sjguoSFDoPNerxUCDstRYXguvtOxt2pJA1OhVLHcz3bTfuNTIt4CRQrfumriRG5hJ'
    b'cudQamlSYyenAOS/e5hS/vmbgoaaba6yzeu4ZrZt7jrhzWoOGCB9ggJ9IvMRRD+SjOFDvYSrWjlURhqajCLd4FHoSh2CoelMC4Bb'
    b'IYJkkJOLyN+K5FMw1bcWb0sja1iqDurlQ5eFZMyX9VGQ0S/Jl3//9a13Ac8jinDMVvv5VMj6taoSpxlzvTOG+iMBg/Hsx9adoVdp'
    b'34QuwFW5z1qnuH9T6N0X/g75syifKqTSNuFDW+/Mm7i80qudvkaZ3wcKH4DgEOBxfm/2bGTijAnOw3gDrqwukLtCwd8O11q8O56i'
    b'pIFzJ+U0/m5r3hezEsCJo7k7USKWdM9z15pYV73VGrwpIu1Ie8CUmrUN98HErX0nq6mF/NowRYnIUhEB+8K0MjhY1U5x2u0ULNVQ'
    b'vnkqoZKKaMIjDvAGNsUEabtblMgfeuxAu4S6PckF0+0b2uw5sqdf1c8nbeLqueonKZVYXmN45/lTnlgl1ZQPX9xeeEqr8zpk/eLp'
    b'/XJ1a2njZ5NFH8s6rkmf61xXrvofweMhuGPDJstNbdYfCIjf3U64a+UM4tZUK2kinN9O5hHDVzJGJPXwXycr4X6K77FyyZXmP6rs'
    b'0aZyRgWXw1i1RxXtxmeJZHzNypinxp0tPQWw2xVSuEX08QZ1oha3ZY2Ad81ybrOXdVn6xk2KS75cnuPASPr/kuIAgSWQkrwKQpli'
    b'4GisRa77PEbDIq+zHQI5NBtdP4ck+m7dbqd9nYevDWejKM9/ZUT3T5FahPG3xQsud2PMEo8wtkMdO4v6zm+1JjO/xQ43SR/0dUPz'
    b'l5T8BlDbHNEuXgCLQIaH+f/5GdGSBz0tFS1YoBVsFfHWYrpzAAFSvVNSuT9qgs5o2qTUJgzFH8+k1RdxvSvyJVRYZNz6bcidG+4W'
    b'SSf93NCki+5QvH0FIzy/C7vSNtg+p3uI8a8vFKxOgVhEu7k/RauTNfrhmXnMz86a0cLffD6dRoeSDOublZY26uupdB6ere/8pKhD'
    b'PLknilBS/L3g8/p3sYM33orTp8DRletb1j8jjLQj3ZBF0V3fX6LHrOc+ex4ukxLyPpz49Grt89T+1vKQ+2sl5toDB7lI0YY4iQEK'
    b'RrWd8AMWektsGuQ3/UIEOu8uLxaO4FnuafmCBWq5r7V0fru7R2KAiyCxvU7UzRCm6OeYKL6ntuoji1RRTS6CrBINy4QLl/z+kU6w'
    b'2oWfXmFwHKIttBEj8A+OsJeHV5IGGvQ32AfxjMdKK3ttY90Kx+YH6fHhFBe92ulnPHa68eD1TMztB7Ws2NxFymhfO6s74pQ32OB4'
    b'gOVgTAtNNtg3J7gXKUaA7Mqtn1SsFfKDD9Ji5bIhLZ14HVKvjWU+KGKzH33VYQskELwN1jjzlyMthR+6m0qgPQUuDE5oV9NH7RW9'
    b'WakLPzUjQwvOOYzOJ+V7tMSiKIN7j+VaMzWeoK+dkMZh9sYdz64HiKSL+grEcI0iWw2GC96r/UGJZxLB80LYvlaZGzmHyCTedMpX'
    b'DDtTxVVuyAJF+6PGveQZDJIT+WM5Gink/PISzEj5WDIfkvBwC+lCRFeNiM/yNSTxXujIVceG8ntDaRl3hPFYLRRAFaoCW43gUDVA'
    b'86l5gMB9ELHR/wwl/dVp2eGNzOzI6D80NpKhuYhFBqTW0gzr3DAWSx75kHx+6rB+dfwSHut3xvPSeF/Cl8p/ZmLwAakEA14QBgDb'
    b'0tQXEAD2SDfegThALmaL7oFTtQzQwD5kvEcSVDhlPOfBpQNelOwfKkkDJSIxCGr6L4CerbMRdjtSnvrNlYP7XxIFoFX1/g14g1jd'
    b'ojBqHFgiZ56E+/WfrIzkNk8TdPRWv78n7j5SNrmBhxxIIKa/H3nRemn2cb+mCzy3EvYTuAp7k9QKCaFLWrCJBgKAeNjiIw8Uv70+'
    b'lgLD/KcxMhDNQFQ6kkH57zEX605mhlzle0cWD/TVMteT6fPAMHb9gPTb5BumUGkyo70ZJ9pKMiEYOA99ng6ZENoZiNN7gUYoKiD3'
    b'dO2yfLpSFHYkJqtS5fq3/xdjB/s8DFBV+q3scznHTkNzK2ZCRIdJm+w/OFM8o8eoyU0CjlfM8SLpNG2ASVInITLevAWyQN2BuD/x'
    b'iRTTqjP+6foQgM6NAM9HN7qo2oAZ3bvp7azWADiR+XCCWrG5PdrKajUHEM1vBgjGMc/GTirEPuNdT+voJ1vdHkdwN/11o/v29F4f'
    b'bvWbmNpeRK34K5HYsq3hukk5i8HqUBba80lIu9K3CYOfWSDzoqN3acjDNkgNi59QunEr0I3PKnq5ugP66/w8tMrx2u3jmzex3Cyy'
    b'IzhH7kKa7/fju5xvxt9pziU3pcGuYEAbdOPtMBG214DVCzyRSIH4WrSHFArYe3oM/P0Bu0obinyzNbtjCmmaql7UUVs7akDvG7R1'
    b'wj5kJ9Bw1ZSwJZRCcw34tSQY2JCGuBQECdVBwn8AkNE0EmXz0042SZVzG4QXTXDWQqbCyKpQhKFs21S9aTL/ueO/DBbQhHjEUJ+b'
    b'Ec7SH9pY3afvcvbIvPH2RQVCk4ndlTLM+bh0DGrY1xFPMLeSStcCpW8sN0ZZwi6NDSsu62XChFcGTBv3beSutKm5YClV+6wih497'
    b'ODidCG2NvAEmITPLYZXJIjAJoQXLfxGQ13E4pPh68lWYx1WS0sJaqbIx0KDksFDog4F2uFj0fuk8JHr+nZLUtDO9vqT7lPLrXpdl'
    b'pmSJazjuW7dF+PjUm4oU0zjrKSoDqGYrFiIMO3SymRRBxWkdYe/RHGPe12o/lRzVDeorM8TuqUo5FZpVtNgqEozWmCBXI6sTrQvc'
    b'DirZDaHNrk0WOxcJ4WOwckrB+l1J2+6JSZCE990KtChWcMLFEz+4nJa/DYRyR0V2pKE/nqQ3AFhYeihXB39dfkpfbBFr3Im9ydQt'
    b'+gkxSn7d0flViVHTwxCpJT9Smaqt68/yZ0gGzapxXEwNs/4WHDb2sKM1eI3/VU8oc682FQw19QbHU+ZcCVNGnsMk9aloGU/ELN3v'
    b'Dztv7YIuazUfiRf4uKsK7sU/jCb27tbHKCkfVR+CNp5uSWVHBoCSC+qV2kEpF6OdSqIvpfI4PArYI1UDzuZLropRlryPn7BD7M0i'
    b'MDi1h1/GQAxN8hTiIW2InLQnAnVQJ7zEe99BOZbxbX/JkQdecEoxVoTfB6zq5DLZHH0Jm2YUJJflcaoc0BR1s/WsAaqHPx3hKIx0'
    b'qb3wNG97npPndJdSR2n5cwxuhSalvBoXXBH9w+OgC+qPE+xJ5AEnJ38oev1vOfr0TlCIDAjlgCI/JDKNjuSvUGV/33rBsvGzKy6w'
    b'JD1fWNdwfzTL5qk8ykZLmeOBzmpWWmis3iDN8Pi+c+zfTz7bepaIabOVMKTXd1RAHFSwLWJIxyu6dNYPPkcFQeXKOa9IlabBDUru'
    b'PiLbZ/0PuKJ/Jtx53VHZpu+aK2UZzvoMI8HS5CXRY8tdWkghMFdLC6l37L5e1Mzuea2pLwyl/BLJCVbsgX3fagYCvfl4sZlNXiil'
    b'54xT4j2pyP43WvhCQHPBZaLG/UAvjNdKvlMg41nkedVTux4berPtCmrPmDAGCdb7berqqVa2rY6uHNTifPMBQrOMtYlAsZGafK7H'
    b'zYdn9xpneCgxDswUgEfCMova38ZArIubqiH1cCo7l5c1+PRJ7XH3KWVR9iHfOITBVaDlIbS9GFzT0MdQgxrwBRoVSCteUPwIMxCd'
    b'lCxYNOc5cH2Lvt5w1r8gF0dMcxk/6RAR8kbM3UWYp1vza7B071HdVdVHL2HbRMMiCLo5dsHKxY0f2+o93cGjvca+dPSdZZCR4rd7'
    b'59u2j4VHkpS0eED0L7nYWoLe+mOCoAAQcmuoVaEgH9t4bPU80tJqOiM4DciWSg2HVKDPBV0QnvIJTTEnnHHqvUUI+E41lIT1tRs5'
    b'CZBPa67mRe5mdLFlEckom7upp4DO17liGrVxWYuc8iBmhJj4r2PkztxULlzJmYNiTBTpYkhg/8Qy07iSHsYh9nzF/ajn+eOG9of8'
    b'WJfwPKNQXzYbvuthepn3fs2EspQB2zin+h7dRVPc7FKLqNc8AzCrp4CLb6EyG6JwEz7VuRpi2MQiWTxq42Q5nJpte9KEddBFGiMF'
    b'Y7NwwmV6eR+NCNu0DyR5vmmGCLFZa1kUJv286IR1titVSTTZQMPi3Gvr8COHkprwaDLKPFmXK0H8qdQ//NbUp36LWrgBLnl4c/zv'
    b'1oFVF1fUHzTIwBJBuQOZjv51c/hLph7REyza7f62mBvnVqMh1ZPiQWrB3u05ZjHPxOPxTxYTXXxtnFQu3IvKB96BJ2f77ckAg0o6'
    b'bsM4SyVeky05soL+GOzbRHskKUuCsQPBGNnJslkvJX1HwGSqbkJFYX76R2lfm8MoZGH6NRUwE2+UfUnic6igRV6eujZdga10NGs7'
    b'PFx/ohmRw3qAkDj15jR0m/2jwLJYq3qsNcyNMca5dtb+0NU53SP+81/EZjo69Bg+6zp5NKHZaKTj+RV6d6gPTYKqh8YYJzGkaquX'
    b'1nD8FZ1sm2BFls7rCNaZtE7MwU1YAW8CnG8Ko207JvTSX0C3dgkLAY8Ugmai7Lde+yywwIPnSNoCaf68C2YR1aM5TzU1gHupu6Bf'
    b'j9xXxBOvaF31SXPxd/+yMwuyp/Y9WZIFNigRXi26Vehj5EtAjGV9s61W2mjd3vguEms4ojaZeddP4/AKg/sTfuOKttc6wJirNnjy'
    b'pqtZKPGaw5ZgTeaP+wNfMsB30YHMMznNKIU/IzIsNIqjA2A+ZyobnJwQFdXfklZL1lu1qtMVJ0j+3i7F1cf2nzYxQnN6YcXwc3ME'
    b'1cDXuB8m0JC5Q/OI+UqSqWl7CE2dpBL/7bdqY924IvbbN3w2kWzQr3jnp61gt8r3+DBjXmr2DKxTlwKxo3ILjBsBWzIUrGatJRNd'
    b'Tx1ktKdbK8UPUVT6lUrYIdD/CuG+mK183C8GzWepAyIRgU9J5p7KJZHbT3F9jIPa7/GPDNQbUfDh3GXwXXne4WZI3MBJilCvDsK4'
    b'XdJDnNXQTpYAhlbJiUcKhxBrtCr3h0dqAuxxJLqjVVRlUVROxHZMLzQgJu8i6YXmq2Q9KpoI/wJMNopo5SjnUPE+NL00y8GvT7NC'
    b'+58Xy7scy4gd917HpqAwVUkPqgNonf+V0Il3VkT3Nbox+4gC0E3oZeEQ/QadW7+ZT+nkcmV24tNuo4/RiTPH1OWjfxB1Ze8/vnBG'
    b'Hu8Sju6upMER/064XUEiB85Z9zpLqtrHdO25PBOCIUoFWnepmInh3ttnAQ/hwv74haBQ+UYrim9bxQWDTn4ElGDiREibd2YXlnkC'
    b'NYd5AAiVMxJOa8r45n2FHXwtnJs/VkcH42HGNIp47FNGUy5nq5vSQHqYOCXOGTpHuKZYwGGcNh8F+0JlZ6RW53aOkcMxJ0cdR4Fq'
    b'bJH6tJtRlVgKGgTe6GVBZpOosa58NHRk59GDokZWUQCSXv6P2nxkQ1CH//QlKSxiPECU+KZAzKy0IVL19ye/bKR0wukzAGjNnyR9'
    b'Jai8CzGzMo0wF5ALL5wGxIh0hfq6xjRSL/ihYn6jyRLi0rsNkmwQyBZGiU0PJje8H/hX9Ib6DGyAF+ro3b36kCNicTHbZ0JocCue'
    b'0gvMWhynZLzbOdhc8uea+z/avwLJGEO2+cB4fZ+C8HPki4v7KP4Uv0SY7wEnNPkdpKyF75jvWTRvbB9TdUFPHZn9X5HScz7lsNYV'
    b'zg+gjr9bKk6i7Q/Wk7FTzutP5Ruk8lJL1+mmb7PselG50xxxJiw/o9JPNbpU64MpPGTLHb9jjz9iHIQ5QVtr102Pzf7X3+7CUcI3'
    b'ov2iWrnjbyWlldP2XxCtgosVhHe/TI+AV1fPf5RJcmsVhwB2knYyEFuIJMf++uZq0veTf+i1B47tx10MpJqDNeBAAbgntsVr2BCc'
    b'NzvYfYTXkfpHj5qpLQkNRRJS4JEbeX1X6FUsBRy2NcVVVzJOZreLnycOBveC08inHKIztdAIoULL777vRvIh+FlMupOiqKDwdJsg'
    b'vvglRUNoDzeF+34VR0FrhqMw8hNrx+IsMin06rBriCXcfYTGV7EgU5rhU6GgO1++6taUF92LryFGL2vK5ana+Zcv3CVJqerKy1A5'
    b'VJ3cXa46X1R3Gu8DvKV6LMLPkn05z3nHWRi9yC47Rz/TLZHjDdkPoK0EuKtDlKcWLNCVFe07xjE3in9vYqjl4U5Ej0/NbFxFaJJa'
    b'F3tJQel8awni7EHyzIZd5pJYXD7cFNwvJ7yKdAAkd+7kDL8B/tHwn+0XdV8Oq0ilKU/GOfhgjXSwyFNLP0tV5Oeig2xu/xPzF0bO'
    b'0BWMItgmpDt8hT2XxpI65Gxx/AdbyesrxiLWjJLXHKZrviTlcYlOyZ2Wr06omddl42Kf1xlKgfHXZcdWEDQ42x2dGSiFleN642EE'
    b'RXH+FxzBK5of46QJ7rF+sgEP8M5O5Fi+GIcYK8dEeXSvmOI3+/2htUGlTSuU7EIavN14oqnWI7RuVM+xy1UUDAc2en/kYM7Nv5hE'
    b'svwC5c7SEp6Gt1Gr6s6P+CIFWqHMPlhn4jrRwQzOymFqqCCGjS6vqHcOxWbkm8x9ESTPlXwvLk1j0K2ajdxst+Ak5N/xEeCNnKG/'
    b'FCJ/yUak+1N8mAlLTdbY+/EmU+0WF/yc+2bQXCENCKf0OxT4eFX3y4ZgMUySgfufG/4UOVWtlDBS/dN9s1g505sB4oOUS2ZZWOUd'
    b'vSdGPlkFvsExR/U0hPhwmQbyPVeyDKmNzn/hTVoPyoHBRVhEcyl9RNadksTU+gCga1XZI9uzfAyztHuL/cX3hybzxKwItu/o7/tT'
    b'A0Kel41CiwLTm7ayIyOcccBbUFBl5k1hITeuhREBx2fI1sMO17VFtvDoxdtCoxc/FYfwNcqcS3lyp9X2KY12bepJzzitrMJO3SuM'
    b'F1/8KNJ7Ia3BXahQMNfZe5U/3RFV2Xj3ts60nbRzgrPlrOjBBZjB2rLNR0cWAujEQ9QFnZyToQF9DmceqIgm9xJwfPKs1N8kUBbh'
    b'PDTfSBktm1iDnbexbrrDA4KUp3yVRvSRj40pa2teplNpVK/Y8Yl56Op8U66a79vyrLEjQVVFRMvz49q/tqUHrIJbU3m5RxePqmwa'
    b'sqgbmdPViMHYV6PIZaHvMoCo0oGnCUpYX6DOubRl4/LeBv7Tx/na2pwSk2pahS+nvtBxjK+FdV4VB8NA3YezkDHkpStfGtKbGvx0'
    b'q79WqnblZcqaqIWsXRAsYsOBIG9dgp5pPSlr9LWDTuFDMsQuXxw2vNTjHNVEDeFnmMeP6gyyG1388lu/JaSAPAQmk5lBmSZSjz+f'
    b'PizgmLW6Nv5IusD82IEueKW+jCWsgb204mwUBrDv8VqRXdTSi99ta89d1DpItGv96XWDQvBuY1y6/KkDdeXk1cMlU31pKeDtBse1'
    b'HUwTjKIgqvlAECrRXjdBHsHhdyXfck/zfVbkxz8R9uQeORVeMJVObqUgIrtMlly56wmEJHilSejJZVADUJqoHUYUI7k65aNqxzEp'
    b'9hJK6xQuDybNTalqYlLOmG0BshFH3HnyHW+O77LGMG6MRtlPswq3FdAHE/OoSIphUfGlfvhiwFeacAjbW1SGB3JRF07JVaKzDBgR'
    b'6Yk25zAbcSxkMOu7OauQXI3uwrCiDXGf5ZRRoqtkY2jrVHdb0M0/XM9HRPzE4R7dqbtLrl6Uh5MmYUdMgfk20RgbJZdPoX2ualCw'
    b'yhpBw1FzX/RUzsV+iM76BK7Vp1mIj18jBBeJYyAsrHL/BmmhAOcrIx1gX/4vBTFzLYaIr/fSE6biif+osGF24QzMvga/60ImJf+x'
    b'EOGC550WPFM7Z6qyZzwHFk401Y71CvLH+/ctv2MdwqSKezZTLJdUDVZfvpkw55/d/FpWd5YKHDF8GBvm+PRf4JsPbfiJmb7bJYfq'
    b'Kkq5aHWy9L8N0rDDkGZLs4wTY009uU71nIyKx8nDaqel2pbA1cxOTls6xf92+05II8/EFJpo5ccqg7gHrT9fpyF+zSvJmPxHN4t2'
    b'bugCo7xNT4ygTyydNxHOMsma1pN3bWSU/XFDucyxLAaoHYbdYJN8V/X7iCBid96Z7cwPpWHdR2t6zct7utxF9Yw5vAOLgSwckCm4'
    b'F4exA/GGLXM5zk+/EbbS7UCYGgyO0CxqFm7lVozwIyg60jsmU7OkbFplaNp1UFx/b6snMHo74AVy3MhgIy+JYTW7X/WUo4EVr2fB'
    b'ajMBC1E2ikLgoJjK8d8NbXlcud9HwBKnhPSByXTe6VLBsl4XUIzmuBU+ZPrVYPDzJGjrWsI6Ygq0t8vDjTd2UqEKtUof2iQz1en+'
    b'iENpTdTtLhHULrT4fPWQur2OOxsfn2cA0Obctox2LCip1AC0bA2SPkrLkwfQ2Mc2sneqX7gKjprJWqV4XbskwHW8XL6Jul13SQ3G'
    b'JhaOiJCVkDLzWNUCPJfguq66Ndf+BApkmUpjfsUir4efG3+kOaFRH4or219WrY5KNlSoXObt77bPwD1Aiy+n3iXPJCrETZN8jY93'
    b'EdIObUOVH+Q+ebPsET4LJF2Dw+RQTs91hKRKgbP2W/4UHJrw2A0JpUJIN3P5hHbIz8WJHD3e8HkafYN84rZOI2S3gSfQVw0jg9cO'
    b'wfVgSowRdJ2CG9XGujBza8xTL3OwXuejUxxRALAtDBEisYaCklpYPiZivc0aAZySbXPNR3RP1gih8yROYRsMJEHfsJwuQHv+nwi/'
    b'3nnKmwEXkNyIFXqX7MzGWxoVlVHiWvnp5c0TYeO3UopJY8oagjaEAYZh5GhnWKVJJCchS/FV0FS6q7527ZX1WfJz5e857PezwiHg'
    b'YokqtSgL9psii9eNJ+Iut7aKJt9p1NO05vM969jC5DVvcnlYjZ1/0GMzphI5Kuu3sFyD7KfzJYnthu5nDrSqNOa8zeQA2k4Ry4ti'
    b'bdlCV+DoTlq3DderP9BORLov5psweVIkJg5qGW5B4Bu4ebAhDQ1JJbkXDj0rwo+uFFgwLo45qkVh2zkRv6DuBWOx3FHm1ulYRcx4'
    b'T+zc2Xdpel5WaK9iygzqlHxyIPdHHAjjKBsLDt1qAom07R+yGGu2i+3NMBYZf4DCWSntCCgynBcquVgyUGYQ9ZgsU0jv5gjyMDCn'
    b'SQiy1QtVW/E8RoznHP+4PiLJDn7cUvaaTFIJr6EVTQzUz55xII/ITb0hdfJIKNGWSNC22teBK3x758B0MON0AfWGIG7x+0bgyqC4'
    b'3FRrUV4e7WKjp/Gl8cHmrjiUCtHxTWDjarBHGTRXdKVQBJuwCWebTXwUty8//OcSXwSQ+YlCUbPJAuSUhSDE6TDDLum6YdKm4FEA'
    b'3Nu+szUupgRyThByae79S/NilRKKrvinWX4PZgL5+AOP8+1NekvaFOmIfyVbviS9eg4o7SCg5mIkF1j7anSndjD1uxRPgIPKpq6S'
    b'KAHkav/B3ZQUfHkHZ+WhA/yaGtSQVoeXyzhVTLR7Nfc5QoJtwk6tGhjjNEiD10sTD8GrUvQWH+OzK1aKzEGYrSbpNu2csaCM1Z/k'
    b'ITWNlQeejIjZe6RposfiiYMRsQ1CxGDLgAkTiTsXvw+bvB6X4/fcL2Oq65TfTQjSy7HcoIy73ToFSNsDld9f8BO3rxcj04w2AwIc'
    b'UkBzIlDW/DOa4LaUilKXa7uWfAeeTYJO68fmPRHa35+46kNZo6EYET34mY/dRpn4sYbg2KT7ZY7UX4V7LViQaan6Bb3Mw3xQEvTg'
    b'SvhOdM6PHoTG6bfVb//SOfrJ+4pHi1jg1gwHD0JEv9aqw8+C+Zk0oegJly57k0Ahf6SNBu40mMY1YKa/KYeqMJyMrKOpMbMIeo4a'
    b'AvnrCwNZ2e4O6v2PA0tpsZLDJZTxzuAPErlmfv3bezq1PKHYQ8mBe/agAFS8/DBQaRQ3EkYcHTuZRGyjrIV1pwi10X9eKhKB5mN2'
    b'oJVdFG0hojqbq3GCNE9XMT5MThuZo/d4+d9hnQDHcVSh/1zthRVsEA92Xd1I3nJwMg6pjVN0AFtKTGtpS0ayppXIw7Qi6QBSa4SH'
    b'OIfG+laHQRCa0wYSJ3FMNbW92MuydXKYEuW1S+Jb6iBZYlIO3sG55w9Tw5+Enb/QtEy8d9wDyQOITj8wZ41Dr1bFWESVEkG7lLho'
    b'3Hn7lPEU/yrv3vWQWVgK7L+5qkzmTlM5LBnq67Noqzcf3Wuy6iFgsQq+23/0kEdtHUQnT0Mw8/GXqcZFa6TZPJ0Va8ffbKxW2yJR'
    b'gtnXrI6NQkCsaDW/RS1iu6VBE6feKbzjo1Lo2vekDa7P2rmoAiN4r7ciwpor/4XLWxuiZKmfiRp3nCzTwkzjDx9DaCYkmTGgaO7r'
    b'jL3By5VU9pOHULrlEsfEfRgDJShUqUx1I0oPL+w8xJgjkS0c17nK0w4xWkMY15w+3se6T/7gfhllx06Dr4oSh+qMBGkBANef2kfF'
    b'PQffTisGk79xCSv0EH4DcHqQbdioyLqcROdYwVb2fjPMb3r1Q3rUcKYkesyMccBCMOf9InTkZzqiyZbxeADRojgPEB175Bu/Gg5v'
    b'lQ4KMmQU/kCRaKHoQDZAhAciTOTDKxJq9o6JluvsLJyWmFN0aBw9IrqYzhd6gW+RRsaIXgnDQg0K07KY1gbNjcBc3Rkg8E9hDLQF'
    b'6ptmdJEXoGog7sXA/qEqoSgHUxjSn/kd/EoVCzwMbPEGmA5j4IghgaUlJNRFgw+mH63tdVi2IGSpnFsWQ4r5FAMDMx39u1YlTxAZ'
    b'FbOuPzd2k48aU5ebObHtlZJG1ED5NVfEpqUT4ih/ru9kNOYScrGLH59d6GhsLKJErcqMqglJLrt7C4OF4ST7YvN97CmmDVRQJL2z'
    b'l7r9WeNNFZtNUhiyHTdeSXg7/GCuVAAEhr7ySsR/C34BQrWgMr5P2gkmpKX6bEiRMxeYcyxZfI/KBcSugUteZZAbCASkV8mdmYTm'
    b'+mfAivIRzqel8Eio3DbcbabrVYVKUhcMcankDoBtw/ufndb0cJAA2ghVfqK216C3sA/JQqLuR4RyCZEp7zfUkysUi3ydZpynrTCA'
    b'gsaaFYM5zupXS8kcwc8XYEunUo2AsfjSmQntd/jXdo0FDRCZbT5uCIbEeJj+cwZBypLeHnWsY6KEKx5xTA/0LY+vQnb8osTSas66'
    b'umyfSLbRovEO6YbVIG/GmUxNsRSg7/11gEVICcOmKC3Vo1OjznULHbttJmR+/DECd/PhUxUky0AwH6PBOPwjI7+GPFoFH5JsPlfb'
    b'Ih2GfXB9D8cQo9z/Tq1sxIIrE30pZCyXEFttcrF82LKxlxO/1I4rIQq0GE1f2SEEmgdM8lV0iKNgm3T4/OE+vh+3lu1OfxFxVxA8'
    b'Mbtbg4xTNCf+EcR/SNq5pt6idmYePg9XHmIr6dMpZHzUg7SZBmGirercppqvjrzCCJY2a35sBRPnm6Tl1zB04ziaO9Z7/1Gv0ksk'
    b'fcBVqUy6GDD+okIlxgBKiq3RZalmApt53j7n8/UVhCijfNzxWgOrjo6harJTPZIMSCHG8FXJaKCKIUY4iawtEdUvbjDXY9fyp9KX'
    b'cXd/jAjZ52fe2+QW5y5ZWDkgpavI4ZNvOqdGmLz4JBKscRqLvsDnVx80SgF9/0k4jvPrDNPNGDlM2BPuwV8ljFcCmN1GSGYWF+iA'
    b'I7D+Elrr5z4ZcqYw+vcjA/2Z8badBxDbTZzE42KKSQEI21qUtszhAoHDPEZC3NbnP+PnM4rLtBieWzMVaBRx5XPWImc5LHodFKkY'
    b'5MgGwQXvBpx48r+RH+lFvIGZD+IypuhrhIOEh7ZDcCtah+OGJMTSXggjqq2hDbQiXAlyKm61KMEGwsK7CB4CzZxXlzmnq4bHP8PU'
    b'mUrhCBzxQUNZGoaqJXR1Zat0yTV1gP4qizOlxXAgPUH7KDUsyOtZpGAbUvzMcFmZ4cX7n0Mpf2IHVIGeSvEdTbaKLotv22+HH6n/'
    b'U4+p7wCmxt86Zx+clXq31wexPIhD6URiJX/W9sDGVQwOLoBDTrdYFMoa/ueCpbD2tbvmFR8gXSEyUV9iLWhgED8vkRxn8YuuOpql'
    b'8zprp4I+njXw6lo88gLebm3DkJi41/mUSAG14f1sYqP34R9WQ6WE8kr9tiKAivl3vP3XHjwoi7MjHcW7LCCCBniuGU8o5wnQxtG9'
    b'Gt60clZDlO7RkQ3fhq/ARG36eiKZjrhHBLcesuBWEZwjrrMUoHSgyg6BHETK3a5nl9qqcZps4keOtYatgclumTZf6fGkwtzxvQb1'
    b'LxYjW4R2UT+jVoP69U51WWEXw4Y1YMEOYV31oZfuB37Q4QZJgomAklcik12u8AorgYr64WjIVBiTmxCFAXs4WQdOAu5h3O2fWwj0'
    b'lZNVWan/iv9F03P9Gr/EXETe2CGBZ8bOXfxt+3Jxjj+Gpu7iH5C2rgRV5FUigqvp4OGVlES0Tb2s3/diEX2+8aCMZL/9hBThYz1e'
    b'AERuLJd6xjAjQG5ZSYclgi9swsIVH9zEMOtu1JUwunQy8LnChggwuCRUf5y7CQr5S9tXQ+09PjfaY3BuwN/6YbZNE98rEoYwuvRF'
    b'xZOWEk5b0AcEPEfFNKDtTxsHiV1b8Vt+lZmi3eVF6MQYNrV5S7NRfQJx7uNkqbxzKHpapvKFjb/+DdeVTLU172X1sXPOiavEOSFm'
    b'SXI6p5KxS6WbBN/CZxaSK7nrhHTBs4kD3uHAuCsq+9xlM3sR2Bxd76HFivapMrrJqxbdODu7+JR1yRtPm/U/3WKzDf3pbUmma6hR'
    b'Si/0qc/qg5F3v10CD4PlegonuQhP1Xfm6S+yv79LgsymFTAdIivhnzp7L4Pq0AMkDka+Uvw0NkbGaObMFWPa/JJPlBTgrT/TQpHj'
    b'kox1uAXEFh+n8ZnzVPn6YxevxGiKATJXlYl8ggUOIl4hDIfNor+sSBitZ2Ww6SOzhyrByrxLCYkf+OcvgK/tzKaq3kLdgcHgH5pD'
    b'w8576pXlg6grpf6ipHqpFXw6ATH7E+ZUAonrbuiVqKgwxQNCl2zhakzJ1vWSK3/MXaati2aQ+QqS+u7YpWObY/gp2ExwyQjDBo0l'
    b'Xsnew2ckGlkgHyY+1YUT1kBVMX0OA4G4fpBjlj+o+phVP08nMa8MhlNsTNg9MK+clueYJMxQr00Kg9xbbnFCcwX18+9DanI/2fdX'
    b'ht+5wyMVAEHGU/RuRroj7PuN1D1whWpWSFWMdbxKDytNcWQbbQrCx0lmJgwoMyKAUCD2fWmQMAbZZv6j986gQK0pOLCjOF9gWmHD'
    b'N45s+Pbgw4ib+ppUT3axc241FOcT8/kF0j0+OSEe1HH5d23LqlbvBgneYvt4jMuzOdMTPiLsTiMMqKtnDESkI6YdZxoJRwmNAaht'
    b'CbVPJMNBljBrENcqJvCeqJuEDpJFTYw/gsZ0x2zYmmFp8BFNtfXIH0S1oO4CG9vW9wjNyrXTOA8qa15uOrM5N9k+z+KXD+O6mG+1'
    b'viNhpXmvbyD6WT+zhxWPUIp2y6eOALj+6V6kv2xHeiwBpVSrhnEsrOVN7NGXf25RZ8u5PdijHUK2lX0fUJCCV5CkeD5vIlN35swe'
    b'Axs0Lg3zEr1cWN5Q6NXq1RwhVptbMP8cXi/uugjYPqhPR3i6h7/qXGnjLZMSbhc8IZns1uo5ZZAWODpydsC01x6jnH8f/iC9L7Aq'
    b'UmiJRA7r8weVxLhSSL7cVPM6ZqacQ5s77FAAlyC3JbcF6e8dDGJ0Yt2hPR085XP7o56ySZhQ1rerd+ICPQERXLsWRfUd9VkbywJh'
    b'U+UQysvdkxhbH6t1tpcGnh25a8ftyavOH54mTxFxW3zlmIoObWhT8SEY+ivJS1Gl7JoF8gC+hIrKDYduuMBnBamXHoGvtHdSFLZ4'
    b'Sm+kEAbzsDFKV/bkARlyqQyHtNZpIuWvaa9rjE3FqeLnOp7Ak1OQEDsxfMGmZMxkXHoTm3HrreYK2euq2rSqfnhfpIqE79T/O8X6'
    b'ioHVhYJz/tj/RRCqZB37Ny6b64zlDYvn2GdyiNfqGIlLf/36AbUUaXT7gjztcrs1uPuPy7m9uqjnotuo1/5bVDgVUitELbMw4EmX'
    b'htpS6gwINTGao2pfodTx9rANxxYBrBinEJBMatQFTiZF9ALNjYeTy8rqRCcUxNbgoDnwcCZNfTTrXgqgiedArcoGV8n6ARjkXmVv'
    b'dglLxinVLjVzxo1ctduiCjJA2BqAyibpl3u5rxGuO5L2rqVLCerlXarlNDqJubIEsm06gtEvdsc/vEjhxDG7euExAcFflC3+zgR9'
    b'PFIjv38bsT7T016rPfs/PotPaxkGd9CM9ODeVEZ55Ect0M+bogSEB+hLlZjgaVoq53fofTgaXQfmO6axgdWwenoNfVgFOnyzrzKb'
    b'BgGRGwEPaDeBfQhdIqJgq6TXiDD2pamrWIGhKmkK4DqFZ4QtTdazAgExIADyKECRw6Yw86oDYmO1pVJyfiT37syHZviEtYazgjuF'
    b'XxWdK/PEhyJmL8Lpi1Be2VXe9iI8pmaR1U0g1aCx7P7EakTrr44wV05WPtn2LuGFfNg0YdOJCZ7yfjsR6q42gglNumZJCWH5benH'
    b'8uT403ngGS9wclEGvWFv4HDp2NqaOQF9OXEHY5lOhPloz0YRvujjpP9e25OAR4XruzgBqN3dXQSg1KiBCZ0kTj1TT/R4/azlYHA+'
    b'rzKW1ChYgfww4wnOfh0+vVZzo8MgXB3uF0ui2kBiBtPYDTzt8cVfpfTAKw9zOQt7D49Dg5Vc1c3gthX4+FVbnRdHSXt/WPO0V12A'
    b'l5EMThetVq89Ke+j6c+4pZQQDMJReXG1Z1moY1XcIOMuPWcXwpEuh/lEfzFfaz/9xLrG2JlP4aia34YrKzNW/wtx9ZLKKfLtj94R'
    b'ZT38tTCubZjGFjmoWbcbVG0Kor8RFkBORlchFZwRyV3Mqov9dG5/3YhMlwq290opejtyVWFGvkhktr7BhIdOYM8zpLWR4KHlnKM3'
    b'SNlq08T3XS3MaCF1wVsbGaLvZK46OYG50XQDHbTyfK15YDHiGcR5OdDj0qsQxj5KILfO0stpkeYHpqSIAmanrgLl+Q8H84N/pNdn'
    b'UP5FndxHb+q3YrqAYfkCKWzZt956RafOcpiHbAHhArNDMtK/jtw2lVrjf0jVo6bnmi6kwdbEke3NoWbpP5aIZ3AuRokA6b6uLxZD'
    b'KJmFzF5ynutMeW605fjVyMs2FSOFdCXG/VrL3UoL2zXO55Sdhr6lGcJ/LyIFaIYfpUlVs6y9MwbOG0NScA53pO+scqksKrjFo7vT'
    b'ovw1Xko/9dDcKLCgd3t0UQqTyztXfEt1SawDR6VU2Rc3+cmYANZ+XoArShBKr7zZzvCm3WLzqoVLHwBdUWQrTgM/Mt2jeouyG38S'
    b'xA4TJYKbwuJh/LUQIU8oHbAAP+g7H4xPOrNQH87+647jr+i0We6Q63T4oEGdOWWe+B1NTK5riJVPSyMMXmXQJayKfs2fNHGN7IO/'
    b'GVeVV8ouLRTAL2hD7iPUxf1Ig1EC5HxxcU1PsmApRjcfSKgAQRFAMuBOdfqAVnBXijCXnjWRyEJEjiE0rL97q+Ggjr+Htw6Zvq8g'
    b'adG/iioT8xvZLWODnylhF/S+2uytu0TkXjOPiZzlzetP7A1fF6ffO6vvuE5faa6ZiLJSYDTIRtww4fTEQr0O9wVfwhBgQbKjb3xJ'
    b'6SgqJixuEFKmS+6ZlYiobMrtCBQGWQHwvAMrpiaTTliDYEYDTl3aaiZvdWfE2ET3+3AJFqDcq5aWbVsiJxBOmK+q9n6sC+uNGd9S'
    b'BPahVihAaY2F8Rhn3Cd3S4fp2aC06UatwCaGnRt8pC5NazUe0TUtRW7CWsrOGJM3lqfaLajaJZd+hd1ktO0/P3WtuVTnXLZI4IVC'
    b'sTvsUkSYMKJgjGbmeca4BoB6tiJ/lWvcAFPeCYoDEODFs/E5/HQRSIkclQWqSuMfvQzFfa0nKyfyEA7cbgI32mybmD8cK1aFxftm'
    b'AAn3+FvU19zpr10EIZl70v3zTfzayY2Iq87YrSIaaEGoIHeMFfE+FyetDL3gU47/YZg/tmfDBKBCV7nFvrqLnHi+zppdD6cthjTv'
    b'lwymsVOCP+9QeF6tAQsU8EfqcCbRyv+3MoCWtKr7g8aoq72UHbEjDb8I/fKGCj88OSEHKrgpEXAWFqqIQyO11tLsyY1CPc0iOoXS'
    b'oW0HXgBvUqY7hqviTFvDGlV7ipzJr7eO0Cqh7mwAKwZnV3b94PgfGt44eFGIsVClyFkxGWbsMPKJXEZE4ak4G1pr8FaLM1svoAg6'
    b'Vrw3QUzFZPh7AlW7Z7qhiOUOXGukK6zpFx+LLhcHfURsZ5EdI1qbEpL1UhE7jMpNlD4oT32aQ13HrwENgIAvWlLPP6MPO1wv9UY3'
    b'Ib2G+SKYeVt97FlK4OTBYxWOOtfKtgCiPyvHhSIbnMTv9Kpa34376ZRx2nHZ0Up+KM75tY7anC2jjQkk+uO1jq71MwrLFDZV93GN'
    b'BH8EgsKdYJ+wXzMFpEcaME8UqAjqXP83o+pJE49i3lKIYhA61dpotyfPYwRD9D/py24AWD7YI4lO2VgKda+xVALHvjdkaxAEIjx/'
    b'WcYvPE7dRp2Z/V6WH6MJ8q3VIpJjsWLJwIrrPtqKNZ79ERIqL+LV111wigFWL+3B4nfchI1Oghx2QRrvMI0EfhnbjB+qCY0BMy2d'
    b'yyTrf4H1ye9LbIbeArn18KD0+vY2TCeYkR1nfh/jz6q6BWqDa6QfuXToWIIcX9XJzQErWSZ5ZjRJ4sp6aRmBgr9DRIaTm7NqUvRX'
    b'47iaoo44s3Y168bsELS32dI/qIx1fku33f1bphupwrkvHkX25dIbO+ddSCAjp4VPC4aoNNbFBDHpWIID1oVFhsCr4ArQYW/4Qcbl'
    b'tZnxOmy/bxsgUKQig3MDLlvbIeqE+5/xHcfQAgRNTAuvOUVv4WZnp+U8K7GGxaZ5y/hR+SzAtC++02DGEbV0Sk/7EOCeGyB5sqR3'
    b'VYqRO3+6DrpqBgHVywZ0iqEiOxATB5dXa2xM/qClH7gDWCpgGqP08DdRYlUVy5Bx2PlifA1wPTDjamTOB1cCZz2ZLmR/96bq68w+'
    b'tNn3qotTH+zdXDhzqWcg7aVGJydldBfss/HAVF0zW7oFvnUEzZLwCHhdv3AOlSWcK/yH1zvhqbe+nZuMH6CsUdtX/AsaP6sExkZW'
    b'tnuxzWHH9LvtZin6Tsd1mVkfMqo+jvKjjCnEhsIjMHpcBohQEYIuNWViC0V+sj15FHy21s8Vkg7qtr9iJFl2ypweiK9MAe01OTrx'
    b'xF0//lqFC0PtvirasLCD6rQvnflO6paidqaBWFjhCOvTvooFiuYcdhO0q9iPlO0dk67+OwQq36ieQgKL0s5quEIHKfxo5N6jqYjv'
    b'mvt08VbS8IeiCty3w8mZ+sWQeaVMQ7qIis8FsUAflR3hPIOy4sboaDVKbxkIR7qdypwgzpl038E+jLvBEMu8O+esPIx5mzIsCIP4'
    b'PXsi1ZPV3cegzHfsuki2CE6OkaFII+Tn1o9BaKpKAity77ZSdlzS/ia2qHNyFT2++uTi8aZvzTv2YUaDYNeowzE543067pRXWlJ8'
    b'rtstKhKsyInKV+DS+GQQu9XsQqIHToR8N+/E6L3AZftdwGuFyY/wW8LLzngsqcj9rJCHFy48AscTkp0kVgS71s4R717/LnvuFvFH'
    b'YeJLxwSjr9/x5EpQwt0Uk0Who/VPMDXO8HRG6pZJ5opnEcrdVndA6BzjAU1L6Vc23D5tz3ciU4jInJPv/An7SX7vei2seNNKsfLX'
    b'B4MBQgj1q7ngm2df7rFQZT0FmFNOPEyCx5sKtm06bzbjQcI8aXh26eAJ2BiNLvm1vzKWUC2TJhJXTeWGz1MMsb1b225UZPHamCBw'
    b'4Tfpr7aXVHPbgMfTUKmLgdHYivQqIJzoLkdRQmJi3JhlyrJM2DPxU2UK9yj+HgJkBWDF6iGYFf4C2FqDh0i0fKxhtZJV74lPEWp3'
    b'282mosM4IA1t9bYL3XxBpvgzZQ7qdn+95JbCRBazhicwk3Sk84jZIHXDdsoVAbKKIY7E7r62Or/cAP9+vEbbBfhIoZ1+nfLpaz6y'
    b'38oH/+mHYS8VjIcnUauFxEO0xJ8uKyagjfFpEdi+/+UXXZnGT4oZxwRpBIyYp5iWYocBDXY75MPU/XrktB4RjH1PzW1PdAHLw3vz'
    b'VGrrSSNoEa1+Vku8xOLIwpJc16TAFaHAFTTCObafuKF1WrTl3x+oiINY3XG6P77LrkIvtCzw6J37X6OVNMSZQRfLZFk0EJ0w0cg/'
    b'ahPo0Enev2UqWtwygQvPFcSOKmvGcMtYHIf3BXgIdY7l5p2uhZdMosy0Q/DHRqClgzBHrLaQ7OZ1K68uV+joKoeywewnlw7kebKB'
    b'wfFep79EMC5Xz14GmEttdEbXIjNohSFkE7L0WOcmtjRDKe8k9XHSq6ZgGWWLyn5zyUwI71TtmOdYlFf2eZ4gKfYh/eVeEKoRe5fV'
    b'x+5+g2UUbm+KDEdY/iJ3CHtZh0DTw9I5zf90x49xRgGnWtATET/fr4hMERogmmkG9cxlc/svUA7NVCvummqNkiL8pFflRE29ioDI'
    b'wOuCRn9Tym6VPZX32X9YfQByutnjlflbJ7QzH3iOQ3PfW11GI/sk0iG529AP1oPJWzyhGq3zSAnkz65rptMLrZLAsy5LXeEDzPZ9'
    b'aejwJGytdH2hTP20TQ6gDoaPDH4kyQZfqk+odFuYHX3KZtUopagvnR2ZHAXNhf5DjvdHFLqsP/rsknAnXqizY6gV15gnYe1l4547'
    b'3UHmyvFbDcVKBvDDeinWKboZRbMqtTIIyL7/PyidYQLGffUgElE394VyDzkDO3Hi3LvGRLfSEkzzBJvUSSZc7Tg256FN+Q+uxJRq'
    b'Umkr9OYqDq3njShjTERgXxyFtGlbIjQr3SYVmnELKQoMuGVJ4g4x0Fih0J5YvCmozFz5iv5LFkoRpMaRr4gGrr2bLgnUXEhD5hJA'
    b'iiwDKVgugmOQXdksOUc3kyU+p9B+wzDG7ocmulEBfI2Cx6T0bdsqrPZl/73ZowvlFsIjdZa23xDGHy8NP/5/0lVmFIjTEarXMn6H'
    b'NHeSGvu9aHNkM4/VHZxQE334ieYs4BWF70ihYDXe/hjFrHJMyrCtzM+RFUfGb/VKgXTeEnQq4ASdpmSrYucjVsypxytwsiMjs+o/'
    b'EnxsjIPiXuDnDIpaFq2371tS7oxA2pmTMGTUjDgYdp1G05jrqGf3msOmgCp4EsB/lgvqckfWuGnN9TZG/reR8SLIDbrJWN30SP70'
    b'zkDwThthBQ9PhpYzcXfbt1KZ5EhMEF8QfcuezSHOMhMoThucxwF2qF2AKU/fdE1NY8lSCI4c44qowlF6Z1bRfSLJP05k77nAcEOM'
    b'CjHTkzXZbhuJZYZ0NUtTKd4VfXKqUxSi0k5pLHibR9CshsEap1Ddg/IsiYq9m74j33FWsFPpglUgLPvAiMPT7G5w5+HkUJnL7hQJ'
    b'NuhgPLG4e3KRabq/zrkvI6g23+T8RJTc53svEaAYC3v/ggny/YEWtJJpQEK9MbB5Jug4C5Rt3qNfJMG/kUctXZ8jIXHNsZYRCXjw'
    b'dQspacy36KrcejPCxv3eHUxvTUGMUAFdfgBrHgG9OH9VQgCuM3+CjWTMOTefZYW/778SQYC0q4CWkU/aEn3gSUpFq0hl0a9lhFyH'
    b'W+XOq4dfJ/tfkOfnH+JysqFIUECohnsyA248dBqpBPt5T+4DoMzszI9CMD9luOxO4XkbUXOba9rHHg3EJCC9EjIufWhu1FzFej1V'
    b'sNJ5Lr/H/wMbg1ffs1EtrqFySjH8ZAKUblrTqboEYiXdOoxWxS5IdevdDgdlc49P+YZfbi+kRsYuxVJYurCQ+HnN4YGaqScW5Oy6'
    b'qEX1r5rYb0OiLsn1LPoRPFNExRt0aGGzd/ikyaYsuFazC//H3IRiRV+D4r0lrFZYZlu/0mIfj8CC0JWAfWW3oFzD9jqW/wSHLrdc'
    b'lKHME/Ax4wY/STaxINkBuixkMw3ZtPyQZwtNPUuhTcpM8Q3PKXBIEu0Y11IK3lbfZr/M69iNFo6KTPRWlUqotWa9iB5OQrdSNQN8'
    b'fWoZehL3j7LWjyAejWjy+4xMTpJoF/Z3j24wuzj9api1nFaQyDLBMxwaoeJXXRgvScbzWy95MQQmgc9NgvWmW1u/okTlym1H9UP9'
    b'+/4IRV4e16lEPft7x1eo5AFjLO2tWcoeU4fYwa45Q7jaApkpFjzG2kDjdATVXk3Wgh8Gf9mY87xj8MYAauzSLnzRUvGO/NLCbj9U'
    b'28PUknc8B+E/hiZHMueqQxrZNCQwALGMVXrXPImj5OtBLbc2mLY+NAzZRE3Qq/+HwH/twsAtfHQYxk3eBTwTLq9hvS+M4C5WMb22'
    b'rqcetCvCnhVSEouYROg0cQNgFTQSpH2KYeYO5Sx91IYV3TDCgSKq3k3hnB2JjFp1tiFq4BGi2idaWGxkEBfup8sxl7vdbYVZrIh2'
    b'teONbVrKHmQE7/paBg/FZD6fr/HsL0vmAbnpYUxsrOhM0z84uZwk1Sbrotf3ftdtN0T65DfoeaML5cn+ogWGyvG9k7CqWh0pYK5R'
    b'KIyPRukyjdxeroWg0fq+v39I9MPHnS56HdMCLXFNpZWhaadHCHHTVLwvXJMPWf+cEAx1EJi+3846Lz2a6AFNWchVvZ0ez7Ilx3ck'
    b'ccmF0PnBfbY1hQccVj+NJ0OBR/7GjGQXKIE3+/TlVZYWSyA6Tge3rjEBYVtgEDo2i+lJ7H8IIjPlAgQCirnpiMrdl8Xxn7fR6tiZ'
    b'sghkwJSn22HeujUqH7CwmZVS6SDsTcVuSdjSE3oViLmY30xLdEGy1e6P5Gmlf3BOPo5pDy8styYhnAq7SKVRAFeyQ2741QApS8ob'
    b'WnicAwnggAeWTGfyafrSaYK8O/786tBOLCgqZm7Ppa7HumzOdL52U9VFQHSQIVHQWWNXzJbXy7ihRMcL7nfe4YrkJDcnQRwtOljS'
    b'DN32/IcDKBjP4UhRMNIAB+ZV1hkTpb28rQOysAs5wOjTrPziMIzoUuUaO6jRGckqFRtTDNnSQpTfy9glyhoPAkdvLjSwbiIvUbQ9'
    b'vV8KmMyc9PgXP9KC4Znbb6KqRqpKLGu8uorViM8oGXzGEBaVWM+6OskoktSFlV2g7GD+U3Em1szaxTbp5AUnNx+NCzGuYURsL3QA'
    b'B8z6ov3s054diHnI3M2mDaYs/mCRCRavpgmySk72ih0sGUiOyQ9x4jai4rpw7sBXW/q7cd4vyMpeKZO8DHraJPzMdka8eKMQVMyb'
    b'kJpCbIx320s6ivrRHTHEOaT9s1dFOrWe1MZmKmcELiqMkrScIFzFpORbLQFz0harKCbLLXC0buOyte2sMAY12UVo/nILH7iVX/sh'
    b'KfMj/fpm/9VmjTWOW7wLWCPaDo0V3UoDsTI3cSo01/MTGRT5ZpwNue1yt5WTUsJTHJYLNwF3pTIV3nPWsZD2DzLNZjfxpcOjYjQp'
    b'l0Z5SSXFEMooC/mmbiuj5mHgxt8VdOUjkojBwjohd0aiiqoHpRuF8XvEaaoJzVvkjy0XZWnDK5HZbAvDRFr0+HVDn1VW5UbK485X'
    b'7mM5QycZyRc/vNRHikDD8YSod1R1U0qnYdpD3+gdPSe8BfX2Q5zYbMHW+ifO7H2LCL7kelxUc+tlYSqyvAmqZeMi9+/fHKX3v6Cr'
    b'g8TYbEajhU+kAlK76HAQgiW6TvhwXbyzezkn7TwgeP7Xiytc28GkYvA0Y/OV4yWhkalUVPigU5+n7mNetIU2G2mipfnnBC9KgXHu'
    b'JrqUddm3N0F4AP48oEAkU2l7S0cobJhi1M6s6EdwwtjW2fd/6sHzBCM2zvKWU43s0vexoP2Nr0XbbdDZMrx9MT8D3eG5rjtmL95u'
    b'MW5qtvC+pITxmOoSyWS3fcg/BTgEp4Bt51MwL/M8hYLtBPZ7Q0kFJtWAXaZvvhW7yVMj43jdALVDKjamRsTyfq9oozlvKhkzg6OZ'
    b'g4XnJ/L9mLxgkCpYWATuLSh4aob8psAeAJQQzTKHQaWwXYXxfB3cj5pn2mrOqpvxjyKYXXt6Os0rd1cwRv5/CF3iXrPGAKJGA/X0'
    b'duETnQM1LGyr/wnuHPCdfuZ+YQHti33L3NAE1R5oruZrYHrx8bFZCoHZtwHPmecQN0GQ09gHtTNzEfv3U20gtFR//dI5f9r2QNsW'
    b'l0uDiKq7fz3v0trnct6oSVAkthBICyf/YsXTZvQ5ORUfBZ345wq1N9oUjdhMkK3L0eIbIh10BTDeIadFZgD1CO+TL+bvsxJfurJU'
    b'Z6B1OGGDwSUOnlM9XU/o1b7wEs+VZssAdM2KiANyDN9C8Nyl5I0ELzbceQZrJKGxyZLi899WHPy+X769IXvxXOwsFlMpAIpBL5lb'
    b'7IzUc0gPOuKR6O30jrupUhDPSa1fmoOYRcYMiLeNBlMnA+24cZDzaGQnNfUKdjGD84Uu0YqB+VCTH30bdlHD5IReLXUBqg0yV0L8'
    b'8vqp44f4o3zp0nSqHUOQHOze/rh87bqaGqigVZTkxiRN3c4tXsTNm6JHhQEv2e2/Z/Gzlq/glsI5gn7xvXMh/KF81udYxIIEP9ii'
    b'M0d6fgyKQb1VLeXBfZss2blgKTVwWtVisZVfUvSzTBCuKkTmKxlDTU7A3sgLWpnQcPhvRkA50MYNG8IIRYPcbIzwhJ4PjPt86nl5'
    b'3G8knUA9l8qFgyb5D5GQMN0mPTLs1ZUDyxUgx0mMG64KLCHfZNLT1AHR3d5qrdGEETShHl51TfMZgO83y4qQOc6KWT0tcEhIWYhL'
    b'+R+9bOScRzmno6zAS7qJespoKjmSVvSSzxQwwvC20baQKS0Cqi4K3GhnC3wUuB8FODV1kIirY5/5OpV1E1yULRiA2g4QVxoOpksC'
    b'pi8ICpHqC8tLgCam3VeDnayqkPXh0VO0hKkN6WK6yoW+4RlOC5frvcWzDq/FqAhGrXdoOh/pZSdw2XTcA8ImD22saSIoyKnLG0qu'
    b'gEDjPaveeOu3N5JuRUNveY/iEr1ORil+4jjc3cJ8FXQ9/FSpyGe9ssrLlQcS24xAv3H9/q4zAdFQivLmF6hqmCptwodhJFQATE5v'
    b'DOyUdP+qVx5+cbWH48zVgnaap/mUNyURuVEhDajPaeuZZDLyDphtspQPEc7GuFa8Jmogqo70CB285KOw92D3RRjG1gCmBEQXzcc8'
    b'VowbogCVNbgonNH0HmV/9pxPGJ6IvtQGGT0o3RhRlqJ5V1Y+G25G2p04zkQ22ql71eF5aFkW/ZbN1qOS0MlANUWmQOEEqWfZMxzU'
    b'tBRODQ0OXoM2BJ/EwuPaYKb6ZamZEutqReESZFOjYtqiKpK/HWqr1nVULFC0j9jdguKfviD4okKtOQrpbL9BRPbmwlx5pAVj4utO'
    b'BfxEqs00HsHPNBPlx6E2Ug9xcO62VOtq6lTwB7u9dgTT9XXBjKVSBSVcsEg7CO2kx7YMvNgiaQHRnPHjN9DBzKjMh3fTh0C9V1jx'
    b'TKRxny8pGuw3coG+V7Rbf12DfjL0Ja2AiJAiAukS1ezNLXnGuSkD7/0m7k8Ba8K/qtOCqkt7fGUn9DXBnIkqiCKeYYJDV4ee6mTi'
    b'O76GnDoZ9FvV1S51Th8qN5yfIoMM/bcaF+G2HwX2p95MTB33pSuGC/5yZCmXDMYOU9BqDbufkda4MzNU0xLtWph/R8e8yzC8nVP8'
    b'nQtmX32qfKf2/XEnpmt5WUS4Luae9LqhwQ7h4FG8JFHrHrrMwuJkzoPcnEljOqc3eN2DRleuW2QmNG460UBfo5sG/DH+qj/AB7PF'
    b'tGpGiFJQzy8LBuUKBIlb7xMGzGZT79ffNqFhN1nmEqhuhiOwEeeN4YF4cYr+hC/1GEOv6PUGOSrYpd/MtAaZwoY1KKUC7vHtVevF'
    b'BimrZMwaWwxKc60u1ne/QMcpkY4TaOX1wNkvaX+BXMTthyOhSKKkRX7k0fru3iADsrAsW4hz5ndsabo8rB2Qxrvj2M31XasUVboz'
    b'JHU++B+YZwLExSajmScUPni9tazLMuZNJUlkiOl0FMFnbUrLiCHfeM5+9dxER7LcNVGr5tl5/+Pe0IxLbiwuIgl63yHNmVdYoaL8'
    b'80pQU03aMrMC560pRGAe+mbWkbW14DS9tHNeSHX+M7kQH7TxrpfC1pWASj2oT48+vhONOfllhsscaNzFZ/nIRfZTe/RS6/A3oPyA'
    b'iJOZraxvOG18G5h9dsfwtvrquc/z1v8ekIjKgxiX9AWhhSo9mzm66Xqol5fNxua2+nnbIVrx/gm8RmMDAUPHl41DNDAGCKkuvlSk'
    b'jgB91ZoA2EkrxKXDMk4yQxSI/TRVu/aD4ttdaz1G/v6zFRjPACU3bTm+2KwRFP+hWX0jgPoGk4l9EZCsvyaNG3PODTiq+/ekkQmh'
    b'QWdMS5ke3ZQryY5Ljd5M7smiUtM2WMmjl80Ty0q8F5/L23EX9yeLeJiv9UOwqSv7Nbv7HlMX0mfadA7cVZVDS7hVZ0f9nf8sqHuG'
    b'DMav/1P4bk+gMe1Ae6ie3DcHTDQH4ss1WAvdN/JEhWAu5XEvm35sAJBYUUhMJIFfkZ60Pwh1B3UDWrQYWRDtRoEwjy5zbiKG3qlO'
    b'P8i47npWNqO0/P9rDDydQVI9gZUAfGfxbMdpSmLoXF8qXv6byEnAk4KANd3I4HqODPI4nFBQ9qShmicFN/7a2Ue7XrehSLAVITZs'
    b'6w6fH8nXF2LC6UTVnGxYhc8jJNMiv5CF/8oOB3Jyq/G1H3UXShDm0VtxjSwJ1uiebpdPJmUW7kEhNmEVweE8dZcMOiYUSvMNUekf'
    b'q+AEC10xp2TLN41+DYofI69YjN2/kgePtc6ZBbawR4Mo7laqRM/NZi7zMTIWszwfSJpGC3WWoqkUu1z0ETXi1qj3ylRRzdVlPHBZ'
    b'gbNxKjYcAlms1jJTPZZCvAgz4NDTWtjWmYC66Vl+ej1MSl+k2smMsLr3NOBKoucT1Whpk9WPcxb4/KuqOReg7LEyc2GgmWtQ9rN8'
    b'PEvKqt10qb7rUDSpytYLox1E3xGqn8fw05vahvpF+RegIphZMd5KbPMQQeuPwNHg8meq8MT3lR13CtUm/Nf6MByMak+yBHs5wsva'
    b'YA7B/9ZBnVeLTdmdZm5NSMd9ZcfFnPDqlPbHxo9zCCDClLxB0KcINroA3qAuAvu+N2oMMdz3CczGjJEwDXI5zf7oYFKHwvv2ska3'
    b'OfmnwUCdc2fWDuD5WfHid9dglHl5Y7mU/dA5Zbh3ts6e2gfA/r+2mxRiNA5v5RgS6KJhkCj83WjizuMgFfEjw/2OhlfuOqmm0NOu'
    b'y38fvChfL9uJIDBoPdvzQowUA+GrFiB25itVpIdUpULFaQ7LHgT2BZK8UdRjmGc75+CmGCIwMbXX5f6ypVuAHlZUX5G6PdYy//Tb'
    b'HeJj6XHpT/z/LbSsMIw6d9lcLwTpoirQKfh0keOGtoc62U8MvapGsAR59m/5r73HKon7CXyC+faY8AjYn2ds13PwAnGYoMxHXmL4'
    b'EQHOor6KrGm/Uj9JYDW5+I8cHdVLAkh/6pwE1VrIBfECAN0xqkO+/kazVwpEYTQiLT6ZRrBhb7nN+PV4JZs61ADgK5iGrvH/a7XV'
    b'kSF9a8EOpysJzDY5v0gJ9s1PVkrV7DKCqg7A7f67uXLD90gqjofzK+qBdopHtcbMiWP8d2asKtOxKTtBqlGFliSqPlp6lLj5dJUt'
    b'DNvuIFoJVVsnmQtSlC8j/fsUlo3WrQFmsEp//NX+aeFxFpTGtMzoxCoczFDmb0FJ8PtxdoHRebkhBtEOuqDSWUumuih63NNlGrB7'
    b'Mj+PkUjMHhLNw8l46BgUjKEe0wrO7C2CJm/YmMY6HjtvQWPCpYpb2btKQHcnAjGVuUbegWw642Ke9MlCeP5DmQvaydBYe099iuIx'
    b'YMpzA462yENIK7OM6eiWuSSYtCVcIw+mD2k0HOHqfbUdui4OOHufbZotZFmfGYEbrezDFEzEpxWv+43FYkHBIvGNa+ygqCKMAaR1'
    b'8Hkuyp+96deOWwEUt5nJCDFRN2jBiXdLFXMFJPQUcn6YLUDQ2diFascGPhluJnvVbxZC6TdrJXfTLyASQSMk0dr4lpbqqdc86CO6'
    b'B6CAz1cf2ZCDu1B+7aMpXCTIlfRULIWIYal7uWBSe2jOFXh7wmCuyVua1JV6bkkWmfDtZ3dR5RCs4xPEqoCPhIwt489gJ5fAoGkT'
    b'bmkrcT6dxvAND0lSjJUZXLhBvMbjl8EVb3NjGEHunftMM1t5dt1JMPrHLx8C8kI6VupUcMTwTtB2fGesjgtyrR3+uM9IOz4mtoEV'
    b'eg8lyLph1X4dvXW/JnhDYBfoWexZEUSZkb2QKOlLZO3d/tPgF9jzQG46L+Yvu5KX9UJLlX/LpMY9sKAbAY9fluAxa4feK5lceuaK'
    b'ReXeBRQFrztsI6RqUy1h4AMksbikDsh0oJQZkjbLgOfjUlDgSMqI/XXCv/q0gmsKzRm0tn5ogEJ1vVkPid55lpjQuXIwJ1L1SaOM'
    b'WT8qqTe+hy9U1QH5+1LyCwweL94TVuJOWRVui3gvAiTEL12Da8bqj9rigr5N5uXQkcZrnxdMfoIyaBYnV7Dihqri+LLjLhHeq3ME'
    b'bLDi9o6srMgI264IyKJJLliw+w63ouj4l102n8Zhd6h7YUhYvE5YK9uF+W1nwbfgjW8mJ+yU7VMBfCZ+fF8ol+RhV8hmaY0CF2A4'
    b'2qMImDCm46orHwOpypSk3ONW6/aDNdtuZaIh33UOImSzcvdt7YD0L/xs4EBcDot43GB/aMUl6Rwk6HrscgLA3/VYcpMnUpZosCIl'
    b'4+70+kHQpYAX9pC/rFyjkjBqu1kLWnjU85jOEAUV0eKWDUK8XF38n7smOg1Vdg1vlc6KSf2pD/tfqQ5vHCujLJXWGlsge3O2rWjg'
    b'fsCCbVl/go1oQOdbLxadteDs+cRgNSSMMB10uxu+xpFiAh3HC0uXRa3TKUW5oRlk1e8yEc3+q+YBr626gF8GsL5CZB7RS/eplNFm'
    b'bOCFUekr8l6M3jaGuAK/GuPSxtL3jEy5sxa/cFSyefk8Cpxb0x96a/xVVC3pexaNBYB9jTC34L5oGbTlRtUi3V5e19foX7K4ZAZK'
    b'FAQS3fC+HxZvRRkJ2gjajSCNdNBO11cWVNyRpcmH7Ob0c/zhZO6rDxOhKNB1X4FPo0YAnqGQbMreArOhMQIt+Y68a7a9mD5IPmVu'
    b'CzjrQwjBtXbivKQZKtj37wio0OZO0v4BfC2tXR2GOhL9Zo+Y5PqdwSA3Y4m/OKV+TinoEjOoXk0nYtPraxiJGDu3o1dGqu7BBjNA'
    b'5iE4z870ZxUL952mazdZRrJYHk3EJuy/dpLeRnQ1ACd+vP9P1EPBOvsZiBYD2nSnZRsp4DRBanAZ/omCM6s26XLBYYBDmrQNMJfo'
    b'FxLrpsM/KBefgKV8IIIEPrOe14Lt6MCzQUxIiHtllmbXxDGm2wpeHnzHWNPpJp2qm5JWUP5no9WzoTvL6HNKwc4Y0CcscF3rDw8J'
    b'bd/Fn0B03rZiyKqS4bxo9DwRb61SlgkxwHjcCm9qTw1rC9ALYqQX8bOIHE87R/XI41pPkYtmCczVGUPlbmCOukjhs9jL5PkP9E0o'
    b'fGrRulZtbfaqCMilHWQx0vEqcO49aLICa5sm1pMUb7Uy+UN5mQjg45KiK/DPr012jN+uRiJUxtzdaSu7CDmdTYKqt0PkH/XBHPMP'
    b'sta2YQd2J5Q/gkqmDKYuZsL/SxO6k48/byqePm9qxcvLaysoqhUoxls/FZ4xui13SpQpBi8+F1PRYIoIZnVH4Oaw/uqaNewpZBt0'
    b'hdR8kaZqdCIiRUvqrTS4VDNIQ/RQN9fKRbYq0kNb1XKcNegnCHg3GeNsftauUM44ee1HdXO5SNz5DN6PSatFrjS4ROIrLy4DV81A'
    b'gdZO5NYKFTaZrRokCB/jyKoyz/ikEsNU0/Ilo2B/wGFOPoKcYBKkmWf0XuyHUorBy6yz8XWeaU0pLYAm4Gt1e9NV4mF5i/ZJ/e+H'
    b'RtMNnqdILgWk2ONTTRLMgM0VKPt3WAXFBpWYTC0jn791ncO+EOY2FQkXFi2wtALG/0cHkYxZBlfSYpk4ZdQ/04ZWJz7X4FIQlcI5'
    b'hD3ZZjkeTqZQJHh4vH9+AQ/VF7BXSIskFxhuNKKmZGwbt2/bQBk1uvPuZGbwZqiJitCAwjAklrHqiq7YRzdEgy4ilE1p4OZ7EXe3'
    b'2Vp/hpIdwlXwTQi49gkSZpB6YkCyA+jQSI0Gc9315cnurPRn8IdrZplWv/e0H/ZGeplQwgln7Bhyq60HWM9DYSonGluEYQ8RbdVC'
    b'mhwb7iVqMmiICJuT52mut6uIFsanGA7g+jCY130Jx7yFi9XIDHmuCqNDdXLhikgJTxJ2dh9bWnC001N5VXVKjfie0X2M05fJ9rQD'
    b'bvkpisYnfUUDK8Dgyii25Pc0GyZBmX/xCNPDJ8yb6HmK0od/5n2tKU5ZQ2O82woJlyMEvlf6rrke2y63zarujbXt3UpjWJksFjon'
    b'S62dSIsVeGKrpzr+i9pZ0qcR+uAlacr7yl2NS7lfG6UxuwfB0baQBEQ7VR7yybupz+W0STJYAhI7CuySYqt0Prg+nRvlqpB85u/T'
    b'HmSgUzdoc1/uscXnuZPuMbkSMK9lzK/JyCsx0fHnl+LGyk1cU9pwADVCkGi3fBJkz+TfK0rCln88PEBZW2pIleNSM+zu+0upP3lO'
    b'M0Cg8+yDNHMWG5mYi7oFoWmEyDSaARG8HwhzmUv+PUvNFq8jeYXGXCEpIv8pkhHHaPG5pp5OP5kK0Icm2rhahRdwHiM1feDrJ9V9'
    b'0zxi5toB7wNv4Mgi+sjA4zOU5OX4z1KDzyyH1kDMp/jpB8aQcbndYgJm4ytCMg+9U2yPS+NzzvDgcga59CELGP3Th4ScVpRN8fEX'
    b'nGQHd+KrQx8anA4vuswg2sBQb5XWnyEfZvJezc9YUA58ZZugGLnaKIrQUnDSFF5sZMHjT6ZrsOBWBPkdo4pVqWKBsKntEeUDSpAo'
    b'MiZvKIvUQfLtL6Uwbqn3PMuyntA27gkHY7um5FFL97sz7LaskLupMlHuZsQV33WwODX6GMfocKIrq8DRdcDUtp+GeemWsJSihg9Y'
    b'ZrfzZkGdXLORb+aQUwqHXs68Noca5xpOtWgxwEcl9lr5+AMzRnthlExUKbpMGh/tsFjwNcD8VHQGRL9LXY+46c3IWZHs1hCYi5Y9'
    b'zXi3LDpcHo5Vmjwp25AP2yB2NJaBQhzYOs3sgfrXkwE+Ygberov7ziF9ajblLMvr5me1lqopqTs1kR0ZU+fHPO+Vnbj0/Pp9Tz6U'
    b'p9Zp6Twe21OCRkjSDFC8rLWDQRQ5qiETk6tS9IuWpAwfTmUZ1InmF6mZbea67y5eiE1hox8e5K+xMrs9cDHBmqiFCNnjWZw/P/3D'
    b'BAYtiyJoYQhXM8pB7mKmn81HfW86S34pmCdwAhnwLKSUnchDjteKazRwqmmKZovpuVqnK+6ni4GJVHT+OJnhGFm9IL1RxZWy6okN'
    b'osUYqWmXcQdu7CbCES1Ig42GdkKJa6mo1tzn85LhPFPrCuTcZe8Byvt78TGTFF++o4NvXKgpNti18XhD4XJl69QAxr0PI6MeMxTP'
    b'yYU9gXPq6JpD6S5nJo2ixOTcou3tZETz3jmSWicVDUZ2QvLzKGJ1dgqOwa/rotHf6fcfBNWiE0gP8MqDTBxnYFgnI6dOfRTEP+mq'
    b'tPtBQw102lQbt+CrpqAXs43gjfSVq23hHRczgxNzIsVrTopQXA7iuqYvbYUuTs3zUUMTIDvtY34Pji2E/XV2LrBK7N8oXasA0Wfy'
    b'3X1tgtDi/IiqmIRbz897HA0ou3pGhznT12Z+PzcpjiasZ66s7/FdVVQ/Kn03P6SqKjT1VulGvUYtWfeHniyN0hyUN+G0eul9c+Zd'
    b'k5ueeiLtRvA60+SLXkttiD06HcyBa0odaHxXfNG1tIbc5x2Nk49eksrAYWBEPJy1DLNb+xmxTi6Qwtkf9Ups0YEUzoBaOupp4P9t'
    b'w6UNwfcuGLJbm6JCCtkLI9GXldoAW4oWvou/VVkGLnU7r3G8ZjTbFXpVtniWZJ5TtvowUPOIHTFKpMU05yfFO4Z7YRl+PAM3SIFX'
    b'bfbb8gskcQiazQ2+0UhXXJtIL1aWPP4/isidx6MbNhPRAYoGmQrkFScoBtrzItPd2131/JHJBU1L/EY+q4SUu51qn78856BrkPpI'
    b'zRpPUQtj6TDHBItFv6eSce65y5Ghs6bB9kBsCZRm56T+eM3B3JXNOBWUH1AGkQyJ7x5h4KQHhBTCHU1MYtCEjt1Y8SVUSLzTyJjc'
    b'bA3rvzxw1bBuLKLqs3m+RaeLrkb4qKf2mrsGpBbIanL2S38XzJsS14RiyNVqbhFo1kfXEITKfz/vMlcKoMY3Ndd2ERwY7M7I+BEv'
    b'qx8aEbAwQmBLntaF0QzuXIsileT+kGSQ1Mjz8mCFRqS2izK+iMXhtjrS8DSQYJlvfm5qYJMCTRItmTMawOzS4dCN+stsI+31xfim'
    b'Le9yqhPx5JBR4GIxox14RguSVCZdNxS0tqMPBSCTokxJ6kttDgfe3w/BeMGhRM9Z3WrjNpSeX9LkLHODhvZP6p0hbCaWjMutF7FI'
    b'5CgOegc/aSPKoQGYEtHjFaTm7+no5Hu2mP5HnbqXFeWtozlAETUt5iTsVRda+XpBnlGljHg4MYxHLrmPXtVxqdHN+ehF98Euyrov'
    b'NBFMrjlqhhRPOS7OZjFupyAE0BstR+fxO7fo+eOpjdrJi0FYrRtj7BfISKC7jz6tIQhBzb6PwRDnkPX1fqQIGCZmB5qyYCJzRm4B'
    b'4dHc3GuvfXI/AYYLK1Cb/qlKMxye2DP49Fi7r8slRDsxS/qJKAfYYmi8aSwAEPxXk7gMtKTZGf6kr6jO96nqOusjpV4pAamyNbU/'
    b'yVCw6PJU+ZoaMSbUsLXmnbJr9Nfjme1qw65WGN91M3rDSMXeVWVDJhUudyaOWbts5WiQVyDeNj25U+umIn3NsnHglnl1oYL3QxuT'
    b'ZTCscMPdle6tt4eJ9G3S5uvAzlHP1BSmQ5FdpqFg4KNNcnG8Qji7pF7QxWyBEypZVatJKo3D8zwgsyms934zdtH9HU4GDIo4SvHN'
    b'by+WfRj0Ws3WzefgdtWdIXaCuMJEXrRO/4xkuP0XpaYzJQmA4dkDBQZpNZnISibvaRxRefmj3m8cAIEN7Hx4SUF2QMYxVpSYPqCb'
    b'WQHhBeiW/t2ROryHed62mdeOlswvSa/QE1gS3Pohh+LHsCGim0YD9BXqFewq6tqBGUA6yclRj7V/triHBYcIq/GKYMq7Puri6Qba'
    b'oBuYAQv0FbpizMG7ktG46kX4x9bFhjIxipMtE27KYEi2EsLBodfW+9t3yUtIZOlRbvpZOrkeUTpM/Lcp2GZyoqEHjTnl9gBKw9CU'
    b'HdQJ8E0ufLcb72I13EgEeUMSznMLZa9j+ZDbstFK+Ge3Ykfox1yMfrBy26GxiZJr0RhvVmI5uUthVWaVn7FWrZadTjf43a7bOTGX'
    b'KzMTy+G3GQ2p0W6Bsw5n7au1+z+XrLUWQlc2ORNIvXv6SUr1iF7fiHq+3L7J9O/9npqM5BUp8gTf/RjATQpsUm/WS+zZQUqTqd7H'
    b'/nYpRdRleVhjG307gXSH7++pSX6vCdffq5kIbBE5WwgRElc0f1koyYWhN7zYQGHxSfACdfQ+P6gVivUZmKW5YGC/44yz2mHBIjrB'
    b'raUTVr7InQGo4P4crbxQyMHLXCcxawvFjLfd4kELnie0BzaBVgMQ+Qepb3L3yRznR71/aMaxs4VD00R4yol0y2z64C2AZeZTx+fa'
    b'CpQBkqIoEStPjejqdpZkeSzsxlHQLb8ZYF8HtEAdh3URpYDPnEoEV4DTv44s50FsmNFAYTgFAV+mEyoc3yic3NmufYDaCR7oeaQm'
    b'dQhlT5LV5Fv08K9NrgQl0fNlx+xB8+EOKXmeVFZ2eacGsqA7BOim2oVwdGY/Y6s9asbiTgnOO7bUOsaN3jamGDkvCs4BiwQviq6s'
    b'f+zCNanaCZCtEJG5ShQq8DVt+yui5hD5Nrs8oLaTYEyyPqIrn10dwW3m3Cl76NdPiTSgOgO1LPjObkkbvuUi7we9pZaXuiIthd4y'
    b'rpHrsvqj6EN0Anpo8KfrMyNuY+ZF7ChJcrIBwZTqTjtIrgaNoc+baRJmaOBhKn9qWswrQ5KOAC8d1CAJdys46ki3UQQUAtLPT1jC'
    b'sZylgNFaePLGftEcb/5Mymv5EJmpZAbGrHex8XFpixJBbtKcXVc1yo6iV4b43oP1/EzDlvCSRrLTdaGiUpeUl85el9/rOpOwsozg'
    b'0RsdWBYj6Ox2dfMrcl2c97jsgERKPlxOomSuu4BK5KLYA5eakh102w9BMHX0xyUISNr1EBEqMhndZUwB54AdcsXa7Fl+cnrQwpvP'
    b'VjLhsqVooIYWacu9lHdgExCZj41IYchTm3o8gpmPpA3c7D7sUmjqT/onBbQvuZy8tAK6NKEaabHPJO/nDnjVAHTpqnfXbvUrMM3d'
    b'o4JriwfBXNTV1QFxKFi9eWlH0dXyKmWgUN6sG9xr4CVojKhB+KtRGtQV4wOIdbz3XU3Zka1fMTkozOqBUNAbt5SylJMWQvrzBkw1'
    b'53KoHk0XFAHlHwCqfiWQrmIWYJEvnrazQfyUxcXZ4IdllVu2Itp6JNoGXKz8e3do3c87zryWnBAG4XRWms4lu3nw3B//A9XoLRdJ'
    b'UIEMXpVDxUszAMUrz593QCQRd1eVyfHfKMSx2D8WWFTkP05siTotonsAtthS2W4rNQyExSMXOM36IQoDEMvriiMzu6Dy4VoQnjIt'
    b'mKFQ+TzUOBEo1dLXZy9UwsRwnRtOHbRwlyWnWvc3vCwr6kRftoKPQHcVFE+z6n1mHCuNpHucR2kU9Lv3rc+3QYmtrneMKPLQnTE6'
    b'/DZh5MKr5p+JiNm68h9N4HmssAekP7fIWfso1O66JQoZlnlnNmiUQwAMREe5FfKZDPjYX4PUs+E4VUgb8vy1+jFnX+qI0zKuuqRD'
    b'Kq9AJ+atIwAHR/NJukr6GptfJg+b7tjyzoefK/Dvw6IhkH1c69JAtGm7HKON32X+l5yLx8Kb3WFM2qP0wOwwDtyhb0qa3qU+w9g7'
    b'RTB6s2K4WbJUDv1zxStxx8Dco0WRVTFC6c2OQ94KhX/rNMNuWWbkbQAoJtDsz1hAv+HQadbt20qWPm+E4GsraMok5m8lISz2Cu4G'
    b'IDZFDsDzEkxxmrQnF4WTeBPn4IAGQeoF5yeFC8si6bvoMCtJRB9My22KPfNLqsXLiN7fJVU/8jlbHr9I3kEusktSMX5LPXNVqwLv'
    b'/Wc7c0NGmZPYXhJBDoDP8MwGZx/slZL+GDupInyco0t7I+bSfsRYvFYF1aPmRvd2YwBbYb1im4fbaLYceGTNtreE7lyhn6o3xk1l'
    b'kP38acFybOzLxy0wEZu90tF2q45AI3SMxjV/No/T34T8gb8BPEjYaqoHt1bMihIn1MmhyBlOUoViYjvl+vVjIQYMW9WSGS9KJKdT'
    b'vmkpnzllyf0f3YJarBL4zt3M+MDByeX5RdnIK5s3s+Q1yr28vcD7/vjxzR94QFWoPfAdTTimSJ2hq5WfpLWvuPRc18LeCQUeSAvX'
    b'JQ3i2azB5kJdCIXaDMAYL1A/oU5WMdNAjDAjN91JWkbB7rnSWT0HCjSJwaZGM7hFsH4Z1scVpupuA84ocpvQEBi6aQzS1GzsIAl+'
    b'IpThMJ5SYP4Tcqs/H/++YJqlrDEUAEEQpWCygSrpKAsi4ATw6/cOXiBqFR7cExRJFt1bvKjoIAfpDWmvvQbzsdCzXcIEf2nEHmrY'
    b'97DWs+D1MZsmhLAWugpmyOTx5XWOs7Dw0Pc9NGRu/JFSWNwenHlFfx/kWbf2LLA376ADT4bQbdlRSE2iE3QCCLwCT3bqXz+eC5rp'
    b'VQv8znucCAU1OXNTtJva9sIOfcxgdchS6Q/yqw75ET5UxLRvhqLOgwK8MZf/gxh1P6yvfI2gl9uIev6IeOg1DLXQOMaxj9TkJvpD'
    b'yFq5YkH4uTvyk4Cbtg4qKcOxUUuJ3DON8yfndkXpfaJ5/yndwQyEUZ3jeQbFMK3cQ3YEzdI6UXbADNw/JXYQldjtmJphMO+alF68'
    b'AkV9QHsQd9jI8eRi9BrEb+dGqIUEBr/79rei3cqu6LxYHWaEyR6cSKGgZfGkNJgRY+U3Lm08pyfm5I08IKFZXmUkMJ14kc91MLt2'
    b'9D/bgyNWjmJN+cIDsk10MWWjYIqugIyztQPmMGpqkzc3Frnw5Wpm0zwteVPtvr1voHnyYwqLzipOhE+L0v3WHzZu8whFTD74k236'
    b'EhMN1+nuTZPq1QB9mnmLx9HOlPOGM4lfJ0iKzKolRr3m9QMQG4LTIsZNreWCyYGT6YGdhxCpOCPaZ/o2RBqXfYBz2xqKd0/+uNqo'
    b'3zosMbZMFwDa40TzBEV7/27S6mmjTv1Q/UXJa7MCI9YDen77s8LEO/nSt5z5d8+EbP31/wb3pcHif3EByj0krJY+7VTvbBU3IztY'
    b'tzwezo11L+qo2GSGqtWLUIX/ahgtHqk79Kv+npELx3Moe/F+8oh+Eaovpx9k58LSzA1IoTyuu5fMn8iOPBFOmOJXb6BTDnFBV79p'
    b'saB5pSQgxdz3wepwjR5YZhchHKqPlLJpnY9jX4EEMleVA2ZFoJRk7V6newG4kwldfaq25ToMVdi+pvZUMbBfFcGNOMLRQjMWLgDH'
    b'3VOw8HXQpd8JxreiCvH2awPhP5Oydk309JPoiSRRB9AT3N6Lsnigt5vdCnVa8FJiho7Hbs7Aa574GcBL2gg0LVL0zjBdjvuKX6gI'
    b'acXZ5jn9mcSTGEK3GnznAnBRX2BDU83+hAxfFySjfAv6Rpl4uDVrdtytoZrjpGrb1cBW9NFXMPK8F5NC/tARWq7NpfMaoJWGdjfh'
    b'4EvW6haStm6UIHx9LF/3HL4Nf8BN8Tb5D7ai5qHHG5WXzpNXW+GhyXUHk4zBjvqCeTxwFNLsE5RQUAKV52cIKUx4iZY08uprczgI'
    b'7b10Dbltg4QogUacaN+ggNa+/MSd1dXjBGSSm6j2cpwaHLXWbuuZV88BPZluXno8PTMah2e5oo/8FAb0t+WQfSRZ7Ev422MHQ198'
    b'eAy0a2q49KY8eyHL6qLjWBpG7HqcS2aHDDYmUXrKOdaGQ0EYEO0mf+RNd4EAio+HbB+0Xvr2y1E7ntUrARX7gBjc4y5x7KydrwIx'
    b'8svwJjy9Wu4nnwGyNdTgUNkBnb/PheGuazMCl63VTOy5rv7vRgjBqWo5QY7r0kQVUmY1gGdKLaelh0SmQIa/ASt0D5QcHav3eLZI'
    b'acgZSzESa4Wj9XFeFr10/IT5/6r7XGTBbyd1Yr8sVX3A6A7E1aroQgVEbbAFtr5jxlpzmWhFJchSWOUxodvHDWGTOXbtZXlw8oRz'
    b'gg3MmeFPn1diuye6K2dg+QmxrKOOnP4gdeyzGjfAd6cz/pDqFCvr2Rr6XaNIrrvyY3S77pP+EolgsIbMyO0Cz8yL8dlPYaPav9A1'
    b'n6Ez6b0GomNy2CV67gJ3PaP657InJePj9YT1Trq1VGyBTHr/+scouEiLjM0gu1GiQG05lDDMv8OHL43UM/bdSi9ERs/sf+YM7aOq'
    b'U9+87pvRjK38AuDU06Z5oJXbGC+1qPkD8lZCrBvM2CJTYRQBUrPQGImcc01nQuJeRzx5HhFu+o/lCMerF879lpxDjWlShooMkB5w'
    b'0gWbpph8S7sl4FADeGGYBMoKG8lbaxI2tpo3vOAq76sEQPLygSgqI8bL9qlZbETbpDcatGkCAG3Cq5Pf3BTEjzxF6I20PCP1F2NH'
    b'jksCEzSMtMxKNRzHk+f2Nzx4Hd6K6aZzRCFzKOlyQXSUMTJT0lg94W9ROks18mvjR2PMR6y1SKtN+UzpMV/qLfar4KHa6RwNmJO8'
    b'yoWUX+F5lgyOGWl27ZgM9s79b/gthucYCOwUPPZuzRwHwxdG0y9aBPuG+FU/5L/Xm+jzVtTo9e//qiYIux1gOlCbco/lrrLFOadt'
    b'0EPYbs8/Z6jGEhHsmhHjJkH46pU75DTniwXyfB9OO+sXpy+4MSekoq93/ZaB6VIMBkl08+D9ENbhyOrrWtG2hUM9H79PHLGXz8Lt'
    b'0Yh4rw5HhaVcIvTf0xrkBrQ+NYuIcx3aIGk8+XiTXGZcAUY86XviHrEytBZ6ri31e/1uWZ+dUHMBHkNAF8sDl/D+OOfpqmtZ3rks'
    b'kJngYwBIm/tVBTvvPEeJeRCIZ9NvWOhjohVD1LBXRQdFgtegBUe82uNNOnRff9fPzvi6aJqtKISIU4DgOvRr5AlF2oz2S/XsFakc'
    b'9OihvbvKj6HQT2gmR8mvop6NDRkRVHAe0eQT/Fzn9oioBt0O7uy1M0MnRhp9oxGhZy2by5orL1tAHfolTOTblmkETivjzyTqJauJ'
    b'CCQ24SnjtCUv4ZKjUIsIq9FdpjfvmpJ9wFzoiu5k9FxYssmHu6IEhKDcaRwzHLwSDoqwrT5ZK2qYhbr8EfC7ZsqV5ukVK0zbsJbY'
    b'UgSylzO5p0EOEfdu7nrUJhW3t9jKle6wjvxhD/reA1msEM9GskGYxnLkwOu4BPRaUw28M0tqx6LKcgZfm9vA904Zqeoniynh8dIc'
    b'mC2oMD7Z+PYkksbdCnnKwsC0caCq8l24EG0W0eCVjTzvMRG9UVSrQbvmTNXN6Z5zJmOQKVG4QrXrJOk4+mvEjqR5Jbxy8ZnChPsd'
    b'P3mupk4GPDPvNBK+m+Y+HnNDYSmOYiX3H9aBVSA6yHkyOM5ckGvjuNp7zXikM08+9F6RZi0SoAMeKscOVvwfTkPDcx1qS3XFDdGG'
    b'aQurfGxImt02gIwATWTDlHd5AP6c/OHmbLwpuv9vKzH4uVlL61r2Kv2ubUbhMlOvOYnlIXW6BcEyKHo+pGUgatAv8o/tsm487lQ6'
    b'Esndl2rMWe5xvM/cTzstucJ81g0wX5wAD8BMKklha+mdC5vPTXdtDeyKWlfPz0UHkxAXCynFrzvpOPEquDkY6RjiRr7aUC38TOnC'
    b'OQmBREa7B1LET9PATLJbW5ZHAN/wE0ms26zKLhmqyEMmdupsRe6OuPDXqJF4USz/oLSguPvT6usUonS3iezMnIK/CAbD0Keeh7m8'
    b'ne6cJ+Qf0uQo6M83++Q331Oj+JwYSX0IrsMYiSt3c+/3oPtIQK+76UVf6u0K6vXnXHy5ZsjlY0gGxjpioZtcATtITE0Osh6QkJoC'
    b'XMeANhzXsQW3oieDmmS2o6X7+hIoIJ6R/EPvvQ92ADeE7N3xB4g9nZpv7OaSLPPqSDxRsqWuXD1csFNSDq4uCDQs5FnkRB9qOvOU'
    b'WI6z1VJakasjrqKu4CPhKmo9GkMtWXysLlPD4RqhMoUINfk3UB7yA8WKMJDUmeedpn3lGIUbQlE9zlCtTQr6MnVCNhlGqHenJset'
    b'xK4C+LC2+JTKdZB4Sz16LsO4tbhttVXbkAosj8AbCvEx31x+weYvzhrVrzJhQLPgfyHRMakvlHC0enfOR9cc9nc3pv9ssYMa52gv'
    b'C5TmSLswAkFtUMnIpmVNcbmtSQt20cko179dydVHA4tkxZPFM5XNY/fHnNEBNUFw6EwRp5++LFeF2ZS2YlnRU31ByTxHxC+Gj/0r'
    b'OOpH1pItyhhqqcm9SxHpO8ULySnSbIMWfmfvM99dsiMQ9Utll6XrZVxqm/xxIIuY+zVdyvc6zG6bCRZq59QHuG4iPyEMKjL1Fse3'
    b'5hzD6GtTAEtVB41hcPM85qLdWvOWs+Sw6ynmSDJxsJd60u8xBbNsmSUrkLYc894m+B/74XLpHMQGXh85n4aPplryhaQb20vjHI8W'
    b'23aLS+7ScTUunwdb7jeErCondDvru0+KvybPd4xkmbg5XP1yt3n4DUlIL89kVolO+wLgv+EGdJR640J4dE1/m3q2rXy1HhpAlNw7'
    b'JGBDNOUO3CYdZUR4AfqT6Q8mxeTD+Y7Dcdz2uSo1M7g2/D+bHH2FncSfMzroK+tiU8DnDUKOfYd42+T72V+K/6vlL903HAkpdebK'
    b'qieIkzQALHxzytNu2t9eWQ7rQUCr4WU67u3gb5MrOrStb95YCXlxh82XdIJezBPfo5a5j40uy54ajBSY6NnSgO+OhuGKVW0MO55a'
    b'7bb7FWe/44CKB97P8bh5PIGKTEsPW9dgJ6w9E4CAwRXcAaicqtQuQpY1C/Ah9mZTgJ9t+FlZtw7uChDb5rOQzKo02jSGmzJe2SE2'
    b'9ElHJoxtRx8PnRZwD8WpfB8HoAv+L4lkGK1Pf8w7qm0zIoE3+R//Rr648tZCwFi5eW5YBfTzwMMRYSGEDgjV2PmyAxRORR46k+wp'
    b'qLkfnDt9Gjai8nSZzZ3hkY2W2Z8XBMdvmz7meBfJcnEZsQXFjuVDsM+IdK8NWYbAa8FNdgxYJgKGNqzsUwQQMsYOpn4QRTWLlLrT'
    b'lXZ8T5771RoOixFhnFSJcDZCqVHFsg6W+SX/076JR5vv1+yJ5wPxQToe05GPo+eLEiwlu8yYR0tx/kEX4ZV5vyX10kTtJO5M6wRu'
    b'pj7m7Qzt04VGqjXUJxdUxcMWBVnNz+ReMn/D+ZP2saYPfELOgN5kB3S55dyCmmdXrxjOead7mlh97034bYN2/+xk4Gbm0izE+77W'
    b'uYssBwqul/Y8HV3UKnLLZTnlJKLqsf1NULpNGAAhP7nT5uq1G3z6hZom3uYK6Qbw9zzkH1y5OMoQxfHOKjomBJM2QJOiRvzwh46L'
    b'ccmpgktQF5tMfQiO1xu4kpUY0x0dCcLCZjE+HgKNEwTVmdIxISJ7LXCWHi421UXp9H3PTYvVRB+lOU10CRaex3ctWXd/dlBu8xVS'
    b'zN/tvrwo/7hgmAZjVZ5hb8B+aziDGD9Qilap1Riqu+ufkSvUfdRoNwe0gmyoorI3whbVoHWwQnDWzRRM//BpODq9QUwtIJmUkrP6'
    b'ReZYmZKVX68DjWZwSwU9pZnvFqF7rGGfstRmSOOGJr3AaO+EznCRFEAxL1pgeAWPj8iG0O7faQEVdihH72I+nnMZBqUuLIQyxEqv'
    b'K7WXIXBHbkxzwL14c6eDp2pw6yPfOflriO6XtHJWEpfIIq6wcPmXxAuamL7Ogx5BwX1B3jNY1F2rooQtg3pSoe+1KJkEbXwBhgrv'
    b'FIGsiNah0nQnCkD5e/o4yFCV/gkBAO54NFsTySB9WjiD6o416mo1cyiI2ZTAy5YhO36AUsAVzGaDHvvgbnd8Pf7Qgppa5SamUO1J'
    b'XLN0/cB++a5AASOZB554XY3WakGaRjfB32jKAHjffLRw759Io3072y83i6YZrVYEA0GrI3fJhogL++Pam5uW4AFef5MrvttLXoOG'
    b'5FcdkV3TjYX1S7AZdIn5b+mJ0WBgEwIS27cOliErgPgb0PH1kkjEDiPAYxcljAzKzO/FfHO8cY3cvH5x+T+/Rh36aCgFkajqxOwY'
    b'vji/LC6l/kBS/7nXohMX3Hpfy2BrpbIM62xGfcH4UqcNcSpl1mpihOr5GTl5QcJnkL3Px00B6K3BU9OI/R0w/6EACcmaH3QfKXkQ'
    b'89dcd6KcrYO3/NqFEqNjHk9X3gsw4vBaDGi3VyX59efNKzaIicX5UF5FpyNH+ZHlWov8jRLMPaqvY3gHS1GczTeaKKnu/EDGRPWh'
    b'oAQC1J3VqJ0JCMgqeDJzfgcyto7WUO0caboYrCbKSF+gMMSV3W9js9Ni1iQoOe8eZw0+3l8Fn6kKYlygPozyVnGPDKSbVXsnIElb'
    b'I2rjsmZkaqYsb/5Yl+TUpgVTlCeWyOgENgh7ML+ywVxxkRNA04paKI3glwmIzMQLg0H5uFTcp1nn/iUsII5E6bh+4W10aYimtXQn'
    b'RX6DkhTe9ta4z8tP4aZvhkDirQZShjfKwrdwvFj+p5HXViGdq7Wrib28rUEBE5a3clMVtXQFMdV6PyliU1p5Kx64URPp971oK+wg'
    b'7c/++EyaPjYMy/JDVVzCou/7DTjLUKFbGv+nNzOq16MVslbdqA9YT1Uuscl3thKh8ruBPHxEMMG4yRIT1M6rXVg9lmjo7IGk43ro'
    b'bM8ytbnPEr0WZkHdg7ehNB5diGGcYUkh9NmzauIIKPa22StlWHq9b1kyWQzl+cYh4o44Gc3oy3I/EBnu8fpBFlQHi5Q0U6v39CD+'
    b'W3vEyAkQOuibOFFRLHX4/e0F1Mm1ljJngbrjoXp2r/V+Ro9OzdFCpFY+XYZcqUZLk92NM/5nCSFrOjhDorENVPb5BgeQ8PwVi7wo'
    b'mo6WWbmJUSciFRRasbUGf+W2vW9GWV8Q4W3ezq1XqeyWBNHELvzLyOCUXug3EN3CpyoDyCy4JbRlIOF1ksFE7D7nTAZrHjqHfUTX'
    b'6GKqw2Bi6eRdhSwLQayqxohwJMyA9YEoStNb6HwU186/CJ2SzpTWTp5gAE/t3Jmlnz6LyYt5fawwONn6+Tzo9NVyASEHqNIn/hIA'
    b'GNWuHPfa7wQEENjyImvNxo5QE/7Tg9ys+Fyev70hz9uCnBNwRUlQfxiwqUhNbjzY5TQr4a+Nssmju5Ry1TWHU/tdvx62mM04zcrz'
    b'YpWCNWgWUY6lQpsTeE0+/xIbtAmvaNEJN2rh8p2e3x3ri9jS9kvvKLHf78jGbzk+CatX7UJpUbg5NiQFh+gKdtSljgZTuGs2YWzl'
    b'37gBaLG6190RSJJ1kWr2xgF7qcwKU0ZiXVClSjeaG9Ily2byiIZXfgddIPnstqSoiaQBM6tcHd+Ik56rwQAC6DCUO+p0iQSQoVUf'
    b'+nxqaeenUn2RwHmdaU/mK0eX7ouYq9W5FVq6Dy17JpddK00nCxAUKKr4ujmWW/1fflwYnrnq6xWlH5kyK5WXI9DQhPmpRO4RiFwO'
    b'+nhq5pq1RXFjgsYSmljAeP8KZVU5TMHSDdemowH1mH7DXnQHu1a1qA9NfMIorq1EDBgXbqcUqSy6U+TZsF3U2q3V+ErRAlyOpwTq'
    b'CCdYpw1HA4qWwaba6BVgpXZB/thdA/lMk6GJs+gcvaxpFHKqbHnBnANH4YSQ26ShnEtOM1R0LhmXMmpDPCZyZgRB2nO429tM6bpo'
    b'204yQv/i3/SutGpSbmNLm6NroMwqsEN5rgcvXplpUNF8bqWevnhQuua5Wb30qDmYBPsmFJ9oVa/lTiI9vDjB6HOuqPF3WW30iHba'
    b'9PvlE9URC7AK67kjIDPRbXNnVNjy4Gugn91s0+gtEADWlsAJJTnKG9amT0zMT8dbq5cU8cVT9m/cKR5ITaLGOzGKRMAW8SXN3SGS'
    b'I36BgGs1eti/FYItcMY7D7MmyuI5EhBbOtyOf1WPIt/G1CSvGWvqgXCrCgiKcMkHzT/ExLRwbxUOEXk5VaShr6RIUqugCDdwnUq5'
    b'vTpF6qtqctMLUwUBpMYxCCr/IM3BVujGsi9Bz2RzT+6nA1bzpxucP7f3+fPrpWQ8u7jexaZjwWtZ/yZcBTfAomwTO7JJJBONRV/S'
    b'NHoxff8pMk//Zmy/i1B6w/9+o5dy/NHzX8OmQDyd+gD+dFIwp7R6VspB/7/tcAXNsD4qLOyIj4qgz4myZV4xvueAI/wj/GgiPs+C'
    b'k7GEYAf37rPA9YS9zvrVG0x5xnNE6N4vJtxWcE5JduZz0n86GzFnZ1g8wB2PCvErANb/kbccBscIZNx2rA5s2kacLcVFKOr5yGX4'
    b'IR6z4yDNauIT5DeuvlRmS7+GFc6x50w7VgNtAhfWxvoEowaR8RwbpFmkJCAvxPWoyzhPShof7YRJVvAM/XyBYMTa8zHOo+pWHoQb'
    b'g2DqQaNBbJFmJQozDmsHjox3GQp8I+q4VC3HlaTzw/Ofo5OF/20XluXcasg/sHcUH35/MF0gEIkuz/Jzr63rzt1eXNoUEmCEc6fr'
    b'jqg3GGfLrVu8Fa0iGPk0tQ+MOcHAjC0W1jWT4g1s+fFDBhX8irM1efj5w9Icn6qW980hKZCC1h66adB0z55TJKP15bT15HZDvink'
    b'1DOLz+qLtDg85EeIi03Tbt3/Ht7Ivd2MDjqPQ/NA8Vfs9cIYkFsR/8Tw4UZbodqjoj2RoayikYFEvtcMr5ZHdTibcPIOvjBPhIkU'
    b'aIqI6tUeFbcuW9SBQ8rJjaidaV8tVLY1Ve+KPDcXiLnLKQPWhG+z+XzxWcv/OPqMShqIz5H888DhPlw9iVAzHSFDcgebLH4VxhIm'
    b't194lWBxMau64n0QeaYaaMhxz5/8EKZCz3sbMlV31E4CpTgU/hmWVy8d71wExqWCx9YR4qzOSfS9LgYRVnLKqPzp/AD3kC6raJMD'
    b'YhOnk8+DjC8OvRzbKouhT93IIwCMX+sTqPzTJYi3QwpO4sw4JTXWlu3wvGybJsHgG9mXA83s01DMmy0EKAP80PBwavprFABdhfja'
    b'S0oy5vGeG7vPoomqqRB0Sgtvc5WQxNcj6gHl8NhTPa3p3G68nuADFc5muZEIO3LWTAt4YLiw8bmQOB4DtAzEbo3uSqYKGVME6WtO'
    b'SwApYbPi6p68rfA9OeKh3c80/QP9FqAFdSRSgS3UCHGgx1Nvot4YLucudk+EAZaIre9mMf4hLPph1KquILfZD4HUFIs8eKq/z0pZ'
    b'L+tkpx0KuIklc56yBJyeZvGD4qVmn13lrzrKyGkmuoTqpq/XxqhIeQX94UuBmjwY4fQDNhEfqEUxR5p+cmCVZnxvFQrNLV5lrnr3'
    b'wBvxC+ltnNLO9rBKWzgtbEZE49dw63Sb8Bsklwr6JCZ/Ao3GGjb2LuzVTfooPM2PAFbZhBiYFRNEJE4pvHWkFj0WfFG7k3arr1F1'
    b'gfi9C4kUQ5jF+ESBx+iSsgOwwJYiwvTta5Rg2R6yKGneDvGYr8Jn0NLN6nswE2/6ITenoEQikkdfIKW2YVkLo3TMMdqgf8swtOsd'
    b'QcVJf9Cc1pyFudlKHpTK81nWyzI4eXcbC2UNWyD+sYsCqr2/wvUBxfrybKhG9f8NsKeG6i/1mVJ1IAGwPMBV1fGRfjsKTF4r0Ocw'
    b'/PwAdOOEkmZNswm+ios+59sYK9lqJnr83lNcK5SaqiUY5YLex4F5IOmQDxPETn3dLbc7Wtw0djnKeQojmLJopSmFAn0qVn7Z+Xc1'
    b'VzNZUXzX4C9BJZMQMP0iMQAI0PO/E7z57/iKxm9T6Exm/1OJFMnvB5z24OMP+wrOMqDKs9As6bdG/Yuv'
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
