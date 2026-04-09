from __future__ import annotations

import json
import os
from pathlib import Path
import re
from datetime import datetime
from typing import Any
from urllib import request as urllib_request

from flask import Flask, request, render_template_string, send_file, jsonify
import io

from .formatter import FormatOptions, WechatFormatter
from .kimi import (
    DEFAULT_KIMI_BASE_URL,
    DEFAULT_KIMI_MODEL,
    polish_markdown_with_kimi,
    chat_with_kimi,
)


PAGE_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <title>微信文章排版控制台 v2.3</title>
  <style>
    :root {
      --bg: radial-gradient(circle at 20% 10%, #fff4dc 0%, #f8f3e8 35%, #e9f1ee 100%);
      --panel: #fffdf8;
      --ink: #222018;
      --muted: #6b665a;
      --line: #d8d1c2;
      --brand: #c2410c;
      --brand-2: #0f766e;
      --ok: #17633e;
      --danger: #9f1239;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    }
    .wrap {
      max-width: 1100px;
      margin: 28px auto;
      padding: 0 16px;
    }
    .hero {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px 20px;
      background: linear-gradient(110deg, #fff7ed 0%, #ecfeff 100%);
      box-shadow: 0 10px 26px rgba(17, 24, 39, 0.08);
      margin-bottom: 16px;
    }
    .hero-left {
      min-width: 0;
    }
    .hero-actions {
      flex-shrink: 0;
      display: flex;
      align-items: stretch;
      justify-content: flex-end;
      flex-direction: column;
      gap: 8px;
      min-width: 280px;
    }
    .hotspot-btn {
      min-width: 260px;
      padding: 12px 16px;
      font-weight: bold;
      background: linear-gradient(90deg, #0f766e 0%, #0ea5e9 100%);
      box-shadow: 0 8px 20px rgba(14, 116, 144, 0.3);
    }
    .kw-wrap { display: flex; gap: 8px; align-items: center; }
    .kw-input { flex: 1; min-width: 240px; }
    .kw-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .kw-chip {
      display: inline-flex;
      align-items: center;
      padding: 4px 8px;
      border-radius: 14px;
      background: #eef2ff;
      color: #374151;
      border: 1px solid var(--line);
      font-size: 12px;
    }
    .kw-chip button {
      margin-left: 6px;
      border: 0;
      background: transparent;
      cursor: pointer;
      color: #6b7280;
      font-size: 14px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      letter-spacing: 0.4px;
      color: #7c2d12;
    }
    .sub {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    form {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: 0 8px 20px rgba(2, 6, 23, 0.05);
    }
    .full { grid-column: 1 / -1; }
    label {
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin: 0 0 6px;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 14px;
      color: var(--ink);
      background: #fff;
      outline: none;
      font-family: inherit;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(194, 65, 12, 0.14);
    }
    .inline {
      display: flex;
      align-items: center;
      gap: 8px;
      padding-top: 20px;
    }
    .inline input[type='checkbox'] {
      width: auto;
      transform: translateY(1px);
    }
    .btns {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    }
    button {
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      font-size: 14px;
      cursor: pointer;
      color: #fff;
      background: linear-gradient(90deg, var(--brand) 0%, #ea580c 100%);
      box-shadow: 0 6px 16px rgba(194, 65, 12, 0.28);
    }
    button.secondary {
      background: linear-gradient(90deg, var(--brand-2) 0%, #14b8a6 100%);
      box-shadow: 0 6px 16px rgba(15, 118, 110, 0.28);
    }
    .status {
      margin: 14px 0 0;
      padding: 10px 12px;
      border-radius: 10px;
      font-size: 14px;
      border: 1px solid;
      white-space: pre-wrap;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .ok {
      color: var(--ok);
      border-color: #86efac;
      background: #f0fdf4;
    }
    .err {
      color: var(--danger);
      border-color: #fda4af;
      background: #fff1f2;
    }
    .status-text { flex: 1; }
    .status-btns { display: flex; gap: 8px; margin-left: 12px; }
    .btn-sm {
      padding: 10px 10px;
      font-size: 12px;
      border-radius: 6px;
      box-shadow: none;
    }
    /* Modal Styles */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      backdrop-filter: blur(4px);
    }
    .modal-content {
      background: #fff;
      padding: 24px;
      border-radius: 18px;
      max-width: 400px;
      width: 90%;
      text-align: center;
      box-shadow: 0 20px 50px rgba(0,0,0,0.2);
      animation: modalSlide 0.3s ease-out;
    }
    @keyframes modalSlide {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    .modal-title {
      font-size: 20px;
      font-weight: bold;
      margin-bottom: 12px;
      color: var(--ink);
    }
    .modal-msg {
      font-size: 15px;
      color: var(--muted);
      margin-bottom: 24px;
      line-height: 1.6;
    }
    .modal-footer {
      display: flex;
      gap: 12px;
      justify-content: center;
    }
    .modal-btn {
      border: 0;
      border-radius: 10px;
      padding: 10px 20px;
      font-size: 14px;
      cursor: pointer;
      font-weight: 500;
    }
    .modal-btn.primary {
      color: #fff;
      background: linear-gradient(90deg, var(--brand) 0%, #ea580c 100%);
    }
    .modal-btn.secondary {
      color: var(--ink);
      background: #f3f4f6;
      border: 1px solid var(--line);
    }
    .modal-btn.success {
      color: #fff;
      background: linear-gradient(90deg, var(--brand-2) 0%, #14b8a6 100%);
    }
    /* Loading Overlay */
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(255,255,255,0.8);
      display: none;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 2000;
      backdrop-filter: blur(2px);
    }
    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid var(--line);
      border-top: 4px solid var(--brand-2);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 16px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .loading-text {
      font-size: 16px;
      font-weight: bold;
      color: var(--brand-2);
    }
    .hint {
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      overflow: hidden;
    }
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      background: #f8fafc;
    }
    .preview-header h2 {
      margin: 0;
      font-size: 14px;
      color: #374151;
    }
    iframe {
      width: 100%;
      height: 540px;
      border: 0;
      display: block;
    }
    .hint {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    /* Batch File Styles */
    .file-list {
      padding: 0;
      margin: 0;
      list-style: none !important;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 10px;
    }
    .file-item {
      display: flex;
      align-items: center;
      padding: 12px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      background: #ffffff;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      cursor: pointer;
      position: relative;
      user-select: none;
    }
    .file-item:hover {
      border-color: var(--brand-2);
      background: #fdfdfd;
      transform: translateY(-1px);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .file-item.selected {
      background: #f0fdfa;
      border-color: var(--brand-2);
      box-shadow: inset 0 0 0 1px var(--brand-2);
    }
    .file-cb {
      width: 18px;
      height: 18px;
      margin: 0 12px 0 0 !important;
      cursor: pointer;
      accent-color: var(--brand-2);
      flex-shrink: 0;
    }
    .file-name {
      font-size: 14px;
      font-weight: 500;
      color: #374151;
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }
    .file-tag {
      font-size: 10px;
      padding: 2px 6px;
      background: #f1f5f9;
      color: #64748b;
      border-radius: 4px;
      margin-left: 8px;
      border: 1px solid #e2e8f0;
      flex-shrink: 0;
    }
    @media (max-width: 900px) {
      .hero {
        flex-direction: column;
        align-items: stretch;
      }
      .hero-actions {
        min-width: 0;
        justify-content: stretch;
      }
      .hotspot-btn {
        width: 100%;
        min-width: 0;
      }
      form { grid-template-columns: 1fr; }
      .btns { justify-content: flex-start; }
      iframe { height: 420px; }
    }
  </style>
  <script>
    function openPreview() {
      const content = document.getElementById('preview-data').value;
      const win = window.open('', '_blank');
      win.document.write(content);
      win.document.close();
    }

    function closeModal() {
      const modal = document.getElementById('success-modal');
      if (modal) modal.style.display = 'none';
    }

    function downloadFile() {
      const content = document.getElementById('preview-data').value;
      const title = document.getElementById('download-filename').value;
      const filename = (title || 'wechat_article') + '.html';
      
      const blob = new Blob([content], { type: 'text/html;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 100);
    }

    function showLoading(type = 'run', detail = '') {
      const isPolish = document.querySelector('input[name="polish"]')?.checked;
      const overlay = document.getElementById('loading-overlay');
      const text = document.getElementById('loading-text');
      
      if (type === 'hotspot') {
        text.innerText = "🔍 正在抓取 [" + (detail || '多源') + "] 并分析今日热点，请稍候...";
      } else if (isPolish) {
        text.innerText = "🚀 AI 正在润色并排版中，请稍候...";
      } else {
        text.innerText = "⚡ 正在排版中...";
      }
      
      overlay.style.display = 'flex';
      return true;
    }

    function openHotspotsReport() {
      const sourceSelect = document.getElementById('hotspot-source');
      const source = sourceSelect.value;
      const sourceText = sourceSelect.options[sourceSelect.selectedIndex].text;
      const kwParams = (window.hotspotKeywords && window.hotspotKeywords.length)
        ? ('&keywords=' + encodeURIComponent(window.hotspotKeywords.join(',')))
        : '';
      
      // 安全起见，不再通过 URL 传递 API Key
      // 密钥将由后端直接从 session 或配置中读取
      
      // 显示加载提示
      showLoading('hotspot', sourceText);
      
      // 跳转到报告页
      const reportUrl = '/hotspots/report?source=' + source + kwParams;
      window.open(reportUrl, '_blank');
      
      // 3秒后自动隐藏当前页面的加载层
      setTimeout(() => {
        document.getElementById('loading-overlay').style.display = 'none';
      }, 3000);
    }

    // 提交任务后，自动将 URL 重置为根路径，防止手动刷新时弹出“确认表单重新提交”或停留在 /run
    if (window.location.pathname === '/run') {
      window.history.replaceState({}, '', '/');
    }

    window.hotspotKeywords = [];
    function renderKeywords() {
      const list = document.getElementById('hotspot-keywords-list');
      if (!list) return;
      list.innerHTML = '';
      window.hotspotKeywords.forEach((kw, idx) => {
        const chip = document.createElement('span');
        chip.className = 'kw-chip';
        const txt = document.createElement('span');
        txt.textContent = kw;
        const rm = document.createElement('button');
        rm.type = 'button';
        rm.textContent = '×';
        rm.onclick = function() {
          window.hotspotKeywords.splice(idx, 1);
          renderKeywords();
        };
        chip.appendChild(txt);
        chip.appendChild(rm);
        list.appendChild(chip);
      });
    }
    function addKeywordsFromInput() {
      const input = document.getElementById('hotspot-keywords');
      if (!input) return;
      const parts = String(input.value || '').split(/[\\s,，、;；]+/).map(s => s.trim()).filter(Boolean);
      parts.forEach(p => {
        if (!window.hotspotKeywords.includes(p)) window.hotspotKeywords.push(p);
      });
      input.value = '';
      renderKeywords();
    }
    function updateBatchSelection(cb) {
      const item = cb.closest('.file-item');
      if (cb.checked) {
        item.classList.add('selected');
      } else {
        item.classList.remove('selected');
      }
      
      // 更新全选状态
      const allCbs = document.querySelectorAll('.file-cb');
      const allChecked = Array.from(allCbs).every(c => c.checked);
      const selectAllCb = document.getElementById('batch-select-all');
      if (selectAllCb) selectAllCb.checked = allChecked && allCbs.length > 0;
    }

    function toggleBatchFile(el) {
      const cb = el.querySelector('.file-cb');
      cb.checked = !cb.checked;
      updateBatchSelection(cb);
    }

    function toggleAllBatchFiles(selectAllCb) {
      const isChecked = selectAllCb.checked;
      const allCbs = document.querySelectorAll('.file-cb');
      allCbs.forEach(cb => {
        cb.checked = isChecked;
        updateBatchSelection(cb);
      });
    }

    async function refreshBatchFiles() {
      const container = document.getElementById('batch-files-container');
      if (!container) return;
      container.innerHTML = '<div style="color:var(--muted); font-size:13px; padding:10px;">正在刷新文件列表...</div>';
      try {
        const resp = await fetch('/list_batch_files');
        const data = await resp.json();
        if (data.ok) {
          if (data.files.length === 0) {
            container.innerHTML = '<div style="color:var(--muted); font-size:13px; padding:10px;">batch_input 目录下暂无 Markdown 文件。</div>';
            return;
          }
          let html = '<ul class="file-list">';
          data.files.forEach(f => {
            const parts = f.split(/[\\\\/]/);
            const name = parts[parts.length - 1];
            const dir = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
            
            html += `
              <li class="file-item" onclick="toggleBatchFile(this)">
                <input type="checkbox" name="selected_files" value="${f}" class="file-cb" onclick="event.stopPropagation(); updateBatchSelection(this)">
                <div class="file-name" title="${f}">${name}</div>
                ${dir ? `<span class="file-tag">${dir}</span>` : ''}
              </li>
            `;
          });
          html += '</ul>';
          container.innerHTML = html;
        } else {
          container.innerHTML = `<div style="color:#dc2626; font-size:13px; padding:10px;">获取失败: ${data.message}</div>`;
        }
      } catch (e) {
        container.innerHTML = `<div style="color:#dc2626; font-size:13px; padding:10px;">网络错误: ${e}</div>`;
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      const input = document.getElementById('hotspot-keywords');
      if (input) {
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            addKeywordsFromInput();
          }
        });
      }
      
      // 如果当前是批量模式，初始化文件列表
      const modeSelect = document.querySelector('select[name="mode"]');
      if (modeSelect && modeSelect.value === 'batch') {
        refreshBatchFiles();
      }
    });
  </script>
</head>
<body>
  <div id="loading-overlay" class="loading-overlay">
    <div class="spinner"></div>
    <div id="loading-text" class="loading-text">正在处理中...</div>
  </div>

  {% if ok and message %}
  <div id="success-modal" class="modal-overlay">
    <div class="modal-content">
      <div class="modal-title">✨ 排版成功</div>
      <div class="modal-msg">{{ message }}</div>
      <div class="modal-footer">
        {% if values.mode == 'single' %}
        <button class="modal-btn success" type="button" onclick="openPreview()">预览文章</button>
        <button class="modal-btn primary" type="button" onclick="downloadFile()">下载文件</button>
        {% endif %}
        <button class="modal-btn secondary" type="button" onclick="closeModal()">关闭</button>
      </div>
    </div>
  </div>
  
  <input type="hidden" id="download-filename" value="{{ values.title or 'wechat_article' }}">
  {% endif %}

  <div class="wrap">
    <section class="hero">
      <div class="hero-left">
        <h1>微信公众号排版控制台</h1>
        <p class="sub">在页面里快速完成: 单文件排版 / 批量目录排版。</p>
      </div>
      <div class="hero-actions">
        <div class="kw-wrap">
          <select id="hotspot-source" class="btn-sm" style="flex: 0 0 110px; padding: 10px 8px; border-radius: 6px;">
            <option value="">自动切换</option>
            <option value="baidu">百度热搜</option>
            <option value="weibo">微博热搜</option>
            <option value="zhihu">知乎热榜</option>
            <option value="wechat">微信公众号</option>
            <option value="xhs">小红书热搜</option>
            <option value="toutiao">今日头条</option>
            <option value="douyin">抖音热搜</option>
          </select>
          <input id="hotspot-keywords" class="kw-input" placeholder="输入关键词，回车/逗号添加" />
          <button class="btn-sm" type="button" onclick="addKeywordsFromInput()">添加</button>
        </div>
        <div id="hotspot-keywords-list" class="kw-list"></div>
        <button class="hotspot-btn" type="button" onclick="openHotspotsReport()">抓取当前热点内容</button>
      </div>
    </section>

    <form method="post" action="/run" enctype="multipart/form-data" onsubmit="return showLoading()">
      <input type="hidden" name="config_path" value="{{ values.config_path }}" />
      <input type="hidden" name="input_path" value="{{ values.input_path }}" />
      <input type="hidden" name="output_path" value="{{ values.output_path }}" />
      <input type="hidden" name="in_dir" value="{{ values.in_dir }}" />
      <input type="hidden" name="out_dir" value="{{ values.out_dir }}" />

      <div class="full">
        <label>运行模式</label>
        <select name="mode" onchange="window.location.href='/?mode=' + this.value">
          <option value="single" {% if values.mode == 'single' %}selected{% endif %}>单文件 (上传 MD)</option>
          <option value="batch" {% if values.mode == 'batch' %}selected{% endif %}>批处理目录 (服务器本地)</option>
        </select>
      </div>

      {% if values.mode == 'batch' %}
      <div class="full" id="batch-file-selector" style="margin-bottom: 20px; padding: 18px; border: 1px solid #e2e8f0; border-radius: 14px; background: #f8fafc; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);">
        <div style="font-weight: bold; margin-bottom: 12px; color: var(--brand-2); display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <input type="checkbox" id="batch-select-all" onclick="toggleAllBatchFiles(this)" style="width: 16px; height: 16px; cursor: pointer; accent-color: var(--brand-2);">
            <label for="batch-select-all" style="cursor: pointer; font-size: 14px; margin: 0;">选取待处理文件 (batch_input)</label>
          </div>
          <button type="button" onclick="refreshBatchFiles()" class="btn-sm" style="background: white; border: 1px solid #cbd5e1; color: #64748b;">刷新</button>
        </div>
        <div id="batch-files-container" style="max-height: 260px; overflow-y: auto; padding-right: 4px;">
          正在加载文件列表...
        </div>
      </div>
      {% endif %}

      <div class="full">
        <label>模板样式选择</label>
        <select name="theme">
          <option value="default" {% if values.theme == 'default' %}selected{% endif %}>默认 (商务科技)</option>
          <option value="minimal" {% if values.theme == 'minimal' %}selected{% endif %}>极简 (文艺清新)</option>
          <option value="elegant" {% if values.theme == 'elegant' %}selected{% endif %}>优雅 (经典阅读)</option>
          <option value="dark" {% if values.theme == 'dark' %}selected{% endif %}>暗黑 (极客范)</option>
        </select>
      </div>

      {% if values.mode == 'single' %}
      <div class="full">
        <label>上传 Markdown 文件</label>
        <input type="file" name="file" accept=".md" />
      </div>
      {% endif %}

      {% if values.mode == 'single' %}
      <div>
        <label>标题</label>
        <input name="title" value="{{ values.title }}" placeholder="留空自动提取" />
      </div>
      <div>
        <label>作者（可选）</label>
        <input name="author" value="{{ values.author }}" placeholder="留空自动提取" />
      </div>

      <div class="full">
        <label>引言 / 摘要（可选，填写后将覆盖正文引言）</label>
        <textarea name="summary" rows="3" placeholder="留空自动提取">{{ values.summary }}</textarea>
      </div>

      <div class="full">
        <label>封面图 URL（可选）</label>
        <input name="cover_image_url" value="{{ values.cover_image_url }}" placeholder="留空自动提取首图" />
      </div>
      {% endif %}

      <div class="full" style="border-top: 1px dashed var(--line); margin: 10px 0; padding-top: 10px;">
        <div class="inline">
          <input type="checkbox" name="polish" value="1" {% if values.polish %}checked{% endif %} />
          <label style="margin:0; font-weight: bold; color: var(--brand-2);">启用 Kimi AI 润色 (大模型)</label>
        </div>
        <input type="hidden" name="kimi_api_key" value="{{ values.kimi_api_key }}" />
      </div>

      <div class="full btns">
        <button type="submit">执行</button>
        <button class="secondary" type="button" onclick="location.href='/'">重置</button>
      </div>

      <div class="full hint">提示：将自动处理默认目录下的 Markdown 文件。</div>
    </form>

    {% if message %}
      {% if not ok %}
      <div class="status err">
        <div class="status-text">{{ message }}</div>
      </div>
      {% endif %}
    {% endif %}

    {% if preview_html %}
      <textarea id="preview-data" style="display:none;">{{ preview_html }}</textarea>
    {% endif %}
  </div>
</body>
</html>
"""


HOTSPOT_REPORT_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>当日热点分析报告</title>
  <style>
    :root {
      --bg: radial-gradient(circle at 10% 10%, #fef3c7 0%, #ecfeff 40%, #eff6ff 100%);
      --panel: #ffffff;
      --line: #d1d5db;
      --ink: #1f2937;
      --muted: #6b7280;
      --brand: #0f766e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    }
    .wrap {
      max-width: 980px;
      margin: 24px auto;
      padding: 0 14px;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: 18px;
      background: var(--panel);
      box-shadow: 0 10px 26px rgba(17, 24, 39, 0.08);
      overflow: hidden;
      min-height: 400px;
      position: relative;
    }
    .head {
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(110deg, #f0fdfa 0%, #eff6ff 100%);
    }
    .title {
      margin: 0;
      font-size: 24px;
      color: #115e59;
    }
    .meta {
      margin: 8px 0 0;
      font-size: 13px;
      color: var(--muted);
    }
    .report-content {
      margin: 0;
      padding: 18px;
      line-height: 1.75;
      font-size: 15px;
    }
    .report-content a:hover {
      text-decoration: underline !important;
    }
    /* Suggestion Card Styles */
    .suggestion-list {
      padding: 0;
      margin: 0;
      list-style: none;
    }
    .suggestion-item {
      display: flex;
      align-items: flex-start;
      padding: 16px;
      margin-bottom: 12px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #f8fafc;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    .suggestion-item:hover {
      border-color: var(--brand);
      background: #f0fdfa;
      box-shadow: 0 4px 12px rgba(15, 118, 110, 0.08);
    }
    .suggestion-item.selected {
      border-color: var(--brand);
      background: #f0fdfa;
    }
    .err {
      color: #9f1239;
      background: #fff1f2;
      border-top: 1px solid #fecdd3;
      padding: 18px;
    }
    .suggestion-cb {
      width: 18px;
      height: 18px;
      margin-top: 3px;
      margin-right: 14px;
      cursor: pointer;
      accent-color: var(--brand);
    }
    .suggestion-text {
      flex: 1;
      font-size: 15px;
      color: var(--ink);
    }
    .suggestion-title {
      display: block;
      font-weight: 800;
      color: #115e59;
      margin-bottom: 6px;
      font-size: 17px;
      line-height: 1.4;
    }
    .suggestion-desc {
      color: var(--muted);
      line-height: 1.6;
    }
    .err {
      color: #9f1239;
      background: #fff1f2;
      border-top: 1px solid #fecdd3;
      padding: 18px;
    }
    /* Loading Styles */
    .loading-box {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      width: 100%;
      padding: 40px;
    }
    .spinner {
      width: 50px;
      height: 50px;
      border: 5px solid #e2e8f0;
      border-top: 5px solid var(--brand);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .loading-msg {
      font-size: 18px;
      font-weight: bold;
      color: var(--brand);
      letter-spacing: 1px;
    }
    .loading-sub {
      font-size: 14px;
      color: var(--muted);
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="panel">
      <header class="head">
        <h1 class="title">当日热点分析报告</h1>
        <p class="meta" id="meta-time">生成中...</p>
      </header>
      
      <div id="loading-state" class="loading-box">
        <div class="spinner"></div>
        <div class="loading-msg">正在抓取并分析实时热点...</div>
        <div class="loading-sub">AI 正在深度思考选题建议，请耐心等待约 10-20 秒</div>
      </div>

      <div id="report-body" class="report-content" style="display: none;"></div>
      <pre id="error-body" class="err" style="display: none;"></pre>
    </section>
  </div>

  <script>
    function toggleSuggestion(el) {
      const cb = el.querySelector('.suggestion-cb');
      cb.checked = !cb.checked;
      updateSelection(cb);
    }

    function updateSelection(cb) {
      const item = cb.closest('.suggestion-item');
      if (cb.checked) {
        item.classList.add('selected');
      } else {
        item.classList.remove('selected');
      }
      
      // 更新全选框状态
      const allCbs = document.querySelectorAll('.suggestion-cb');
      const allChecked = Array.from(allCbs).every(c => c.checked);
      const selectAllCb = document.getElementById('select-all-cb');
      if (selectAllCb) {
        selectAllCb.checked = allChecked;
      }
    }

    function toggleAllSuggestions(selectAllCb) {
      const isChecked = selectAllCb.checked;
      const allCbs = document.querySelectorAll('.suggestion-cb');
      allCbs.forEach(cb => {
        cb.checked = isChecked;
        updateSelection(cb);
      });
    }

    async function generateArticles() {
      const cbs = document.querySelectorAll('.suggestion-cb:checked');
      if (cbs.length === 0) {
        alert('请至少勾选一个选题！');
        return;
      }
      
      const topics = Array.from(cbs).map(cb => cb.value);
      const btn = document.getElementById('gen-btn');
      const status = document.getElementById('gen-status');
      
      btn.disabled = true;
      btn.style.opacity = '0.6';
      btn.style.cursor = 'not-allowed';
      status.style.display = 'block';
      status.textContent = '🚀 正在为您创作文章，请稍候（每篇约 10-20 秒）...';
      
      try {
        const response = await fetch('/generate_articles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topics })
        });
        
        const data = await response.json();
        if (data.ok) {
          status.innerHTML = `
            <div style="background: #ecfdf5; border: 1px solid #10b981; padding: 15px; border-radius: 10px; color: #065f46;">
              <div style="font-weight: bold; margin-bottom: 8px;">✅ 生成成功！文章已存放到：</div>
              <code style="background: #fff; padding: 2px 5px; border-radius: 4px; display: block; margin-bottom: 12px; word-break: break-all;">${data.path}</code>
              <div style="font-size: 13px;">
                💡 <strong>提示：</strong> 您现在可以 <a href="/" style="color: #059669; font-weight: bold; text-decoration: underline;">回到首页</a>，选择 <strong>“批量操作”</strong> 模式，直接勾选刚才生成的文章进行一键排版。
              </div>
            </div>
          `;
          status.style.color = '#059669';
        } else {
          status.textContent = '❌ 生成失败: ' + data.message;
          status.style.color = '#dc2626';
          btn.disabled = false;
          btn.style.opacity = '1';
          btn.style.cursor = 'pointer';
        }
      } catch (e) {
        status.textContent = '❌ 网络请求异常: ' + e;
        status.style.color = '#dc2626';
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
      }
    }

    async function fetchReport() {
      const params = new URLSearchParams(window.location.search);
      const source = params.get('source') || '';
      const keywords = params.get('keywords') || '';
      
      try {
        const response = await fetch('/hotspots', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source, keywords })
        });
        
        const data = await response.json();
        
        document.getElementById('loading-state').style.display = 'none';
        
        if (data.ok) {
          document.getElementById('meta-time').textContent = '生成时间: ' + data.generated_at;
          const body = document.getElementById('report-body');
          body.innerHTML = data.report;
          body.style.display = 'block';
        } else {
          const err = document.getElementById('error-body');
          err.textContent = data.message || '抓取热点失败，请检查网络或 API 配置。';
          err.style.display = 'block';
          document.getElementById('meta-time').textContent = '生成失败';
        }
      } catch (e) {
        document.getElementById('loading-state').style.display = 'none';
        const err = document.getElementById('error-body');
        err.textContent = '请求异常: ' + e;
        err.style.display = 'block';
        document.getElementById('meta-time').textContent = '生成异常';
      }
    }

    window.onload = fetchReport;
  </script>
</body>
</html>
"""


def _load_config(config_path: str) -> dict[str, str]:
  def _pick_fields(raw: dict[str, object]) -> dict[str, str]:
    return {
      "custom_css": str(raw.get("custom_css", "")),
      "author": str(raw.get("author", "")),
      "summary": str(raw.get("summary", "")),
      "cover_image_url": str(raw.get("cover_image_url", "")),
      "kimi_api_key": str(raw.get("kimi_api_key", "")),
      "kimi_model": str(raw.get("kimi_model", "")),
      "kimi_base_url": str(raw.get("kimi_base_url", "")),
    }

  merged: dict[str, str] = {}

  if config_path.strip():
    path = Path(config_path)
    if not path.exists():
      raise FileNotFoundError(f"配置文件不存在: {config_path}")
    merged.update(_pick_fields(json.loads(path.read_text(encoding="utf-8"))))

  # 自动加载本地私有配置，覆盖公共配置中的同名字段（便于保存私钥）。
  local_path = Path("pipeline.local.json")
  if local_path.exists():
    local_cfg = _pick_fields(json.loads(local_path.read_text(encoding="utf-8")))
    for key, value in local_cfg.items():
      if value.strip():
        merged[key] = value

  return merged


def _initial_values() -> dict[str, Any]:
    # 尝试从配置文件或环境变量加载初始 API Key
    try:
        config = _load_config("examples/pipeline.config.json")
        api_key = (
            os.getenv("KIMI_API_KEY", "")
            or config.get("kimi_api_key", "")
        )
    except:
        api_key = ""

    return {
        "mode": "single",
        "theme": "default",
        "config_path": "examples/pipeline.config.json",
        "input_path": "examples/article.md",
        "output_path": "output.html",
        "in_dir": "batch_input",
        "out_dir": "batch_output",
        "title": "",
        "title_template": "",
        "author": "",
        "author_template": "",
        "summary": "",
        "cover_image_url": "",
        "polish": False,
        "kimi_api_key": api_key,
        "kimi_model": DEFAULT_KIMI_MODEL,
        "kimi_base_url": DEFAULT_KIMI_BASE_URL,
    }


def _get_kimi_fields(values: dict[str, Any], config: dict[str, str]) -> tuple[str, str, str]:
    api_key = (
        str(values.get("kimi_api_key", "")).strip()
        or os.getenv("KIMI_API_KEY", "")
        or config.get("kimi_api_key", "")
    )
    model = (
        str(values.get("kimi_model", "")).strip()
        or config.get("kimi_model", "")
        or DEFAULT_KIMI_MODEL
    )
    base_url = (
        str(values.get("kimi_base_url", "")).strip()
        or config.get("kimi_base_url", "")
        or DEFAULT_KIMI_BASE_URL
    )
    return api_key, model, base_url


def _run_single(values: dict[str, Any], config: dict[str, str], markdown_text: str | None = None) -> tuple[str, str]:
    if markdown_text is None:
        input_path = Path(str(values.get("input_path", "")).strip())
        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        markdown_text = WechatFormatter.load_text(input_path)

    output_path = Path(str(values.get("output_path", "")).strip())

    if values.get("polish"):
        api_key, model, base_url = _get_kimi_fields(values, config)
        markdown_text = polish_markdown_with_kimi(
            markdown_text,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    custom_css = config.get("custom_css", "")
    
    # Pass manual values if provided, otherwise let formatter handle extraction and fallbacks
    author = str(values.get("author", "")).strip()
    summary = str(values.get("summary", "")).strip()
    cover_image_url = str(values.get("cover_image_url", "")).strip()
    title = str(values.get("title", "")).strip()

    formatter = WechatFormatter(
        FormatOptions(
            title=title,
            custom_css=custom_css,
            author=author,
            summary=summary,
            cover_image_url=cover_image_url,
            theme=str(values.get("theme", "default")),
            # Fallbacks from config
            default_author=config.get("author", ""),
            default_summary=config.get("summary", ""),
            default_cover_image_url=config.get("cover_image_url", ""),
        )
    )
    
    # Format and let it extract missing info
    html = formatter.format_markdown(markdown_text)
    
    # Update values with what was actually used (for UI feedback)
    values["title"] = formatter.options.title
    values["author"] = formatter.options.author
    values["cover_image_url"] = formatter.options.cover_image_url

    WechatFormatter.save_text(output_path, html)
    return "排版成功！", html


def _run_batch(values: dict[str, Any], config: dict[str, str]) -> tuple[str, str]:
    in_dir = Path(str(values.get("in_dir", "")).strip())
    out_dir = Path(str(values.get("out_dir", "")).strip())
    if not in_dir.exists():
        raise FileNotFoundError(f"输入目录不存在: {in_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(in_dir.glob("*.md"))
    if not md_files:
        return "排版成功：未找到需要处理的 .md 文件", ""

    custom_css = config.get("custom_css", "")
    cover_image_url = str(values.get("cover_image_url", "")).strip() or config.get("cover_image_url", "")
    title_template = str(values.get("title_template", "")).strip()
    author_template = str(values.get("author_template", "")).strip()

    preview_html = ""
    outputs: list[str] = []

    api_key = model = base_url = ""
    if values.get("polish"):
        api_key, model, base_url = _get_kimi_fields(values, config)

    for md in md_files:
        markdown_text = md.read_text(encoding="utf-8")
        if values.get("polish"):
            markdown_text = polish_markdown_with_kimi(
                markdown_text,
                api_key=api_key,
                model=model,
                base_url=base_url,
            )

        author = (
            author_template.format(name=md.stem)
            if author_template
            else config.get("author", "")
        )
        title = title_template.format(name=md.stem)
        options = FormatOptions(
            title=title,
            custom_css=custom_css,
            author=author,
            summary=str(values.get("summary", "")).strip(),
            cover_image_url=cover_image_url,
            theme=str(values.get("theme", "default")),
        )

        html = WechatFormatter(options).format_markdown(markdown_text)
        out_path = out_dir / f"{md.stem}.html"
        out_path.write_text(html, encoding="utf-8")
        outputs.append(str(out_path))
        preview_html = html

    return f"批量排版成功！共处理 {len(outputs)} 个文件", ""


def _fetch_today_hot_topics(limit: int = 15, source_id: str | None = None) -> tuple[list[dict[str, str]], str]:
    # 定义可用的源
    def _get_baidu():
        url = "https://top.baidu.com/board?tab=realtime"
        req = urllib_request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            },
        )
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
            
            # 百度热搜的 JSON 数据通常在 <!-- s-data: {...} --> 中
            match = re.search(r'<!--\s*s-data:(.*?)\s*-->', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    cards = data.get("data", {}).get("cards", [])
                    topics = []
                    for card in cards:
                        content = card.get("content", [])
                        for item in content:
                            word = item.get("word")
                            if word:
                                topics.append({
                                    "title": word,
                                    "url": f"https://www.baidu.com/s?wd={urllib_request.quote(word)}"
                                })
                    if topics: return topics[:limit], "百度热搜"
                except: pass

            # 备选正则提取
            words = re.findall(r'"word":"([^"]+)"', html)
            if not words: return None
            seen = set()
            topics: list[dict[str, str]] = []
            for w in words:
                w = w.strip()
                if w and w not in seen:
                    topics.append({
                        "title": w,
                        "url": f"https://www.baidu.com/s?wd={urllib_request.quote(w)}"
                    })
                    seen.add(w)
            return topics[:limit], "百度热搜"
        except Exception:
            return None

    def _get_douyin():
        # 抖音热搜，使用开放 API 的备用路径
        url = "https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/"
        req = urllib_request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            },
        )
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            words = data.get("word_list", [])
            topics = []
            for item in words:
                word = item.get("word")
                if word:
                    topics.append({
                        "title": word,
                        "url": f"https://www.douyin.com/search/{urllib_request.quote(word)}"
                    })
            return (topics[:limit], "抖音热搜") if topics else None
        except Exception:
            return None

    def _get_weibo():
        url = "https://weibo.com/ajax/side/hotSearch"
        req = urllib_request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Referer": "https://weibo.com/",
            },
        )
        with urllib_request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        real_hot = data.get("data", {}).get("realtime", [])
        topics: list[dict[str, str]] = []
        for item in real_hot:
            word = item.get("word")
            scheme = item.get("scheme") # 微博链接
            if word:
                link = scheme if scheme and scheme.startswith("http") else f"https://s.weibo.com/weibo?q={urllib_request.quote(word)}"
                topics.append({"title": word, "url": link})
        return (topics[:limit], "微博热搜") if topics else None

    def _get_zhihu():
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true"
        req = urllib_request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Referer": "https://www.zhihu.com/hot",
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            topics: list[dict[str, str]] = []
            for item in data.get("data", []):
                target = item.get("target", {}) if isinstance(item, dict) else {}
                title = str(target.get("title", "")).strip()
                target_id = target.get("id")
                if title:
                    link = f"https://www.zhihu.com/question/{target_id}" if target_id else "https://www.zhihu.com/hot"
                    topics.append({"title": title, "url": link})
            return (topics[:limit], "知乎热榜") if topics else None
        except Exception:
            # 如果 API 失败，退而求其次抓取网页
            try:
                web_url = "https://www.zhihu.com/hot"
                web_req = urllib_request.Request(web_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"})
                with urllib_request.urlopen(web_req, timeout=10) as resp:
                    html = resp.read().decode("utf-8")
                # 粗略提取
                items = re.findall(r'\"title\":\"([^\"]+)\"', html)
                topics = []
                for item in items:
                    if len(item) > 5:
                        topics.append({"title": item, "url": "https://www.zhihu.com/hot"})
                return (topics[:limit], "知乎热榜(网页版)") if topics else None
            except:
                return None

    def _get_toutiao():
        # 使用头条 PC 版热榜接口，这是目前最稳定的爬虫路径
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        try:
            req = urllib_request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.toutiao.com/",
                "Accept": "application/json, text/plain, */*"
            })
            with urllib_request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            topics = []
            for item in data.get("data", []):
                title = item.get("Title")
                link = item.get("Url")
                if title:
                    topics.append({
                        "title": title,
                        "url": link if link else f"https://www.toutiao.com/search/?keyword={urllib_request.quote(title)}"
                    })
            return (topics[:limit], "今日头条") if topics else None
        except Exception:
            return None

    def _get_wechat():
        # 搜狗微信反爬严重，改用百度热搜的微信子榜单（聚合源）
        url = "https://top.baidu.com/board?tab=wechat"
        try:
            req = urllib_request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            })
            with urllib_request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
            
            # 尝试 JSON 数据提取
            match = re.search(r'<!--\s*s-data:(.*?)\s*-->', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    cards = data.get("data", {}).get("cards", [])
                    topics = []
                    for card in cards:
                        content = card.get("content", [])
                        for item in content:
                            word = item.get("word")
                            if word:
                                topics.append({
                                    "title": word,
                                    "url": f"https://weixin.sogou.com/weixin?type=2&query={urllib_request.quote(word)}"
                                })
                    if topics: return topics[:limit], "微信热点"
                except: pass

            # 备选正则提取
            words = re.findall(r'"word":"([^"]+)"', html)
            topics = []
            for w in words:
                w = w.strip()
                if w:
                    topics.append({
                        "title": w,
                        "url": f"https://weixin.sogou.com/weixin?type=2&query={urllib_request.quote(w)}"
                    })
            return (topics[:limit], "微信热点") if topics else None
        except Exception:
            return None

    def _get_xhs():
        # 小红书暂无稳定公开接口，尝试通过百度搜索聚合热点作为替代
        url = "https://www.baidu.com/s?wd=%E5%B0%8F%E7%BA%A2%E4%B9%A6%E7%83%AD%E6%90%9C%E6%A6%9C"
        try:
            req = urllib_request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            })
            with urllib_request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
            # 从搜索结果中粗略提取可能的标题（这是一项尝试性的爬虫逻辑）
            # 实际生产中建议使用专门的爬虫集群或付费 API
            items = re.findall(r'\"title\":\"([^\"]+)\"', html)
            topics = []
            seen = set()
            for item in items:
                # 过滤掉一些明显的噪音
                if "小红书" in item and len(item) > 5 and item not in seen:
                    topics.append({
                        "title": item,
                        "url": f"https://www.xiaohongshu.com/search_result?keyword={urllib_request.quote(item)}"
                    })
                    seen.add(item)
            
            # 如果百度搜索没抓到，尝试一个备用聚合页
            if not topics:
                # 最后的倔强：返回百度实时热搜的前几名作为填充，避免完全失败
                res_baidu = _get_baidu()
                if res_baidu:
                    return res_baidu[0], "热门话题(备选)"
            
            return (topics[:limit], "小红书趋势") if topics else None
        except Exception:
            return None

    # 如果指定了源，则只尝试该源
    sources = {
        "baidu": _get_baidu,
        "weibo": _get_weibo,
        "zhihu": _get_zhihu,
        "wechat": _get_wechat,
        "xhs": _get_xhs,
        "toutiao": _get_toutiao,
        "douyin": _get_douyin,
    }

    if source_id and source_id in sources:
        try:
            res = sources[source_id]()
            if res: return res
            raise RuntimeError(f"源 '{source_id}' 目前无法获取数据，请尝试其他源或自动切换。")
        except Exception as e:
            if isinstance(e, RuntimeError): raise e
            raise RuntimeError(f"指定源抓取失败 ({source_id}): {e}")

    # 默认流程：自动重试 (当 source_id 为空或为 'auto' 时)
    for sid in ["baidu", "weibo", "douyin", "zhihu", "wechat", "toutiao"]:
        try:
            res = sources[sid]()
            if res: return res
        except Exception:
            continue

    raise RuntimeError("未抓取到热点数据，所有备选源均不可用，请稍后重试。")


def _filter_topics_by_keywords(topics: list[dict[str, str]], keywords: list[str]) -> list[dict[str, str]]:
    if not keywords:
        return topics
    lowered = [k.lower() for k in keywords if k]
    result: list[dict[str, str]] = []
    for t in topics:
        lt = t["title"].lower()
        if any(k in lt for k in lowered):
            result.append(t)
    return result


def _analyze_hot_topics(
    topics: list[dict[str, str]], 
    source: str = "热点源", 
    selected_keywords: list[str] | None = None,
    api_key: str = "",
    model: str = DEFAULT_KIMI_MODEL,
    base_url: str = DEFAULT_KIMI_BASE_URL
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    titles = [t["title"] for t in topics]
    text = " ".join(titles)
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", text)
    stop_words = {
        "一个", "我们", "他们", "这个", "那个", "什么", "如何", "为什么", "可以", "已经", "还是", "真的", "到底", "中国", "美国", "今天", "当日", "热点",
    }

    freq: dict[str, int] = {}
    for token in tokens:
        if token in stop_words:
            continue
        if len(token) <= 1:
            continue
        freq[token] = freq.get(token, 0) + 1

    keyword_items = sorted(freq.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))[:8]
    keyword_line = "、".join(f"{word}({count})" for word, count in keyword_items) if keyword_items else "暂无"

    category_rules: dict[str, list[str]] = {
        "科技/AI": ["AI", "人工智能", "大模型", "芯片", "机器人", "算力", "算法", "软件", "互联网"],
        "财经/产业": ["经济", "市场", "股", "公司", "融资", "创业", "汽车", "就业", "产业"],
        "社会/民生": ["教育", "医疗", "高考", "学校", "家庭", "孩子", "住房", "城市", "老人"],
        "文娱/体育": ["电影", "演员", "综艺", "音乐", "比赛", "球队", "冠军", "奥运", "演唱会"],
    }
    category_count: dict[str, int] = {k: 0 for k in category_rules}
    for title in titles:
        for category, keys in category_rules.items():
            if any(key in title for key in keys):
                category_count[category] += 1

    ranked_categories = [
        f"{name}:{count}"
        for name, count in sorted(category_count.items(), key=lambda x: (-x[1], x[0]))
        if count > 0
    ]
    category_line = "；".join(ranked_categories[:3]) if ranked_categories else "分布不明显"

    kw_line = ""
    if selected_keywords:
        kw_line = "、".join(selected_keywords)
    
    # 构造 AI 建议内容
    ai_suggestions = ""
    if api_key.strip():
        try:
            prompt = f"以下是今日的热点话题列表：\n" + "\n".join([f"- {t}" for t in titles[:20]])
            if selected_keywords:
                prompt += f"\n用户关注的关键词有：{', '.join(selected_keywords)}"
            
            system_prompt = (
                "你是一个资深的微信公众号运营专家。请根据提供的热点话题，为用户提供 3-4 条极具实操性的公众号选题和内容创作建议。"
                "要求：\n"
                "1) 结合公众号读者的阅读习惯（猎奇、实用、共鸣、情绪价值）；\n"
                "2) 每一条建议必须严格按照以下格式输出：\n"
                "   <li>[选题标题]：[建议的文章标题]\n"
                "   切入角度：[具体描述内容]</li>\n"
                "3) **不要输出“选题标题：”这几个字，直接写具体的标题。选题标题应简短有力，能够作为文件名。**\n"
                "4) **每一条建议必须放在同一个 <li> 标签内，选题标题与切入角度之间用换行隔开**；\n"
                "5) 建议要具体、可落地，标题要吸引人；\n"
                "6) 格式为 HTML 的 <ul><li> 列表形式，不要输出多余的解释文字。"
            )
            
            ai_suggestions = chat_with_kimi(
                prompt,
                system_prompt,
                api_key=api_key,
                model=model,
                base_url=base_url,
                temperature=0.7
            )
            # 优先提取 <li> 标签内容，支持跨行提取
            lines = re.findall(r"<li>(.*?)</li>", ai_suggestions, re.DOTALL)
            if not lines:
                lines = [line.strip("- *1234. ") for line in ai_suggestions.split("\n") if line.strip() and "<ul>" not in line and "</ul>" not in line]
            
            items_html = []
            for l in lines:
                l = l.strip()
                # 尝试按行分割，第一行通常是标题，后续是切入角度
                parts = [p.strip() for p in l.split("\n") if p.strip()]
                if not parts:
                    continue
                
                # 第一行作为标题，清理掉 HTML 标签
                title = re.sub(r'<[^>]+>', '', parts[0]).strip()
                # 剩余部分作为描述
                desc = "\n".join(parts[1:]) if len(parts) > 1 else ""
                desc = re.sub(r'<[^>]+>', '', desc).strip()
                
                # 如果没能成功按行分割（AI 没换行），则尝试按冒号分割
                if not desc and "：" in title or ":" in title:
                    title_parts = re.split(r'[:：]', title, 1)
                    title = title_parts[0].strip()
                    desc = title_parts[1].strip() if len(title_parts) > 1 else ""

                # 最终清理，防止 value 中包含冗余信息
                full_text = f"{title}\n{desc}".strip()
                
                items_html.append(
                    f"<li class='suggestion-item' onclick='toggleSuggestion(this)'>"
                    f"<input type='checkbox' class='suggestion-cb' value='{full_text}' onclick='event.stopPropagation(); updateSelection(this)'>"
                    f"<div class='suggestion-text'>"
                    f"<span class='suggestion-title'>{title}</span>"
                    f"<span class='suggestion-desc'>{desc}</span>"
                    f"</div>"
                    f"</li>"
                )
            # 添加全选框容器
            select_all_html = (
                "<div style='margin-bottom: 15px; padding-left: 10px; display: flex; align-items: center; border-bottom: 1px dashed #e2e8f0; padding-bottom: 10px;'>"
                "<input type='checkbox' id='select-all-cb' onclick='toggleAllSuggestions(this)' style='width: 18px; height: 18px; margin-right: 10px; cursor: pointer; accent-color: var(--brand);'>"
                "<label for='select-all-cb' style='cursor: pointer; font-weight: bold; color: var(--brand); font-size: 14px;'>全选 / 取消全选</label>"
                "</div>"
            )
            ai_suggestions = select_all_html + "<ul class='suggestion-list'>" + "".join(items_html) + "</ul>"
        except Exception as e:
            ai_suggestions = f"<div style='color: #9f1239; background: #fff1f2; padding: 10px; border-radius: 8px; border: 1px solid #fda4af; font-size: 13px; margin-bottom: 10px;'><strong>AI 分析请求失败:</strong> {e}<br/><small>请检查 API Key 是否正确，或 API 余额是否充足。</small></div>"
    else:
        ai_suggestions = "<div style='color: #6b7280; background: #f9fafb; padding: 10px; border-radius: 8px; border: 1px solid #e5e7eb; font-size: 13px; margin-bottom: 10px;'><strong>提示:</strong> 未检测到 Kimi API Key，正在展示默认建议。输入 API Key 后可获得 AI 深度分析。</div>"
    
    if not ai_suggestions or "提示:" in ai_suggestions:
        default_items = [
            "1. 选 Top 3 热点中的一个争议点：做“观点+证据”短评。",
            "2. 实用解读：结合你账号定位，把热点改写成“对读者有什么影响”。",
            "3. 系列内容：复盘关键词趋势，连续 3 天跟踪同一主题。"
        ]
        items_html = []
        for l in default_items:
            title_parts = re.split(r'[:：]', l, 1)
            title = title_parts[0].strip()
            desc = title_parts[1].strip() if len(title_parts) > 1 else ""
            items_html.append(
                f"<li class='suggestion-item' onclick='toggleSuggestion(this)'>"
                f"<input type='checkbox' class='suggestion-cb' value='{l}' onclick='event.stopPropagation(); updateSelection(this)'>"
                f"<div class='suggestion-text'>"
                f"<span class='suggestion-title'>{title}</span>"
                f"<span class='suggestion-desc'>{desc}</span>"
                f"</div>"
                f"</li>"
            )
        # 默认建议也添加全选
        select_all_html = (
            "<div style='margin-bottom: 15px; padding-left: 10px; display: flex; align-items: center; border-bottom: 1px dashed #e2e8f0; padding-bottom: 10px;'>"
            "<input type='checkbox' id='select-all-cb' onclick='toggleAllSuggestions(this)' style='width: 18px; height: 18px; margin-right: 10px; cursor: pointer; accent-color: var(--brand);'>"
            "<label for='select-all-cb' style='cursor: pointer; font-weight: bold; color: var(--brand); font-size: 14px;'>全选 / 取消全选</label>"
            "</div>"
        )
        ai_suggestions = (ai_suggestions if ai_suggestions else "") + select_all_html + "<ul class='suggestion-list'>" + "".join(items_html) + "</ul>"

    # 构造 HTML 报告
    html_lines = [
        f"<div><strong>热点报告时间:</strong> {now}</div>",
        f"<div><strong>数据源:</strong> {source}</div>",
    ]
    if kw_line:
        html_lines.append(f"<div><strong>关键词筛选:</strong> {kw_line}</div>")
    
    html_lines.append("<br/>")
    html_lines.append("<h3>一、今日热点 Top 10</h3>")
    html_lines.append("<ol style='padding-left: 20px;'>")
    for t in topics[:10]:
        html_lines.append(f"<li><a href='{t['url']}' target='_blank' style='color: #0f766e; text-decoration: none;'>{t['title']}</a></li>")
    html_lines.append("</ol>")

    html_lines.extend([
        "<br/>",
        "<h3>二、关键词聚焦</h3>",
        f"<div>{keyword_line}</div>",
        "<br/>",
        "<h3>三、话题结构</h3>",
        f"<div>{category_line}</div>",
        "<br/>",
        "<h3>四、内容建议 (AI 分析)</h3>" if api_key.strip() else "<h3>四、内容建议</h3>",
        ai_suggestions,
        "<div style='margin-top: 20px; padding: 20px; border-top: 1px solid var(--line); text-align: center;'>",
        "<button id='gen-btn' onclick='generateArticles()' style='background: var(--brand); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.2s;'>",
        "🚀 AI 生成选中的公众号文章",
        "</button>",
        "<div id='gen-status' style='margin-top: 15px; font-size: 14px; color: var(--brand); font-weight: bold; display: none;'></div>",
        "</div>"
    ])
    return "".join(html_lines)


def _run_batch_selected(values: dict[str, Any], config: dict[str, Any], selected_files: list[str]) -> tuple[str, str]:
    from .batch import process_file
    
    in_dir = Path("batch_input")
    out_dir = Path(str(values.get("out_dir") or config.get("out_dir") or "batch_output"))
    
    count = 0
    preview_html = ""
    
    api_key, model, base_url = _get_kimi_fields(values, config)
    
    for rel_path in selected_files:
        in_path = in_dir / rel_path
        if not in_path.exists():
            continue
            
        # 保持相对目录结构
        article_out_dir = out_dir / in_path.parent.relative_to(in_dir)
        
        # 构造选项
        from .formatter import FormatOptions
        options = FormatOptions(
            theme=str(values.get("theme", "default")),
            author=str(values.get("author", "")),
            summary=str(values.get("summary", "")),
            cover_image_url=str(values.get("cover_image_url", "")),
        )
        
        # 使用 batch.py 中的 process_file 逻辑
        out_path = process_file(
            md_path=in_path,
            out_dir=article_out_dir,
            options=options,
            polish=values.get("polish", False),
            kimi_api_key=api_key,
            kimi_model=model,
            kimi_base_url=base_url
        )
        
        # 记录预览（取最后一个文件的内容）
        if not preview_html:
            preview_html = in_path.read_text(encoding="utf-8") # 暂时用源码
            
        count += 1

    message = f"成功处理 {count} 个选中的文件，保存至 {out_dir}"
    return message, ""


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_no_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/")
    def index() -> str:
        # 允许通过 URL 参数 ?mode=batch 手动切换模式而不触发提交
        mode = request.args.get("mode", "single")
        values = _initial_values()
        values["mode"] = mode
        
        return render_template_string(
            PAGE_HTML,
            values=values,
            message="",
            ok=True,
            preview_html="",
        )

    @app.get("/list_batch_files")
    def list_batch_files() -> Any:
        try:
            in_dir = Path("batch_input")
            if not in_dir.exists():
                return jsonify({"ok": True, "files": []})
            
            # 递归查找所有 .md 文件，返回相对路径
            files = []
            for path in in_dir.rglob("*.md"):
                files.append(str(path.relative_to(in_dir)))
            
            # 按名称排序，通常日期目录在前的会排在前面
            files.sort(reverse=True)
            return jsonify({"ok": True, "files": files})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.post("/run")
    def run_pipeline() -> str:
        # Get values from form
        form_values = request.form.to_dict()
        
        values = _initial_values()
        for key in values:
            if key == "polish":
                values[key] = request.form.get("polish") == "1"
            elif key in form_values:
                values[key] = form_values[key]

        # Handle uploaded file
        uploaded_file = request.files.get("file")
        markdown_text = None
        if uploaded_file and uploaded_file.filename:
            markdown_text = uploaded_file.read().decode("utf-8")
            # Only set title from filename if the user didn't provide one
            if not values.get("title"):
                values["title"] = "" # Clear default to trigger extraction from content


        try:
            config = _load_config(str(values.get("config_path", "")))
            if values.get("mode") == "batch":
                # 如果有选中的文件，则只处理选中的文件
                selected_files = request.form.getlist("selected_files")
                if selected_files:
                    # 动态更新 config 中的 in_dir 为包含这些文件的逻辑是不现实的
                    # 我们直接修改 _run_batch 内部逻辑，或者在这里处理
                    message, preview_html = _run_batch_selected(values, config, selected_files)
                else:
                    message, preview_html = _run_batch(values, config)
            else:
                message, preview_html = _run_single(values, config, markdown_text=markdown_text)
            ok = True
        except Exception as exc:
            message = f"排版失败：{exc}"
            preview_html = ""
            ok = False

        return render_template_string(
            PAGE_HTML,
            values=values,
            message=message,
            ok=ok,
            preview_html=preview_html,
        )

    @app.post("/download")
    def download_file() -> Any:
        html_content = request.form.get("html_content", "")
        # Get the actual title from form if available, otherwise fallback
        filename = request.form.get("filename", "wechat_article")
        if not filename.endswith(".html"):
            filename += ".html"
        
        # 使用内存文件流返回下载
        file_stream = io.BytesIO(html_content.encode("utf-8"))
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=filename,
            mimetype="text/html"
        )

    @app.post("/hotspots")
    def hotspots() -> Any:
        try:
            source_id = request.form.get("source") or request.args.get("source") or ""
            kw_str = ""
            # 优先从请求中获取 API Key
            api_key_req = request.form.get("kimi_api_key") or request.args.get("kimi_api_key")
            
            if request.is_json:
                body = request.get_json(silent=True) or {}
                kw_str = str(body.get("keywords", "") or "")
                source_id = source_id or body.get("source", "")
                api_key_req = api_key_req or body.get("kimi_api_key")
            else:
                kw_str = request.form.get("keywords", "") or request.args.get("keywords", "") or ""
            
            keywords = [k.strip() for k in re.split(r"[\s,，、;；]+", kw_str) if k.strip()]
            
            # 获取 Kimi API 配置
            config = _load_config(str(_initial_values().get("config_path", "")))
            api_key, model, base_url = _get_kimi_fields(_initial_values(), config)
            
            # 覆盖为用户实时输入的 Key
            if api_key_req:
                api_key = api_key_req

            topics, source = _fetch_today_hot_topics(limit=15, source_id=source_id)
            if keywords:
                topics = _filter_topics_by_keywords(topics, keywords)
            
            report = _analyze_hot_topics(
                topics, 
                source=source, 
                selected_keywords=keywords if keywords else None,
                api_key=api_key,
                model=model,
                base_url=base_url
            )
            return jsonify(
                {
                    "ok": True,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "report": report,
                    "topics": topics,
                    "source": source,
                    "keywords": keywords,
                }
            )
        except Exception as exc:
            return jsonify({"ok": False, "message": f"抓取热点失败: {exc}"}), 500

    @app.post("/generate_articles")
    def generate_articles() -> Any:
        try:
            body = request.get_json(silent=True) or {}
            topics = body.get("topics", [])
            if not topics:
                return jsonify({"ok": False, "message": "未选中任何话题"}), 400

            # 1. 加载配置和 API Key
            config = _load_config(str(_initial_values().get("config_path", "")))
            api_key, model, base_url = _get_kimi_fields(_initial_values(), config)
            if not api_key:
                return jsonify({"ok": False, "message": "未配置 Kimi API Key"}), 400

            # 2. 读取 SKILL.md 风格要求
            skill_path = Path("examples/SKILL.md")
            skill_content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

            # 3. 创建日期目录
            today_str = datetime.now().strftime("%Y-%m-%d")
            out_dir = Path("batch_input") / today_str
            out_dir.mkdir(parents=True, exist_ok=True)

            system_prompt = (
                "你是一个资深的微信公众号创作者。请根据提供的选题和参考的写作风格要求，创作一篇高质量的公众号文章。\n\n"
                "### 写作风格要求 (SKILL.md):\n"
                f"{skill_content}\n\n"
                "### 核心指令：\n"
                "1) 严格遵守 SKILL.md 中的所有禁令（如标点禁令、踩雷词禁令）；\n"
                "2) 保持口语化的节奏和“活人感”；\n"
                "3) 段落要短，多用逗号，模拟聊天感；\n"
                "4) 选题要有深度，从现象升维到文化或哲学层面；\n"
                "5) 输出格式为纯 Markdown，**严禁包含任何“总评”、“修复优先级”、“分析”或“评价”等元数据或总结性内容**；\n"
                "6) 仅输出文章标题（用 # 标记）和正文内容，不要输出任何 AI 自身的对话或解释性文字。"
            )

            results = []
            for topic in topics:
                # 1. 优先按换行符拆分，第一行通常是标题（包含选题名称和建议标题）
                lines = [line.strip() for line in topic.split("\n") if line.strip()]
                if not lines:
                    continue
                
                title_line = lines[0]
                article_desc = "\n".join(lines[1:]) if len(lines) > 1 else ""

                # 2. 进一步清理标题行，移除 AI 可能输出的“选题名称：”等字样
                # 兼容多种可能的中文/英文前缀
                article_title = re.sub(r"^(选题名称|选题标题|选题|Title|Topic)[:：\s]*", "", title_line, flags=re.IGNORECASE).strip()
                
                # 3. 清理描述内容，移除 AI 可能输出的“切入角度：”等字样
                article_desc = re.sub(r"^(切入角度|角度|Angle|Perspective)[:：\s]*", "", article_desc, flags=re.IGNORECASE).strip()

                # 4. 生成安全的文件名
                # 如果 article_title 仍然包含冒号，只取第一部分作为文件名
                filename_base = re.split(r'[:：]', article_title, 1)[0].strip()
                safe_name = re.sub(r'[\\/:*?"<>|]', "_", filename_base)[:100]
                if not safe_name:
                    safe_name = "untitled_article"
                
                file_path = out_dir / f"{safe_name}.md"
                
                # 5. 构造 Prompt，告诉 AI 标题和背景
                user_prompt = f"请以选题「{article_title}」为题，写一篇公众号文章。"
                if article_desc:
                    user_prompt += f"\n背景参考：{article_desc}"
                user_prompt += "\n记住要像个活人一样思考和表达，遵循上述所有风格指导。"

                content = chat_with_kimi(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    temperature=0.8
                )
                file_path.write_text(content, encoding="utf-8")
                results.append(str(file_path))

            return jsonify({
                "ok": True, 
                "message": f"成功生成 {len(results)} 篇文章", 
                "path": str(out_dir),
                "files": results
            })
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.get("/hotspots/report")
    def hotspots_report_page() -> str:
        return render_template_string(HOTSPOT_REPORT_HTML)

    return app


def main() -> int:
    app = create_app()
    # 开启 debug=True 以便代码修改后自动重启
    app.run(host="127.0.0.1", port=8765, debug=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
