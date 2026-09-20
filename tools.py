#!/usr/bin/env python3
"""Zouti pou bati APK Meda a.
  python3 tools.py web      -> kreye www/index.html (index.html + pon Android)
  python3 tools.py android  -> mete MainActivity, ikòn ak splash nan android/
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BG = (0, 40, 150)
VERSION_NAME = '1.0'
VERSION_CODE = 1

BRIDGE = r"""
<script>
/* --- Android bridge (enjekte pa build APK a) --- */
(function(){
  var origPrint = window.print ? window.print.bind(window) : null;
  window.print = function(){
    if (window.AndroidBridge && window.AndroidBridge.print) { window.AndroidBridge.print(); }
    else if (origPrint) { origPrint(); }
  };
  var origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function(){
    var a = this;
    if (window.AndroidBridge && window.AndroidBridge.saveFile && a.download && a.href && a.href.indexOf('blob:') === 0) {
      fetch(a.href).then(function(r){ return r.blob(); }).then(function(b){
        var fr = new FileReader();
        fr.onloadend = function(){
          var data = String(fr.result).split(',')[1] || '';
          window.AndroidBridge.saveFile(a.download, data, b.type || 'application/octet-stream');
        };
        fr.readAsDataURL(b);
      });
      return;
    }
    return origClick.apply(this, arguments);
  };
})();

/* --- Watchdog: pa janm kite ekran blan --- */
(function(){
  var lastErr = '';
  window.__bridgeNotice = function(msg){
    try {
      var box = document.getElementById('__bridge_notice');
      if (!box) {
        box = document.createElement('div');
