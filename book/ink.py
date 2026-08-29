# -*- coding: utf-8 -*-
"""Bir satirin gercekte kapladigi yer.

PyMuPDF'in verdigi kutu fontun satir kutusudur: Inter'de puntonun 1,44
kati. Gorunen harf bundan cok daha kucuktur ve satirda hangi harfler
oldugua gore degisir — 2026 rakamlarinin altinda kuyruk yoktur, "who
burn" satirinin altinda vardir. Kutuyla olculunce duzgun sayfa hatali,
hatali sayfa duzgun cikar; bu yuzden olcu yazi cizgisinden ve satirdaki
harflerden kurulur.
"""
DESC = set('gjpqy,;()[]{}/\\|_QÇçŞşĞğµ¸')
HIGH = set('ÇĞİÖÜŞÂÎÛÄËÏÖÜÁÉÍÓÚÀÈÌÒÙÑÃÕÅ')
TALL = set('bdfhklt0123456789ABCDEFGHIJKLMNOPRSTUVWXYZ'
           'ÇĞİÖÜŞ()[]{}/\\|@&$£€#*†‡%')


def band(text, size):
    """(yazi cizgisinin ustunde, altinda) kalan punto."""
    up = 0.56
    if any(c in TALL or c.isupper() or c.isdigit() for c in text): up = 0.78
    if any(c in HIGH for c in text): up = 0.86
    dn = 0.27 if any(c in DESC for c in text) else 0.05
    return up * size, dn * size
