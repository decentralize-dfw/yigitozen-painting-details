# -*- coding: utf-8 -*-
"""Tasarimin kendi bosluklari: hangi iki rol arasinda en az ne kadar var.

Sabit uydurmak yerine kitabin dogru dizilmis sayfalarindan olculur; boylece
acilacak her boslugun olcusu kitabin kendi olcusudur.
"""
import collections


def xover(a, b):
    o = min(a[2], b[2]) - max(a[0], b[0])
    return o > 0.25 * min(a[2] - a[0], b[2] - b[0])


def build(pages):
    g = collections.defaultdict(list)
    for q, P in pages.items():
        it = P['items']
        for i in range(len(it)):
            for j in range(i + 1, len(it)):
                a, b = it[i], it[j]
                if not xover(a['ren'], b['ren']): continue
                d = b['ren'][1] - a['ren'][3]
                if d < -0.5: break        # cakisma: olcu alinmaz
                g[(a['role'], b['role'])].append(d)
                break
    out = {}
    for k, v in g.items():
        v.sort()
        out[k] = v[0]
    return out
