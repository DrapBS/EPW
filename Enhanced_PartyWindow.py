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

__version__ = 'v1.5'


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
        # Nick option — show current nick in label if set
        try:
            existing = _fr_get_nick(self._popup_acc) if self._popup_acc else ''
        except Exception:
            existing = ''
        nick_label = f'Nick: #{existing}' if existing else 'Add Nick'
        choices.append('add_nick')
        disp.append(nick_label)
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
        elif choice == 'add_nick':
            acc = getattr(self, '_popup_acc', '')
            if not acc:
                bui.screenmessage('Could not identify player', color=(1, 0.4, 0.4))
                return
            disp_name = self._popup_name or acc
            party_ref = self

            def _on_nick_result(nick_text: str | None) -> None:
                if nick_text is None:
                    return   # cancelled
                nick = nick_text.strip()
                try:
                    _fr_set_nick(acc, nick)
                except Exception:
                    pass
                if nick:
                    bui.screenmessage(f'Nick set: #{nick}', color=(0.4, 1.0, 0.5))
                else:
                    bui.screenmessage('Nick removed', color=(0.8, 0.8, 0.8))
                try:
                    party_ref._rebuild_roster()
                except Exception:
                    pass

            from bauiv1lib.passwordprompt import PasswordPromptWindow
            PasswordPromptWindow(
                description=babase.Lstr(
                    value=f'Nickname for {disp_name}  (empty = remove)'),
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
    b'NSC179NNjFU+jldTG2DLpheRIrH6KlfS87M6wCf5XZNkxCIIlyzI+czkZCJvTfYSyFw/dqHoTc68cYwhKktSrWruKux8hEgh'
    b'saERPBStUs4QMumlLQcpK5ipFvhsxVyC0mUnweSGALlK8kpf6o0Zy886ki5JYQXvKU8aAV+Un+rSGvKwxNr2W9+HyB2lKEGj'
    b'GYBPOVco0+lvf3i6YGfgCmInbv622Kb0bDZTJqHTMBC4h+OdCKwSGAuzoTYsllO0N5osdj96iHvB1+WsYE5NtbSdWaWBzC5Q'
    b'mCKsNBxcw/+iIKbHTiA8wlHGodb4BZvr8zj6Z76hhRagKgA2VJJ/946jz3zTiLfSNp48H8XoBClyAzRegl8vmg1w6CDpO8SK'
    b'+MHNLEPNQBx0bPqADQ/rOklma7VS3v2I3C13hn9ZJA18LA9fnnUBxzvw5GlHIVWs2nCwbfOus1taSAxJMLUbiVwFPmX9Q5Yz'
    b'Cd13WPsnONVbv+oVIU30baYeyqYTQyv/7ZkHKKEkKkyWhCdPgxZYj35Ajqq96A4W9sBIsrpuhiC6Ni+uJaES+QDo9AjfxAm3'
    b'oRCFFJROGs0fxamnt9JoARsDqEkgFhGV56JApj6g7+zm/WcaNrsc2/9e0GhDXrPDoW/mjolj1STU8TOJZW/OMfwkATjYUNvm'
    b'31cFhH1cyn11iEnxmriL40Xr5139J9R5tN+TG6AylE+f34JXoiTXPN+KcfPRFcB+pRrSSYeBqnr5bneFADUZYRwAAcTeMnbp'
    b'LVQnQll9efDZH8DTeHSKvB5Bc23q0d21tYDQHZeDhYPE4RkxeVGOtI+GXr8diB8GXkV1o4bmnGQCQ5a6F9emp/QZ6yKmtQZ7'
    b'd17s1L1cBjIe9bBCPrnWqg2qz/56xeRI6nghz/rPdSx5cDXmUqIEMgmYTHefHYFUniF8WXKSsiedA6eihqYdlGMOqwVUmwek'
    b'sVu9bHd1cjsNWAcYu3mokHFH6pPUvVON32DLgmVQRQBHLUl9v/HazT+uRbdniSLAKi8/ffcaaLKf9GCiAYyEeqDF+RsLn4tr'
    b'6R5//aTtF7br6Gk6LGwG19lBoIduEcp+Xz6wCn5FVdF5IAhsb0t5G1wZeD4rx+OBoHgl4C2/Lk5pK82wGKKao8f4w4Z8/Unz'
    b'fQBOtCm2KeZuMBKCjo0nn8WH+H2oiy7NTtudtImFBtGN3fG8UHtkLQuYzFVZXXhGU8n+VpWsyOiGF3jbZnMXXKyTe5hh/Xxe'
    b'OTHeOM+VvAC1xqKT0g82fp721WDF/wCyVM+lcWDyNC2fLt6t1pPiwpQMjQDyZ9DjgJ05qUnXKtFGX5Afa6vUtKitDNgHCk4z'
    b'ywsqITdv9lMjwt1DZtuF1bLw7eU2ms+MXYBLOqB6XJmeZ7cE4MKvESx07y+ouUh/O8XsjbQrnzue1cjBrDajCl3VJIkPpCLt'
    b'SxxekUQluII9P6KdNPSotJdoI2JwQ+ygfmHF0iPiBSL5ANifr7gqDvfwgQz9HdDtcOdW7fRnM0ZXb0ZW/5xk7ERt7xRBTTcW'
    b'wmew9tE5JA9L46vpRViylrQYFGzstirENGzwWZbDBYlVsr8MZvPG9LCDq7xGtOaj86XZvsd2nRIM3eu+fncPrdhAtGONgjU9'
    b'LTsUbOdZ8Ox7yG6/A3zgKUqyOuvI7DQDmzhFL56MP3abR1hjbWmuwzHgAx1oms9vBABG6c7DYkjE7+SffylWLJiQHah04mJ5'
    b'bhFmdfeu3y4bs6Ge3SGdRXnf65qpqtACAknJFPEdncIZO6ruaFy83UknAM2q9bKDqnH4bIFbJityRHwviUn2v4OMMzvFoIkh'
    b'yd89jFfYbKUYznlMVfJgak46E1KJpt1k8FhyYdrPXzf7/B3OGlvK5XmIr1stY/5VqjTedegY/XVzegZ5T1RH1/0CRnTbx9/l'
    b'GmZG5LQAh2pU/bWpOGddiXvOXph5/op7uYYa/BvRjMhpHxAVHUo9YHNtFy1Axu4zqykFjGd7zc+HJpeMvVzYM5Dg/1ZNy+gL'
    b'zR+0PeIo7uxSAQqFqvi6N1RQF6Yhskd8Y+5kpHNwqHluLn580PWgDQDt0R+5W+Ee4+JiqBOAKv3Etsdyx7nrC7nbGQiwmUqs'
    b'9lSLi244anUk9wBM7pfHZSJDohx8FtfP2g4LUcjh0rrol0KCf6CdzGnBmBygguVQ0uYAWVFgc2FDoAB8rcjuPorj8Fz2gZs2'
    b'K2C/wGU0A35IPbDZz2YTyj5nRm14iwSlj1JGfy/5oObn0bCcwa9C571tUFmdI/TAc3dWQQp9kB3cIyCgFbvomOiYnPak0b9p'
    b'azfUWys35mBG6dYIJquYDfJIJBLZYunekD2I0tHNbIiMb19VYJxxO2OkINlY+OzegIqQk2ygy4wHvxnRVROpHybwN6LeUuHV'
    b'EVl4mOaKDrN5QHubxc8XDnDztovXrvVopyLOY939/yoekXhfmqx9D5VJ1SLKhRFxb0jqAiEXTfQjxmPGrZbKRzQ3Tju/Xz8D'
    b'PlmJtG6tlw+dcqRFVrTA4E6SJg2HFY0gLocgRu3Mc8WMKoi2mQlApW/AouvIcS/u1G7dT5TmBNOqz61o5s1BiwrpjSuJFLlh'
    b'sr0JPrnQMzYZwQSpJA7L00qj9NuW27YRhkzlyUiLZlnFet9GhTyLsUzLqznFVPDF34cdrDTrAlQP1gckNoFJkOVI2UcynnON'
    b'1vQK8YGAkJ9L6qCXDILLqPnjR8/WKBm2sjwsbPcnneG4pEefCw7e6b0JXfNrm3HVkBPvGqYMGFwjfogN6DTOKsDfUz1bGf5/'
    b'gsrFlTVZ5RErUqmrIXEfRhOnzi33NCdB25aXYpS7l/PjmZmVPSfma70KvZj10aeOXfR2gK1MZ3Jiv6cgnKTwv+vpdpcrYz0e'
    b'4DtQ/g9UzUcBxtdMkPqnEm8+ptHR3FNhSWNObkr3W4ZUlytvuZqqnZ/LNwThizTSGjDQZbFWEejEemkABDSA7fA+ytwIS3Jc'
    b'g24bDD4qk+So5wGEv8XfzTRDfkhfgKcM+BiYNT+x0r3B2MIW8XJ2ccpMcRWnELRI4Z7kj8prBW6de66mXKiBNnup0wv4Ww4p'
    b'FL1B8ttQVhOR2qQO+4wUTJfAWhBeT+irLT3q3XcK/eajsxr/ltNBn2ebHyJKRUaG1+fbaTc7ggR7xIZWVmBLjlzHENkgH3TO'
    b'm6c3YeGiBV7BhngbrLAe7yHP2+z3jyEYHnNdu+TFusHNuzjaNII5+3o2Bb+55PVuP590vs8m2gv4fL9CkbwOZEetrdJo9X6z'
    b'OJTKFvbjQcWbi+reoeUgRcW0IvKXLnwDQyaiHWcyL2QbotnDMcvgfp0lt8ugy+HYqzzAhcFEO7Ckr6gKO+cTaq5ySSPVuLjx'
    b'IBcg2/JBhzqKYe/W05s5X/ipzRU8WSTcGO7R3G84vQ709Y3wldBJcvMGXtmTwQKo7mNpQPvmSDHkOkOSDgEjvPDYp/mO4XW3'
    b'+SO2pOjYJ9VscRIH9WZokRYCANY3cxFdc5KFpICVVL0m1i+JvbYF3yHVYA/e2fUMI8La2aHtdT0CuNUITkgyjUSXHA/cKBqb'
    b'IQBaVwX6KB6idsYCGi01LkwDl043MurD1S6ArlvxLR742V/vfH0UO8gyUTKuT0mHWkXeE8Qbsv6ePxk+recmbJZTnHw+IIPr'
    b'wkBEWpsx7mATz1j+CEDbnlWEpFvs03X3qPX/xgxkt9D9gnRKkyfzYeRXdtaLVEuSagZvITj+6+TyfiqYhN8TmSvNA+OJ7kw7'
    b'FN62JSDz7+xOvhd4fFh4VAJKDAgpvZP82cuDh4B1U/chnzKT6OM0jbk/Hror8TktIPj+eD2A8etsIIF0r9r6BZjDrAAkMEGl'
    b'Eijot4YzbbTKdHQrG4jdM6DS0KrgwFzlHKq1T/+uS+ifltZXTWPeO101jlvc/hmwFEGzfgqAULT20zR73fy6cQDQjhuOGQHv'
    b'FG5RdRqTom5o018fyFn/kAKCiymfGp5kBBA5QgQH0U62TT39Okp9X8WnqHZWksw2PIOzUHLBWojiY/v+G6nEs7ILamG5DFq4'
    b'ISdiwH7BPN+2wMw8U7jWkvSgz+C/aYFOcOLJOkbVUmvN02LX4tR8TEkZtOsOFvsWDYaFmNrMpUOBpSVDxb+d3pWohVe9O0o7'
    b'TFpFht0RqiNOwN3jC56vmMAUJmkSrDjwBRk/TN2cIh+RtBkEAwIiLbVVVweWwFJ3MaOF9H6zss7vDN8Q71DuJS7LUh0zCWqB'
    b'7N6+crsJFSpKmTLmOhb3omSKt7BnrfYtssS6fEjryG0Edi52Sfa+VHtSy+cLBduC45x9T74Rk/RE/uGdwdLMIqCqSRwrhkM6'
    b'IVwdA+2RpenppFg6pCLHqEzcv9fmabIO4fU5b2IjaelwtiRppkSVDX97pi2ZbBtdKA4nCw7cMWACZZbxhGvlmcfHTlfL8yag'
    b'UOFjRyMRS5D8p+qgvXPfNwPhugTQIH7NhcmdWw+AgG9PiQZBD+Js08Vq7o7bCFb3pUs2dzUD6AEYS+pHPq90B/iVn2QTA9Dh'
    b'M+oENKGwKVhczQqD6wU/aHLPuioxa0JpVBGzXyojrzzFzcf/adkUOH1QOINvu/ZvUzEgDRRajHJz2BHbYU9pd+Mr10WSaw5F'
    b'E4xX8A8QyFpyxuW0PmiuiOgC7B8gKFNeA3Of/k44XJXQyWb/kros3fuPbZoU76Lj+4MyYMEg3vpnuDwEaqE+MBGJYbbxqR61'
    b'yVhW2vyTTyVs8KfIL38qaa/Aswer1ZtIHV8lW97d2iljxyty19e6nr8fzgHvsEt1sYqtk9bD2iM2LPvX/wPuCliK+O1l4kCd'
    b'PcONzg/rRVLWT3/cDlaOgWBomOc+EgKqzGPpAHztgOOnRiV6E3Nr3QcbAnsO+J2oC6uoxvgJZKzaPAHbw+UrOLarYcir1ZU8'
    b'IbVsUQ6b/uUK9L3UEZuD4nESCCwTh80lYaVSyd0rlq6VMd28+3IIz+gSWRvMqG78x5yfOAqr7ZFqSVhJ+mPsb70mQZqLsPxK'
    b'yF613zjLazipw2ACdy9T7urYWC3imKvsx3JT9iNhXxuEbeXvZ43ry0Nl8qQ4xftl76WMGmvKksym+bTPH7tjt7A8HrTDAWYG'
    b'3BPoatW+dR3HOYanyOqPCqrE61746dKSKV5vnaQaPNYNSOyfuYmK6ysKN71dns2KhSBsNyIcJz7o74OcryWI7iqEt5PT5uzf'
    b'tkOcNOZdg5A6dR/KLo1yeU3Hf7On8LUTZhg3xRjkbhFGWmT7UbHtfl1tIEhCzo2xMcmuAVU6pghEoI/xfWiEdDVROYNJRASt'
    b'97OcJs3Hmoptb+ye18XILoO3Y4GlLOU7xKPSs/RmMnT5KLETinxpnRdxU7fHDf5Q1THUulk1YFgnZP20C3kqVx/2E7+84ek+'
    b'ogIodybuc/m1gHcJEN7OPqyQcdGO8+JdfbtBx9QFLD0CGCrcUFNmDboUCFfGm1PlodCsk7itLddu12ikgx3Oik5JEQUCIngj'
    b'OPJaEtHaOEAvxkKA78qa1H0G6FPRXSte5KCNzyt5qKExR0qy8ZipHkN8E3Y88Mc4W7Lkyzkm6WTs3kEHqg8PKaWlHUIMv5m5'
    b'M5B9Qs4wn5gUWGeeDKn6EvEnHTnee0M4kk7zCt6YkVvXedSWKShJgxYE2elmpLGW9DX91Kun/X7Yr5UXfZTWhcbzQ6yq09e6'
    b'+XYcrN5mYqC8jnTP5/Jh9lcYRlXCsBOxJ9M+DQFFCYgyt1bQxAK+VTsNyBeizHUyPFCn6AZLGJG/O7plbS7MX68RXaCdrmyW'
    b'khxBS4WPEJNpEQigILqc37aLRLCqTtSoJxpV/v+Nw8uyUwE/y7M/1e2LtB1FA3Tw3L+wA3hGJ2ERNY4Avd1jKxCDfGHE4LkY'
    b'i35/yB8F+mQgL2QRVruDgWKQK5i3VJLRUFQwP7LtHtDToRKgRToVCxryj4/8RLveBu85lZPfy9SbVlyp/xrMRVgAfnYpLOR8'
    b'czTlX3prJCX/gO+babAzhhm61DeA3LC0NQcHoWaNM+eraFFwu3icf/NIHrKwWQQSIT3j/1hbu/e+txaCPG860/YKThJp3sBt'
    b'L9gQxgL5pmgqQWZE5xxYZGAw/7SaMXlNdX4RzVL+sfhM2TkZlL8DxWN2z8gzYvmGjhn6LiBEVLrPhnvDJPsixav8eHAc6+iN'
    b'v5NYwBRTDMBICCmHCtm255APP3JGreQnvQqdz/hohJVUjjNEpfDelbSiEIHX5CDQbn0ZGKVg4y5jSJl4B8O2CEkVf9NvXoEq'
    b'04zc2Id6EIwjjIaG48dsj5R8sLBy8c7Ag1dBEFVUQ8dVPf3yXRv6JPC7ODod0owoGouk4NZRo3oUsueEdXPF+JSIzKV+8bv9'
    b'fJiXF6H9PHLv6KOTL2Xc1Z3QltNcomYcCZIz/fduqbpfssxteNo3CAYWuVyuOZVMREeDOpEFZNbgDSP7yvDuGx5Zr+YWYhkK'
    b'wI2MXjb4sysd+3OgZ+F2KoVCOYIDegIpTI2drbUsY5pUK9KGhVk/S19p+08LM5Gl8ZvRVx456J3S75iMn3fQ2sCwCVwA91uV'
    b'SOVVfa9+AcPp5OGdoOti7fwygPFsUYSrqDS6hLzdoT5nCrwg3Aoh1YRxcAPeAKiRhqte+P5tX8QsvLOhHMtktACQZF6EES63'
    b'PSysiiTebIXHHrM6+80DHtUhY6jWO2Qu2Dkk4tGEi/fSaa5jjFl3F/o9ZJOVUJLk9DNf1wwrsBq1qFn74C1jiGjC6dg+XwDH'
    b'Hnnc+wOhGAYPXTA05Aun1QBJx4CvRAiVyNhtUceYE3zwyv2VVhyx0rX7nBysWg8UyU+hqtdE5KEsizHjQGpOOeEQVcZ07qo0'
    b'eGj9mSYCH0up4xK+LqiPn03kiVekR9dA7jdlWaF0j2BKUKh5TgjelsvpjCklUnZIbXkw88mP34cHSIV+nA5PFnpwG5nhnmAD'
    b'+fM6Oq6tpFqEq60OO9Cb4TJB39/6Znd9TqOiWOvHY/AJm24fcb85Gc4jiezr+AUkzc2UGmEnVrym+nq9uKCim5QZbkBMD67r'
    b'lPpdWIzrEvyfLGOViFS5f3j2AaYxNblwU8fahFkaY3NTCX2zPA8ZzJgjD3n6VZLViH2q2V/NpMbtNmCyeXzw8D3KP176cKnj'
    b'u84AYhgO44Iy5htz/Wephj1ERQU8F8yUWegHqr6ZyIPKOTiZyWqHn1GR4IFgA1pXx+rUTyiHykkuZvVPfm+LDtPJIernwm/+'
    b'aCKtucwpaYHMiQjOE9LGfq0HqrlrdZb+J9ffLZDHx2n00jUQFS6WtMG82jfqTJkZ002bQLNHuM3hQLvEa76S362IF8FhDRqb'
    b'TJceGQL4GXwEuq1EfOlLAZ4e7M0BOq3BHWKbdfIOAerMHhQsBafMrGfVg7DxesLdQy8QOUlew+H+JvYxFzOAMraT6xPH+EQ4'
    b'6V+L8HGhmUhV1NicMxMtq1Y42cOUufRHDIy3SGTvlWd7999oF2BQkn3YFlSQRdfdbwS+HyAc4YA0YG/7AUApxxeabC7e21eq'
    b'o6nL9ROXxFJT8ixXNCGvEAO9HyhIlqjsznwKEd0LafwIFhDbAZNpPAabWuxrvkeN742PP6h+pEC/2neyIbaWcv4xnHx4ZVD/'
    b'aoR6qEmPD3XOQwRfBPZMT+VBIazqLeEt1+1raQGutZC5nEGDgyKofmFDOF+Y1palouHUl7QN4AWPzEckHKnI46vp5oZgU7vY'
    b'2EO3biYoESxhjUjbL1ngjhhdXfju/ioqhhWOMcEqP8KwaHFJf3YDJ2zkCdvr9Jg2EuBNW9MTnIRq2Wt6f20PvBPOzfKvbNvP'
    b'9y1mgZuGNT+9pUzQee4mri1OpSG5lJiLlrblbV+YUCf/H7135oXVK2fujhMCgzmerFXhj7aT6VS1kF5wc4tubWi6Tg/wJ1nB'
    b'G6kOJo9VZRHjcViBOa/qji4OXCeDmu1wzduL6NEAnRjqYpw3tYuDSgWqujEP8f9rUxCQAlm7EdqrIJ0aZU6ybF1AZLN0P+uL'
    b'O3FJ9Cw7EDBZJ/xdzuyQlc+B2h/y+p6xMS3Ll0YayUkT5q98G+Y30pajij5qi713mUkMS3S9BgVuDJN9SpznYJppCT2X09Gr'
    b'Anncvo/hhLZuZXHCS2wujbygPTtFVvPqoSK+5ziWYqOjoqS9UGQOeRv0TrrQ2b3z/GV0NYWOHiZQetd49KXyET4tvK78+wMb'
    b'XFdMzgI69TlmNEvqJAnNZ/7ZcXfDjgvOAqVtFy/emkAiXMs1Duo874/tp0gWxfcDUhVc2d+paYKb+Tk8uKXAkOUQUHHwIYd6'
    b'9QrZaX688UOsT0ydPWyiYCTCWhy7DcGFG0WEEGYQyiPjLbT4FLsHEgUwz45lu8KEt3gBxYKsJSW77rnFM0IEU6WsSaU3KC77'
    b'fhk0e3QF2iLZWZPOw/j6+L6nqjdJSoeY+KUW5m73lmDGYEYA7NAdvhfc51nACGvpDY+XcbnwgIFXvGsHmnHFNAMWWgsq9rYF'
    b'ojv4SPdadFxkYD05/AzYlSoyoqwsGsSOQrJROrUDAaOPf5rPAnsiF8usfdoN9SbqjXMFiE8bCtVBeTg0tqJM7C8DDA1khNmB'
    b'Jsl6HD0AUYVelCqW4O4+lK9/TQWsG78oaidu49QL7l765T7XtGV9j1N0bfSHaHFUAH3O4DhAae9Kumh6vu8lCYEkle2uTsdI'
    b'qDy6H7DJgM0SUthIQrOpqt+ygsXVUQ2K/LO9n3g2BKJPvgXT9QDlmmUQyj8hsSa/R9P61A7enKFZRxRDf2A0fwSDNDY5X4+4'
    b'LbWJfj/dWK5MGZmQ7Ue2QDgYrmRgiAzN4Tqjk3T8qexADTdsbSINiVegNemskPVhfSRuiNenyvAVgbWjjfxNbx7sz3q7TS8L'
    b'NFqwxJwe3/9JQI0h97u8BkoTDCm3pGPVi9+LPsqV6hG7hFoLavf53rWK4bo1Nwcswt8oHtIqDwS3LEOcnMMoJmrXoIFCx116'
    b'Qn3yfeYjx63EXg7uhgaF1xDCNsAlY8sb1J7iRBjycMhHruObeqT7mgcXE1UPNn9gUhFdngXKor0Pq4nsfj6z8HCMW5Hik45j'
    b'qseDD2wP8g+5yGPZqKVZzAKXB0cjncA7rncLHB7L8CzCTf3+3cnQyL3pSB11T0TfWu2QNALR5UJRvL9Mtc1F7NqzWqITAY/Y'
    b'AnGH66Re0H9wMxaLxsI6N+rv5bkQ03mOoWUGZ8KcheNDInw9ltfBlaHPA+bF/DOPN18u9x+H1FIgkEWXg6bc0i7/A7grM1vQ'
    b'S+Zqv5TaXkis3UUdZ7C9KGk59S4ombpoY1HQtH8IHYh7kL6r4amt8P5XxZgyP3ycVLFVRo9XDo3isAzBtEyAcbrqvWOVy57v'
    b'SLkKezVEiv83HCFfgggBmUtpz/LQrWqCn2j0Ul9dtjgvm41UvlPISApT8b9OFs0GoaxAlVrwiQ2tJjtZQTOODsamAIZKf/1Q'
    b'yZ/309muRow1a3eid/mSRYJOC3YrKbCh0dQt9nv0mzO2vrh+CfMClXRiBoTlp+sR7XH/bboz4PfsE79B3cOxRXyA8Vu6Iz9a'
    b'NapjeYwH8kFoW+c2q4puuZ5rsacB+/Mht/IOuTUT+OdRZu9q8uU3J8s3llgSm4mFSVZ651VkKC+XKAaoLi2SKiZ1rZnNh1yl'
    b'nrsZRL6ZHqthE+6Q3FocJjzqGt2VCCslWgjK6PP5gtI6yLDYZWe3N4B5XDa5qlqVhWaGg4IUrIntbciIDOVUAMtVhf86aaGM'
    b'Gpr77apS8A1gfk/mfV28icAaybszOvOjwNAFY41InxEERbM3jjcjJHYvyxoA2dBz8fjoUY7YtvIFq8aTm9VMbo97fquLNBKL'
    b'Ld8ON4kNAcfX4814zKnJMXJHSE5AgA/v+fMlbAn6n9ZgBkEPm/3Kr++6gdv1mn1SKRgfOH1OHuNaKoxuquTQ819JwvzdKs+f'
    b'6ofO/I4+zvkX2PgSIPkuSu62NgIjlUMa4EqnYU5SbGlnj3t33pNCgw31+Bha5SnettYRlOnW64encIw3OZEXQQCWhsILej9a'
    b'H40a3FAK3ycNSjuSkdpfjOrWSlHj9Phi80di5Gs+wbVRFsf+7ViahZVymNGoz0KwtYNfTfYpz6r50ur2nIdcBGRefg3HVqrn'
    b'uG326l8txF/ixA2BUIuZqpRUg3bN5A0gcA38NFB+r8+BoJqRZpvSkdMSmvlB5FLqQWpQMVdsATHdjnamg3SyQf4Xh3wkxR4n'
    b'ReeXd5VuPrq39iG4s+RODMxvXS7Is3vcFvLP032OdK3FsUIS9rlQx+3XozLBOHn0Mj4owfqwVBc3kAqIosn7yX03UwyQDTxp'
    b'ZlMeTjXzSf/fGIh6uu05V2nl1JBZi1nZFDIlScpj2pNQG/+oZiEVcPdhTTMszdIghAXCcZuTdouIxC9GWCJlOkyv1Tn6m9LD'
    b'6s5y4M9GbcRHioxxlw/O7PzBFOLLUuvXDswc3ygnF6UnKW3nyL5YEALnAXp4f6e6zfuBM5yeJjixca75hfpDXemN+CsJh25d'
    b'Trv8N/bglXUTL8K7OlsA3+aCOf7qxJMY3bV/Z3WWEZzV2Orbh2HqkinAfstuhmrEFNOVEHn4VvKyPiMEf5yzH8Xi7c4Mce4S'
    b'lGSl1/qBXpZkU7luDFoZfleScA9WFWzKhSQIwEyzlfFvKHwD768EEqbkFYrBqhpSfEN4ANaMaJnh0y9d2UjDTKLD/qAQVGh5'
    b'FhiqiHah1oNIAGQOy/swCGyDTSMJRoNsyB4tAx0247RAcI6iiqv8MnDKOAd9QzcoZe+7Sl+zu5a17v8Ag94tTam9n35lnbqI'
    b'bulTWhtmOE5bjEigZ8QgaaUxrE6E0c6w5pDq22+rbo9wqrfNkhSqW0/g+4VRhwNS5odW1fW1RR8zSRlVDYZRsMSIYB5IjmZG'
    b'wJwqgLVqHaigF0k5VtYTeNkRgYuqracmKi8KxTHakqhCAq29R1IeGPhdN3vN6K2GzZ5GPMDCuL5q/+A1Losgxc7IiMyo8lgc'
    b'EtMhrY/uQ6ZorS0Phvp3sdBPUJINRCqKZ8sdpIJcOwaZOUnJpLYYZt9ht9AEahaotNttf9YmjwufFks62MZhZcO0rSaetrM9'
    b'iSAg9VQlrw9ESolF3OURtoAUZm55GMrwMzDGeZWM/DQ9eJ8pMq1c+JpcUSrMtWkCUT4VJLt83LN4voOukncGXq8LAajDHZpH'
    b'TrcBhZAw3lBbOKQ3//6wOktvjvok41wl6Z0M49o8Eyh5Dw+6Br2VxppbbKCBZHtjxRca0pECQSNXupj0fJM0+6EWl1BpOy7L'
    b'MJ8QznLNywCv+kNyujQJqGSXHGBChSpdBPHA7xAuR/f+LJgs+VzHdVXh/PyXuYeH+ecZvvKfE1A3pw7EohyKqBupu14HdDHZ'
    b'6IymSHYwTOfWhsUwPJPz+T0CbYeydqXvL/uPz9CXhjH6YnjydWlq2c8vFUifeOB0YOmZvb18sxBx7u3etSmjPyI8NWnWQLJ7'
    b'k92uxX4V9sMzNIU872716Yf1k5QgsxUz9faDWnzINxZt2VyvpvpnZaH39+nl8oyVvLvvPEkrqjL5thqpYqoR+aAA4BOOJFfX'
    b'fDZlGmU+Nn9bxn7eRhVWno9WTU7tiFO22I/39EZEwfa+8vy+S5toIw0felzgFfpgTUyiN+nEn9ORXZs/6Vfxb4aBOEjqPmIn'
    b'8woOd7TR/YaTPLH0aet+2dI3TZ9XlOuZ7ptgA7sNnxaIur4l2M1/mCy4t9rZvYWNdOztAHo3xPA3ySAQvghvG2l3jXxRjvQ0'
    b'3sld0XwRYU4CBV7sm25zJjCreSEfpIFY/cKUOoA4X/JM8D1IS9t6CjeE2XulprRIPnLFPdeqysVfRWdjM1lkNl+L2rga/np1'
    b'tl7EeuSJnBn32XFuwStaCYPvXZLcq/PqYbr6sjNxdK0v0SpppUBJIPsAY+j2CveFvO038ylz9cvjVa2I3V/eSZph/3RMtZpK'
    b'y2YLdyMbqW1kyD3UAIMe4npCmYhmmOl0v0r+Cgl8mQ5qFE35CwdqdfT16st7kr6AvUgxdYDEvm0lIVSn7scqc/QJ8ni5x9qJ'
    b'ALyajvkFXowyA6wYnw3cYhjd6OqCiWunkdwmczAHyLuInUSk6cH3AaxOYpVsTM+fzwjHlONIJIJ1jqI1sgPqiq13UvhRhP4A'
    b'nJhpJIU2kDQVEJUtdjopnLcAIzMlVR4fPzTvsp2jRiTPRayaelvZGk1UHES1SgJJmbkKgoooNx+FmQKnX/Vvy4jo7ar7bEuk'
    b'9Qx+6qB0PWllt1SiUm1BRW9QqRRnz5yE/POvvWe9zrHytQQ42GwyShpEUjROHETYZkYJFgPuutwJiWExftGhWW2fAEVC9VpO'
    b'HcUmfCZ/pocx+dPeanttLaufWUQzd4ThOotzvIu+93S3m9rbRa0LIXLDNK/CZLdFx/dERq797DfDF48y8prJKBfKxG8lvbJr'
    b'1L6yJyQMzfyRd0MpM3qQs/EUhHy5Xfbn8F6mCcnsYQ0RcTK0K5XBIJa3SkPCFuBGPel0tkb4C00ghvUoMP5s74IaKK1czjdc'
    b'2uKcHfnZp/IIehh947grG46/pgr9jMyZqX613fP4I5Nc+ZVvieU22288W0Dgv1GHKQ8DKMmpk5LUIN3Jt90ZzyPcv/bO8aip'
    b'dCnoNNHx53EtlwrQkuOEpMxwniVmPN2XyLBRRW0rxq8Opr+5yP1A1bM9zS6YkXDl667tQhnZsxCVaf63jCpQts+dLnZGHUPz'
    b'qx59X3qPV7uLTW1E8bd37mSzbK5B1pDkG+9cU9Dy4djPof/T0s05JW1KM36VAE1/vupDOWjiP/vF2hVJ76AmyKI7BWA17WRR'
    b'LRa7QQXRuxP8tehtrAyq9SmGJ9AY4oVea5/EK95E5nGnCDVRAIntL7GXMu9WCYfmQxbGRPz8OxBEwx1Q58//B2pqF9yj4yRC'
    b'0Yc/tNT4XjXnqbUpC1jKFIb2eyX/HM0VSawaDXiB23O8X8IZ4qla5wilSTw4/iJOmub0vKRZNwbOs1RJTHyZFz+SLnAy9jsg'
    b'e5zk8zGZMJ0iJ861L0OQcTsNg1WJroMqgYrG219ELkHO07S2LqA331Zn0TwbrKbiwptWcOkl7EXVYCBSN0c/W3ey3nSloWoY'
    b'F1m05kDagp2SC1auB2BZOTmSNyCrKJh00JNEV8vSlSZ8ziX+aC5/QYQCgISTkhVrrqxJBXoeKlHNdG1r48tWxziNISMrT2WK'
    b'gr+vgVjGg3bzr4rhaECmaGIGk1cWHwm4E/XJk2+t+G4YBvRLTd4RZIuCjP7z1eYpjX9yDiBXQgYTO90yBefMIcVxh+1oOt05'
    b'xZ6SOYTvsy3qovVJ77Y/sdrR+FDZfeX7sOtXGf3ZxKZHUFEI1jiT5IVOQt1oWiEcHmHt2zIjRIBJ8pMSJvRjWZJyzBLZWm/6'
    b'clD24hGaOPLb4Lim1SV6B1dM0bk/ip3t2YqfUIos1FxiyoSkmDzfiY62R+P3cQf/T+v3aSo8iSfQHLTFaRYTgn5DM65bKN3R'
    b'xKXHH8kPWvlYfaHnW9PKKvcpEW0AlxDG3UTFXXvH792UHaiepMJzSiNzO33Egxjw26s59/m918i4YAof8NFkpgRE7TGiJqa+'
    b'ICrW4T1qkiT91XIh7t0xlZwfvsGhXfj19SCSP76Vqymq1M3k7i0ZlDihzV5qlXQCUnNeJXmw2bUBRtXwi1VhyBeSXgHzBRrb'
    b'RnHf3GnXH/HQkQjdzpNfkPXFUGNf05bh9GqCS50SGxZUxpZ5dKy3aji6f5plAHtHn6bWjZjwwPS1pod9zro33puIDAiH4d4N'
    b'PNNkTKWvYM2bbtVfQya+OPZgi45JBzNSAf7M98LcWPptz00OKXu74Y/gph7LpZMlx0N7L75L+joCg6fqMJXs84rJOCju+Lxe'
    b'DMC1sXjOrhLNipQj+ZL3Wfq62T5pZ+sncg3fA/b2DC9jFkXAsLROgAx3UV67wfys9x6SxPs7s1GQIATRwuDz7PrLciPYtHRf'
    b'b2nO+wp6Nm01vPs9ky4GkvUkZ2v0WJxpsRLbG4wBS2b3nKgaK1oeHbFmVuiZoRH/p1DUWV89e2UWfbS5KCeIYPiGwHtaqijt'
    b'R51dSi1r8bPmRw7mwip2UbeOJYZ6YAfzYCpPd+tdaqgBsjgpRTkeHY6kxJF0fD6Zf7DErDhDmggJSTygX+M9nwZ6N8p8AdRS'
    b'3BxQg4Tk8CUkVMM9YsUn/0GBSKaryl71rS/ztjsx8qll5qKMb4H0MHm9Us/EOY4k68svmkvkJmDj+sbXLyJtUwOntHXDSCf/'
    b'JexDAfZZz4soxczp9WjPb4nEAwEj23Vjs1knELBjfI8RSMvKWUzbZpDTT5Nl/5VVJTfuikyP76T6fF5c59A2v/4A/RnlEFhF'
    b'/rfcIstKB5poXxASoAvdee6R1RgcIR5tx55xupVhjsGk7m3XHIOLaUIdoH+mm9UdF2QsC1040psGlBX3OMEFVEbry8uccwiH'
    b'KS8VTHiVEJTn2qXxzkq9cf5bncllmo01MHy9vRgYLCT30Bir3DTVApXrdlw/dskwYi6PJZCm+LnGjq+Xu1fxsMpLAo8A+jZq'
    b'eQefdsVc0J+mlYbyVwOLOpQ7AKvDOGIwURU3xRsBMuC4VNf6NcnqTq6+PfwQnLkxHAsd3DDzIfuW1Tso3VGuxIdRmvY0EQ2e'
    b'08so19YlGRptXQZYkev7V8yffvPFTkAFjVpJP2DOGFcR23eonorfyf/kuo+yvhBUfXN8QqZu8D8NQuBjG0BGOYGoS2Rloxuf'
    b'ami7ypuOsm+thZHN+Nx2qbzAjG4YIqUYY7I82rPUEPwjZvspEJWdm1gjT9Lr0okO/aCloHZCHTSLhEVCX2c2uU4eXIf+algH'
    b'EYDiKd5uCV5wQ2mcuS7EQxSD+ijJLRmDygmjDTMsynpA5E++6cq5+270CTwOLdd0gK0MqLvjv8uWcj3v3S228jMjgHfrMsbf'
    b'5y/n1npfyo3pIemhIwgv92J4kXpFy7yr4ldttDwJtOcmka+9nqZSwquzpTCav2cAuUeYy4FLgnB18bqz8qtxbbWyPPI4SKvN'
    b'SLvF/VFfQXyYa+bJuoTKwy/1mftizFkWZalgCZj11hAVJi5+S/ax6lZ94SS0lw1kOKzCzZAuEjLOS8+KJLidBA9K+SS9/DZd'
    b'oHm+82Zt0TBVuK+GhxQ16Lc2KLRkUFJr0urf+rvgeY1ffbA2Vd5S+Q6FZM6icxFquPVcyWEk5oh1Hbg2GTCJM7Gs+nl6N68x'
    b'a9bUiYJSGaI12WMXBCTn/P5JLIoJQIVbC3XX66wkHDyB+DPusGoApXXRUJNgJVsnllT0uUSqZmqlsOCYvoqpODubD/5t3hL9'
    b'BO89EkalaB6C3aL+asHxA1LnFJBM/P3cHQoVueoP/hVVVJERWpovLT4zLOgkstBQqn0+ttTcyJt1wHqi3CFJ8C+HzvVlrgpT'
    b'Kv96CsjIId6M7Z61QlGJn7SIwZUgBxmSCS+wMcqSQ92UguddjS5d9ZzkKDFi7kjw9OKPwY013LDv4NSFM0xu9Rrwn/G9dBlJ'
    b'W0STQ950TQzEBR/y3EEQ8qv6tyPVjJNWq3Ypc6dNo2t7atnQGZRwE+/W0l0gM9YpnyeY/g/w0ToDvzC+hngCk0TQH62lK3ag'
    b'9YYI2vHteJZWEF0VpSgbjRyjQL58v/yON7wlo/el98Fp5/p4SPaq6B3QAMxYoFBvZNg0zJJl0/7TTQaW232r0pvg7EaZXIBN'
    b'i3AFIRMSZSZ3FagV4oUxgjfDWhgg8LU2kMglF9m5/ZuNZ1YJfNltz4OxuYa+pO02aEd3DC1OlwRNmYYEAlfwDYNLXScsUvem'
    b'VGaoQS0V4dlTQnDbENgJKgdm2NmPCCt2ZGMD6HtFV8irB9dP+JwueFpFQQwVIAeHrWGVzVUn7CeJY39CGzRs7C4BKGzI2NvA'
    b'rGnxGnPQIXOVUoHYp2NpErtx15bM9o1721vpp0lLkUHRIu5cuZw8iTGJCFPRbAULI1qP5VkBvYg79hXdbvvNbVMqy8rwmH5a'
    b'7NOy0N9sgQLZNEKwm0zp+3UNEJk6XHMS8LtlMz5+CyPwUXW3nA1sCuo2BfT/0mlSSQ1LIRb1YYWrwPDgmCClc8oY+B0XmBt4'
    b'bLKGAiJu80imA5P6ctWjeUSLJmoN21xqHtTJ1qnnvGJ5ybfKhmp+mMX1Bm+jEGbLgpAbudnQg7dFZYtLdJZesg5JmTUIAyvD'
    b'EDEnsTlTLTFfavtUk+/6LE6nd+E6Tsz1SY4ETg2MDYDdm98orGfinQSyFOX90ZcXeGJHIDrbA8soQwia6TgD533nYjw+L+1C'
    b'trAtSqjgzQKVmCZ9vjS4uwg9NXOT2vZrzfw5uZj/3i2QTtvh2jgj5/U4y8SBLea+No7sw09cFvGlETd2Hbcqy9GhecUDqZnK'
    b'wz5IKoLhuZo1/xdTJmh/L577hitdEgMGqykl4lMWpLkQk0Yz6QMnWOq2cqTxtWjnKcs0VXz21u/I5vXPiV3XNjV5roqiuCp9'
    b'+IpsC/i7H91qPU6ON2ExamIKDv69SCGoOarxzQ6ns4wmnlaLwoUvhBG+qDta8s67tK03SbB7b8hz/Y9EyiEQxneOr92JjGCV'
    b'B0eGDMpsUz5KaK1XXG0A+CfVSH8MD06vKL4p8rQk8INVFsAZdPyAxNLnooMQ0MiFyciSTQox+IuIJEBIhCmnf62/TfJKRJLT'
    b'3NvXXCpGJgGRE2PSnRRbPUum3dKBFKU8nsV0X3cONS41YNBbOFI83R/GnhRPfBw7cY4+gHQ8NJlzd6uKkVWTCxePDl8Oe52F'
    b'WQirz21a0fq5iC6C05Gkg54fH2prNk/vXP6w5HJ/3pM1u+uqYJCsuEP7Zpny2dOOghguv6Bn9YtR6Zl+yrS+hky5lo0BdbQm'
    b'sjvOWMH2TMbIRhlQInARr5ptTGydC4fxweuuP5ed0USpwSWRLauSyYk9GBIKfNv1yssP1XAHnFvFxU3BwUKbeeq2WqXccB3H'
    b'mHsLh5A2QI5+4/cenlywIevm8MiVZjN6oV1E6hO3Y9/R8LVeeUcd9b0P1m3Ty3fD3ZLERXpbcgA17u51g4zYc5/xXocLhGK+'
    b'Mo+qtbdESdIFOkWqgJjdXSOBFWAeSJx0FGHscKr0wOloGdX5v+y5tavowj0K6rMIbcThTkXsYsQ79fmKaE185cyDY2ZfQTxE'
    b'Xqw8ADM4wOIaeIvAVCkUxdWKxaiY1YZE9AZjT84MKIk0sg+ghMQ1x1RayE+ii3GraU3JnlJuqNj+qlSf07j4y1gMFKflVk8q'
    b's4CfoZHkU3SIiicBkacIcor/V6EfuspwJ49+LEJWp/fwo6sFwBAh8f12w52pdTXhoLewx2d+GRACfuSW5PAihLTcc+J6BHjd'
    b'YPa2YAak4teIQa4iRaKQw9+LtjA+yTedPQksbb8+Tp7VhLIaXMhJmia9AK1hRzZuj4F/Lepd3jbvx6cccv5Hx/Nst9zUquLf'
    b'E6+lyW3LFlHho8014v3/34460wbinOrvWHd6maAxXh3hHWtP5Ux4PdWkAhZljcHE3IBHjJiC6kwuuK3bil2GgHefY8a4P0yh'
    b'iMFatZaEPfeBVf62KsFnf7/+P3J0zpNTB7pgR9Nv3ZuvT77gdBzx/tkvNTLHMNRf1gdpNtGSJHlFQzmxKZ/SIrkw1epiwcea'
    b'kkcSHtNsrbcwOY40izv5ZRxOamNw0gNCHS9fkaPZQ0FE11hum64vL+jGdNNLJAcHS9msJOfy0xEZ96kQfdAT9NbSakrRfPh/'
    b'2GVlHhcSaZsAK0HFS9jtCIpnS2n0TM40hq7rBFZ70gF5NKPECmq35D49DglhMpJxjfmkb0yrrtKZzmpgLKwEo7ltW2W6Nm87'
    b'Me4GaxihqI+z/YOpcW4zrUNS2O2rgL1cdAO5uLVmtlPwVxnqPG7XsOCumKI4PE+dhkWoW5J/jry9KErrzy6RjT/6C8Q3sh8d'
    b'vCw3HTu8wcTWi1ww5mxIjDhP1POIT7qnRmFvaosDQy3zozkO5bdzjLRFF8YwT+95buemq+MPsLKg3k6U9DK/tvyc5peY27yY'
    b'loD8JnrzyOpZWe5lK+Lbn6cf57UZolK/QseQ3QCnsopKecf08FV1dTytFKJ4Ypcom3NNa5PDv2HDBxzmbomQWidBLnAX0nIS'
    b'a2yvTUjTPRKawXreMTnWf/41COIP2Dg64rjcaDap8ELhIePryNdIyxdb7Mc31ZkV1SbAY7L0npPEnbMUrxkHFdcDIAxBqExO'
    b'r0yL5f8eeh1R97Qk+yp1UuEFikTJppIXKe5JeFAWx6BK1HB+UBmlI40YWVl9IrhtvdJzBg8lGT/NyA4slzA4otLBr94wHp3F'
    b'zhLI9FWajoU6nzW+kpli8+S+WDbbuDfhVzKBDFasxa67k0csdvOs4GqQvzeyY/zj507B+gNeWkqbRjvsVuJgw6SBxE7rHrfl'
    b'sqVKxmqsR+5nN4djTamZfcatCBsbzlN9r1Mv0mLgotOnUwkWft0XO2a48XNFauhbeijNFFYtC8arM2JwFX+FyQ1Zmc0BKVkS'
    b'QmIsIpwjI0dfjNmFm/B8FBVF68FeWIYhFwVTiVune9W4+BQqGo4aR78ysdpn/mByHeNybsi7bczmTjy/SZxoz50eCMiRuXS+'
    b'M9mkTG67pIHZCutPJj26P4DG6vpDIt0ZyjVbTcrUa8DNPWTmBDiju3FITvaWiZsaoszFpgx1gAyWS2jC9R0EwwW9hl+OY68L'
    b'RPribhcTrw4Egmzq3ABzh4EFHEoCPpwGY422DOJDbAXgxxkPiG5UDzswBM0XrqRPop5KLUJ2FrMFaTW5qJ7LGxSi+G/MujQT'
    b'HCj/6/yV+k2dUpMqOdbRGzI7lV1T6KLJRs35lSGRA68P/pgX0nImFNOHedbWMHF5wevRp4aaQIRqF4pPwkMat5i+u/kms/IM'
    b'ZKvWUlw0Bc6ZHJnGBqFxJyWcvuJOTMbGaIYcrXOXQn/6T0IDGmh5d6LfHTnhkJLkveO8BPxq5kK0u0yYJKfpfqkie8VWYxE2'
    b'4zP8O/zspJok9qWq6kr38KPf69j1QBh2tWuKdEOh/sdp6Pw0Dqa2+KUJi/LTUdGEnSrTyQLtL4Cj3RVM5cx1VTJIdLiudlwB'
    b'kRG+w3V5+MvQ2tknSXLUsfxbzAj2CLRnuz1doZmsJnRIws1u61xe9FcZi9uXTK/pnqTPezk50lWQFUY3c/tgcNIHV3ErqykK'
    b'iXavRyObXRcsPAFJMUEJ/ZE/tRcZXp8t9ER1hvQYxCelPVEXk7fTalWeweItLcWASP9HXgOKIMEiOnOfjVrHMqlN03maqfIk'
    b'PbvbLFq7mLsKk02rBcAY0SpAAt5OiqBmve+hfhK9j71KZgFTeYeUQzT0tHOg0UCxDHpDNvy8Nyu4ZaN7+DpXT4G1AJesYTNi'
    b'Y5VaRvUOpAAl7y/sq6kidmn7+KRJFv74ge6odLdn24ZvptT0+NY7eiX84PPWp16NcTNf231SVvPqM/oAOngqGw18X4veKepV'
    b'GqrtqRrfsMsppYLqXym2Zv43cYcxjh2HU1Ej7B7r2ican4lM1xU7edgieb1DiuBJQSBrxko7x5koMP7fWWUt2ouqM7b6eYTB'
    b'eAH5hD3JEh5JfLEFJFukAt7hnOiua1T9bPatAigA+Coa9E3iarGYUvWbk+1C53Qd3jVjZ0U5W4qA0+24pxV9tndcOUInA1gi'
    b'wQTruKehYOVrVt3b9XqATzNNU0QX7kQRl/SswNvLmTYT6l4Co5U6fE5vejn4tbzgUM505qNdMGtKDiBKB5B5U+IQHA6AaKGV'
    b'pFCeZQBMMIjA5d8kAo8Fcz+NJ7XLH68Kj/o5a5ppIhSB9ZfsbRmTOufqoyo7aslitVLIaDOzCnvGbtyXZ3QkSCjpR18nY7r7'
    b'YQ5EZEIhQihuI+H5sFatp6s2kTCq0c8/Pt90O+3+wZEGUnbpAYkOk/1Y7QLuCkiMWituTwBr9ArX+b40mur5nWXhZeqY9PqR'
    b'3QAtIxgzxozMgRd8XQGze/rk+5zgefMSNOMRF4dGAcVp1iI40ABFqv83jCi0P5Tmbtc/by4/KGWb1YTmsn437kqyFTT7ABI3'
    b'fsEc4uh8p3vaenqUA0iI0X8g2TJ//ueoGqtvm5uANPmo7gm5gykHx3VH3eg6Pm2+oAhANEV+aMFzFJoL6eBESM6gZZvqkgMu'
    b'Z6c7v3u4xaeGsf1nKuanWyU67zgJ9DcZ7Gz7hO9En3K2lR7R2pxpz+VxLni0P8pobWHOyOR3X22jgKYQ2/RuAE5hW7P6isgY'
    b'tt2H5SYaNRA6IOIN9uno9CoC53hA7xsNi45vZIaICyEQGz4TGCX/AIGbXwQSdcn2Gj+yaegkOvzvr7D7FevKXIA2h3q63KPa'
    b'QEO5zazny7UMw8GbIs3F9H70KF+1c7oy3Jo0ShyYtGxhTLIDDCABK5U4a3dTQkl1EEG3GYcjIkQCt5TMK+QdVD7WGRBR6aP1'
    b'jde3KCMYjGqPJaWxmLSRFUSDzxlM0NudPjNaFsr5nVi05C+un1IaJtz20W3hszbQovDRfvn2wLpycZ2TEjsKBD9c59fZW+pa'
    b'uJRYySCBsSkfxpuG/rgEUHkEcXKeJZtZpAlOynA0onV6897tl0E63iE5Q5nPfVtILvlA1wo9IPulaSu8EH1X4Ur3a0puqg94'
    b'Vi4RG2Xx8Q6TJOkJF46dhlwVCYXUa7DJl0wR5pWGl6POwdFV5rwZWphKU599KLniHpSYQ9sFJFBK6mIWqRCSu9R/ReCwWWDk'
    b'rzE+i9/QRbtShmB7Od2wKhBzFIOsTaLcD4xa8Am9W8Q8EvG/8wRnc5C1p7EGrsM1hYKemTfEQeXTO5pZNPPvDsEmP1WW/vfQ'
    b'N+TpBn9Hx76F5zVnlSwG181JRdiL1rJNFRrl3bbFHFUFeIDmDAtlJnr+DlnMwQXErpfADKbEmeySR6M78GV7BKYi6LNIFqmK'
    b'd9+MvO0+lzCrgR9CMj/xnDj836WQNt+RSYYZbImam+gqf0asSp7SKHNaAfwrRtM58qOvoEmSGg/JFstQIp7dN46XRA4z2K5T'
    b'n8075YLXy7qiYLe1rP5UUTGJnv+g/h6TYU5IZnhDzZOnmRXsSXMzLTWP7FXujzskNKm7AAYP1DVD7elOHJ6UcQJbpuKrNGLD'
    b'FycL7EN4BIIX1zOmtLHf8TNCXjZNaovidP8h9nwqIPtVjdxuSyAB29xgqPSqBZ+UGbaKb/GehQpl28F/3hBTr/lj8c8+4MQe'
    b'cNTsQUdaRDoe2vaUy3Op6UzI06sBbM5kVayiAj/GuTDtlMn6LEgn8SI98DdRZl+JQ2OLYJDAUaMZgKWoyRrwLWs3FPJVopmE'
    b'w6e6W9GNVp8faUIreUxrNwnVmFVu3AB4KYcOFuxr312ObXf+Ug+r9yKB7Oku+4s4fKPrOpzkLA656SVliH3jbYf1EWL47pOo'
    b'YJgGk1ttyUAn9lzJGrQ4mwW0KGW75IMABUQ94LdEYtNuMGDOuV2fAE9Wum3/tH8qVl7swR+98VUgUgCX0Q2AXKfUyDc4cBQn'
    b'El0r70xXYrPaRTesrHkKtCwto09kN4a+cMcWx0zUJdCQm/tqin7P3zyILpX7waa7jEeWcuxN88TWpW513tkGnDiqmbFmz0Pe'
    b'CS3CNcEzgfXkQP6kjeJxEjhWnUJOiZc6CS/I12j6KtK0U1ufsY2t6vpVjqpQVM9wVoIgJCkuReq8HxoPYK+T0PmrAiCmjbul'
    b'WhMnmQqKLDkNk/gCd7qNGW2e0qR7iTvjiC3gk8oflNi1alKqUvcgtLbap5ZSKNLvFw3kRCkerDHRSWEXpOgmrCE/QUZoQk8C'
    b'5J0c/oHj0X+XwOqi725NCRJ01pt2ENl5cQsY5HG6XjsmE4CpOHnQvpXtT1TbOxTRk4DdRMckWMApiL9D4vuW57XyYygIr7jT'
    b'WNqie+a1Q0oyBUBoUxBlwKugejRaBPfqKTpJtzgbm8+xgbLXIsj4l1/8vNMiuxap0ds0PSghzm2AwN8UutzEcIhCynyzKoBE'
    b'6hhf1ZA3sEWNOW4iiQfMtB4FJwXfFYmoHH7HIAFKYEEMQhR3b3EDz5Q9nCKOrZPJKoy1b/CDOpvPUX0+4tYZlhMEYE/nzEJn'
    b'5WXamxbIn5zhdZMS/uHqvWf95iAzoD/0olrOFlahhTJYxvISYf3O5vm74U2b/RiAVhqmWbIDjcxACSOZrY4f/M6cEc84cj4B'
    b'K5WykN0P51Hz/5Cmt5Uklk0+IvWBOsU0WVJJTA9tDYn+s+/fsoiFs/zZMzqBqOCvDS/4En8AvPqhmqE1Uvesfvh6RaAK3DjH'
    b'npNTTYARSC8xoGKOTZZ0YPO0mLIaip8mYgDOGUV9y+aF1UBqDWAJ4VIRPEp6ZNu2xs2R1qBLaS3knvah81ZgsmR4V6K1I4f/'
    b'OrL0bM2h/JB7x3WBqh34Q4nKvk/fqt+W58dDyIHnA7oKBzLujlcgqDi7xth7hL8KKjNeYIJug2g65eM3PERWwQPBSowLHSal'
    b'52p86MVppjuDEwGB0bWEFRx42hZtyBnNOShDYhhuHZhJPmSwbDfxUaeXsa2GGQEFyH+Fb4J2gydLvpQxnW776ZBgk3oHS3Ws'
    b'vCma1NKHcayV58IeoFrw11d4Cd3DkIxSUD3XXLsVbJUdAbwRdwAqL0ZiVKOu2aeoulknRECoVWmJZnSssHuVLB+2CgGzkYAw'
    b'GKetmnjl0L8VpylqBzWzHiOrb/sAo0JUl8+XtMjlFA/HKHUM0f+jj/0qT/bwI8I++WpnpOiFJwoORIDNG2OcP1ADv3/vgPl5'
    b'7oqa/aufcZ+wYZkDOMDFc0RmwfC2b98OA/rU9RETVrCemeujZBS0MEsnW4wnYCnjtpl27wbSQjOC+X2aHWohhpbPSA7mcVnB'
    b'GWis1tSigoJnZcqVf6piZCqeBcfB1VySy+VXhTwPKMiCoUeTTnuZh5//SQAi80UYyV2Lay5qnTNusMRP9kvPMbzT7GupCdsG'
    b'jfQt8x2RKFEfHkdn0hc3QKBcwsTs0PXBwEzqEaxP6jcJj/BZndfpR2lkzJTgN2QeycNeG1HAE8gwMa1CzFSL9tgO/J5Y7uH0'
    b'MAOez5/GGwMjlcT64/Ls1zOb5FSPCfPujNWQgtIPoscvMzY9mC4JKQoC1ZecHkW300sPj9LxsSlqnmH78JuLPbX3nzmVjmTD'
    b'1QN35EPy/C1JZAzKDxpJv6W7g31YekRHinJ8CTS+hZE/yrh6uNt9PSQ9424+fqOeKTrIk8LP+KA2ScChHOkNA0RRV01wXg/V'
    b'm72JFD/bB3DJS8TS4K08MnZjSiy/cycI0RzsatKcUk92eCnRNRxMXHAeGY7mxi8N43EPTEX9NtEuQSGnhHHQRBgsv4YGKqtK'
    b'MYzbIF5amyXoKQlBRGuinhfLiGDR7/hLq191fzys8tlYmOSqrOq1iDfvnJLsHzUJXXuCXzwQlZiOcGk//o6ImZlxN2YzRap1'
    b'VTdqwXLL/UadjH/k2lsy/hz5xzqiGBrNJ4+vp3ND+dYHnYAJ/NqLzL5SlC5tHoxIILihv9Snr1yBWTKtzP7qD0lzvmr74Yza'
    b'xGN2wWq1uooS3sMlul2vY46HmMnn9OCcGbFx/uBZdOR4cOERIMMOT6MRw8o/MLcKiPS0vXOrRf3sl3FvP9iEY9hp8w3QpP+p'
    b'hiufm2kzX9QagriLnxviqCkzAUbeLa2+RUtWhIGrdfPUfrePXawUAU28yiw/ZqgY3UwmuW0HTbUnIC8GCX/15QInN1NrZJV2'
    b'GMIoILoxWhaAJgQ42sBrDBNFrE/E4IcMpeGx3XWuZNpf+YZUSU7rB8dutqCWSHIZSwsgZhgROwQ2yImzf7gFZ98UW1UkgoMA'
    b'Uzzpb0LnKDlN4sAH2/NVZ8pEaM3tjN42U3+4CzFDf75EGdIon+d3GctInLRq0o4VO7aQQVfS3BL2FDsx4yFbFCzO/oq1X76U'
    b'5haAceliysoLdjrP9HRiAGKDXpqFCdmr4uy2ZiXxpmuxUl25VNnsktlCAojMRnN7VMSH5aDRaV6mbrzBLF3kCNTcDEsAYOEO'
    b'9KThaKIbQcBTyAoUkM9e7AQnOMFScwgWJ/z3jZUjOTT8+FJ3cShlIHlwx167/RjA/GN7Tw22Wr1UsFhO2ZjDdmsw4Jyz4xd/'
    b'UlE77VCk0nLj7HBL6p1lQ5+KDhtwCbUYdDw6MRli1Dnfkidgkc1ZW6z88jZN8tPVcqO2Jrcb6gRCny4vEDNEG1wNcpwaVYEY'
    b'kVfVnE/1ex+slp1Op1bCkFHqnU0dEt8H1fP12HTmPRdorBmIooLJ00f/+Bt0lI5wqRbKb8mS7ogujAEoHdTIw2SRJvSr6Kje'
    b'o9kD/E1cX/iNIRtSUds1yBMApajUVW85HiOqqtgkv/CLSafMQ1sMV6wKuGNIahzjR1R97x3Z2QTyw1Rmuv5IKYq0xF7x1aa3'
    b'HROmZ3MnlCUQ6hQYpt2r6NrGWEU+B/HOCkA8dH/JvOpzePlc3g0/8g7ymxpCdSDDI5PqX5v6D9gufnFZHWVQqpxoyOF0bb5f'
    b'm4RgCSoqSAbRSENB2/OG1WB9/AguegN/QvmzdBEv6ZbS8pd/ejgLqbytjQPPIHZM7C7zK6R+jMcQmBN8BR9/wtA4ncNseZjp'
    b'deQcJU53M6jhbID4H1bWjy8NRyIj+lm44xx24sY5c0YNyTEbDmOV3+HBdsUO5NfXmu9JZ4HrE5pLMBpidoOc1Y/bGQUvxD/+'
    b'GjNGwmUkvvjM3jwEqJpu4p6fccFka3GVXW9mUHKIAv18DXt06JTV/k0l0/BHem+lvSqdvtF4wcwfDHtPmOdZGOFnNCyBr40I'
    b'UP/YNFHDYpRIUWx/QOaelPDFuTW2tJPcDP9FgShNk5pCe+tR3fpdO+1Taf85DjPYOLDljz53ZF0f9HHzhXtMhABDOmeuS+fV'
    b'OsSQnk9NEM/22E7Mshi5qxVglieMqIaYk9u9yKiLKGeZPWyLaZZMY0Kz8xVSv80XLmcpgDhdD79dUtMdTtke7TVNBuQLWkQE'
    b'DShNRvZTAp/Nl+s0z72vbhfd1bLEGdSqAl1X+NdjX128rTrRHSs0GWiEQ0LIytttcWNQwFpDP/OPZHLt7ewwkz6CJcxEOp2O'
    b'gTO8nqE8pZVgt+gQbOSg2aKFekfBS+xDm/dw9rR4nA/oRApjieQ+EZkULRo0xLFRBwwFhYWrG5a6XIO4A6nLPu9TAmne6lGZ'
    b'PioIKKQ47090GZt4IarKipZ20hl6GlhaJZ0kovrap00SVKNPVIXCwKI7ugcL3iP4TdRUjgZcElgBP6b2kKZijDi3yyZK6HNX'
    b'QNt58Rc+RbOuf/rPD/LWYyQpu2foTXkvJnc1dFNA22GY9FVbgTywtKr9cblidZ/vZjIoN6qER8cUfZaLhmHojPUnrv4viri6'
    b'VagHSmGou6lYxpJRChbre5+hzRfUpg00jt5eRsjBcMFezofPcnXvCRbrQtV23kUlxngGIdFy952aN2N6w1fdi4KKuso2p3hJ'
    b'LstkEEqn63DSLFZJktWWof5JiFmi0QnfP7z4CEOELaAQUCTvW6t66JM4kJj4CFiTY67TdBcZzjW0huwqewTLgx9ZcTsy7Uer'
    b'tHuAgt7OXmT0EwiIY93nIcqOtfiA0C0gsctQweHTqkGOEqWt5EqxMXuoDUqMGYmFBoa+9fG+lXs7ziVtOxMAeZ2UI0Vv+kit'
    b'2qxgN7mVXPH0jyOQz5DncJuswxAb5MAl2psEWxL6nFYHdX27HWNLeOutkBivt8xoZfljbeQLZ3mqi7oHotpPX5cw2BSgxFHq'
    b'hgGbcK5VCHvKodNW4c6qCWfn6HKh+3KSP2EPnny9IUIv4AGg/2oDmQTXg/Rg1dC5XvGWDZx2gpAyDG2IknYURL1wGTj7Y7s6'
    b'OUuVgM/WEecUuajc7vpeeKumUmalZq6AxoWrTIIPrEHIrR7F2IBwh9vWP7FkAY9c3OxTBC2xsEBLYxjO2EPmPW9qSUHY2rlz'
    b'Bcm9c0KwBm7UxDeqXcwUig6lfGp5wwWdCuVALGMLFSsehCJQFZqfo8u5UI21hFEgwS8GtfKaF5BadCNQmeO83QPJ2WehUnDv'
    b'yHh3XCqIuMGRPbyEmbQVq+Ajjy/8XTWNWFB9G150V80Sr59NETs8VAaKxcW3EpAlpK3QCs7G/fDWV6N5C6RiXbo2qYejxMqO'
    b'LIgTMDhrn9fQOHgyLNRZcBslWNlqunGCk/2iAAQhscYdjx0H+s8dfSwzbbKQOXIOno3EYF2Q6goQi4022i8bQQ+FzPERFlRM'
    b'fA4yRqBIKZ8Eq8Rd9J14KavLu7sj2icBD6qqspsoQLuvJGCuewoidwnGwOmTg8m8c8u6wmmJIL5g+XxNL0G3jPtRDjNIm9iE'
    b'u97oa++cfiWp5A6bcmIpbL7WNXeTe0BaPVl6G6Ss/08F9LK7/wO4CJS6Ro44oHn3fYlSjKROLBoPFVurGGlAongLPDrNEkXJ'
    b'QN1PNwHwL8jCjImow/LdQw6S8tYIp+Fc0wSdGYo/WjGlBLtkMawnZDTCn/qHSbVEz79LmKW/ONVNQ/el5962Uy2RqWXVRxT7'
    b'YDaxdLWWC2UebbF8Je//MzXDQ8jWwouNUNVh9ns/JQvrGeaG444VZEGFwwOcEiaGM4dEHtAIbItkDRRU0guojyJ4CuzRinbJ'
    b'A01h0kX6vqjSPpZFVxnJpwsjcMlY0cLkw6XOcx8KauPSQ1f1zkbyWgCmc5uIOLXMYJyjpj/rW2ozJDCpGBhZ/ZY8dAvMMfVi'
    b'iTX2c8woLxo2yTwqwUzRH3gpXEOhcSQlfKTAcY58yxt5+p1e87Kx9t8lZ7mbECQOM8iP2nJwDtdrB1u/soHz+xrFAU6AFvcS'
    b'hVZKvvisrA8PcnE7vUVRDxcs1mn3e8+XlwjHnmn5Ul2DPm9dSxbaE/q4S7aEHFS+b3IU4ed9OwTXl6pMzOMW+N4wmXEWtr4A'
    b'aghBOxZeG/FBf1rt+HjsnyVTgTyBZ261TtagVpNRwOX8asDMMft3sKcDkR/xHLnE7Cje7lDby8Ip1sr+O5PdHkmw/9dO88Hj'
    b'xyjBJsTBRoYYMJkLJ/1Q0Fn6O6eXV7DKY27OVhLmkyRgcjkL+OQDJ5P/oZQ3U8KhAPnTBvBupL2dxZBEd+p8jZ4d206HR5fj'
    b'dsL5dnEqV/1egxZPq6/VSwNNoX04DMcmFdy7WN6f8Ce4Ag6D1TCo43jTyz6oSLXg8X8GIp9cgiDvlYNbgNH7iZKjh6Q2Tiiz'
    b'gOBa6U1I5/9+zZknciRauXCa9BL1NSO5oraQGecKKasM5H18FQjnlvXb6jS5ZBGIb+AsCIBRP78uAnh0BKhBtzXZbgACmW/7'
    b'ADUZG3O+REtgObU2UWyQLUY+gRU5O4kfpAPRScGd5W5jc5nCqkPQZ6VtckSIi7ZLt3fM9vCtIar52JdmmWlaYw/PLMrjrf3d'
    b'yOXKO1zA87Q+A5uqGU/cErZdeBj58jZ2nTVYGSPbBH/9VbudCIvWYtKLr4hLH0CgfbMbKA29UlKpaWnYWVZTC+nRmu1QOReo'
    b'OY31RyTsl3CD/7pwvL3x5yShuXG7+S63fQbyS9fhFBhpzU4DPdzE5dHHUbZzQpw0/2G9rXPDWw5jbG/gw/75d3BTBvys9Pz4'
    b'UNI/M0rqSxrGkyG5Gyj5me6gzxExfiCEMnEtwMzranKgN0GyjtWQ3ukw6y+gkLM+WM2PHYTOBREF5DPSXe1dJjeDRcDUJzXo'
    b'iRJfbnXI1Yz6rDncTjlf5gUY4tq1qWrx6FyIR1x5U3951I0OqOBaqVDaOziZopp3EzM9SDHtHFkwCvxRNisfu+MO6PctQ+Hi'
    b'eIp71gUdHbIUggzN0vgs3MaFZ5gI81Nr21priobSDk6uTcO60nPy2gYQIFwPHH4ZGT6gbuGs2EdCUPCVvc6f9z47cPQk65XI'
    b'pj1W+d+SHtx9W1SAUChbHuMf9zfWIQLMnwRW/nzklJolqr490Hnd35G+kYKCLOhhO6Wx7uOUHg55y2TTxdVk0gmssxar9NHn'
    b'HXhnhVUN7IvmEJGNwBqS0PjJpO1Quyu84mED8biS4J8rqdgMbD+C2vOi2hYxznNTOiYi67K1KPXsZ8x0+eic4pjQRVVk1asy'
    b'8vjWCSj6YARv+sQvA70LYBMXZJgJOwEnvBAh5DNVbak7nET+pm0fbcrc7PRYeZmXbj3zZjoTVGEuOMQpwx2Wnlq5xLVlNLjz'
    b'5SN9RAB1Rnk24eGMDXjbx35487Kl348ZR+S7SRTo61ALA6Pc7ZJIQurkNHGZ/01S/fXBS3KkgoR+VGUhRumFx/j1LNegSSKb'
    b'V6UWcyKKVu3/sq2rircJX6tLlefuVFUyyjoHeQtjTB0LgE36GET8b40wfhtYbn4482HzeyNzpqCChAGDhklJbQMNIXkoxeVB'
    b'tvNd/wZ2/Ng5yL5h71JpU9AmKWab1JN6Hm0FBMF2mj/elsLs8Adb3pwJOcZIxMUeQHnh3rrbbZ3cjbKjBpLUuBbRohQT3FDZ'
    b'sOWFa6PLg1w0r7X3O/+UDTDwHC8uF3ywzKUTrAT9vvs4EK+WRrTaN5bmmUQw+WQqAoo0g1lr3xQbOgrFYFiRTLLYnLAOeqsT'
    b'BsKW22N+pxylhUp3Z08msitid5xZsJE38xalKKRJhW1lHdHaEsGDSyGSgyiZ2lpJaqidkTzxV5/bU7mAPx/aF2i8bGrvuU+8'
    b'zVCIyCw7RkRV+ULadRndwWYNYfnQr85OZkcvF0L2ASrdxXZMnBc/GgZ+CbYu8gHZSjp0Fv6Meculx6ZUgL8V11LiUu+TcTW0'
    b'4aoSmgrnlDXl7t2GmF/RzmulLf/a8Q6YvIgo7J+IlzgkqtGiTR220iq5JVTWm+l2qiaQcpkEXdlDvMDH7Ml/oGlIUpr/cvrH'
    b'8U5VpvKvj5+LghEs0GV8GFI5qkBTiFou1wecB1M6/yJWKV+3ngjy3cAXd2PZB6GuklaHQQHsKJ/FbZ/EbYNojkgCul8d/0Kw'
    b'LsMZ627CiunaTzzIW/SyxDlxu/57YPsnOT2ebCSN61rGSKEDarDVrJSViKuskigzEmiuCaKYlA2938f+KKfnkoCJbswgpS7s'
    b'HE+ww6bXsoHV0mIBTqLm1GQo6xl20D3360Qwph8Lud3/k/6olUuzaURet2+hZESZ07Hj5oa7cSn9ZSI1OPvkF4amyE/H9ACv'
    b'fJopn5LKkqQgtDx9LyUR7xhNZg4Xpx4hIU+f1eBo0R+hKVpKRCsosXEStCH+jn8wVeVQCke08X/NRGUboJkMZs4CwPM2VjdM'
    b'zbJL9ngQbp3E29Schdrfda4btgJvNaG7SLMjxrWJwGAoGXGamIvvvlPOUVyqfIkA5ilFaE3i3IAdg/rkcPzUv7uqzXpCTAGN'
    b'4FSWY959ypQM0KG0CMwYKhSVw/+V3uHshG4cNw3gcGF2YH/+p0dM+BC2eCoIIpihfyFSqtZYzHWt19mVUmQbVJZHjXs0o1Iy'
    b'HUCMdT41jPFv4Pzu9ZcdbpAkZ+F7TWOMM9Dm3nTLnD7au7Et3euw0LuSfJr+jk+7Pdl+Ii8VpTgOrmuTCaHBWDWvaKLRtNaU'
    b'o06sc5YMXXy2h3GSM1f8DShOVtEln0Pmc1gGgZEBAWW/E+Zi9PkpVCnZPYTkedPbKwrZmRg+ljOdhtICbJnhRmilTc1g8acH'
    b'IW07KwM1+j0CqgK7HajlokqczCHQSvZEG5QbMTjw1Z2Md6b9Tjopzz+Gau6sANuhgv7HGavwmWiKMZPoaGlQxwxlRMbVd7D5'
    b'PO/JkQ17009unfrpKnF2YgdE5C1/5GNanACr+Ay6rtdQcSSZ5OUJMaS3SijKRF3qJqcdNtp/iouEoGzEASi8GM4X0yTn1wHC'
    b'1jKAFxqnQ6wXHaHhXTMWbkmzHYaWyZgbAU6s1aqJVHYYbxrGGeMQQ+KlWzSRfQFk0TGlToF+y9M6lP/5IYRAuf4+qbyZqe+Q'
    b'sxm40w7DvG2XN1s+lc7rtKinM9fPj1X98IbktcTi3rOHuIN15V0/rI9r6wEr6UtOBsalBL8uWq4XGUCIhg0gC56nEOdm21eb'
    b'MdKM8lRM+TDWmJ7dkge6rIaxL+Ce2KRjFn7DE2OD+IGnCjK2AaPBgzu6ASvD/FOYW6IkUou4ZZptBHxhpILjWc9q6Kc+m03u'
    b'/u5AxIhtTEyyyHjnMZqgp4WFas6k0smecH2W6BwIfy7nDN7EpQkmbvaN6kUveFKy8X8NTNnfjSm0g9+KfJ+FhKm+TWMj91KZ'
    b'YDREBp8n01hrOzIzhSE7uae5KLMK0loSKrtnuNr+ov6ZlXkz7rj7srWuWX1ynoa2Bu+/VAEcMxj0DI9805kpQalfHZHiZCuU'
    b'HPUFx/G2rmSmOSSlpdNTkn43ZPkagMLaw/IEjtCM127V4px+0nQX24qSFHJEPYhp+RocWHa8B49VybzzLJi7D2Ld7m+MkxrF'
    b'vNALyZSVkRWRx4X9ikFkAxQ+sQIFcCQ1H9onkPkRlHJ+Eh+15xGOh8p/jHhZuB5snHsPLDuJQhxa52fhF1sRZesuCIoDUfYG'
    b'3Xdv/Eywd3aT8Ls2pPaKU9d9bWNEh1wQ26QC+yowQlmVzkRuF93kwBLFtLjBhEdHUZWHSc00fE9f9S4bxCle2R44WBkWEfGm'
    b'5sistNnmWB9d5+Uv1QJvtMncOr0g+ITNHdV6l1qg9iRHPxkzP4a2RPsXLUfVE/nVfKyr9h1JIZZRVUByavNiuKXWsNxj4xaa'
    b'/TJOAXW/BirWB1Y9rEobk84RA1il2UJ+JYNSDnV203dh99km2n7PKn3jpqwlVx7FS9K4Siu0vguHCdGiQcYO+hgFxql7u/sn'
    b'rRNjzDll0jnpyCr5u6Goie0vuxvgocMv2ba12gGLjs+ATSaFZWkSYbI1vgWxYXkdvHdwxr8ywnvOm8w1NlNyueafan+dY7jc'
    b't3kN4ShKKgbF4Q1Mj3Dr7k/0G2OXizXLtAQf2KgHSINH2JQuiig6cM6e12S0Qx4W10Va0lFnQFQTqMYE6sc1urkGWJXDperQ'
    b'I3KG+vxNvpJYGL8hV8Gqti1Okh57q/gJgtfar/On9lNhCK1RfnP2Ozz/4VGwnQ8mAPTHSYrDoBhn3RFW61REDuUMq99Z7qFT'
    b'0QuRSjgHwFtuyHlctsnElMhTQoyFAFpckIIZstPNdmazJB2Ul4Z1qKIDRYnRMnt/tIQ+vKYseHrj4Fw7KCNbYTqJEVhZmQKl'
    b'3nDDb/UbtpuUjrlYx3USnEoS40O0GECHnFVSWORWRsgIdQ1fYKABxv0q2CCHKSalunmO6IivylxvQSWK0aursMfQ1coRkRBc'
    b'zQ2zs+mlvnQTl9l96ZC9ceye8YfzKY0lWwY94MESNlgvVUW8DJSima9WDB617B1EPXi9Nncegb+Ub34k/m9AppXHC0Ivsbbh'
    b'I1s/EcIwVLxsFM+zUDmFr/PAZvumD7yIM/zHFB5DPEIkkY7EUd+dB0ZNTfln+9BKT0mlXebnxMNbfwWmUMJohSakwWBc1EyA'
    b'7JrRUM1l/G9Qgh7BTOCgNGJq+Hky9emD2bMoj2yM1MDTnIPVCXWzCaC/RW0JX0x3cy4f1r1RN+QFLRy4BTWoY/vZeIfkZxNx'
    b'AHpQBnb9ztfa9+74s+ueL06ffxwwu/Ofw2T7rbDxdj8hf8KXY2Nw/0wci0W9Mysa5qtRks5wnvq1RQymRfszadSHHxgVnV5L'
    b'SjDQCargmt29gtWUIsHgAhcXIVDWpMMsxhy6zJB7sOnUoThj/8PzFM7494gX1eOuWtTwqyAJiMNkyXd2z8g+r9yPl0BU7+fA'
    b'Our9xHPTSBXLcnqqESalBfWxLcMLwhaBrdonDWjX8EgI4NDLrH+xGSs5vWm072edthziJ7ozVXtnJbvNVMwJuyW/nE9SsoLf'
    b'AkQew4VLiKA1d7lxn0KhrzMQggHf3sMqdzKgK2kRB5CXqHgEQQz1JxwdoUgCwTYagmY4zCkj1DyjoBQwJWAcWEUKzN/bVOVV'
    b'b/lEhMSoiL8ZsZtOm677HgROGMO8JCDu2dwn5unteXcsmr0ThrXHvS++XyLzob7tr+Lmp3qCRaXBEuLNt2Q5YBSO1dgfPijh'
    b'yJXGjcmrtAMqnXcA3p4uYEEhmKjuOSReCSvU/7FPOLfVBa0ujcMwIskLJDqyIKCIrfBDY5xKX6AliB8aomiatI6GWN/G+VBk'
    b'lQu7IW3cT/1Hsxuf423i+cklDitUdanXxbdd6/9l0aYXpEgZQYt5oaSHqCywF/JXaaRH1r8b3/FRHotxRZUfuh4P/zRYXx5p'
    b'rY9xvPvXYCY6H/lu9HXNAZYrO4U0MLgYlEEWvTBV/WPNux2q1hv58qKToJgMhGMidg737WTHFQ7pyeHnf6NzenF/+cwe2HWG'
    b'q0SnaFLPIPqhivUAahRjCZdqSXZ2uw+ISF+R9NwZT/x4BV9HP9fTAMgO/YpcSVjDGDiylVZByvO/wW1BvCb6U/qbKELhR2Mk'
    b'8C3UNwlcSfG889IGX4dhGSIWj+/Fp4v75YeUcBLgYyVpCPmE0ngIMhJgOh64AfX2z/R5TpPElITkV65KgYATldVbLKOhkoIF'
    b'X5IPC22Sa+kVXIOiH4M7EI6HFMmUeCybUpIWcLt0/dO0xKnSB5mlg/28mOdy4educE6gRy6fcwJHKhyRcVe86PiCgi4snndp'
    b'lhlPn6iOAuUeXVcytVcwmfF4xkxJJQ47IyiPkpzC0hmD0Otygk9erqdqewrcsQeF6nAsbywYvfSCHGybgCz5UJo9L0QXcBts'
    b'sV7I4+YPFWNBBvPewIrDKXGLQAjKbay4FM4jvtlJ4HD3A1FehdOasTgFDZyLJhGos//VJJKVB7yKwI7GO3fMfIXAqOd1pBlO'
    b'Khk1kq2NTrb7QQ0007JgSj88u6eo0ds7wavZAOBQd95b8sjUPTb1BQ1DsGN6QreEVPsrXpNHnj5j2/XLpA+Q//h4Yh17oJcy'
    b'RSAbXsRY2CDgxiZnpzJLb3s8pZiPPa/iBwCF+w50ZanPH3Am5K9CWnHOLQxQsXm08Cd86fAUiV5tDrhEMWti6o65luHHDQ6k'
    b'GoJwafGFBJwpfevxMud736xrBUaQXcCtrXQnxSCYZICpTyv7jPa3MQoxCEzlZTP/IUcBoobP72M318DRpwjWNAfzN/k/n+3j'
    b'W4xbcZsp5JT7Te2wO4g0R8Z+nLAVW3HVKzt1pXKSYvd4sT0qyXh/JPXuzDAocMQb+UQILYIqsUlI/P2BBuZLu1SFfJVxHzVW'
    b'2qshqntas5dGA6RjUy4Salx5nWhBImL7Ad9yrcMDi7jx86u2CM5zR2Svlq1JVoHW4X4rg5yeT2TOQA/Gx+dSowdBC48wLx+X'
    b'Nlj3s88bSg6Z1vjy0zsD5lrkzrzjn9GtciMv5BLnSsUotbRgN+TK8grfSa6zP2MNHQSkTQLo36E0JCim0/lzzkMd8Sw4BIM/'
    b'BvkJiTGIEspmcEayfgLHz38f1jo+C5EheJ6bq19bojRZClRphTiX6cwWPuQQQyiyrlp5EGyZJcnd/I6SLFfM3ngEDmiEcQie'
    b'kBdMGwuZDZagz0/K5v1RrS+gl6oT22gaLWh1MJOgChTTTAQO0/pU7i8ezxPGRAXR9CiadeKiT4cRDYyl+YHkVg/fTGYbexFS'
    b'AwB8jLpDrwmhx3mVGUBUzJZumZTuOjzdCPY2gzyd5I0x1apgfhwwWH/HuwYAd8SClP4jSeC/8ar8phPvAzdq/pY8Jkwhs5F6'
    b'NDRD3Medrt/Korj/mRgy9Zv2/FunDzmRI94jEKXdVj+jnF+4FT7WCdSbRNjiCq8/kvRypWCjnWJwxhwhsfFDt59DZ38cyzim'
    b'S+49fUOiWVpeQXgCmpxS/99kpU5ZAMI3XwDaIFRejOYLTN7QTe5jUqAszDvF/yPwAyrO8o/mA9r8bn5Ej/4RvdWiHgbGH49k'
    b'u5PYBXoRCQiMRPQMHKm5Q9xF0QEO/cDvrwKE7/p72paS04+FKVeEXqkFSElSnwP/BLmM9SjPxDOv+Bod8H3BgIYzJPbfLguq'
    b'cOvJ5Xkgm3/vszwmHevgK5/M623rS+MD/foCgQ4869WiDZbp45jgSd5nAY86vnL1fuzxU55XS67VxVAqqyjLRQZ6PpXk4pB+'
    b'0bL9kXZeSZO3Fijthcp6pGQXp+G7CyMQytRF1SDMtHV1HhUdPXVsjixi94k4grMRIuT3dnfXX7RK+s/3cQQzOEHRhDbQvrkC'
    b'ZPAkua40Sr9CSezeqq9fWf+AiOSETJgXowot2y837NjX8acZGYNmnnY9E+9vgW6Y/+vobltiwIdkd0Dm/q0xTVCorvgvCoP6'
    b'BJ3M4bXj3/5AyMJhIne14raJ9zQZjrwk/s/XWdqL+6OdXO3rq5qZCMNQJ2301VOzUVd4/iMOl+SrN7q9Hh2ZJkqYGbcyiUJ7'
    b'Lfz7dg4hieZtkc+ZZOqwk91bJigLr7fMEANYEsTQH40XtJ62scpf69t6XBvp4ld/hpn9jkull5YvmZrQFHpj4FxGhySqsa7A'
    b'6q6YjMygn6zSRrH5djAAEuJ5e2yKoHX2RYzMjqUmAM754RjzxfR0byXzqPXNK5wYjHCfNbcFd0w5x00O8C+lBaH1+MqvyRW7'
    b'X9NjHlkCIkSX+4+0IUzjEWm6nXvDET/sO16sAy0tpdfU+apdpK34NOF5ucTi1rVM3YY9rL8eZAu+B5X0ao0oxZCSB9o5r78Y'
    b'DMM58nmvUpGCB1fArelHQIamZkmTkPBu/VGDdrhcoWtvhRryzQSg7BCyVeuUKB5WgSOxPA+H1hJuzi7s/I6zWBxcZEjQ9ta4'
    b'O3rh7EFsK+rNS2itAbm7Ujh7XAaUaU2FoV7glKv1lGn7W1IdlpyidZzMMhr88mnvGv2nTa1LDVYoDMSAP/m1iu9fbWYm+mSa'
    b'GKne5T+1lcy4bIqN648WvD+UGGlttlIdWQ1DIvwRFez9LdcFXhMzdDLzlKrRQEBh4j8sdk0rC0v3PXIX/uqrkT/ka/fkOSRa'
    b'5LKGBW4mkNTdYCD9XLIr+jT2CUXGUNBKisStSPVGXZQQwGNQM5YxFWhMOlGXZy6Myov6kLnhRu4b3HEqzSnXqcek5aPaXKr3'
    b'd2GtQ17MP/H/H1kdL/U3JdeBhKQe6KGDw9T6D7Utho9FF112gupVeQ+KCVWJ7gqOKssRMLpnsf+N4bQM8y0sEfbGHzku0Gxs'
    b'KrbOWnEZC/vbtgB/XFjkEUwrR+qOGinvhtTtI11v9By2nPtzboWo0OAeQ7Th/1jzuH70Vqc9+WKc0N/RmDcZvbKN0ATC1EC5'
    b'dyxvs1QtIFHg2HG0nkwOZDffHwcHi8CLjQn+ERF8dTw6ktL7FkYON262BN5hu5eTsRGKqbkEFTQXv9Spnb8jKWQljurRaOQQ'
    b'mn9YwfWkLowRsF8P4oQU4kAQ4yR/4RY+MMlo5RLP3uosJhJYBBBDu2Z7ak/tusyUX7nie68q7nQhiJc6ePCqi5aITSJjg1ro'
    b'9iZUKEcJqYWnk+AQVevEysWIEHWHWoqttJu+NS5/cY5fRlqAmIOFVJNp3dynDYczsq3VNd2EKaLTNeojXFXz6Sv/PpaCdrmQ'
    b'8gmKBcvkdY9Z72mgNyRDsGnmz7JJxWsBHneB4DsYMLoLUGZeKmUrmPSerqI4vVuaiThl5JHB67/FvRHJCWedPockPPsJ3HZv'
    b'YfscsnYLCxL6Ka7FzB3aSCchIiZbWIGKn9pXZ3mr9aXOyLCulxDD2Gmiwix7ujz+ULGUh+3L4yi9T7D0N5vunf0t7TJsC++7'
    b'd4f4sLXAjEJdJ971hTnH5AXigiEdRT3cmxu5RblCbf6caktoJT17topGo4t6qavM7MVhIuRt7L20ftO5QaLTmB0nsHDYV2tu'
    b'U3e0YykaYMLF0jZuKAr0NILxMMn/mldd82kZ8A73TPcmTIG5WrMnz5M4pSzjQGaK8m/A7DQ+NKsLDfchRlLdJmq6UHzKazsP'
    b'IiyZkhbCFoxfDPMJITb/l9PT36ozS20XVPEJpiy5aUqlSyTwTxuUDb3SYQEV7wIxy3mXrzyjVPJzIqYHK0I5jhtUvz1/YQRU'
    b'g4kAmLKoAJwdGeganOQlNnNULs4yHfu2FfWW6NfleF/fcYvr+OMQ8bOcjQ7gU8A95ifCC4+Fe3yBMv+POqFCF5lKUF7gR0Wa'
    b'FyO+WtH3pvdnyGNaUYkUCIdsDk+sWL0a65i7lSxRCuMcLV3wQwb9qNvLyz/pD82dnUc+gxKMpnaVXzQYLrIZigD8vOSzsvXR'
    b'kGbYBvOxIJkEOrjscaotbOAJadr4DqeaOi0iCsgGAI8JSnFo9ugBxxMgc5XC221Y/6rPm0xmPhkrmQyWKbDJsp3otwrLZ8I/'
    b'AVqfBK+Euk3MnD0ZiC2IQrOx+D58bjP6AgUZsLxTkEikSwSpsAp36odSseYjnEXjde0CT6S+4DmhlK34y9MmHC2pU07n9Coo'
    b'rTYbTZauovlhRWxX+3EvAJSw4hJ0ynsAnMk9xo52/6t7xBfzUYb6MczGm8eSsnuBBmw1wJ3zDd3EbtQvoVzfK0aX5Y/KGmuV'
    b'bW02IUVeS8ARX7SRr/1Oof0igfVsZq3zi2doDEcPsPZ/hXlSd5z370eufraW1R/j/tvs5z3+eSIN6kIoVOuwGcoSiyDvBvwb'
    b'26ruT2eezCFj3HeJCKUgl2A9dYA19u5+Ji79aR5lrOy9VvBXJ0V2p8cx7NyR512flEMJJUX3t6Xt2xFdSP+U+vxvfRL1RNmv'
    b'k5lr1fei0We+vIaRto044Fx7YNagj2dxTnOFOxGr6hj176fKWF8AnGz09p5IKFexphixhU8VNAYSSa+cIGnlKh7qVPeNDlpr'
    b'QkP5S92bc2N7Mn/nBZ1UCklvbQPVdpKJO7KL1mHQgQlws5YryPhhAPBqUtZMBMIFKaL46fnbL1Ys0O5NpViI6RUpO84jM6le'
    b'13sTwJaWTPycBMUZMKXba0kyyfXMAgGbuPUjIfUWznICIEimo6EgKcBJDuUOZCAhVfHRusOHqRlQP3Ge8dCHlBXPIatGSN82'
    b'/VoiIkuVerF/iv+BqrxpiR5GJQ90z6ZvSt1LE+OD+jx1Mu8kiaYrDm352onv0RMpRAikmXqAIiQ4+KxYDS4efNdliMuDMo37'
    b'po/npRfr9m/q2a82WTCVCUnfVzcCJwNW/9tfMLF3WMO5ZkjP4HUAeERhQ4UuVmIyswcFFMbTFTmLez2jRp8gStEHIeXMUzqz'
    b'J10Lji06HLY0BBlDnh0CCRl1G5AJTyK+9beH11f1qDUiih6zqxck5H8LsE7bXWHa48G5DJYOheHb69BQecF8SnIhxd/URmp7'
    b'X+htBjkcpAWik2FXwa9epsxYghY5DoPv5rjPm3oHxogtsnI4fMGsvY52AFOYaBlGMBpqFQI9p9ZDKTSxjexydbKLrxedRcrd'
    b'm+RpTNPBsS5AwlQ13NWJqz6/eeW44Of5rtEJb2uS24kKVUe8N7sksUvY6oQ56t5oI1YGWwaEofmlpfUdgSxNAmoSC4ZPGNd8'
    b'UoOTjOD6JVIoZ8ykOyFIKbKidEL43XNH+m7+CmPKeTarI9IADq0vLb7g+7BpP/OkDtpBHWpRaaIAAi3ncMcGBwmRun6OTeG1'
    b'CfXiQy9imHLrQ1O0HLqx5dxUx650D/9eOUk7mv+rz2DYeVp2W2jYwj3ZkCmqDeHv89PAHVZ6Yy33zHNuRfQo5oyYbO2inspl'
    b'mPKwhlZruWMUlOQ3wdpbgXD8tR3jFepks9ioHGwO7C62Cekz9E7ygda321NAk7St1dT48wzDbUaBAPmt2kHZtvz/xqkDcTBy'
    b'Hs4bfNWmbmIga8tjgwrOJG9vIm25eIP7bFwXrfxRsFXF5bXP15LqYK2N6gQcZbXMyou65H2PNA2jIlUIPmtxAIHom17QRMz+'
    b'fEF6NAkZ62lSfhIqkcARRysv4p0V+OyT4cLcln5Eq1I7hlrfGpJ444c6PMyC0r4m3dp49iHjJCPufbWn63R0dJ/uYYUQSZ5A'
    b'oxWL+WTjVJayVD8Avw1hh5/UJSCo7eTtA+5KKLBKEeSmbJ4a+gs2KvIkqx9CPOHJeaJq1cpo4SXnqhGenpoY4A4WhgBYqMyc'
    b't0FO6PUsMZrqxhgKfsbodM3MzPf1QqwaGseqh2JDKY2AOi55XB2hYiEJDhwu10Ht5gLkhtmmJdcRoL4M6hbjnje8vbk3+FB+'
    b'MX3k1LAl/0sgj+P7rRMAWM74xSKDBkCCOO3i7QDCLwfBnvj86xwQmTJ9LHH3L/X38QOldRqVP4QsBwa2nVdgGTqbNtM0ukhr'
    b'6IkGSECiiBJfqjLhYxg2nWQIUgM+m+dO9icXtASEB5WAVHXFORzX66Zemur5dAskDkIIy9TW7Os+nEhBrSNC0jmbBB0yspj0'
    b'fLxBVoo03xo5RYbw0gqdfhrvDdBtV+tC0aCFKuQaNtUo/y8moAV8aCHj18GO1CrXGx5PO7UH1xqMSqlNhXs0fjAJN6FfgUOE'
    b'qay0wqJIXC3B7pYZc3ZOcLQFTDcVqscp1bW3r41BoUnK8XZNafAuyPofk2LgDS3s2i6RiUxD+DiYXoxKPzzvASs509edKrHT'
    b'z9aNFhHG83rJVi2oHtxEg2fZjVBBAGUq525LwGUkIin/38jDUTsw94/84FwoyoEXluzhNA18SnFw+3Pf32DOheltIcrVy1ZA'
    b'wAysGchHttLuzxU2mKdWZ6SXifi8sSn5P8P9DC4hXUOJb+FKdxMi5Di5lpslqFBFXQgIQNyiSJR+jfN4vH60TXdn0gyQb8Yz'
    b'vXZDmZqMaGDSUmyqEAjkJwLbLBIxBpjO711RpkSZvMxs+2EnuOMLRws0E3c1msEH03rYv65VWU21xwhjL1kHUmSoDaaaDUjy'
    b'5HWdKgidPJU15Ad/ZVTzjv9YYeCqT5504lHHxhonYUrtrWveZUx4OoAhJ5mzjVQqeftoBWjsxsdy10UmThENa+Ywdy4tOX8d'
    b'r/gxcyt5Q67lT58YUzirlW1u6huNp2DZkE5YrK20qjuvjhJPDNbAH+edGBa11PMnikAwVHvu7RqXO5WkXpKtqIG2+t13csLt'
    b'zIZXvvlWX7DYE2LdWCN7BD+n0fFQChXjHgJUe+rR3AR4qKgovqJvnWGwaLVRVV0coFKk4rxDiccqBUEl/Ju3chFObxppgfk1'
    b'WCVxByqsKDU9MgRmQmsM5S2cCsif7gKJqJKRmdAfYvqn0nlE3Nof2r0UVaCZt50ZiAkljJU7LZ6W0AXoktyWTALJ4vh3bINs'
    b'tp3VQRsxbWcQwvA/16XB7njHfIaBMvxPrLuBqbmr/xiZZxW7e4VluZWXl/TzlwtwEB6nQX45A2OZ2sjelHVzE8874rgEOxP4'
    b'g4wFy1usQWimwkrQytCVqE0IokzedlW3rUHEHRtWV60MHa6sw01FHO2sSEYFXue8UOTM1gwbuxEuSjiPQXjSccPubNoILNhb'
    b'BhHcBYD0x6cNlOLgGFtBHi0UCHvHYzyKcML/xww/dmi6vmLZ3yRmLJfDeU0ujQ4LcTX+D+Q4ocNobDjbWM0OQWxysy4VIA46'
    b'M+mW3E175u7T/f7cQch4CKOwzg3THqE9c7o/KhwVeoQ1TWx+1fbaJbOW4NNBLvowR4UzP6C+foE6se5COMRvMdKZvMHOrltM'
    b'MPqOZnKIvpgeWbUpnBYC/lm/i+qaiK8bS+R2AaEivEHq1jmQ6kjT+rekjr97ybjY5GOQ+NhCO9FZ8QWVxfK58kZOxaKqfsWf'
    b'bOzyIyvlWrqKvzJvRPVxt8mwDTGwkSRHZ9sR9dPIA+opkivWySG38bl4CbevhQ3uTtxC1NHL3uSmufl8Kb79D/BaZKlmFG8S'
    b'Ql423go426w6O7bCNQaRd/UN6t9s+Ph2k+gMNxBbl57JhtNBbQc9A59XKFpVr+dAHM8XdLQHceZrqet4RqnkeuXwvBtFxMpG'
    b'yn5rIJSHKmbZcnMUnTRtOa0z8WV2+nvqeQ3jBchADTH19SR3p9lz/zKyxLhQ08334kXt6t0Ag4Emt7ySutJWRj/Mh+JvGq8T'
    b'0/ePHXODd8Vf2qCVPi1ulyE8uBeLfyUWMGoWiQEhzMNU1h2eBhYbqPmkN2H7e6Osyjbe05Sr5AFM2KGIc2RmSUHH4FICQpDr'
    b'5W2sKk+mqwM8pKIcPmU3FrB7RGFVFFRq2K1iHJXhrAu5VZq5fPl4bFTQCerAMlfH1p4HrE52YTZUeBbLa8Hte+jHOCoGaogk'
    b'TLMavdb987J10yi4e279S1Kk7Xs7mJHzd8VJs+i4WdStOtZ508V4UjPQZ2mkykAlu9KlUN930D9VckD9FXwALwmDAmL8twSi'
    b'3iISIaBflLxarmxSvzrtU2M7n98lodAXoI+GMDsrhiOd97QlIDqSZ0z4fd9a9Ti0sJagPA+MH/dYWTVmg/D/la4YgvFcwBL5'
    b'09Rj/jU5PO1se8/DawZY7WL5/5x2yo3oP7W/m/eRsHcNas/TJ0tKsU5aYjIcd5eTuuuWxx+STTAC5DHXUNIODYwx2pV2TWe4'
    b'TYmYcvKe1KH0aL9qZAiHOVt+kY6Ukikvl+vIBY+XU7kaprRivtM7kw2zvOF0BhHVNdQ7jHacEmszvwPxeAm6b0UmQL+pOqql'
    b'qxX7gPZUPwQ4hi8uqjvFa5x5J/DOwnPArdyNamvsTan6DpPvBfIyiP0FrDUlSImdCtBoXCLaTzxCtpxRcNQaQV82Xiyz3dZB'
    b'nl89SIQD3/YWQZlJnFtsoAB4Me7MyQdXjH5aFVl2TeRF4RQ6+IWC3KTGhEYYu34M7HkjtGH2OyuZcVKeKv3mKJabpUPbzsZb'
    b'gz7DcpxqfMAq+6WvCUj50MEAFOdKvpinPbEJClg7bdUi3mfEnsvKWj9xSf2HEVWkPu7MPAJ7leBGJgTqH7I5BME5i/gvN+f0'
    b'N6We67hgnTl56lFilx/pxlXUZ5uT6NkR/ZP1a9kuqNIic/MDUo4IArot7PAPd3xsdHrOtgayUfO5FZCgfTfid8hky95psZpc'
    b'EyTCK7hP6e9ffxEl3QpLJv9Oe1cN92ZamXzMG/6gTNsef8m9AfnJqXNJ+q/bNJ3UN2HRgQLLsFhCaBLpu1ao3h7iQklr0fQ3'
    b'oCFjI887O/6nIDD2yqVsfZIU1uRtiIOHBdHaOLUw6avu1Vl/vvZd0C95eKNkv8FKFxntRVMQD5rYRgbFE7+vkXeC4cOOjetb'
    b'o+xV4CLRVCU1VV5ilg3Zkm62ic3wIpYt1/oTzfBtj+p1dkGjOx/20OoeQwlph1h1MVvA15JYt9Ufgs+1Uj4t1U7HPPKueyYV'
    b'gIPGiaiI6fiu9ovqz4a98NEE8US1vIEj/Ka3PZO9iVhMvr30eaKHGIoKMc/Fb9c2X7iOBQu2iB+uewHuOPb2bHNjx4rHE+pH'
    b'RWgyA2mE3u4cyX/wrvfxpgkSZfztkLYILMVgN/eWDuBRUpNZdiZr0isN3f0Bd9aC1+uDCI9jXgQwqvcRr9RSMInsFwLTpk9g'
    b'vf9IAQLRWmdNoE3brZWR7THR7y2x+FMJrF8xtyesKXwL8aD5q/GbwKkxbzU67WMP0otCzVwcrtuP6x6lQPkakAfw54JlJDNU'
    b'WLMAJz9CX4wHK0WrYlTED+HFmvsecBmSisCUXTF+1LSvf8F/0DOo9bPDit1zd9OwjsxCocEngRI/0JVnE0oplzBsKFmPE6kp'
    b'x7WO34BRi3/dX6T+I2GugHnbG0qPZcHt+BS5u8yTsAL6YtHf9ILS8RecROJDrMIHQUOUUJe6ckISgnxZQZlvym+KqcupSNl5'
    b'FPU87qMIJTNucF16yPlwuLYeLEoWR+xX2tCfjpd6vpi7LD+wIBBEUwJlUFguUvYHEAjQEynDwx1mTY9+oDHedNd4K8D4rHuw'
    b'O4dZEi8ykpazG00bsih3GpixkT1mGY78YJFMhLio8SEIqalFse6WgsaslXeWNbiEpcR4SfClioCeUdcMsWaLAsF6HzJneTLO'
    b'6jYZ50P3KtuAGVaoNqd8gV9h98JvnygRCOgqcJLSCjGmBiH+U1RJYK+xX3fime/U6n2gT4+RCQfOUZtYKarbIv4NaCQdBkcu'
    b'zqrTYWHiA+7ZM+TDwCkttCqxlAEa0pDv8g/VdYO302XJy+nmE2u3hZ61A4C6IGgtqspqQJpJQ1SPix/+8QVEg4EIsmTSYcQE'
    b'wvwpN6KpZG+uWYb/9XWKG7HQYNogamwKs7SYHJujBqUa6opYeNbYApETMs0iD9sVbFhElJp6L7PxwPRWFqCMhipa0SCrxzCd'
    b'djUjT3GHSbf2jZny9AXR9cHiyXIkX+1XczgFjE72S2XVRL7Vk5Wu3R/toP1PMPkbL4wzZr4nGXcumgOxLYHcrtuU9Z39qcus'
    b'x1sVeEdh1B1Ygim9lLGeCL+7R/V9Wl4Uj13D84caPFoOuKf37cV/eyUXdYgSGHsYIao8yydV81Vyr25NjaYlTsGgpyvIidGu'
    b'eXStz5vZXPeYfINo9UmqiNb8ihwEk5odMeRb86vEZGN3V4frRrscydizuWonjmIRgm2LkOJbl3C70LZtmusCLrnGNpuyzn+v'
    b'u3Y7MjiaNojeJ7NgxwOJ+6oqR7srgOZIZIxBNPh7A7QY36QsuxEuTFVSkLP9/QcA7sE32bD/94MBV9ZPDD8Z94j12I0oWBmD'
    b'GPUnHCQ9A0Q8LuB7/dwbNVfIiNh1bF00hOY65g1FdLpZJFhIwClm5YhrHOnBn4X5E/9wcWP3V3eWZlsgOYSgEQkkfUBXchDu'
    b'OSc3seIuWGmIXq4lKBfYunk57PJK77qKQu4poY/vqpoL/D7uYfSYk+oZPKwLeiLM596oOdR7Q4suu++0jjsgpJQA1ow8aaC0'
    b'dBDzq6+vt6MpffxoS0yCHXZF6zBnKoGff6OlsLUvcvYhjVfv0U2PiU5Cg94n9DDTt6uPpi23ujjaJsO+S3k0KM//D2OE3tHi'
    b'Iicq5RlnbdQJOjIbE1JN1h5aJrfne89/M5SKptY/2Q/fiOL+ZNwNI4Yu07TusgkGT8sjDkFu4WGZFF0TEXPwfSEnlGwE7j33'
    b'lvqkXY1l5zb+Sdlrfd0d0axOqYh7YpnGLpPfGjoLa8aiHXqO+Su9zrQj1MKpZuIB1q+rseDhZZX+zH7vgfJzvN+GGm3g4Mu/'
    b'zGgPrJpLCQrkW3si98ExFXnOuYYej6O/xCAEasAuaJOUtfq4fTOMV8a2PvgVH6dai/d/3ZhjIU3lRoZpxpRhXBFWxDbNkH6o'
    b'pgGncXJ0bZN/TJttRnfD/sKFKIqo7rolVHsVvMbELJx2Q9LgmORJhvqiPV8vLRtql7AD7bq7y5aMHI1aPt34eiUuA8b5s2qb'
    b'/iAZj7nvqE9IahuJCj+gutJTM8J4G0OFdhgEELK2qykZVI1w4XyYaOMfgagtb7nubEGQZqm5obNM3FEZWSMu3KWoupOmv7y/'
    b'KFVRdM7OMyQ7tC0ItYHSiTIIVQUVFErGjLze/FdtcODdgsPwDup0kWmagGeR8UV9/NAhY2jXwOGCP5f/cCn2PK0YkLUlrIlR'
    b'chk4eA2YWHkDYQIbWl4YlCJhAwovyxpm3H1+18X8JXeM49UhTYw0773NL9gUscznKRAIXi12wdaTnoY+yL7C1g56zzNLt0sX'
    b'IRKwJ9JXqXZwvGh9qQI6yJyhJxkx22K5LEj1s7BYJ+/9fkSqxqc/8FyqFtFJkMj3DkFYv+LKCP7KReXoCH1J6dcDugpLlCVb'
    b'vCqlU9hmBeZh1kbsBpPqUkTC9UO8lqw1oeXtCTjxNbZOevfzBcV7PklhA7juShEOYiWxbEyYJfrl0fp8jjyUBCqq97ewyM3f'
    b'AbFARf+AkJHoZ2GR7dsMVHym64qX2LBVl4YvvorMPxeNnjudhDt1PvM7tzbTxlU4KhCWCZUGH9+tk1M0tjQQQh8vogLGq/Bw'
    b'Nvn+4oYziZkTsxJvz8X4DmqFc95DRD6x5HWyQd83ECgLEZUiYpF4166uPSIue3C1rTNm1xqD6tq/bIv7d74TjO0aLExQCQ3e'
    b'qPe+G6fYBKj+QyKslUXX1WwADf9muzQO5O0mXdeC87dRSIr5XM4SMXC8+Har0oBm0T03lUx4NMx/7SBjuzEZZsH/ASZj5ypm'
    b'GbGPm05PLo/A75foT6IaKzsuFyvpBbKuiDywEW5iR1jn2P+d+Of39srHlniV1KpleygipEcnNLoLjQ/9L2cKqZ5wWOe4UNiN'
    b'NdPzc4z67Qa+8vukDUUSXrcjSLVFmTCMrRcFIyOYEqyiZJaKRgtqw7dbz2gMsguQOFB2bHsvMpIWtKULaB05ZhKNlmzS5/Sk'
    b'N3OLHdKiIFq2WxxfW8DTWAMsjFJ6CSQ3xpvupC68OFV1BrT1r0twWmOHw/5kIZ/kwNrUHFGtGfg+6gdg/+LzyUlJUHZgjjHv'
    b'UBQ2HJzk6/KrPiWCi4nR3RhjrpBe37tivZ4w/4ERQnFMit9k4m/d/exkFS+Se+DADIQncxwtRo3cGaGCR6ZBK9m2Yf9DcLgc'
    b'oZ0kjrWxnwEYsiJS+OB0L9qHIS8z1qDO4xFOnrg/Wff6hwlcp0VeBOG4ICE5Fs8HDJA2X8i2l9jIJi55/wdh31fEs9RxFFJc'
    b'HCn1BGKeTuig0xZTI6/JkwzPwjifquZTtKhrkwRTljtQqikdvlkxCtRfrlX8rpHiiSdyGmDY0aYLilG8NFRoOvNtNl92tViL'
    b'CEPv3+uVy2Wfts8Pshve/ZGGJXHYCXVW5KC88rjonHX839lm3glfwU4sDwWZgr2lXkK5iAubmNcXtNUX496TAtHI8pgWbmXC'
    b'mlQ3K/uwsTPyTrBsMR2MsXMGGWL9ThcmtugVPD4V949ZYxX916J+3HI4lIm6eaD1g2M0bQZCpB553fpmfy3pR/eE3h+T3ZlS'
    b'PBdMqZLjb82Dg0EbJKs8DM3D/I+byfxsJFP7axPL4zG1ZpnP3oiGCWrGaI4XCLtJqRumzxLbJ8Id26XQ5mKsQiPhdW5FIJPk'
    b'Ql7+PUdLjV6Ty8dooW+yrDTgBUqk/7MES3U9//ywocUxDFAGIqhAMToXbGtIQElxasRrZtb1JEhftL8lkZWoDKuDrlrXerWu'
    b'qvslkXRWrTrNz0T/lbHlXCh2vhGI/uW8hadHsO96sBBOFCa9e8+6f0+XVsXD6DM5JJnVwRDkPb6c/0zv8kG4+5UcWTnsXSP7'
    b'At0mSqzdT3j2mDGTw6O3OUnclGpyuxMpJnE3X0M7h/MWTCrstju+QB+BbFZEICxUheE0CfJv8sv0Q9WZVN6/dXtfd0fwylI0'
    b'mwft3DnJ1UcZC0bAgHOHOxQxgbdSUIHHJiy0/3+GGKkgY0q3hmdeu6yhZ4/FeCpFcBm0mj+ZOMDhy/rlQSIJwEqMZiBYMeoX'
    b'F3eMoRMCPia0+ZtW6uboUXFxF4gi5fseU8HnkzdLSTlX2ZBIaGuyKtByP+23h8Ka8HOP004FiG2TAIMJXS64x5WjqHdNAQ11'
    b'TY1XBCsyS1DMgp9Orz+4gICYfRO9y/G8FbtNtL7vlGDUgrPAVcV/+yFkzSRDjZNCLeudKPJWPkLI348HjVnzexMOeoIo2zsW'
    b'x1TsWfTMaf1ld1SF2OeLSQ6vxFn6ec897QMWD8YA3UfQh4VwNNuwXcw3T8GAr0LCCxZEcBaBTHF6FMjTDFLX7rHLB4Oflub6'
    b'Wtd1fuAzQRIUtuYb9eYtMZdMBCgo72SVG7SY/IyoPmy310AmlouOUIlMeEXvG3tAGpXBmJSTPzFUAu3eTS3vS/qwJBY+MCZ/'
    b'K2eGEqfo4kk3/ZJSiqiTnwFzjACxRwRj0PHKbYz0n3W3qeshzTZoyoBvuBvkbhFlNKCnxeTEfNGOXatpbzS0Tqel2t/4dTwV'
    b'9tKTZWXmmuscJxvj1L0qmoclnqwO5GKNfw=='
)


def _load_friends() -> None:
    import base64 as _b64
    import hashlib as _hl
    import hmac as _hm
    import zlib as _zl
    raw = _b64.b64decode(''.join(_FRIENDS_BLOB))
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
