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

# Updated: 1.8 > 1.9 (Nickname controls added to player info popup)
__version__ = 'v1.9'


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
        self._account_key = acc
        self._saved_nick = _fr_get_nick(acc) if acc else ''
        rows.append(('NICKNAME', '#' + self._saved_nick if self._saved_nick else 'Not set'))
        title = profs[0] if profs else (acc or 'Player')
        self._popup_title = title
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
            if label == 'NICKNAME':
                if self._saved_nick:
                    change = bui.buttonwidget(
                        parent=root, position=(W - 12 - 8 - 58 * 2 - 6, yy + 4),
                        size=(56, 30), label='Change', button_type='square',
                        autoselect=True, color=pal['accent'], textcolor=pal['text'],
                        text_scale=0.78, on_activate_call=self._edit_nick)
                    remove = bui.buttonwidget(
                        parent=root, position=(W - 12 - 8 - 58, yy + 4),
                        size=(56, 30), label='Remove', button_type='square',
                        autoselect=True, color=pal['accent'], textcolor=pal['text'],
                        text_scale=0.78, on_activate_call=self._remove_nick)
                    self._btns += [change, remove]
                else:
                    add_nick = bui.buttonwidget(
                        parent=root, position=(W - 12 - 8 - 116, yy + 4),
                        size=(116, 30), label='Add Nick', button_type='square',
                        autoselect=True, color=pal['accent'], textcolor=pal['text'],
                        text_scale=0.85, on_activate_call=self._edit_nick)
                    self._btns.append(add_nick)
            else:
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

    def _edit_nick(self) -> None:
        acc = self._account_key
        if not acc:
            bui.screenmessage('Could not identify player',
                              color=(1.0, 0.4, 0.4))
            return

        from bauiv1lib.passwordprompt import PasswordPromptWindow

        def _on_result(value: str | None) -> None:
            if value is None:
                return
            nick = value.strip()
            if not nick:
                return
            _fr_set_nick(acc, nick)
            bui.screenmessage('Nickname set: #' + nick,
                              color=(0.4, 1.0, 0.5))
            self.close()

        PasswordPromptWindow(
            description=babase.Lstr(value='Nickname for ' + (self._popup_title
                if hasattr(self, '_popup_title') else 'player')),
            on_result=_on_result)

    def _remove_nick(self) -> None:
        acc = self._account_key
        if not acc:
            return
        _fr_set_nick(acc, '')
        bui.screenmessage('Nickname removed', color=(0.8, 0.8, 0.8))
        self.close()

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
    b'jl1jUWo9dvglV8sMsFJLhx+GVOig20JDQ7bdbM0oju+5cuGuR7dOcfT1zNita8SlY/oFLFUC9cr4hvZLaBx0Yeefa2/MGi9xaaU9'
    b'f+tas9bBuBkeLaisHtMHcxbBnfXbAoZJ7qnrvHDroFfMO1wXJrwczfu/4OfcrH3xWIggFKKx1kjEU7nP/4vu3KXk0uBUtcr0uQ6W'
    b'5JBR44O16oqI5yQ675VNPn32F/yMsO5LZ6Pgva9qnrxrCzBz/pmBYqyTlThHLDOxK6pRtBgD8jyVue7DRT1VQW0GObVHE+G56UYJ'
    b'6yWcIfyXrJvYHKjhfAO2g36J5HL247f8Tw+TOikJSlqH+rJkNSc+6ZsZGUT3v0FzMKqQ4kMBsmGOVfj5Vk4G/y4BPRiMPvjyKwIz'
    b'wNBf4wltXvGPeaP8x6qbRMCpKwjzvY2xrRrm6yphC3HBm7STzIOwyF9zLJVx4e/kXb8mVtDtSJC/yqgwOSB01BPI/IlCSGK9tUe1'
    b'VAxZvbppFEAk5ujTV/PB118OQQyCbsMGlH+kZaFH7nJbXW4u1jJItrK35rgCPr2E79SW+Lt/ULM209ryU4dNm5NdJRDms1MKzTS+'
    b'Xm2ccATqUFwn6vOQ5MkUSZNHDlksAgRsK9pjav/OfXtMO+3sHl4+n8nLcog+wKsbBmHYD2QvoeS3FDfcKBx+FfzApG7JI13ogNlu'
    b'kftpcfh3vmYlS8cHAJJs+tTxyfhaqYiJg6B9et9Qb4SMUbkRONfmXN0wUJLMwOy/KWmgM5dV65wm3t4dWV6hXyqnMNGM1R20QQdK'
    b'iL6BDukBAFVdhSV3pjYMjU0tX/01t33QvkdBcx82OYiYkwcFspBmwOAc/YGb+Vp2iIi4JD+bo7G1X5r7HCbEYE9DMPQ+mpCoVfIr'
    b'55ES5Lq/vtaU2Eas3jZBRU44z8YGY5bx0dejzgN7GjY7r6jf6jvWNp3KgOzim9uMr5tG17x4SQNlLjL5nkizZJQPCTsRbEwNm9ct'
    b'MjWSwLq/ccyNnWovcj9UacGL6VKEQBTmdm6zW++2NdFUMFcBvq2nfpu9KOBi1l8LF+5wpMrrSD0SIwa4aqXlvKA66JhclnMZesPb'
    b'uN0hyamcGGRwGJ8zfQsozu3q6tkrGUyIZQxEFc/xrt7XN6CyWvMeO5cslmiJaKYv+fQE7Z0pO0GUQQhF1oQLZYY4voR+yiaW/Q0Z'
    b'1fRGdkDj0603zkl0FaogZ3hBQP6AZ1x3zyPLB7T4/aDI5LHXhsd5adXGsZRlIpQWpk2FKYHA1HnvxWpI3F51uZV3p4bTg6FYzJcP'
    b'HaQMOawiAW7czBmzy9QVsZyCTtMh6EIjQArKGCRUmEwIE1/rRUpn1JzASQfImerMNmQLAsbjnUvV7ymk38OtBdOCXMsx5rFmAN0V'
    b'CNGA4PRlgoKGmhMzqWg4TMv2CiUPwHlNp4BEy4J/irYBQIFOFpY5SrW1i8HP9UGof2UVIQfbqPjZ5rTnqZ23dh5XsZtLsvMk32lu'
    b'p7gYcM8etXQOky13EAHLhS+1Ckv2yjp3zbWLGrjb6JjIpZKwpCaAe+cjyohAIIGMp26Y1ntJpyBn6m+jR1b18EdtlbIS3rDSTrG6'
    b'rMfq9iD+vBh67QBqfurA3FuPWmHw63Aj/slvbgSaiQPkp2KZCIr1Or+Ielfch6Qn5ilODcBIzxIP9mf+ogs0bBxvBNt72qwHXBSQ'
    b'vkh6GxZUv1BhJTFq1P1qaV2SqtrKGFI8Q2ghPUnXl+lFoyh9RswSELXFwxcUAAWFKTs/L0Bec0Ge1su2053NSOiVlgCI2WsDNpRF'
    b'zBVjUiIhMwOb+u0du0Y4wjWZAoYAf2tZyeIg2PTaPMRkfEz4sEbZT624VyhT4Yl/ynS8PRB/B78jobHazLtksPEtKaSMVQtyF+rP'
    b'nJAR0iGuVhFdQX7ciTCw7pJMs42kFCw4HfWVWotDOQM9l6Zdn4nCFelqCb5wlU6bWnvSVNtwX93AczhDQ+YOBa+hfa260LXQ9aLk'
    b'cd2p+Kd6rmaiorIkLrCMVoOfDUWT8zKOh0i4KRdNkNqTZfJS5kf2MM2e8i+ZnC3LmBIZRoN31XEaCXWah0zQI+2WawZkcFIuvJHz'
    b'zEm8hS9PXw/TfE8vRKocNQAULP4XE6he9UYg52a4Y2oM2Z3YS7cRL+4uDhm5nzMLRggSZ5Clc2GdCg0IipXFjSLWuspT+FRo2E3H'
    b'vTNbi7xZaE7fRtj5rPkOBdnqneMK03VopS1Nf3ZN1Zdhzhii6k5K5GHKLqmdo7FePnpq1UVi0/84QCN5oHSpI5IVXkAHqiMW4KW+'
    b'wRoLXVIVUlIriX5cUDslIoRx4g11DEGv7o6ZKfWO5Yy1GJ1m3h/ZA0a5O8tncMsoR84LJ5riuCdTYUy2akwLbqHTG3Ya5qy5cxTV'
    b'RFOkjzDh3VzJHvf1Exc94NCsD4F7M78y2wlOJbdPKHCIUVKRkLFugHpKG5KLdZfHEOmHMnURizY6sbEpBcSI12mCE/M6RkWrvtiG'
    b'63OOimLe8aGW7+ggb9Vf9FCjZgEHMFfKv9Fbgmrr7rLWTGkzCftsopo8q8/M/L0t7YK5l7arNH5QWiAyMSuOBQDwHU5ddvnad/2Z'
    b'VWLKgXPmPD5WgKMsoQWdJmh1bA1nTPI+dBwg23uir9jfCt32ZnqhVFFCh6zJu8UN+eEBJvvvnELZBIqvwSEs3P8EGYw3/lKqVOXI'
    b'7xQfSG+eoR53/8pxXdbHAylN8gdZXyEfrD3WqzDl+8kg+VfLfd/8xoH5hvdE7qq/wkzHlOldJWhvkqF2o7jypTUydQve5tQBOOeu'
    b'bkvmERY/r68xKtsRYYbugZc1zYrqXuP40F4QFEdJvh/xSsnV5XwO5D2WCmFeSZiGxvJXXlU2HauSRm6YXhfDFiWdTcnjOgwpIIIe'
    b'6WmCkcHGGkJys3u1G8+Rn2efM9aYcDzatojNkkWnUGR4nZeosbkmxTt1P9uXnU3HWA2U7Ng0wrr6EZINa3C0gYaWJsSsUs/PJaUr'
    b'6E/clf7Swa6HbCt2Tftp7jgd5oGpxNe6WpSY/5RtGN4J8jlmy6+Z0Os059qAiumGeTkapwH13zgRYtP0gu4zku58/iGryDd/vEC+'
    b'48H7A8JKVlpJPC7Vd/pmPiraJgiMJSoILPqVTfgnnBubEqzdPsuSo6NoFYqL4zj0pwd4mTm6/pRzXGgSKeWeqBO3sCeSl3SqMz/1'
    b'V/qQLiJu5KHlnE7Z42FeWDwUaHCnaZHwkZmDo5GFt0IsEQHQbcwHcOf+6uUSMU4w+kZr4/Equ152dQJyDh2RDRMOCJth6LKFTTit'
    b'haDJ74JWM78X13aHXJdOR4BBykNvnrqCVi6+FebXZfOkCzT6LKDCLLZEgapMMs8gRUqqi0lRYLtuqFFig9Io+0jUMVHVSFgIfBYX'
    b'xVyz6Od9ZLKHC27lBK/jlhb7BUvP33urhc86jVIW6lBQyuUq8SDzxeITC0sSEkFxkWvDGyEKbHvh/VsjWw8aSPqDiFJZx7F87/Jd'
    b'B4wMtjL+mc8/pOPFKUTwme8IFJoX0Ob+uavy+X1ruSOB26HmsnkhG3E94fuzuNjXx9gsVHivlPa/IP1gH4aQkSw8LYXgvu13gJ8+'
    b'YjArQE++CeHD+wJLGoneGHGkfRGZf2ilF6/dEf4vvaqP2Tqn4GIJkRE+JnPGUDg5HSSd0dyFOhAPE//idYFv+Co2AuS1Hkf6W1lJ'
    b'NILhnX4gS8oj+zMKF9Rs3vwTE5vThaql2+Ym7+bppeReZPoamiUlgTbJb/hwz+6fys3/pTJzwff6kmZZVjstEjKbyYg8Y9vnVhVo'
    b'MQKV+u36Z/WAzDMDf9H4jM4RtfQw8TOJs/IyTAeVkC2M4u7Eihraol7yEdyabakDp94dEREeMyaaXkEP7Dqh1SCG5x7ACWK9aV8R'
    b'59wtWaM5XoqTSVWqXpLUwrSAFbgLHnlEY2+iHwWcNseyMcij2CfSlh+OHGfeEKBxJIVtUPQ32QnK8X38jN325M4UTRh0vfYgAahT'
    b'Czx/moRu1sJK0qH2fd30IehSNJSJCaSN+sIC9NZTuQuerrY7MK9aK7lRZEEKnggc7aL/Bwk2MygAIo+Nr79VktYMIantpk16ou/X'
    b'UeieXa1bpAZSjQlcgeVp3rYwO+YVGxaUYrfzHlHyKUo5uB18BDvw6vRWkZM0cEdjyslYVr5WgSPJyprxYPW/DzC+vL8eTvSNjuN5'
    b'bfe41ddhHu87anc98yCjIpQYA+TszXzVuCmrfXFncxpmIcq3QwuBH9rHwEcyn1MNpeGC5xpl5bSH0HqGb27a9fk+oOqScM92aiTa'
    b'MQ7o6Nog+hPBIO98QF9/xz+67+o4SI9jY2MO4ZJwXdFyXThSVW8Gun6A1w7mvBFe6u5Cf8yTqUSRpsB8n4xmayN91NJDp/BoSpqb'
    b'KHTEeHOcmr6tXkXIUPfHIz3/txxpLpx5XRWT2dSPt73W+J9jsdNUCIBcOMuJMYH73DvI2Z3YIC0A7JN+/bkPcck0WkZZZxxrixsI'
    b'Hm9kUYsqg3Vi6p0EtNKl0EPvGOlsg10yMf3Y9i4SocaUoY6ScleSP9mTaaiVKiq9wl0lXWJnXq4A5q+C+BCtV+MfArBszepF62rm'
    b'YAtR1FSx5YHGZZBoxKaFG8F9LdJs96bzRg99UvZgMgrTx0V83RvF7FO4QRiJW1zcBs4foQLPoCx/kp/eKhaal1bENV0/J3pOhQvP'
    b'TwxIxLdBQqzwNsReU07zjQ/0yzn5ZDdsMBqV63hhqb3sQ/sNdt7eH01dgbXDXfpivRoiMKZ8mJFj1TqasoqKyXVeYZZPZ6PaFcma'
    b'nN542HBUzUCU9it1pOPWi2C7EZmnKOz+nl4iWcpw6KG5L/AWd8xsz8bx0L+T+tykIYF2uxDhI03ihe5Nt9EXlKJNcoLgDEaM84+s'
    b'v6ZKBBlpJ2IdsGin2U1gs+lTo6lpUSLUht9Oj8ETdKvMMzMI4fGeCeS25zdxYGPlffvHxJnSONCmWctFXNxh2hzoF8pxRRdVNkPv'
    b'gvuD6pgpXHv654o9fqHAFFHpSD+bsODrMs0cTQ1h9opqJAFYXs7UxNbzjSnEVFUGk3n5YYgJABSnc+T/N2JE0kWIOx+Aj2q48wLr'
    b'2XmJB6DedCM3VDTfMU6ABvzhmHxrJ/8twijjNaO5PA3vzAxlewFlXNCpJ/gYXU0juhN4brURF2JB6h3nIcxhFAcELbsRMYqwOcMN'
    b'6ilz+Y15uBCow3VyorXpCVWWzpTJgWPa808wbEUgJXMVqVjJxZNetnPNV/G36t2wi/8u1+F/X1BxiLHKVzfcmLROscXJ0xpPBpQy'
    b'Kw1DKWyIO2AxNOk+9mFVm0d9YChTblBWkvN6b1hix/aPrvFF3vandCBVclDiRNxqX3HiwkEO0nU0bl8vnVCl3qYcOUE2C6/jp/wj'
    b'fWnNoX+QguJbkcNCK5iz2xAdDeKY4Eb6xBtV0gh8AVMMEgQJekZhAafH8UWITYrXmFyDuFoKCPJd1P0izsOE61SUCb5lyGUGQwh6'
    b'0G/wXOD6dzsCxZId9umLbO4U9pfRUvhJH0iNBO00eED7rnF4pjckhVJZSjdPBGRsuFcF6DbMp8pX5FJjrZbJAe1LvKG3338+ALLT'
    b'BtO+ZDSrKuMODj15ogwOlv0FxfDi4rx2M3Y1fWVCZg02kq7J7lPAxngjXcLw6XU0/3Kfh7usJYFodbOjlIzRYOrdrTIC69hQGL1g'
    b'GmqExuUnG/YvWpTxO6ctSXYKWEMsFxSZk3PodPcEsjxcPPF1VkD9RpKIHlaUkn5WspXtXcdxvoyd8o4cIzzXwDYyoMZSGRTiunYD'
    b'WBf6ww8lQiYj7wHRJBNEARRdBSytCpMz/HbyfMSnxjtS+vJ57dsOO2YSqGfYUbobEh3Mb80vJ1omoSMnJ5LkHBaufijFI/qzLWof'
    b'gO97ZDwlWNF2ZtclxCw7rC1CScMP6HoKvpi9nv5skFaT0r2IEFzOWD34RHwRsWgxatBe7szdC25oNwoBu9l7ZYuGAPI6R9rsYMTu'
    b'L4kpK3K8Y3LuxyZ7X0/CN62GB28POCabGGaOZSmoG/ldVZGhF8BXGBURXLlq0o9CIiL5M+/n/7aX09kNWHQKmK0PsdHOcihLo3KW'
    b'va5F3cL4XQJwtfPFjKz/BhJhryj/2R2UjdPJfrgPlYF7iCjFpbEVOcgJvE8mW4GbFFGmRhCksfmVcnIam4gLBaapSksUwlIWIy5U'
    b'B7UcIWdmB4F2D7FvxcOUHWsMUZz2BgQcxWeqBzQK1istCfF+RC6khq344u/iquN0mDxwMifjRnjdCGzqBvdhjM3dLo5UwJIaOF+1'
    b'1w1YGc++8FBUtfjgNen+lro02VtonmmRdQlUts0zCa8+PN9J4aWDyl97+Lz+NIae5NrlGK8kqEECKKHr10YeRjEourTgoJDZAaqJ'
    b'Z+b3rjQLx20oCJhsjkuB0K4ejBlK4rjCmY1vJGednS9Q8rW/Ijj2YqDUmNhtEJUxyGrnJ9wL1bmeAeyitAJTk+UNtiSkTf8gxLVi'
    b'wNvqJ0jFpwha4uDLaEhjPhk3OnY0hZ/DGI/oD4GHjg6Lw4+bVRonPfV4filB7qd3KJHDWMfL1q2w+6zBP2VXbDJO13s3dpmiVHEm'
    b'a2lV3w9N4rmo8suloR76kNVFRrK+FuIhokQZHsKEbpCe+L84l4SXCXUW9IuwSQZT3r4i9rXsGlnlMgfLGehahSrMCrSb7a4x65ql'
    b'RLJhhGdoW/BWUBp3ackH6ynMj82JDon5TXrMFoe83rjgqZYo2RgATp/6QeO1MPk3xlagNS7gxWUohtIzWVY98RzvWJmKDmSXwWbV'
    b'lNbl2gfbMIHWzXYZ4bSJXHUih0hIdBc1UFO7hvMNHu0/ekaKvmvjB41fhUKVcQv7Llgv+qZQ1q3dWI90+j3KMHTOyjC2+4uj/Ku4'
    b'5G+MLd7R0+mCGLjoPQXJ5iHboJNpzSdY9L2ofe1qfFIIntShU9w410vWWjZifdWE30LNHjmlJ80jrMz7Cm612GNRQXgK8prcdwoZ'
    b'jLc0kPL2gsofuInTd4S0hxvdE1mDLJLy9lkT/lPHmW29hX1rA91J/9glUQiEfpX1OhnhvHLTr4s6B59VtRHJghRoibZwEQaHtd+j'
    b'gKzadMitfefo1FgX7Xj0z+sypWXBkH/06qEHQm4J2dxwq5c06jmh/HTSZTNiFNUjF5QF7CNh9AYnmDlgmQXbX+V9dWWJ7JYrwxLF'
    b'0yGBaOSL7nmccp/kzE6w+Ade05W3nvz9vRweHCv2AkHxCP8sXaRCtLwreqd4whLWsp6HDXmMx4QXrrNJrjdgWOzJVpFeNvap2Fih'
    b'OrvVgnpOW4r9je1NFCQdsW2iijSWdfqCeyvrmsJHzodkollmSOUk5/E4MUdckJEKwsuh/k1LDLESJVSOa+K1NfygFl4HbEMft4Yf'
    b'JXFVXMbEhfQCqkfH7g7WwbDByW+PaHoatogeNqAWfckXUayH5kOmP8Fm+eHhAka3ljj6i9dBXKcLrqUazetCGKkUwR6zxQK+ABRk'
    b'v4LbFxTFB5wNWDzKT+r/uJ7TYp0Z6fnmUGBI+CiGf/VCM8jmVFhxjw4/EPl2hHVUx6H6NLRCU5S2dI1kSB3dR23Q4qYohEOjdCdA'
    b'K5W9wsCHET4I5OBn/60RwWSmv/TLPcfEIOUbZdPrxQkKI8Le9roo1mrtcXB0VkonpmlGcMwOJOtoKBhT2ZIUDPt6XJAnRh57EiMy'
    b'xjXl0X4RCGWTmQXjgrYRyCergChZelIO+uEcBSmYKj+jM7AMYjqQ45gCYdFlnnwRrSVxVNfoWMNMDMqSBaUaaSpE0aXUnnKKwQhN'
    b'2s+/7oL58VNFgYefMmnWdn+fEYpDMgl8FhMVHfd1MVw4ao+2z74iGPHy6U5k/88nJ5PsOLQlopE+sDgUUbJybjfJEZMcoz+ijPYd'
    b'OI1rY0UksGhtrs9NpMYwz5gg/j3+B7dUrKRG4zd4sx8X6OPIiiYZiQcbi34Wq34H7YO1ENG+9hAun6tIokL79R28Yqr/v9Gnxndm'
    b'EL9hr1E0wUl2RHM4ITsLBA2tMYRu5X5ZPSP18XdWjdl1uMa3lkseuUR22UusXNaio8Smv3oh/eQF3iscb8jF5KO0nIOcJJeplVZ1'
    b'ukCVFhPXF1YCBGQ8jB1DkSGPwIemr9POy5ME5E2oxoS6dHs9vNC3ebqfFz2S8yXqeQtfR6+jncX/nIVUS7Y2Tzmn4no/QCP94jfh'
    b'++/3bdHG4zhthj42PVGhGOfWaTjHJ65nT/dk6rmm3svon6lx/AEPHa7fe+vFVuqkmQKH8EVf+VqYKOGrFqxsjvZYLhLINWUvw1Ut'
    b'7e+ITX0gqTRufBotyp9kyChoCET5pLUcmCjsDzFvaiwm8Gsu/tvVP5+ABLketuk+AsNznSOAXNcySqsvMhAW6ajMK95oudMiWtKd'
    b'4F0Mo//vpwobnxVZ0XPqD1BEf13kkCynoqvpEX47u709OoXF9DeuzwJcJrdJ0tBp4tuM0TOwxNnzmELp06etZC3D4Bq3Ecm/g24i'
    b'5O9u+F/UpotFAXs0J6NLBKQqddFSU5RBltMSObMXx1AfaF63bL5Q11QnqjjWgRFpTYs80lRzt2yBiG+Ek2kE6rPEnk96wKMAtKup'
    b'XuceEpItYUNTf5nnRXYeVrf4eIIupJrjoGB2kj66W3amVfKoIvZjI3U5wF5SsSG7Jx1l/Buk98YnSzCOdvmka5kur0ddu9JwZXTX'
    b'DOHu+5nd18rEB60+jVRVP2GtCJWNVCls/wEgr0oY0kVo7SvRQfDvtZ9aduFIq4Pi8e30XMQAtPD/p2oZ4Hr6q0GQtLux3gHoZgvL'
    b'zdlTY6TVNgmlWbTopoLVEw8hEi4FNzNMt0FgXefQ3svS5idF4wMOzBiBoAa7+w3We1V/9qWTS15cCkWNcnZEQxx329Wuk6iAENGE'
    b'nMXW/ryOYT8cMfAlNFi25deWpxjGd/fOlIAjHnm0ylhiNMT+nbSyjFBRrtdnUGhiEi5EGFhKXOdiRH/WfLo+GqrBepeOjDHpbztf'
    b'OzjwiWJH9TvNMA/06hnobaCAkCAY60I/qQOGmd5C+BJOvlu8kOnHKPrJSXBoasbeVYg0hJB1TxTcOPnijMYfRmX0bwCfjx8jnjIU'
    b'UGxu1r08CicG0oIcyhg6FdGRF4tEv1KbirDWtqWIyIbmMNM+L/esalvucNU0u3lLSonG+JRmFJZ1UZda6r8Ek4qkyRjNzMU2eRhs'
    b'FFFSaBjiGjlLL1XI1gQcsOkpHUpj1pEuuIPhmvs7uuli5Y708JriBmLMpOWKzwtG/9m5XIG/oYtWjxxnjoyen3UrDJPE/cq21356'
    b'CJjr57tfTySz2eb7qhvmgxjm8148rVeu1zJZ9uY69NEmstPMs+/1Sp3Ey74Tc+y3x3U23AsOEFCP6m21s/3BFGZJZtbvxbFAzLEL'
    b'WUFpPvJs8bj+H2QALRI/308ZIkJMzMTAi7XDnW7OIelS3C+RAadALIohK2palFTpwLIXrscR7CeAlQRAXYA0ihIiJ8V5/Orww72q'
    b'zgHT6WNSlu/N0tQEGM5zuQKE23n5piEOn7SpLLWCQfq8cdZh/ajEhkOkmkWPWNYVnbah9cFFJLXjMVbBznXA1eqIT/q5+5sg4Uko'
    b'2F9kuyL7LtThrE+EMVRwXoFlnmfBkxGvUMUWWTLQCzob3Zb+PxZV9Wdp45x+7piLIOA36cjGOneFBIFIIWraaVb37ohDLZiFnljt'
    b'06bWR+xsTjhnC/wt8oFGN3e/cI7+qnBjCmtGXdaXK4usFoSBQ43a775tjusMN5KJgE412tKbMI1VCJHrU4jmcXAceN1aamX3dKbC'
    b'amXBDPaYcE4SaSZ1XvBISbGBBD/QAwNwKNiqOOxb0fI+g83kZ/ZZ5JXpoRa/tYXHjiC6OueWuJhx1Cnjjy8VgrbHj25dJcISjjM2'
    b'B5Nz3UHmQtKV1hXfcaTSWp14/+t666FgyECK9hu5ZmRbKVVeHTDWVCYLysmHumsrvbefZelUV8MIN1ohvGWJm5u5oSc+Q0J/wtpH'
    b'z4mwn40nsoXv179ykGhrWBVIjXAGozaUfNC4xWrlHR8nq6JfsW/1SHLbmbXaRXmH/rf/INr4WsYjhD5jLdSxbhpYItlbP4OfdHTq'
    b'uWWoE8qILQh+c+mPA2/hHXX328yybmz4sAtWEYKhbRDnTMtlRPbH6A5IKERRp/phF72FWJA32stCfhL0qtzQi4fthvA/LoNk7vu/'
    b'vW4Q6sigSlczbu+2PX84f6PqwLD9TJZQpZcgrUrVvm5EQQnt/aAKAGIcXm3vZBfBdDQFS6/Wo14gRLF7aiRUFZZ3FTya+p0tvvz2'
    b'tchponiB0NuoeqKxqAFBDewIhBpdV059OAHgx+A2jFNq8HCd3+L/5A3YQNIZM6o9n1N2wnGllE81zAJYvPQsVlLCk7rcUrnOBCAJ'
    b'iART8fgWfmCbWqi9yY9MtVEaPA1yMbzmIalzR16IRZf25uKpOO0IE/IFd2ZbkDdsLbeTKIng3Q8sfiFJOHDZ/WbsvJii08lFuFw9'
    b'PRXyKd1TRKDYhPrzZ9xHaf9YIAEEPXdsJurMhdtw2UdWM0K3aZl9GxYzmKgQzFjGqqOLkUXHU42Nhsz4E3GCyvhT18dwa4WTUJNY'
    b'wrB72CLMvxvliWVO4nVC/fqiiKdO6oFZ3ldHEEZf+7VeUxYuZeOF02TfzjOHT53dVAutOeXgQ9jMkY+6FyYGsGOy6S3Mw+Ki05hZ'
    b'Tyu/Zsp2RL6N0psjmSSAV8/QQoGB81/IlcaQ70BeyAd0ORkr7MXY0Kqim5JAFlQgzEsulx4Vf+umX7PboifOBD/3Z1pJtaOp/ikh'
    b'x4ev6s8a/S1RZiwHI/S4h/EHZfgBBRFzZgG62DI63ZfmlZTwoc80g2kMhPpLlZpu0bibZvYdJrhdzpSgEXchwvC1yiR0WTDhimvY'
    b'Hr6pwP+4X4Q1mn0K2vukrwpaXz+j6mB9v+iT3DE+8zIxSo272CnnOb6c4G/Sm7ElfPe46M4YiqRNsMNVr+yIQFOauOgvSLkvjWfu'
    b'7Vbf2hxRc8kWtGEcwDen7sHqKMUeLHni1Yk6ZPEdwOcq+iwk0QXDoBUYXmBxnUjRXYBfUyvn/TiFBCwJGjB7m+kx550z8nYqp9ZM'
    b'RURFtyu8+cVWPU8oucpIe6fp9qdqjpr7xYufRkLkF0v8P3/EkJo0hwWnzPxSYEpvVgujeQhDaIP0/iXBetqBNb86toQMah/Jk6Wk'
    b'1dOEopE4H7fV7caRRJobFfeN2pHSad3524TL6kTXfve0uetjFBfsFjZFZNEOdBas8nbLNs7RYrmleB+trX6XilGc8R96NM7CjYLN'
    b'y8cF0WFguX9dZ8/ea23AgVFc/9E3Lh1ENNB3ub9O0i2sT374R8n2TqUgftL+gtPh921bj5BE+v4JQmSr3R/ksK1Owxjj/MOYza1X'
    b'9rGJJsKQ31zseA7UNUPaaK5uOxMAfjBN0D0tH3PSUyTt2fpuOazKBrJxd+X4/hAiIjad2aRO2ivvvqDhzt0yLyErOypvuSatuHYS'
    b'LpxUfuL3Se34LFgBV+V2KkQKCB5W2/5cwKbeDf7885rc9CuLg85nRQWNYQb+U/o6OswAa86STNqKTCorCriqCLERvgVeEcD2Ua1Z'
    b'yA9ESY96/3nZ0totggZwIyZ+mHjO8EZXM1pTzBMebKRTIpDLinEj+1kGMckb0MVN6HVFpMaHxN2EwISVXpTwniKRkR6hmVVUe4Ci'
    b'TcXjEATD6fA/XLU3UFESACJ2/GEq9i8mF+tBK+JCWQBTtqc7coRcVQr88sqZtlU88OxOTdc9j4hkj8qPw7qG9JWFwCmbARHCnnyV'
    b'v3b+3GNQzcyPSn3ktTaR5rqiVhF1+3L0oKlj4vqGlBGJwuSi9dz3JNcp3GNTNFtlapQph810/qPHRx6WxMANk8RjtcEcx7AXaUNc'
    b'XX20wvMTmmdTSUNTtHHSlYUmrTB89IVl+aFbNest3x+3pG1tveRifnujj6g8PTfA/Jq9Knvkfxr2MFcW0I0fhj/U5dBCxdrMNvRL'
    b'IvDkWTSj2FgSAEkzlwu6YKVm1HLv9UPWLXPHWGsAEm7Bp9SwTuhegbUtbrbJUh3GLMKIQoqTPQkwtaSqkb2axBwIH6dvcXNsyYu9'
    b'9lJvzBmG1ojPGc4Z/XvA5utaLs1Do4wIxYmVUCQ0kN4YWTkuqg2eAvD+sLdMFDGCUKeruNsPP0tf6cv7bOpd9DW/Y9af01Sr5BcT'
    b'JymVZ63QL4xaPl0SE1jHt719jN40a9Ez1Lu16qHn+G0WnjF40NyHGrs9NjiGUMsK4do6T2ubGYmF+a1jZ906Qi/EU+WurlDA623W'
    b'aRePwk1BR+e9amD4Uc0D/KrM3FoY+3GuYMNSN60kZpJ4GbvMT4zClabHUEof5GR90BXpiO+SrUtw5pAErKpxF+3dA191F6r5zIAN'
    b'HPcyuYZnuSLUR4ReIKtdbTfF6XmwvXsiB3Ahg+IWP3qsp/vAItWW3lzARLABBZq3WKE6UxBSg1HVtBgD6SSYg/2vOJcoFddPqbak'
    b'd//AsjMV4siD28gUmmBLU3CWvkVaxx76EazbUAtXvRUgkVhm7PPGNa6+PPMqXPgOsELixqvAlc+ro4MMKBPfr91GJ89dDMjsW7vN'
    b'LWyQEh6mXVlmP36U5EpZ3BgjrHP+e0n9HgerozPFhRgTAxwGWPmd4xfTZPKe4c//xlJC4KtmEv1YSFsMfVSYekX5gnMaZNGLiVNK'
    b'TBdFVyjw8SZpPQGIFjCgMlEv1GC8DOpLtVHnTgz3LwqN8a/gwR12j6VgPZEJms7++SZ0aVvWEO1LSPOJJaR31uGQ3EeEAB5Zx7CU'
    b'NTIZYIDcA6Z2AmVhW/7COs8KAaw9CFVYm1SsoCjrmzh3q7ra4qQh+BJOAEEZO8LWLiNAaWVgLGfU4zGorfYLtX8hpV7pm9w8t1kM'
    b'Q2aKzEwW2Svot6Jucb9XoY6K6Y8HMtAM24CIuWvSFQY78uk1FlqcukONKoYCOE+KXfBDIRjfcEGypujUUsKOSbrJgJL5tE+naR3I'
    b'PxffuEKjDmpeHZHj+Kr+NXUl4oplLHgSvOlzPvF2VO7VZT5Vb9tFKg8V2qzkArNDz0hYvSAO2zPZSCgK52n1ydqnRa0XKmgZ8K3X'
    b'HEXPdPdf8Z5xAFY7iwOeIrkkTEW+ZzywABgjD3yRcusOlmayDFl3jmoYPd/1SC/X6ZMSVrsKRQXqdNQgyPXYK7yrNxCx0AGjdEZ8'
    b'fFrPs4j7PQGeE7QcHQwJwGFbDzKL7T/JqiqwSkwsyjKpkayHp5UDlZr7TFZYj8s83vseR9EINhdJxpC15eBmTAs0jzFOPNW4v/VF'
    b'JMLZ4pfOLB2Bt3mA5HTdM3O/Hb8JyPjdx5lQmazi8W/h372OKiO/zPm1Sn9h3J97EmV2XGdEKuEianA9FjK85ZHqEfa4ld1/3Aqk'
    b'CfLyOzytv+Y4hdjf0UQVIYorrVUEBF5Qv/e7BUJrxFwj+wRpEns74krH1SDSk0SLVsgjY/az9IStmdY6JjWEqyKkPkIF1UWnsPKT'
    b'CfTgFQMeP9u0DJYxu4N8vn2j3s6vvtF69ikjCj6+KxYA/9AJsoRR3tIEJ9L20saqUw93J2BPeSsoN9loS3F0TW6YnwgcTD6niE2t'
    b'FiL2IlEJsavCnwQVgDdbkQ/m+zfYj2g0BrND4n4xj+iEHqykeWsFa1FagZkqCLUWqeXRqIFmBpU75uDRzZioyt8o+ZyVc016fNhL'
    b'3C9tGgRAwvEFAgr/kxKUsFoDKDqoPzjXXfyP8VNbkGbXl5NiKu37/dFdufH24HwLWIRjIrxM+Y5Q9mGLJubDCjwFOSgVScv6ueCa'
    b'dKdJ0GlP5F3z0/nBgDubEiP+f/XjiZeAHJ0vJnnAjcxXVDVw+wpmt6Mccl+m7s7yikCuesoXFO6IdhNthRGJFrKVNp7+Om37v+7w'
    b'5D5m9H2h4iV3Nyv9ABWJFRIbuo+4kXEswxfJ29rFlFRQywn73nRcDlPANsKHurj2xPEnbgHTqVr2LB6PyjAAL5ZWoIfX0cFLgm68'
    b'YZbDq9LxaR4l5ZDiMUFHHq7BeQEs6UUec0nEVUSTVgmXwVOjCJKynaxx4jZbeDc5KYgdQa3kIuhf8katOqiE120kdyM98xr9Nx1K'
    b'dEE2z+e1jJwTsdHe8vImzBPGdErcfnsbzzE/MD81MGRfhREEqAKNW4BGCZUWrYS9TkI6uloXEUy9+jKRX9Zz8uga3HPdpkcRq9NY'
    b's2LDnOkZVqXpOw/PYnlrG+z0S4EvYyFExOw7SxgEK9KJ+DGN6NhjV+dxeJOrf3WOzSAg/47hfrywmpfk4uplSGv+pioitD4vVqy4'
    b'/FoM46ACE0EN0IuRzXZz0/SoFdjTLtGQA+bCVTbM4/yb/M6KRUOIek5okSoYFknP+XuG0u3UHI6FRdyeIeuJC/EnglfkWOXEVMFZ'
    b'ral+Tkyd/JUTbqrW6EX5irgWzEGwTicyK7Q0E5c4bjpG132R30HcZ0bpM5UVbbTHZYPrVoM3nR0oeSluPxSkQNg/6/FMgfuPOZzk'
    b'FAlQF2Mh5UaSfPBB0Zb7MMfrLYHceLNxr9lLSxvpa+fFsF2/yAq+PqrDRzrqNsI0fqSvyPppgVEl8EgL/t+kGnuuJDTP4DPct1mo'
    b'bcws1OVy5jUh2t0WroewLt8I4gq8N3Bbli9MA66W7KHu+n7SEaFpK2/UyMqjC24nT1+KoEPIcEcJHKS5ewYyJary/5G1c5L7U/zH'
    b'fenQXJznIPPXVO42NWLX00q5gjcI7u2KGGTM2GW5TN85/GKTT5khcS6P7rrQMEHxECe7K1bngY2egoVIP4oEIW980scuH1IqkSDE'
    b'ERvwTciOMNiVhLoQZagzFEUliDai/CNIvgzMVTrmPGF9OsoW56PMojoBAKyXPAz8cbmOGZoPm4OennyinjkpuSpO2GA9U5GPa/zN'
    b'SpYpe84nDD7D85MYKB2jEeuKKEuxNWs9nlu6i6REc0zbvniMKnzxi2h97hRbxx6Js94HxVdSd07fcQ2S/trxvgn0zOD1Afg8OSlD'
    b'AlcAhBvB228qK+JcGx+PBJNqAWAuNteXKxZuLgF3XfIgTRQrlbv5v3KH2e40Pv4mjWsU03vwu4fkFXhRc0DMZZ9hkZu8e2ln4zvR'
    b'hQUuSgEO7dJGWXgx0E+/zZj3Orrhoc0q75RCosYkI3ygHzzVvoG10D9JC7QR1YZIvq31bc/4QSZAjPu6Lf+7i/fz362VaVAZDWWh'
    b'CDmBhG/EcSbi06nNis6sDMn9LPJiHzkBd/z6EKVJeYtDRI83tOaF5joeC8eceKOcKEhjrB2G4DAHgwf3wybA23mR6KoL46kdk7qq'
    b'zOxzUDpjduSiIU6eisYtyr8/qD3S5UBJAKbxv4f1KSVIsWj0tnkueC7ps7u35sM8lV2bI6pgkV/gge1pRwrT65mPM4jFmdRZlwOM'
    b'ACIqQ1RBUJMtlLtSPfk3Ki50bXIHuBjiMG5lE9mNnvf79FiABDJfJu9bCBNHHaVpW9kN7mjpyIYUiRfR3eZhOWgC10cEO2UN7pXm'
    b'VCy5sV3tGEMW7/K1g8NGpv47AO5hTdfly5qVqxQsMQDW0u7fcHi909pfmjouvA4ghayxKc6k0Qi9+CbohkZCdH5hX2MUjrTzELwS'
    b'wspe1MYlMT5VwOBDgKp61/OiLApLrxxqRLza/z2kfToexg8b1SN4fUR0BXNKOSHuURZPbTUeLXrJ0tgmTFOEdvz7GsofwQGirpB0'
    b'W8FubEgzL7gCn6bFcILa9+BHAb2YlLGQPv3tA617IOQD9nZ/AnYoat0cGzTHtVLk4YSK3HyP1xprdmXsbNkyJ3qIxEZjWGLpzl4h'
    b'GdaqJh3pfhFor+GIArS9cS53vkBnDzFPcqbEOABgzJG9PgkKOsEYvEvAYintyvpoAqvP41fo1Rvz6xYglxbHLphRS+ZnaEledsJ4'
    b'BsfYAayMdsrcFqS1wepqpKMAb2weAvZSO6yAleZof5D5TRGJ5lyny7ZA8bodsMVnXPM+X1ZBL+n7TrRdWSFFXW3TKEdmHSadKh6p'
    b'b2lfSHZa13rVPp3xWin2tZ9aKT3rLASMGx30+adfsvUslRr60LyOcpgJodm/IDCE3J0KsozPHPCbjYinghMQEcf3604SvzwQZLzR'
    b'g1f5gYDn9PX6dsAsxOXwj/YF4MVIJ/+6oQqaTA6mIInkMN4eVpWU+N7qXUyMa6kr7U2dhISy/5HFrSucQedRUsyvb8TFae4llPyx'
    b'uV7a+2E1vDg3et8KKEHsaoIuSprvHej2o/L+zzZWDZ14OqdT5I6qZWTQvJLCDR6q+1aY2dW4ilfBOQTzujcKlJcXwdC367Cq81jL'
    b'RxJRTpkLKTUQN8uPd90P2XdM+W3LCkYwIMkJ/iB/mItdQWyBoaywR0In5NVJscZmUynery0XRHr/8acJOE1aIJ1yDLIn9sF4/SSf'
    b'jeEK0YqhBY5vPLOyPodBLtfSo1duFLReywlfrKTKvrvkq6EPwxqcoVKICEd/W1Ym3P17J8hvfH8LmVibmGBVy2HpNNvHTFz0vx9E'
    b'WiDjgVwcgRfZe5ohQFOB9FG7tZ/cwSjVBv/ZDDFUaFi/lFTEeWyzQKwbRB7DoebzkIron4EuxScvQjWZ+lyZEe8K39zbd5iYwYf2'
    b'lo6CwT+5qQI8Pk50qVyBRrvu+x3z+Vg/1l2BfOq7QxFL813PgdnjHiOaMdlBSPViBgJdj79ii1cIkJ0r7IpdNrOr7lfXyb/WbQdK'
    b'1AMW3p62klsXWWaoyM4TTC/loBn35BC5/PoKMiww6dhppkOx5tGNvblDwWh3tEiKT1H22FERv0IQli8BqBHtvCgqF1PyHkJd3gwS'
    b'tuShIw+BonlU1O9oqNRp45V9d9FUB2Ry/7q8/5dJOGJkg8kD/8ySfhUReOjp60RrnAFapSo4LjkuFwF/T7Z6csSBi1D1UvSxkPJS'
    b'Oi+3WDFVYgr72X4d9EAjvfxRzhvtkFdhJKIDfe8flEGKu/ZNY7CIhBqIPNa9QHYcXRUyWQEkcw4354imetxQg1uFdgAhzDaCZTmm'
    b'IEfq8akeXyB8h22zkU7aSvncGcpjQGFUyzojGVIG80PbDzn8+WiWQ7bQ807lgflNBeRleuwwEOupjFnW2UaSFD/SC9IwKq8G+FDy'
    b'kqKDj20kP+g/AMwpgtKViKX9/Gny99xfSNa61VeYeKwBXPOpUA4K9s7iJAeCYNl8C2ZhM4hadsCL6OJ9OyHqIlhmTW2hYUl7oqXV'
    b'vt9GPpbx8njoMvqOQDprpLR0z0rZudnxnfWncLVqL6TJNQCvmuHPPrppIuSTQ1GDXyw3+kjMAwH5WZeal9CFtzGOYbvQXKaqqeRZ'
    b'n0daGUAlXJJxMjbjJ4X4InTsXubNszQkhp6+u69cB1yt42V8Ra+kWf8zuigBpU2qWUIJg7eWTdHXwpHaN7GSropFZdrqlMDrZcnn'
    b'iX66rl4rSFOnLoluH1436/cbaFaBmnBosVzZP6g3mKLlnho+5RPwFAuZQ/cGUaITD595fWWdAv/bw86a3YOsFTSPx/JzbWcTJ+nj'
    b'/3ilXFyymORdS1Pa30iam4FxarJbfqlZlwGkjkQBQDXQdk7lX2lN7NJU41BSuKES/gL/Gr+zQLM9/jBhXLcl004zdH8g5rN3ajWl'
    b'z59pjgCrLWE2gHdWdm4XdDNs5tQtiIPFdi4viudw8Zg0u2B+n5z+EyzEJ2EZwiJ3QqkzfhdhbZC1tKhOO7TFccF8PM5DTFQVg7lX'
    b'lJDboWMIT2m2zzdBdHR2OWFVGpNUjoR+vwZ7pVerI+kLtnyi2xjBL9i9a2QHLjz2U8+rMmriknqOlUHLMPcagfC04R++UvOQLpbw'
    b'SNR9eD7ZdskcSZpOSt1quW/3IZ/RfOgsuYmSGKSNAniHN+fBS66dA686cePYQFY//pTiSPD9o9L1wNtdZaj+wqzgL6fqme6Cbln+'
    b'GFbqwwxjVMFAnZPET2p7w/pOb7cYuZz50tsBbsVirmNW335Ji0d4FxMiEQq2UhdpnDn/NVN/xkCq/KdEo73DKDScy92WlGUWTale'
    b'Fd+skUba73cvlQ5eZXBiVc7/YpvAIuCWwtWIo+odSF81WSkwJiLmyr6V+zPlmtkTimAq5fHy675Ho2FaNY5U5k/AnsYl2xBsrVr9'
    b'5ThADtwn4TQCR46TZj0hi7lEXn9iMzVR74c291VMlKerPg1siwZ45h6f0x6ILJldzDcKYALlVQSztIWbCmqJFDs+E6rkSotTUSgx'
    b'LgpwthyU4fNoDVMdTEJogJCEJk5TRlQGOjWry9S4Ghe6PwmZqkjVMix/P81oYa9H5k/4hz9gPTHHeEkWP5Ktw29s++Td7uUPAgpx'
    b'y9uEkmHIpsQL+NmI+ydnv+4Xa4FyWUp1oCKdw0guhZd0C0Sid64Plp9Z8WnGbLQvJy1BV9ibZC/0561frOM+5oklf4GNZaX9k9Fo'
    b'ezocs5mPr38+cahTEbYTju2CSn9XmmzZXThMX75ZalYpoOnjYyzjfNOJZdFpdGkLq2w9TPO76G6gfoi+WfVlFEZTKlFs2x7pgro1'
    b'Rn8ygCfykfdev7NVpiHZGjDKBby4yNUPE9K4TlC9SqSFUxpri1nCsP/k9SOUmnoBAocT83VCFuzO6vSE5LxrVEdnerQnlsR3hKyv'
    b'IwetTM+vg/Qt60XBG8nXK+UFYizCuwSUeenEUg3ihs8OCEenfmL9tSdnxtmT8u6qSZdgAZq1Noq9T34VvfTS4pbYGorJRSfNpi52'
    b'Y56aeoPXIKbSBUvTz2Z+8aGCvryh3l8+jXfEQlWkqB6vwqF90aBlW8OPcRVexQNWeaCQ44iuqwowdPaA2yeEPl6/Zz/NN4LBgztR'
    b'3LBZBO2uwms00N4CQl2473poxNgB7VBwAzk5aXYvTxy87dpl+sCVNz/o4PXz+q+D1vmCDLUdDoCDmmqlX2fStvwkmCENxaEPstpb'
    b'ARJAndULM3DBwvwlPguLtT1JgAthi6XNV25DKskErLsEKOe89huHPM0/nPTG7yKpKNjomRnKwvgj/t8gWDhkKYBXViLh8KrA14cH'
    b'dFh/oknWLLcFEQ28gDFI6JinKxYS2bLCcSM6+xRulkPe+0pMbLvtIQ311v2QfKstjYT3T9JuyBROTVSaSvPikvp/PqVYSeRFOlJi'
    b'ep4gsBEjT8Q39lkrMyqSC3PnfjiLCUkF4zgMJiGX56AurVJCCnAuYHsUNlT3aXN7cMkm8MoBtIMwtyLCi1D6q1miB0AsF7R+kCYb'
    b'tUfM6UQBp9sCxNQOyG2oY3+1mRIZQjUB+aQsQAafmi3nUg+Urf5r0poz4rJYZT9ha43fKECJuToTjif3REOUSoRPEZZstmg7Cg8x'
    b'PLoTOix2goL2/Rjz2NELFnUzsnQyCGp2KLp6GdOV9feDmvb+fJlH1DnI9QggWIQLK/n3tfth5IHoRyIUE4bXjnxXE93OBw/MSZgL'
    b'jQ64xSZ4o0+ODri+O8lA3EFIbZo5QvdJIe5MYAAyr8rjDMzqLuZXmRIibWru4CSLHATfh4qUSQlw0Vu4zM4yccXLxiAAgFGGG2mH'
    b'coVE0j31n5KOrEyd67Ltl7AWeootN1PAW2gDbRJHf0rzcfJkshAuOxVEnZeEOxDSFWUa/jCGgb4y0A4rQLnvU8tg3SeQ2SPAZabE'
    b'4klzYjy4Ohy4sDbofQZlw1GoeeoHTEi2h1tg3H9nPk4Lk8cjLr2RHcII0MjoVSvhHG4Ltagz13uo6ZUX8urc2m3tg0ac+URTT2HX'
    b'b7nboNivWEc4GPUABFdwvSA310XCBd31HbRYIMBPTffViuaXgg8WGNgyTfTIyftm0YTjdu+NuC26ttPdNY/D41fc5s+RqGldmGvu'
    b'uegH9/k2hlKRtKbqbKVWE1+Z728rfpXbJLpfVMGVHyaV2ciFox/psc2JoJd45M+yExeXexw+LRJV7qkCAP6E3Llj0BAD1hdK1gwR'
    b'AIgLJvRgaVSGV48O/FQx8jksZwgDaWHN9vXPuiOMjlkmejonbZ4BMO6DLqLzgYohGAnj1+eejnXX7JQvuQmd1UNC+EzYntO7XGBV'
    b'HRJd/N85VJSbESOYrPOCKEE/RDt+7xPFRzhMpcL7x5arMJ6bfjpxhwDD90xvOtNiC9GIUQHJCiMxFANedUrYHvb0gXEmyCreUO5Y'
    b'VOUqsxfF7OlXmk4G4fg6bOwFTrDY8kdfdEdR3LvfdefrkKpUKPartyKN2XfKyobi4Ws8XKgK3H08YZX3TJ9zN5i2XGIaVAdxulrV'
    b'6VEFrIeAE9zeI9EdsnowyDAgN2YiP0qS+DwF04zTB5cFYuLXLZNE1DDfs1fvACQ1+s2mB0yADlCkAvCRvF5QchpL8tsShLTXYNdY'
    b'UfznD9req+c6A68dZ6zWYFW0ufmrv/t9wPE0BbycCyx7+2cAHpQnO0agGJokeeGevpOpcD7Jg8BOSL/SmN+P+ZAfBvpDRvmazEag'
    b'2/Xy9B7rX3Kmilc+8MgsDUgq8FMuV4VN9/3z+/DIUG9KvWGBEOsWbFuiWmjXJRAW7eu3/wwHxmTYC1xWIiSL0SGk9y2p2HN+ut/s'
    b'zBznKaH848qpdU3EMaOLYuAi0J1h1mqRi2gFODhd3964ftgCRxz9X9j/x1Fsa81x4NydXy50f/LmP90fRZPZAdJDRZMokfRqgEC7'
    b'H05BN85BHJke8MXm33irdycfpzCfK/sTD2wKm+v6obzJQKbyZuZe/WWiXmru3y3z42S3EHiNxhw4dxXEcR3PvIIHJ5BvKWcaZ6Vd'
    b'QgmjJBE8wftGpmeRgZYSPLHdRDlDq7BILcC3hbiswlxMooUtslFZZ7h2csrJSl3c/uvnIYVwWzCW8+QvRuj98UY4ygVYTvHnNzmS'
    b'7q0TgNKsZZj82aDst9ySrwPgsfrCRqjok6n2HnBgUIVnAIlWE0NHX/lvYKTk9L0ZTBW3Qf2eegzdrbbdvqprGJ42bgr1Kd/aLBVB'
    b'rsxNGYBGd5DxaF4hkr+IvWVGXLNhxAnFMPExTotkTpD2vAovYs0tnKa5x5gqElUz41HBsaNfzw6DRT77Wt4dEpaOS16U+nHEpexy'
    b'eUI9pm584NiTW+c3VkV3TmEbwhtlxydDimZmwzmwt1txpEhUfFSzfza0qKgSQvnzRagJBxERPAA3hdDVS920F2IYPz0ucTZNU+94'
    b'yEU5ePzNQv/KvVj4O37F6FNcXwt8QDyvHcCu2F1U1zfWrrPUSGiy9tqct/DR12O8bRMXxEBgp006ftG20mGnP7w1PbFV81WepJ3C'
    b'9w9DaSWcw5YYN5t8l/PFHzxpoETpZKXNreI8KK04DQYUyD2OGCGdwFvJ87Db8Ad3asSd1dJB3YDpPh3DHAmiO66iNvXWYOD3ZYxL'
    b'LNcaEpJGRU+MGr5n5YuNnO9o8H0641QUauqqzxAbJo7VrKteDFyrlf/Yvn7XziftIZHBodQViDNWhHGE2j+2huTdcObIJoYLGreq'
    b'02O2BhRrbsQAmygtVH4koSSWZQKrAzzPaguwkWlJysY9s2eLBY1bnfEiAbVNyXH5nUfxOHrEI67+DzdoyIs7s5rSlTMc1rkUkgH8'
    b'8SIZkzYU0xEvH0mBjgKAelOLh9SecVHR3eMnuMBpJs1GHrW3pLVcFZ/TvvzCMlW4yiVwTDx3XGZDSfxdvroDeV3sefbD3On1rdEq'
    b'yOCMD6RRXZrEvBJ3Ojc5h5/NVhWXXOPsD3F9yrBRQzqFM3Dr2GiROSATZ+v7sjPps5sMBedkXgZ8b0kVt+6XDCjgwwXCjH/2wNsp'
    b'Lj/OHu2rlTCFgt6ErTwRfcmhq3RCpDj+wA0HvjtyV3S7ENdAreXduiZj35Zgg7+O9LTTyEVIl0i9phJITejCP/r04l204kXb0nXd'
    b'8II0zbWQ2WPECjdk7/2+bQDLzzO46UBAl6eFhCucnMvTv2lIMCsiZAW3+IDXj4A5S2oLm3xnWdxpKkfhk/ob7Wn6pi6C5hJArTKZ'
    b'LwHkJ93vfEimwTeNefc3LIwG76dV/IXsBN9sksTKdr2J3REvDhTIFgDdaGuhH/U9osCj/KxLN050vi9bMMPdm5cOBbIgPZF2ZySX'
    b'Ix1rkbzGiRz5BWDoeW/gGZa1W7tH9DBMX3uiaLykZUfGuvbj+uscFBbk1HhCNmee2ddWNkxioPgbYDt6nQSzbZTok32+71FebMLN'
    b'kQOzSEak+XOStIuKohAXBk32djxhplZOC3IEJLrOynOAJMdDXH+LBdJNu5tqd7Xi1wRlkGAsl7RvXq8l/SOtSzxUJrn92if9u5Ms'
    b'6wVr/jO3/XvJJmsaijm1dcZo3Zfss03M/WqigXR61aOqXXSEGWiMgL/fPkmRbg10yJuRRPD6xNWRwcYFq2TM4oDy4VxNtqCt7jxR'
    b'p59tyeExlnM6b5gY3FjQg2zOot/o/WrUCEjER4axdfbHxYVoxG2HsefrT6HOV5B3QSQNhUeItqFx9DO7iit0mdWZQqIKXq5Iaqx4'
    b'i3laIh0q+v/9/dni9olmozjk9ttmD64Ifyw/tO9mFbPWpM5J61yvSXl0gcKA5TxCK8Ccu/BebdHZ6I5Hob+8wFdP71qSvk+31aYV'
    b'dI9dQl6jVu4AsT9oR126X29UPvtJrYg2URlpfKAdutwYnRiZ/DzewdhgMueMC7lHFrLKgLbNJjPaqOiqjcPZpB05xMb0JQIloYV8'
    b'e9LWsRUCkt4XummQR0Q885T1Vjq0/7o/3/MlovugVaJytY7A9c9DEuc+obrjyuKR2TEMTg04x0YShqSfOqFVRRN0QTTbflRgL9yP'
    b'E43smcb1TanGhhsuE5jGwIuZoCa0ZUsf3TRcQ9pwLk2hlucCoVE6aQ71VykkrVXig3t3Fsptrx8ErxIicH8IacoAD5ZZu74zHBpk'
    b'LEB56aG1kosuDpCwM11ZsNynt8hr6m1kdJ7Y+ZPeWITejl+xkZLq54g90MXeAz+ZPHASAypiAIxexbQ7piyBh72qW0xqDZysEOQj'
    b'nXccg8W2mlfNij7PP3HwefWsiq262b4GxGGWS7cW3KvUkH7gBeS8esKH4iWSneZldyZ6H1Cs3AVEY4hBA8iQLpKNE4CH83p+4DL/'
    b'nmVICdrxnVAJQnKeN9I8TnzWV2IxfHPdQMU3ItKEGZIyH72AFHaL+5yYWkPnAAHXLMjbpBFrO6wluxsRPI8oDTIKF3+nGpRtLAQF'
    b'1HeRFjy47Z+qMLtUWrv0PacAWdffFneSlywdtYYWKiKXxXRovHoaq0lIXt5PAL4aarQPMPmAI2JNdhTUijMZlV/xmEfDFykP44D6'
    b'Kzml1UjrPz3MlkeyQvrAu/7/p7XuRk7IT/2tfIgK5sBx4I8y0+GjgTh+Bx6FT5GEuTDhjqvj7MLqwXMbCdsx8OqpEYa2IMPAFXQi'
    b'oUUoZPoBknn8oW5Ry8uHTDNCrTk/bpY9PRKVTs04SSHM+vfbHWmVfq5fjrBHhKEo3KySXyD/HclztIUqb32ABbKu6kbfA8Osk2aR'
    b'nDa2p94stP3Swza6SGr0WTJDxtCdtbd7DF+1TWEyGw4/ZpSpdfDvFQRJ/LzX3tS2WETGeq5kOO5kB9IGtOcxEVfz6rYV7qNjvq7G'
    b'Fg4w9CwcN6904dLzGfb5uwxc20Xk30mv+6gKQfXCQ/fT0if5Db81b5pzurUKp4KSuzo/rA8z9Wz68WFqcjpd4I5QHNVuhDC2RL+P'
    b'Mn8y/vdDQ/UKN1w8pTssO1ja5IE5sZqgH9j9jAk5ywNYa/eu1YnC9GknsSzkgpbKHBQSbJwFjuaFwwgIS04ZI9/VcBkdjD6kXfIo'
    b'qRsN4s+Y8E0DxN42LwDFlITMMuDP8ruavWVc1v98L4KDZKsTISDKs0+rHpoGAjQ3+YPn0n7m7enhe+nseDzvQkjOw1zufqUicCiO'
    b'wrTyV5qvrbGD/P4dg8AqShjLRA0tW8DZI9uQaZpsXd4vu5epRbQQqRmh1KNr2MgxK/DPOeRI9ALIu6jBAqPsyVhScwwuIVLYXt26'
    b'w+Ga6MvSIG5xzOV/+D9T4O6vjOxX0F78j/PQQtZKcRWGO5MCUUCT0bbqNZhR5lGsgi/iSXvlLrATI/NULo2IbRVcMdbMbcTj+xAX'
    b'c3jbwk0vqHGlE0A+g7r3TiyBzE9nY95maxFqTGHF6LObUofbq9Is8FBqMLW5C66gkOongjytLox+iqZve9XTx0B+KcgyuAz/7+UT'
    b'3iR59czK7FX0VbVn/x/W7ZvfWjyow7MMwB81Otlv61Lt0brjSgs4yCRNvLXXH6aPMsqA1ff8v0zt8vVatnXubGYQ5Jvk+NMt6ykb'
    b'pbneDlSWShyBoSDQiK6FaJYm7jZUbZEwid9Gg0g9QyOHW72A3kL4TFW1qoMRbIgCxN480Xj/izXzK1stHfQEuMRoNVYFDfLwaeqj'
    b'GSvI+e6v6dGHfiZlVh8pCAnhfQnM+tmq9ehFU54N+4En3zStmN70pGDAwR7O9Cme4U1jZ4reI3O27sem62a4DV83Z3c4SKbHctOZ'
    b'cTYV6TaRMmt1XIYakBHUlgrdvNJAQuJ+tOxglHkiayA3Sbz7A5GzvJsZnRd+lb+X+3S/+BST/l/0xeVXAcZchi+T62xlDpP5s63T'
    b'InJx/I1DgwgId/jPy6OVIfh4b5hhReWbz8AxTmuqaYT4vZSteb2a9BB401zcNV5QjimdyR9QVBdDupJ5b/DrEASdsZMs05cUVjch'
    b'ufmSHe8CFaqJhIZKAPalLNUaVuE5M6+6x0K8YlTTngcOfbHq7trOEbyy/fASL6hx0WFwo5m+lxRXYE0Y1D5KLrk85tEtyQlSQbt3'
    b'pGu0DbAX1ffennr6d9ePb2t776bHs2l/iI0vwma0HWoGC5R6VLiLGGtdzjU8eluOngu6chcslcD8qCSfapZvE+kHQCgpCukKIWWs'
    b'F4Lm2UrbNphV2NUkCarJj8+DK0PEVcWx54qP6IJcaNB/5OWfjFajBqCrAhV0ldMLGBPWWDL+7Ht2+d1KJTERfOJ9J2r6daIvkv2w'
    b'MKjxOjJ9Wq4XUgVJCZYBpCJKec0F1iSN8tsD91tKs2j7Ba2rBgOteXcEnZbAG/EDuWxFfK/LO08rrr20sGkTYDUWpzeZnvbgf86i'
    b'lfplFOa/sYAeWaOvZ413cvVtt0JkAaiWil3wV9j+EKF3TXruCQ9UZW8i41mvCaeXJ5EEvu5mziXj55G3S5xgU9mv4QsEMXzZ8pST'
    b'Ck+lo02pe4Ytb2KUMzpQiLnLZ8xaS6cLTBfc1fIwx1bdOiFkql0Jm8ogpFctiVmRe66tNLotHQi0B2onREBdSW+gzCjdxf7kzL3J'
    b'XZcAsnP9lVnAPhOv/n3n9j8JmaLjzIOHz31N+EVKr9j6h+bdEhBWfMnGr0LAyekF46mEda4aMUMZNBZDBwG0UVegjSKJ1Te4PezV'
    b'DAJ1lCBnSHtg8LmzmeuMBAbk2v52kcdupPsl4T+IghQZTlJYOAXRb3VNnx5efENv3CuanI2C1cbgyTFBv33qVz2TOCw+jrSzrfbU'
    b'hunutDQPsu+ckQwSZWpaAcbgbBjXxJFGZ+hvQUeDPr+K++HwBO4vzk7InKOmEqPif3a9AaDfUQ54Y/IZ/8Jhh5KAdyXp982X/4bi'
    b'8KNiSw8SddCi4GHz0pAyxZxjAUacgZ4l4ypp91OLrHtCbyHLk40nk/tsYPTAyZdu1PYtwx5kOp8x6w4FCIFrWFyV2cu5lln0OLNV'
    b'f0snmxwdWXYf/y6tjhIY2Un6iu7Pswl3F8R+yVdXxuCSmk6WSxkIu9ahHPjzOrLeWM0hpdMW3yMmCXtN6fUjp1OjqA5uLEm6kGeZ'
    b'BAheI2lhCDylWKo2xqSy1ml9ndOv+kVWleeUM8KK67KhFqVbiNfYf6SWwUe7YAo0d/yDyaCUPSAkuIwhf6giFgOTWFilwDSUeqHk'
    b'vM31JrHa1WQAQBxyeh941+fERyISlaWiwmEm4BQT/LTli3Ytxbz5XJzb8z+XFvvy9nVxD+v//b6PB2CbywpteUMx6XCDEdap3tJH'
    b'kroxT1ODyMLRP8bduoG3Kcy4OjCMVe7u4vhrN6PnvrF/xc2pmY+KwUBn1SS2MTOqmPH9f2h1tYbcEOfB2GmRFSL95qkZdbNOLjSu'
    b'KPYkM8yrwwEo7ct6N9kIi9Yz5mtrsEZd1i7ZrWaqZJXBEFeqWJuUbcojDl+zXGR8GZ0OCQxPqpA7SPndyCybD7cg6CHU4r1zKyX0'
    b'wTtdIKUfmfUX1oYXiEBLr632aIj8f9eMapdU6sXlud9IdChf1bSbViVUJx7RSlPukAs5mTRD+Hw8seYyg4SI2JLi+dwEvnqAVsm4'
    b'6U6s9y5zGIzqnTcCV2aLrqdaSyr9ULJYyUafukKgVE4zOy13b6pEH5t4myyjljI5dEqICliC0axcTRbLurMXlBfPYTVoRQnfR612'
    b'7CJKmGoADR1rJE2jUk+qumslfR6HOV3PGSsSbr4LFjDH1CHa7CJ+sFQpGdjxbQAUZ+7SNzYB3LFuVAHXZmtkq5XxYxO2rQkL0Igw'
    b'Dw6iOOwG9LRhbYxf0lI8ijmpp0eX93NgFrd9y4se13YnL5/2dHlyUdAJVJDh77kcEEHBaWbHn48j3XiPCFVo7ZouOGq+2tG3EVn3'
    b'84iE2uU6ogId9/9Cxqy3pwG5yCbWDyzbRD2DGLL8oKtt33r71DaIUTPn7by7CSzdvp6yuThHDIfRqzXszfzavrjEeYh068jdAaV6'
    b'ZXJOGJYIYkL6evbvmgEfqktxTzF9FRXzL1OleAKm6KeDK5vWWZjVHiXqOkaDStntnP6loxfMXr+EDuH5x+BMdz6E0ySFpk0BkkGn'
    b'DuXu15emZxW35jQA7P49VqFJhvhf+StQL7aKo/+X0nAxczSD0T7KnLgIytlj4IdYMeMby/QqYKWJhy57FVPvZI129lVHQ/ifiHKU'
    b'WkdBgJvyjBYzCVphhJTze2pg1+NV0x3fv7vGs0dTr0YtiGcgDDPHWhFa/E0gcWPgGT9/D91fg0H2pxoCFVoKnnYI++Zti4ogJcHI'
    b'smfGa536NIBh6kyqsQSkkmOlYWMxztZFr1q7efqJJBmmPRAqIWZOfDhy6nYQIISLRWwIRgF4HHcbQBj1JG1Y+5/UThLX0AM5jXUi'
    b'd8vv8sPNik2CAlNOG32C069lm3RDUcUcGh3O4mn6CRPKOLUXFT84BQ8uTxj2Ahk/mvGCP6/tLpm+03iXCpjvcZpXvHyacQXt8Hzh'
    b'HbAGhgKzycJCXd9i3O4Upi9L6jZA6gwN3q9MHZQi/H46WljYX04asH6IxYkrIzxbrci/hM33HUEPt7clIzPx4AG5cshvOlSAB/qZ'
    b'lM5Yq8z42aTSWHahZ1THthi1347nGCwUAreQG7cpHoeroZLu0H3dWahD6PJ8/ACKSlOIyDuOsmVOn5Pdvc4bH585oA10hCv2KBwO'
    b'71eoPlBBfGJ6HLTaCx82AKDbvQQQiWyNgZf9aIKbJYaoHh9OYDkGhu/HyiWqLPKR2IE2iN+//OEfcS5rohXoRXBOiL+X9kImUitC'
    b'h9Q5Dj+ZNVETFKFGe554LF8At6oNGQ8fizPCraSGy5JBwRvxRBmVTypwALS2Em9k1xzTghr6z5EE+VZ+8TTrjx5KjOieVXFsRyJt'
    b'9O4pYpkVMU21aeUGAqg2HREIa0PtJk68A++I15lMnBfsbMJfFNcImGOORtPTdbFravmYHyviAopr5FW5Xmx8djVR0eKgdcrax1Bp'
    b'pF+rH4UlptStaZwLmorfqZG/JRjh6g/2RnyWWDcn40vgqC632xwJKGTlhxA1SObdO/0VkwhGEdPh9NktQk28OpjdXgt3krVRAwzZ'
    b'BCh1cwcf7fbqHNyySk5vf2tBmdQKO8CYEyqb+waFiQ7EmHbXx2BWoBqc9V3fmZyk6MIcSO8nxuj8/fvUtIbISYC079sppJuOXxTG'
    b'JcS9TCLrBYpBfLQ4ZiH/gydHqwyJJfWZ88DEaVZmMlKoRtZLgcUlCZfIORuRhErvliSMzW8plXD4ytd4/rsQwc/FTd+GO7eOdPcJ'
    b'3Pkl5HIbZ33+nyzTQyCRfJ6MgjT2feZEh8p2KcEu20lsNAP6axhNQ0E3ala0oDcUBwLmmAoz/OzHKC4EaA1QSUX4jfTfutfKuTD4'
    b'docZRJYt4s+Sb5p1Ft2HOQ9p+E5oyFTgF4+53I/s7NP6lnW+BUH6OBuL4u79uXFMD8YFARwaZ9YbTBypjDgIFLaZaYnbmN1ay956'
    b'wyB4auzi1Nrb15zvmAV2V7dtCKf5LX1rgDEp5ihiGn13rSF+NDqb9jOjDtQaob+7fRcml6wlHqC9APQYsXi1Ck2HSpLfo8V71zqy'
    b'gUmTHyBQoBQSovRARO/JCuCv+NDbFHphiblZohgvHk9RIjUeE5m4rkKTS2qclcWR7hoAq17MHCDzTfHq7Z+22MakM4Y0/JgYXeDV'
    b'uYNODZO/H4ZkAFb9cI7/cbrYnFEa1FpnMZ5fmobpUIyy8Xj+aaTPr2u/0H/bhNEa65WYJsoAthia1xTfGoNt9c5k34EAPWtjqyyS'
    b'6yf1fKL+dVrMlDlHr4+oEW3rsl91VMiI5Z0czqkOvBGoIMs8+tYVqoQanoFhqC51d6xPqnJLDNwCr+O5M3SDQaFaxrpNAaoojhma'
    b'nPzI3b9xImk0PMeFNI8kiAvRvS+pG8RgJMFlXig4s9P4Iv4mXvR7/VVsK4b6GZbGcrW10vJrBfOkk1FLkgK+edMmlyoif7iivYMo'
    b'tdhe5iTFqSB8Qd5afmbOvuh4JeqC7EfV/iTGb3qIi/2c1Xr3QoiJDxZ9uPxT6fiCcg4KF+TqIKsYiVUfyX5Iy/1hGoNUokp/o425'
    b'1qixsPzjtsB2zjdYXfyxDBqCIxY1FdMrDU0h6prUDG4qyM6KxWBANfXiIzePXZDvjFKrAVR/Ehna8VAhWehAXVkrJxI3KeEfn9IP'
    b'zqhJOCYqnYFqRLq+A022BWRd+Cgcws0HRChuatHiFTj5SLbiPrma3pyCJV3qJZ8oHPRzSh6sjnADeOxzEvoJND8pyAqmzha+Jvps'
    b'DqjE6+kS6+NT9zR28f4gbI/aLdRQbFQPZiOPu1VSmR+1p8F4bu14T6dE2MJQdu5KBMfK1yKxOhhFFKCqQbUDsJ8N2M+kTlW3rUZ1'
    b'b7p50NY+TYOtz6sfr79UnE52Pxp2RkKOHXh8ND2CVbbwKAP+ERRYNLQp34In1bjHLHhJFoaPtaus+6pfTbZuZl0OxTGr03ORue2q'
    b'FZeuUEk6BW9m2f63veRBYyYEZrTdzbMD14Cr9xjriQQNWIS1z+otgjoTo0qSdCYTefwI+KcAmb/36QrDKC6u4Bas1PPtCPCgyVcC'
    b'f5F1aNFUtkRX2qSKDkko8sdNEmgFxaohyvnnyUckYDXjV2IFiU0sEzr2UKTNsuIVhnwdpprrJmItO4RaY7/3zsh2UOkj5P4bZ416'
    b'u6Ogyz9XvuZb8pO8U4JlFzqPXRlre8UfWhoPdpfWvz9X+IbQ7QhHFGG/m2o5JU6rtfaIr6+BIPmMIyQEy91YlDrGKr0RedXrp2Uy'
    b'hEZ6sVRBLPGiQ3PWe0H/C1RlKVvEIICnu8ViuvQLFpxf3tNvVjLWT4fKPRXjaNbgzPb7go7mLmmPBkV4raJST1stwunAZO+uBmLd'
    b'BE+RhMLTNRkV+u+4STRe2sUHW8Eng88k7C723vajwZJEReZvo3jQNLtgb8IIlfyUX8QrwQoBU+dJ7MMy9w1NKRNsqAk6ykFm3vXW'
    b'w4QQPJBwSQIirYKA3Er5E74TEEG2dgKRUV+KYhYTtdfumRgnvna5ydL5dlOWYvZY1vyPkbD1gm6XUnPnj7fO2fh7ZLgcDySB2EYu'
    b'a/j8Fvl+bXMGhdkmdBFVTH5yeSR3qqVoKyO60QI5ixtQE/mqGBFEByOxFApAKrhDQRXqvdNr+5oj98Um1NVPX8cSrMdsC7KweQ+K'
    b'7lzRRe0jPnqtDLaogGXJeGoKX/7gVrN1m/evhHl4isq9mBNgQbfooQ0V27IZXvIIJSSJiEjrgJY+2ECbwq3Wdmu/VCsgcJQJS0j2'
    b'bJ79GE6QCk5cAqvv04jjdraQl4yCQxV46zG6pMtbWAUdG3DOs4Ky7ZoUALc76tTIcqzFH8CxiFi/7gWDkkfuJBpCbf+LJd+IYE18'
    b'XH/RpNPvw+A59P7on1OnqFWpnTLrUkKORU8BV8IfnWZOF5iz6PPlNaev88agoDvsGLgsdxurkX11ovKzgbcxZcAQwjmdYBfhvjXq'
    b'VNE8snn9U+pGNr8eOcOgfLI4XGiS1GVEn4XpPuffaTWAFEbb7T/llySYtuQh4Bu2Ytb34zuufsHnnnbj64e2rINF2R+FXNU9uZEY'
    b'wMcFgtVF5QhoGV4r++f/KYVJzfHn2DFM8fkQ45D7HTqCQbFmEToHoxW4CQSdFhNpHOpyPmIrNDRTYYos6vkzyiPT9G+yqVnByUUL'
    b'bvxNfFO+LTIBM/pHM2TKX0DmlB7besAhE/uoorssSa11WdPJSnIeI05OJWAN+sjrBtwmYkRT36Yxce+HaeGaYW+uFdW6x/3s7E9U'
    b'HtkXdJbv5qpO6uKH1aayJA5yyYZBItHQEHcJMxLRg89qyocdgDNRUALibf4ODwm/lge8meq3S2VCqK6CryNcoy9wakOND6Tccqo6'
    b'ZatnfAo+Ruzf9+4BLT+YYPUk2i+nuhszu66JYirflv3dRmDWFsrf20chFjoyKZzmwrdx7rR/7KQ7KDczBosoKa+dlaDzPQPmKMhB'
    b'a7Gcpw71ZFhYhaukuGSW6jcTPmHBkwlwHmaHV7jMRmvxphapZRyIKJ7hY6L75lkg5XA+zXizu4GVXJQWNZkY0rwG60NhGZ0igArZ'
    b'kJkl6iZrmfXkOqupOhKjE/mnHBsK79zBMDvauRFVHKIsuOwKFjHxr2nSK48g6dgPDjBeWmLKz18zP2vMuGBHon5iROZQ55ocHz1r'
    b'bOqx0OxHfjxU93tbvPe/Dtf6IFUAAWhV2pewXcYvVxHoSVQwpD/bjUvgfZQeHmtdUKa9VNfpqU9AYTY2GROVXmtA9LwVw++E28zR'
    b'LKEAnRgqJlECrSfSV/IePqlC0l4l+Ix0npB43S0TxSTTT7vfKfByM0EFlNTT/HRkj3KD6zSFOGG1ySXU0fLW9DXaZpyaiGDECr7x'
    b'ji4mFGMTxIpKaCSbFHYLuNMRnNEkjqRwdeaU3Fpjq9JQHq1yI0xcpwCtnSongyzyEXQ3ygcNrNjI70RORfflJuCVbQc2qxikHXEq'
    b'cAvVk3PZWP15hoAN7D0oBsfEpqxN0SOgn/Fkd31rQWsFdfgX/YmRQT+2KyjSQHzXRuTm5yYXV4MrlEznl3Zn0Pcx73fU2ie1O+nQ'
    b'mbX6KKhjtvk224IobCMMcp6HcBmSUprUzpKGsFWXG5x1F+FC3k+vxBEWeh+sPdD9keJOWxuzg8wQhQSG5Vz1QGbrGNqFUQFD3qx8'
    b'vvMriqIlkitbjjKy2EXGG0Vl5Xspoe4sueuKt2CJhpxh3EUFWIkHLeKz4CSTBRo/97xGUKIJD01l42TG/jFMTXVLaxsKD1903nF9'
    b'yjWQm9MvVH1bisiLrUdh7GToWBpIju256G0Mgy9dfd6iFIRqLDiCT00I2tOl+/WhndOROZg+/qHukrzlXSYRItO1gMbBRVivM3dV'
    b'50Mh3oraM3k7353P/1tGk39vkUYqkBmp/HkurRJoSUAr8PS+hc8/eLhQA4xHjymv/HK3QYadri4s0jIWouHocapjWLg7JEBdfM/j'
    b'FT+ifntKTbCSc0cYeDhNCC3wsAFuKoqOZuBsTJCjOXlVuPDcwXSSxKj1W5y9OIWLTGkiuiY6ej/Mn/bfb/HRnZIw5YT+L+916Lod'
    b'IVFakN/f3XSBs7dc46Edg3BBLZlUvUITMgFggI6MZ6Rrc/VOEXFOPFH+mAvll1Kuz8YE2sO0hGv+ArWaVt9Xq2S4ItSbsc8KuowB'
    b'jofTYqgf7mxNlZpiQI2vuowOL4oDQs1Azz0f6m2Dt03/MG9Ls7kDIQ6Gn7zylcEvWN4ELq2jvU1wCgF9EPpF4at7UaV9WI0GuS7p'
    b'HB7l4QSEAArueoDxDWpn3D9JXoDZgqxY6iFkTUWY8e6ek7X1qBNOxbxECYR6RFE/5l9EDg84a/EIz5CDL8cOICXQjYeNyP6EoDGF'
    b'SMYFCEZUuRUmGoinXLfsCwLgOJf+VaTZlG+IHkr12+DUEeAyIzhvHefjsgp7UAUn/Zj2IUxAcd0e7k1ZwLLAuZWwaZobV7myJg65'
    b'DgcosPtBExCBVocu0KLmaQSjqja1p0NX6+i+oUeSN3Y0siyTAof607pClxmvbLX8kumJfT5eunhmLpqR9Xd/bHcJP8Jha4qgGn6U'
    b'PRORnJhrXI6SODBp4e/1oxZUt+9w+cXyRN5sN5/HUSn2X0Hm0B2xYUCfBFS5Yk+dLiUGtMzgU3+uzIjm/UqJ4gn+tE8z+26ZQZI2'
    b'njawfwBdg8Db2w1zhZ1lJMEUjpXOMunCB2S7ZB1XlVfy9FyDZBrY9+hC8NkizNnkjQJZIAdbluCfthlD8K1YqXWM+vOROhFq7WWe'
    b'7o3q5fkV93MUVQMPaNw1E9F0hrxYPnmEpLSk5COpYih4Gp5jtopc+VnSZZ8PVxel3vi9VPj8didGosLzKmAfWNcye2wxFNXS/gP1'
    b'wOMaJGlCa+StIOYXnYhmrLaMHtrqkvj92ot3PvYM+2q6GtF779IgV7kI1cpgueFltAyP7vU43wzkQzM2V3zvVidGV1UuA7Ngf9F2'
    b'YfWtZGVrcMsJj/hpO4poT/cq3ufw0K7vtsaXrGe/ot7TUzb8Y453sCdxFRfci5Kwe9Ly7u1HLS7qOgs1rj3S2tEBYROHa03IOR9L'
    b'L135dF3A6qEACifWi11Lt8Z63cq6/W0qChNOer5B3EM7Cb70M0jx3XsrVXuGlBYdLoaN5Fex9p2lK8mvV90VR1O3Q76b4mKUjwPp'
    b'IIIUu3mBSiE5HDQtezud2oa+LwevGANMHmaSjxfgNLGBdu7aq8SnKhLF9iok0SjmfGDF0Eh912ik6+svAhbNtU6CYQjZdkYd6TOc'
    b'MPRNSUsEm9XIAbjGYSnfeMDURZ/zlTfDoGYekWQGC1kmAoaMZ1WaOlwBrvAKJqs46QZxNY9FL2I2GbUVaAnoTBe0YQ1U5FwpeHHJ'
    b'XqIBfK4SU54VrqidGvrewDQiHuzuejKJbVOxH1pPXJH6F/meJLR15uDdnyQtVo358VqEIMdJ4LZlQkccqz1V2xB1a7YfvJt8U3ID'
    b'CrZzSgSu/Q9EQsvBL96heJFgshmo+S7h0NUI4zNSaNVfFkAW8L+ZvcQY5SLRFrcfa4ucyIYa1ykDErIDsVVdM5cs1qTOMZ0mCFGm'
    b'nUozuZvrtAhdp1P9tM5jX70XPUhnBbmJ5mnxZbqXDtyzKxHCdKzDU4xJYq0CHQQlGkEYvsBTGDncRmN/US8ijty4cEi4s6dmy3L3'
    b'/P3WSRkaYIL+gVsrzjDwxAmTfziBQ6FLiE/Hc3hzFFnKsTQzo0i8z++by5dJEzMndvy8zvArvmhmqrbEUYP/TPGCgDKDRdzdVrft'
    b'jaZafrJ6tcA8hnUqpLXTXprT66/ULEm1U9CauzYdKxb3sLmZjuXQ0aiaRj29WQVXOTeoBRI5/xKBbA0ccGX8nhyEnSt5bXZQs2Ix'
    b'I1Py+jwksBG5+mOpPAIxyjmghC74JUJQPOCvTlbqH2V+St4RAMfHouBjkLfN9BIvi9VnTT0xTaM9w9D8ltPfXRtCN9BeQSc46Ok3'
    b'bCO35RKZ98T//tPln6mXSDs69NpLInh+7BgTNCQZoiA6CwLqUe/6TPR4dgAqxWytVFjFQvKKwpLLflw/b7Ey6EqoC/XX02j33pfY'
    b'lyNPhLcBykvvrMuWVJhls7VSFzHEiLGQ33ByGQ9eKoQ4ka8x9aYAq/Lng7Tifqo1PAwUTvhBmxXM7YDBraEPEUt3ZLeWiO9hdBX+'
    b'DutLTHiBQDNeLQ8JUnaqTU5O5wQlna+JTs75l91r51GOWuRA5bP4eclxXihOZsznUVPhky/9HdsR1bIqxfgkouc5bq3FVZmXBO+D'
    b'u1HyyPVb7HeRpf+eUDmxAIUvfnVXJRnVVY9PQk9aLsI9tU0F+J8NXWqZjTf+E7y+BFdkUNnJaEVO9P1rEP4MLr60shuYRJwC5pQg'
    b'ubfECxbm2n8ewRwR2cQDXmp4MWQAIzjN2Tp1XEaWXVIoM7qVoaO8aLsunPHjgM5PY02VhNH0mBxfXKfOUsrJIL3ocwCc9m4lrmye'
    b'87Y9VLsu/uU9O1K4xnV0pRrnHEnOR3qWB+0mRd2Yj9Pyb+eeO8XuKCHEQyyxFlK5EG6Np4PJG0QST4i71XXgqSz6UTWvTlf+HI27'
    b'17n2+Qxd2K8wbXYc9ZY5mJMqDA9Z2u5JrrOHQRA8b7XhezVXBhGNry2QFX3FVGWRYoLMtt6hbTUGVx9WPFBZFwCsz+z/jglVkzqD'
    b'Izd01tJ+vniJ3Dxi9FkLxozspfLIsH2IISFzetC+M9h8F7fB2jmsFPEYN1lvxjT0Gli2AjmTRAA7E6JYym5OuTgjGXwqnQ9BWfk1'
    b'EoiMm1rV0mGoThVedRSV+lcZWPboWES0zvnWGkTkQ2cStM9PYLX/JCbqpqtYWOHrX/L8+oaEmTguv9Y/5dcq4EiUJW1tKsQdhlnn'
    b'mVqEmRU3SGm509ZwKbi4Q8nwl7CK2IIEicx6PmEMGDQatk9ckmgkIrbEUgf6hKbHGvn88SGbWJGoupRiYZpHIGln1tRDF1R+1mkx'
    b'ULaheHSKue77VmHhiTUhYmkauW/0bSK1ubAIdtdOaKBKjjrwUIZ6DLckrfe0PpdrtdyW02bJ/unnTW695FTgHq1pLrzRkUCUWYyz'
    b'VzkePwSxggVOfz+tfz04HA2bVOk4HvNmWGtGDMwdNHlwpG2djtfvusFgH3HErBysuICn663/cpJrrz20gws/dEjRU2sXeNoOaKx6'
    b'EUEYXTyzuWj+UIlFoKEOajrKfkY80VAo9knFM0MFOD4vH2kSmsWAIkXFAQ1BLz/pO9XXU8At1YO3ePS4jb6O5AgyaLoA4Yz84vgy'
    b'5m/AY8LOYvc2MQ85ujlEEFKv0JgFoXzIiLlvDUze3roWlX0UHDIxIUddxHI3U6F9esMqpXK6q0UjTODn2i4YSLyAj4oTbhmDx9Q0'
    b'O6Wriqu4Hlis5Wm5K9Y1IlNJQb9lQtMR2X6Eq8jLxnyBmMJ6CPn4G8w3TzrssITOhYF87HGH21EniLLot6FxRnfAdCGLt73b25iv'
    b'YYUVOt5gzxfpNMXffelj+B95oZIALRKtXQjnW/yU5eOmo9ZBwyTDRLxwrhzipSmomJUzVCnXgjfbWVlm0JXSMP+xPy4KtiCzJrx6'
    b'BpVvqJZ8CzWOL8tzMs1BqQawvoVfKuMBfz4Kcatcf9XX+kuyvyH7iLU9ZYwwuH7yJu6OIKDX/nuQcYVcjo3p3IMII/bRR3J+21J7'
    b'ksDGBvdRq7CJVWGy/N1HNa8/kSUdU6c9pQXruI82AlOZxjKbIPVSt2k4yWGpWE1f9PABKSHatch+HnCH1iasfWSNYfp769rcgxj1'
    b'VTM1ZfeMUg3NoNk0O3pjSvqZ0jYe6ocKXSaBPZ51kLZeKx2Fci913AEjzepi0v7qR7vqyyHj3XzW/QX46zbRJDlX7m1ZOCQTIwDr'
    b'oeloHzfI5ntLkCRLEU3kG8YDhA620e1YwbjMHi4hH6ArWYMvfdX+4BC9dIlzZ9cMscx7zxe6Yeujx+iQ/jUE/9i/glO02arUla5u'
    b'vSuYUd+WPq0cJr97j8MXNY5/0pjNb3vpIk9El+C12xjT4mc+Q5CzOULeIYc0xEwP7VzJJzKuFWvNVVD7CFqxpYLlzHEPX7lhhhz+'
    b'LVPDigkdLX/cQDWzB50SRyM7E/SZmvC6CWeCwEy/WDrmw0ZinB1F/qbbtYV1s4dW5YTaGSRuWEpKtj5mn4iNH7P2tBI91c6KRUo6'
    b'TIIBsRNmn5sjfr+mRMKTIxdKy8shpR4CgcyzYbdNzpoOk2C9Fh0631NXjzH2UNtXDPg2FMdQDqelkIicuutg+4x7rvnr4ygLZnkA'
    b'44OBAXguM8L7g9RdTe4kQ49hefY6TQNEc72hO6S+UyD929QN1EL5KJ8FucqlhH50GKJLp0D9jngM8cn7suRr7nm+cBaFYjZsFQOS'
    b'h42vdKybq+dgE2DRKKnb3elndXksSrGrQwts6+8cIK0CqGwDf3fhSOuXn4oAmOESZFbaYz/hEKClwyQgekImDgSy/8i6nUnLyIKI'
    b'sN1xkHTTpQbW3fo8tEVUl9Y9LowoV2sTKiFqtspxhFkY8cVO+8XiTIeQf4+BVjYeOz6c9xaD3AP5KaLqvuuu1RKUD1yNdNQUPpLR'
    b'sN0e/BZ2HKWIlnR5BhNsNB3PJVLVoTguKCfdPpq9UeXXarIYU3AbWxGbiMBvDWgjc1CSbfXGb8xXoQVv5+k23qnO6ghW7U9jKLoD'
    b'4lv1z3+YaqbNsTmCgJNgIvVnxz/gWpdgqCut+ajQE7DrbIl8m5UNpSZPVEi68iwDKnywDityYh/+Z2SFo/n4aPH3pIy2Gydq6wit'
    b'fFi4AYSBCVeIEgVJ8KWDnE5DbOaHBQFx+xAvZs2OESnqFhVQw3bHZ2uwilwMBFsar8+8qkSKHccs63YddhgFlfVmMxtsEQgNpsOx'
    b'ip+Uyto/WSKcMwu+kUt6IC3Pw8ra+rQKF1W2I+JiQkPl6O+HCD/Tr/L7scdENEfAjcOPjBGiLRR96D1HNKr4TXNkyBTvrpXbWw11'
    b'wXbjNMmExBQxFODvlN7bL5aTxfPV9HM3hk4T5cKsEQjmAGIyVnidWtF9SB+HNHzXRJhsXVnup9e02bCb72gPO3h+D/lrsU/d2/tI'
    b'Z1G77jlFW+HkyzTj2Li6F4EI6iYMkW5SuhPQqAe1oWGB1IfJga8erpKGhn1dWiOY6VfWyyCq0G+2TCsBuhaSDOBOegFMunayGPfZ'
    b'FL1uAAhPKYxbokFredIBzovN8DtHQk2Q3zV4ceAkrP3I8gLeWYVJk73nVHYkuTOQcV2cb/QcXxnIwRFHpxhvji/F8HP2EYoLybmM'
    b'+Vd3OaUFyHcIlUE8UgwiDa+zobFIkmPIsai6G7HfO69arY14Jf3NzshgdZ8k1JX1uVJM812eMOTLyiBt8CRv3g4H7RTtsYzJ/2/s'
    b'jWtvy5wzcFfBlOZ/Ye7qxNvA4kXKu7CzgKLHhOK5dINJkgp+eaHvkgbMhw+zff04F6dhYtmcd4Zikn3OzFO+IVYjYA+69MLcGwM3'
    b'snsYOlKxMSSkvJXLCMnU9nctSXy7RHIhDI4clp5vPlRzcdWNXRpH/L2A7BieU35ekzbENTVfO3sEwZsLOsG+h0TVVdWLuFBh3l/Q'
    b'+lIQQ1n1Iz2rZYCfbqa/pWN0AEMJAxtwyJa+M5iJENywrNn3xBhF61IoJse6G9gJpuCGajS+P0bvuHc4dbVdM2ivGAb61V6tnmLV'
    b'iweK24OMg3Oud2RBL4tIVXitkhjXM6FgDfJpCbCtLmassKXmJOuAIyFdpQLmconLf5goQ3Tqyylx4hsWdovkbfF4rQCbk416Nzy9'
    b'VlDtXaVgckoiwD393+V4vLoMHs+0llOOSMRmDTbMsG1drYtCbZnOrjHm7pgLIbd1d2dzRmZrLIncs9V4Hj0vD9H7SVD9Centhply'
    b'iKJmVf6YIlXY3fZ5IfKZPjgMz0bH28KNJI8WLpdm6fX/VWT7pXVr5FiOQS8nEMqm5YyheVX1FviTIcGVfizJmtstXtOpZKBdbmLm'
    b'6RyjyCIPkpZR4t3VfLpdkuD0bh3kfkJSvB2l/MwTDW6X9UTyfmL7+rqqUca+sBQtW9actLhkw+PPkrVglMwbMMyXMZhgYmVYHaFc'
    b'nt5FJA53haJemhSpF6gMTa9qIMNqmSXQIWeiaseAACD4qvlwe5uU00Uy+avpvUJj/3g63EN5l+mxNMVpcAPoX/Y5rHK8qG9P/4qj'
    b'4883R9vLay3wRUSRpHUowRQsSCHeJvQnI9v0/7GDScDIkVXpyN56fIrWSNZ7oUt4Y5r1aZsK5B113XQsAGnoCBnF/CZCOk295yOk'
    b'RWjMQfLc/bH+a4il64X+wKrOUEyw9bEpG5LQ58JHT1JUF+D7sbol+OitPmOAw9U1m9xexgzAMrblDEUPNMPhHq4USXk4R5EtoxbE'
    b'GfFTyw5qgLWoGhvNRjq/m8s6KxUBwNlj21M3e4vBwQHg9kP0ZHLz6ILLsPvFRhTvyBhjBpTYpe6cc7XuUoWqjx9cY1utcBS3Ii9T'
    b'bdA4frKfCUJ+uk6VOxFLJ2ZmnKv5mUlYvARMgFL5eu73bdodoufaymw6sFnye75Kx2FYvzmI7K0jH7tXhqfUOrRw5/EJtmiuxbCl'
    b'SdiDctStiHMVcBD9LZiu9Q0V6y9WDfWCySfxm7UCUdC4U87AgLrNObv28e5gN2+x4YZ1C899EMxtSPu2exseq/GwsXDptDfDVf7r'
    b'nfBvsH/5WgLjGstf+Pi/luLeYcqc3CdGpQ2GtrXjKL/S5Agi444l3QBlYSpH08S2laks7VbpIU3ZNWVBk9eNz+k8S7sqmYqVpofU'
    b'Xol31Do94bzbLjeaLRKLoDYl/k1Z2b2kZcdLu3rzMSCt/7YuLqQvVIDd8rVk9/fJ1HxAmWnJxPWF5MoAQUPEgM8kx7Aem23p6k45'
    b'xg7p8UKxt+D1uxMvy4qwqFbaDkNai84XXRDUZiHHI0n38Vsos791DcVhO4JriwmOd1ZNYBpxY18R0cg5wZ8NH1Lb/qQnF92idroQ'
    b'7XoM9npA6ihutWmx/eHPcPAlF5EdLqgzAYt42kmryHE05w+CjQuTnFWTTrAIdzUA1us1+BdGBSKJY3YOO8GeecM3bpxDEhYsU7+O'
    b'F8p1pPLuf0aNaM6BwrdZBgoV6QR4GhuJsZkGEH4J1sLpWwYXA4rul3JCPjUB3Ii7iwJM2RbsYTnaFUF00kSQRvhUYXZTH/vZ43pn'
    b'7hvmoA0c0H7q8NqN7sPrcj3ldH1Px5Vs5JU/K0maX4/qsfp6VVBdRnEFFiwm8QQvKdD0HHRR5e0ksV/geys7jOsRLfxDLAjRcA2t'
    b'G9T203HXn6exmrhp2rHjFfhe+oDuiLeEDJ95eGG7L8WVIL9CH5lkFFb+KBT80SQ+py2X2jwXx3qElGvF/ATGOYWYHw7lRm87u7QO'
    b'jqls0ALWOlLfe2GwFJnpN2r46qXSBK8YCkCRi+ZSPo8NSqEa+ej34f/fJlDYN+WWSWgrEfzTwrltnu97euOgFSc5ZK1Fsg+8wFQ1'
    b'78Mqyy06MqgRPiwzbHC7DPCrMJU0jBe1wWHKzSLtppBk5s2Lqo7QeG9VTqR5p6A0KeLqtBPDgPq/PvdSaNu7rU9HLQML1r2XDiPu'
    b'IKGkiRjfNkexQXQMRoxIxghpqUKEVRm/2r9cQJRKaPkkl4jmuqSkCKoMTooIrN+fw7RN2FaCGTq1pZfI6d5U7VFw0gOmoWeawqyd'
    b'dXPBEqeDKmuZpL2aceFGAq/2oYp4Oe9ksEq21cicOyNJoL7dG9t6lxixmcLfwUH3UGluEw0xUD/aPEfsb/LSXCFfqFAZygAutBBH'
    b'8hoDFOXMDiLNsxERbYzWP3Fly5611bA7B2ajJu4MAf+lu7kiFYEvXDCf4UKG87SzU4yLKfdKxpIlmng+hmjkKaisJ3zBr+PdZ1vw'
    b'gEdx5nYvyBcckxV/hr9MBrM/+f7JXzOxr9ti69pqrvMHcYgIkKJkFoTUa1ta9jyL9kIeES6zyHzdZLhvZChZS8slawoiRsh9mN7e'
    b'ap+7K5jNaeLTXmgTYaeUAQPjxxs8QtEve2H/sN8F6jrxnfLi2hfkjKKi/UodaQAdTCLZN10mXXe+9Vqu9+tlVRNpy8Yjg3nTRaR6'
    b't4bq/9D8HqVGhNTzgJCadpTY+fvSJAT0F/UFeO8EzhceUY+b0yLbmXkJavkU6G4ztdgrwpeT1YqS+uRAYS2cnaA8TrC14rw4Vssn'
    b'+LA+wf1hsWSKF26PWU2lr47zKQTKXYXWLCfAFXDGapb7Y96YQH1bHt4u0LJeY6omJDKAHHyZp6j5NqivOcY5J+7pXf2U07dYHiNA'
    b'yZUPNswdWPDJfqLc/k+wl9yPLkASJcJgB/9tsagfBKVQMhrb5Yb102nIh+t8oZ49QNiI2RoHiWwN/LBbLdPR4v1FrUcNgVfhHGNz'
    b'mu56q7GigGaF+SqCrBl52Zrh4Ln/gcXjDcjYPVMyQCmYSwswI7JPqpCK/84sMZwCjq74AYqyNyIZ8jwENcuRdTswgKXvuNs5tf3q'
    b'DaEnG1oybx/JUHKkMH0LLA8gnfhbPNtamq6JFXBolfyq4nv92Bp0y8mhD6V+ZnEvx0qyS1aCvAf10S1a0fxdvy/OzUt2SyOXPhxJ'
    b'L58hDdbrbBGsMZaloOPQxMgOOPWKlIf9cpz6A02g8HmLUn1hhPvVsgIyXawvK5CghCG5BkaGbP5k4viKAZP41mxV1vXe/Ig/bRPk'
    b'AH/BmgfEPgeDl5LfgBOotlYf/QLvqbJNfWPMXhdWsnFEhY6BwjIZT82dAnwcyOFA/UXpkcWC1Mxup3vg19dyjqPOHOvjL19Gki5s'
    b'BjiLYoEOAantCVwVkX7UYPqR3/s8vm/JDfw27saA/J1wL4cm6MUeNgloPz4+0gHmAhGt8U9CI41epqv6lg8EZgwpv+sIK3DOAu2Y'
    b'6/JctxaRSujzWpZTRF+va2z2SgxE134mC504Aao8VdcXIoVaMQYXUD5KF2Sj48J242bU9KwUU22VXbVlbgKs5g7A3J/QpCOcuqlF'
    b'rD/1tOF73et7C3O7SEd1dujqngIevQwTnssD+HF8eI7eDXgo7QL3bHBSYTX/ZCyAubNTK8Xt+7QuUm3SmLUIomDaY5f4VpofuDF4'
    b'nrEe4Aupio9gl1/rGlVb5kgizvWbOCYwrUQ25ryvgttBkjm0pCnJ1DQLG8/fxpJbUJzOB0f/ympw53Gy4ukD343/S/aXGQUcvt8I'
    b'7R0AeKdEBEVHt2S5vQHTfyw5LTyw7je+i34SvYk7zXNlBcgW6i5ogRUCMaaKrlVTj0eUa8d/3HUHDOae2spbu3tPCDu8XKI2VGIE'
    b'EbzRZ8dO33I15E5pHwBq0nqjSasjKXbyQ4Fo6XXn57SqY9JAG945zo+byi5KM560OWL/Qci25L0BzueQFQGK/z3QlbK0Atwpi17H'
    b'wbdXEkhUct/ZPPbCMyijm8wJF+E6ZajQqlxBYE/+VINQSmXa/crcv6skFey5TKwlh7it8QHHqsR4RFHGXRJ6/v9XKvEhX+2BXnkl'
    b'+SGzypf1XSD5ZQP1XgQ2aDOxJfl92CKYacYcDGOzy1wC1WVGty3A1aJSSX3+NMz5LpzjPtaRvgSPShPaWC10jvvbtoxK0D2Ym3cl'
    b'3tCS9L0pb6JbkwQsf8p5TgRiWNagNhIRdjucyq3i6UUpWQMUm9h6xcqGZ2UTkX7Xsw3+gFShHvMttDwK98OPF2THlhbF+H/kr+3X'
    b'3NAwTTHRfzZn1pNjKqYZrhCbtgeEO5BMjnQOUTJ266R4te6qMaRuexiIAKWj5Bl1+AjLSOuxXojaAe4R/TZYtgQTrqdYt6TEUng0'
    b'djT9uhMOQOso1udQbvMvOuF0KV65AEe8OfbYFj1IKrhEkpW1MvR6Hy3tJfFinzHCcALkXoqDU4kX+9HsspUP9kGXkICiWk2FqtCW'
    b'QDDRakVnxa6W2zjffaAOR7S0bIu5yi8rqPnVumAP5LWMjPzrdmOzgUXyaNvydM1mgfCzTzOP+wZU7zyfW05Bp8F9g2P07pqTJN5/'
    b'yphpIRwP17BWQQo39ivzQ0kkM19gK4veHst32XCXBIXvY7w03z6Fa0Xq7oQl6bIgijue5iTDq8/VyBmHHqnX+bVhghOH8hpSrswk'
    b'LEUi8wAVoqw3J3O9bOUymxcPRtf34KEWnoCUeo73YeY1WpMlpjquch2lDQanXfzG6gX1WEMc81QG6n9DVSHXCgbg//mbJQtpuSFb'
    b'BlxRfO8oKBj90RU3Sv5TP5p/72MBb+oc59qO1ZvEIxeB832qMWIgoTD/pH7fS77EQAmNFEDbDl750FF6zIAVJUtDm8KF+OYLwpGF'
    b'RroL1vg6dbi66WRaN9j/3YVQMC8HyqeDpSpwq3S0anNgvwwoXC+E8FgrKAhxJBbXYO6PLvQZ/YhFpEdmooj1m2EDpzlaFvFDRuSj'
    b'lzICFjIwglEtHstvqFy827M52gLqCcTPA53vueEJcGuBhNqR8ySAVn0cGn6h7QQBC2bxbBEnpybigCjb3J8uLRAxzCNlVXKr+ky/'
    b'AVfRZr/JI5xkSCjC3JokmuWAZvOefxzOp5AK0KwWUzHSfFfn6W6FBg4K7g5xoaNeonAD7AgsXqInyHd7doSdcXQv5KLHWVPwqIQ3'
    b'oYTlgUQOvo513jh4bnNz+IaI0edMYYP74X/YBopWTGmWSreOttupRFxtOONBJqk8qShtE5epFnktNeJNUociw3KFHOVJUbj8xmU7'
    b'K7rE92P/zVTAIIY6xWJtCnS10HDKyqdcO9FCn+bMveWyEIHxJ62T1/LoFo4Jh3Bte7x+I4wy51WnD5nka8IQ+2b4GSm18dPUiktE'
    b'5ZFBgCtsUMYcwZc9LKkXFmjn3AjAeJ6Vhda1s0wzRU3ZKAYlEny8vqwldkLUQ+xJrJFUpCgJgKsJnsiigu5nOVBuwlCz/mWK8+dP'
    b'puuGscv529n1kBQyqAbdepEIAqw7PuVVBZqg0aDsstcBB5jslK4y2Trs0g4mc3/dd0VhqLxH+h5rbx17COVEai6ePcToQDI0IBmK'
    b'smmlL+tv5DyoXtJn/FtccIQYFxejGXES6VYd9jGRnpnwsCrDJs56qtaUAnm0Kr1NMAw/X9uw+it/M2wlJpTbPpOMLygr+gPmnFjh'
    b'lLRj0h5PSgnmEdaasd1TdY+0+CYS0pZIXXHqkxr9lDTr0sNMUVgc1lldwpcT3L1mY9zXxwxbxzX7F1uXa2guR6rjF7g9v9v//CyH'
    b'M0s8l8Lia22ZxNi1RSP4XfJc6UjKOZXEwfhZdi0Y9tF9u25BQyHin9UivBPqKq2C01puUwo8v9u3FXYWcFBpzWOV9MdBViCZGO1G'
    b'tM9avuAOwJMFEwgQJbebP1cZ7nSzcmRx7ar2C1rxCR99TWideVRjF1BGVqCqTwEJTwIyMxQEsu8SAes0F6vMLA0zyddOoXDNjz7x'
    b'qj086//W1M2hxz7wVgtjmWq+xqSOi1ZchCzAgAI/gOYVS3gFaGllJ4CkKogvRbN+WulzabJZG1DiUpwY/3sq0MykisB7IdgkbElb'
    b'OyasR27CpPQo5eg3fumbnnddJT5vjBbwaeDH1jekpoWlCkhQ9krahtWsHCfiEbKW5Qnvhs81q2alDzif/pfpB2FuK6/sRUcKxGwV'
    b'aKss8n4P0tE+wSm836JJHIW2zHrWE8gCmNFXz0urbXNDPy0Jw6qRR5dkwCe2+oF5Y2E7nOoPSgfqCSquvU8HmgBv4Ew4DtaG6agj'
    b'Mw62EqhJwaVOEZ6t9w2A+8Q3C/VEB/dLz+dcOyMApRVPsqad9iPYKhCM/WWU0NRxJGW65XF+ZHng95C9DgacayWa9nAMiFsV3ufE'
    b'XxI1Wq60pXSvtBVMG8GwYsL0yEOibKnYn5bxREwBMhfDNAsyPp8SU1UJ2vpWDjjVgos/F1ZCTT8IyfbXxeCvOSGvoMM6sU0EFN3C'
    b'qPMJrbfYLBaF9Vsx79MXzk+UJJaWg7hleatKXwLc7zSeDZOH4zCOBXhTf1pTYl0sQ12Dcs7MBi658cTAZE2VUWENGCvs9zNct2K1'
    b'wi/mFN7r5gO0T1XPsEaU3K3EaCm23DX24ssF+JhBRlun/MQo8MEKBJurnzsHmSiXYR7uP9rutGWBM1OfA46A8TkgQ9odRSPMqkNz'
    b'/aK65779d2+Bn5wZ1fDDKBtEcJYHk4P6BmaR6CJj63O3glJVe+AyUeSXu9w9ifowPXKzdqigI57O48SwgNss4OPArwS9FRS0byng'
    b'k7LFp/vpBNvEwg+eD7z9xC6/p1IeQ0kh8r+WbKb+g6jVUbuWqHc69y4aZCLVmBkG+17OwbB1K0a8PJQ33QM72VggdI3RHOTLzEhi'
    b'DPqcsYaUHO0+hEK5vk3Gsd+qR/HDEewFxFl5RU/iPXeH3ZMJ203W8PKL8EfzFf1l45ZB6y+Bw3U7eLv4O7kHQnYZhFu8KDr5hcGq'
    b'8fXeN1lk6hH4m+/9EYhtI8TZ5DfBZZJGfq6wP+QQ6oemjHebI/Q5jBGu7ge0PL3DFZk9oKxy2WfM6ThgGT6iAmByMlgPgqqAwVcy'
    b'frPqwyr5g14/GJmX4+MrbnzFTL+9MgtFzRFNNRfmVrs8735JA+fxmUaqYKOoykDdC4cOh7wT/vgNKiGzQnlME8Dp32IKm83Tl6ws'
    b'rOOqqpl9aSeZhfwnxwI9yIpxhIatT+ykGtTF+E0MHc8pxuhIYvCNWp37fEYlwpucJlWelAPz+gugZ393PD39eSguOwfKrLn/bMnL'
    b'3FP0a7KBSwDCC0AQzHKP1J3uNtFDeItPWZjmtEi5+MPL8BrqMv1zurBiTvcvNST9gTZsy+Bj2i8CoDuU6dPW0dGZwDOZuVTWIzHQ'
    b'ihrRtbMOJbF6VPztb7LobVhMDV33gTToVa4emB5+kc2F1LxudNH7Vo4UJnFFO55Xz2D+8SZxm2YOUrrmomAu9t25UUixnHdtMgHg'
    b'KnzC2hreAvL8gjDq1ROoq62FyvzFJYOF2SavVtG86A6XSN1X2L4CqWr5m1OMnPhk5dvRLUg6SuDQahhnckeTtixcNsTqE5FPjHGh'
    b'QSNDoyceMbUveQE7B9h+Z8K7tYxUpD+1FV8xfF0MuFxCODGlel3oKZPA9jGpFVh3muctGdJk3CdMmJrvKSgD5wlGgvM7w26pcjqN'
    b'e5Nw/xJMSEJ5h93pek0b9vHlX2+w/vsDjl5kwl51cUjZ1QNY3kT1TK0gRfG1buO7KSXSS9YKRxFsgw8sSDrJABw51dZIMYfVgS/b'
    b'MkwQn+rWeuMzrrn+RCHI9jIZ7UhJWD80K1we4+9QNf4/KGUGn/GnoWdCWz+V2OyBqvVrWKMRsWpIGGwoEwuvDawPC5olP/h1rqnq'
    b'yQFil3ZroiAl5bEkiTuEyuiisaxaIkbcqmJ21CVtAd9558bgV2wKOMCP/upoica0YnJHjSXOnQsYM9BuRMYH4X7AhfUmBSWPA5UE'
    b'6y6dtfR0jpEzE8JJVso1G6Ibk8zLgThUQKO70kTXfrWPZ9kOzgt+GbySpt933meQye2HNWU/TfZfoWvWZ6NART5dl449z7KhpIXe'
    b'5Xgwa7gXQ590sOt4mZinrYlRLsr6sGEEck5Hh0t8VPSDE9oOD+ud+xw0OckCB+yBvOXu5z6inh4+C95pm9e2/P1JkKccQtWd94CL'
    b'vzyhThdhDnQX0b204b3Z1Lmr8xmjTKPhDTBxbXhgq+qDaaaxKMwkfbplX0KHgHq8G4Hgm5fUwyij9Tvm2gnCrWOCg9YLQxYnwLTd'
    b'BjowiRjpXkzcAwDmBZd9Er0ZFv07+9TK5fx6nnk8bvpD29SfhlxZGu3XojkH6R5tR5cXAwRsWKwlTyQ2pM464PL9rGJGgEJHf1UR'
    b'pqmD4t02+5W2rCD9vJW/p/5he2FuGlbuXwQg2PhDGxI9WfpCKvlVcj8G0hw02jeCnImLjcmwImUN3lbLG8wQ3E+jbfiOj2XkheZk'
    b'38Oo6p0TGLYElX4r4od5IjsC/ZkaTFet3YzYW6oFeHiCk9v6z8Sl0WcRNRUBBUD5T9dJ03cVHaaBhwD79Dbt3j7SInAMTrlv8gq8'
    b'fjDvjvsPRZx6B520uRsqiZalHqKg9rO86Dxv3TFgY/zjLKtGJRrqCOYJ6Myf48UZcJBqZ1b58F1dJ4wQgwP5huC9BkiA+GLFSEQ/'
    b'B7SX9lb+94fJjcLWIYMbmA17jGyWDoKmad+FbO34KZDA8yJj72YpzHdOJB95sfoeYrAo4qyTAjnp4h6s2c8E5zTDtaLONKaVOdDW'
    b'j7BJjPMZnRGue6ZAIsdhiCNhD/16xrUDYSWTl29oxDnahLm3FZERttnbOMYSZ+lSAd6fPd6VfEAQd8vovHnCMBcCBKeHvxFtxfSq'
    b'oCeJCBxaKVh8c2IC9nmcs6ozhnXnqchP/Y9E0JG17VIFAckT9MA5f0d0oaTiTJrwJQ0jeo8a2ydmaMyCuC2ttWwZUIGadian5uHb'
    b'oEjFAUgZ0X8sMZ7fHuY9Vx1ApLBcjtyL3ah3NEev0s9px7FXu2Zn1ajRYm+NxU+8uao+zF4G679OTWUUXOcl5lWmolWswC/ESesj'
    b'PCt2sfO91gauoBAsTPsBfGKgZONtk2Omdi/cQqeW6yiQ4UXEPFiMtxq2gCm+h4hbTRg/RSNBo1Cx5+G+FD5CriI7k6lhw8wPiBmr'
    b'+emWK4/YhIbaJDC3V+CbgWyKAvjcaVv1O+opHKPMDo90M5WQQy1EwF5NFKgpy0AYMBXCPmz4WLziRRXLMZB1ivm3E8VEQIrNQ+KT'
    b'N1OzSLW5cROwHr/dsqjkGEZ+34B/mdBzYnurTpDxT8HaCPrMoOka7tWR2uTIvUVf1mn/yuhOKbQzIuwro77GT7xk7DWPlCHRFJiJ'
    b'B6trEdP419xqhsDK6SyPZJ9yoc8JRb0mRI1nATwSnLUqWOwfPg2GHbZh31hz0JQru0yfLmRP5FGZvSjv60Nxf0nH0bjS1PO7YGDr'
    b'VdZme0wOl8bL2wYf5QAHMSWnebDnX1TfIGF23qwEl+lKS04ewEEz0aS0JvWkdqyb5OLlQZjvkBvPGTyfDToixkta0niurUECIjKI'
    b'eB8qitYcXJZw3JgFoFSowUJGMkJA'
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
