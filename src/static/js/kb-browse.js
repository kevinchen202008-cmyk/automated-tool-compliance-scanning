/**
 * 工具库浏览模块
 * Knowledge base browse tab logic
 */

var kbEntriesCache = [];
var kbFilteredEntries = [];
var kbSelectedTool = null;
var kbEditFullData = null;
var kbOrderBy = 'tool_name';
var kbLicenseFilter = 'all';

function kbLicenseCategory(lic) {
  if (!lic || typeof lic !== 'string') return '';
  var s = lic.toLowerCase();
  var openKeys = ['apache', 'mit', 'gpl', 'bsd', 'lgpl', 'mpl', '开源', 'open source', 'oss', 'mozilla', 'eclipse', 'agpl', 'cc0', 'creative commons'];
  var commercialKeys = ['商业', '企业', 'commercial', '付费', '专有', 'proprietary', 'enterprise', 'subscription', '许可'];
  for (var i = 0; i < openKeys.length; i++) { if (s.indexOf(openKeys[i]) !== -1) return 'open'; }
  for (var j = 0; j < commercialKeys.length; j++) { if (s.indexOf(commercialKeys[j]) !== -1) return 'commercial'; }
  return 'other';
}

function licenseColorClass(lic) {
  var cat = kbLicenseCategory(lic);
  if (cat === 'open') return 'license-open';
  if (cat === 'commercial') return 'license-commercial';
  return '';
}

function applyKbFilter() {
  var q = document.getElementById('kbSearch').value.trim().toLowerCase();
  var type = kbLicenseFilter;
  kbFilteredEntries = kbEntriesCache.filter(function(e) {
    var name = (e.tool_name || '').toLowerCase();
    if (q && name.indexOf(q) === -1) return false;
    if (type === 'all') return true;
    var lic = (e.data && e.data.license_type) ? e.data.license_type : '';
    var cat = kbLicenseCategory(lic);
    if (type === 'open') return cat === 'open';
    if (type === 'commercial') return cat === 'commercial';
    if (type === 'other') return cat === 'other';
    return true;
  });
}

function renderKbList() {
  var listEl = document.getElementById('kbList');
  var entries = kbFilteredEntries;
  if (!entries.length) {
    listEl.innerHTML = '<span class="task-status">' + (kbEntriesCache.length ? '无匹配项' : '暂无工具信息库条目') + '</span>';
    return;
  }
  listEl.innerHTML = entries.map(function(e) {
    var rawName = e.tool_name || '';
    var name = rawName.trim() || '（未命名）';
    var lic = (e.data && e.data.license_type) ? e.data.license_type : '';
    var active = rawName === kbSelectedTool ? ' active' : '';
    var licClass = licenseColorClass(lic);
    var licHtml = lic ? '<span class="kb-list-license ' + licClass + '" title="许可/协议">' + escapeHtml(lic) + '</span>' : '';
    return '<button type="button" class="kb-list-item' + active + '" data-tool="' + escapeHtml(rawName) + '">' +
      '<span class="kb-list-name">' + escapeHtml(name) + '</span>' + licHtml + '</button>';
  }).join('');
}

function renderKbDetail(detail) {
  if (!detail) return '';
  var lic = detail.license_info || {};
  var comp = detail.company_info || {};
  var comm = detail.commercial_restrictions || {};
  var alts = detail.alternative_tools || [];

  var sectionsHtml = renderComplianceSections(lic, comp, comm, alts);

  var meta = [];
  if (detail.source) meta.push('来源: ' + escapeHtml(detail.source));
  if (detail.updated_at) meta.push('更新: ' + escapeHtml(detail.updated_at));
  if (detail.updated_by) meta.push('更新人: ' + escapeHtml(detail.updated_by));
  var metaHtml = meta.length ? '<p class="sub" style="margin-top:12px;font-size:12px;">' + meta.join(' · ') + '</p>' : '';
  var toolName = detail.tool_name || '';
  var actionsHtml = '<div class="kb-detail-actions">' +
    '<button type="button" class="btn btn-sm" data-action="kb-edit" data-tool="' + escapeHtml(toolName) + '">编辑</button>' +
    '<button type="button" class="btn btn-sm btn-danger" data-action="kb-delete" data-tool="' + escapeHtml(toolName) + '">从工具信息库删除</button>' +
    '</div>';
  return '<div class="result-card">' +
    '<h2>' + escapeHtml(toolName) + ' <span style="font-size:0.75rem;color:var(--muted);font-weight:normal">（工具信息库）</span></h2>' +
    sectionsHtml + metaHtml + actionsHtml + '</div>';
}

function renderKbEditForm(toolName, data) {
  var d = data || {};
  var lic = d.license_type != null ? String(d.license_type) : '';
  var licVer = d.license_version != null ? String(d.license_version) : '';
  var licMode = d.license_mode != null ? String(d.license_mode) : '';
  var company = d.company_name != null ? String(d.company_name) : '';
  var country = d.company_country != null ? String(d.company_country) : '';
  var hq = d.company_headquarters != null ? String(d.company_headquarters) : '';
  var china = d.china_office === true || d.china_office === 'true';
  var needLic = d.commercial_license_required === true || d.commercial_license_required === 'true';
  var freeComm = d.free_for_commercial === true || d.free_for_commercial === 'true';
  var restr = d.commercial_restrictions != null ? String(d.commercial_restrictions) : '';
  var userLimit = d.user_limit != null ? String(d.user_limit) : '';
  var featRestr = d.feature_restrictions != null ? String(d.feature_restrictions) : '';
  var alts = d.alternative_tools;
  var altsStr = Array.isArray(alts) ? JSON.stringify(alts, null, 2) : (alts != null ? String(alts) : '[]');
  return '<div class="result-card" id="kbEditFormCard">' +
    '<h2>' + escapeHtml(toolName) + ' <span style="font-size:0.75rem;color:var(--muted)">（编辑）</span></h2>' +
    '<form class="kb-edit-form" id="kbEditForm" data-tool="' + escapeHtml(toolName) + '">' +
    '<div class="result-section"><h3>使用许可/开源协议</h3>' +
    '<div class="form-row"><label>类型</label><input type="text" name="license_type" value="' + escapeHtml(lic) + '"></div>' +
    '<div class="form-row"><label>版本</label><input type="text" name="license_version" value="' + escapeHtml(licVer) + '"></div>' +
    '<div class="form-row"><label>模式</label><input type="text" name="license_mode" value="' + escapeHtml(licMode) + '"></div></div>' +
    '<div class="result-section"><h3>公司信息</h3>' +
    '<div class="form-row"><label>公司名称</label><input type="text" name="company_name" value="' + escapeHtml(company) + '"></div>' +
    '<div class="form-row"><label>所属国家</label><input type="text" name="company_country" value="' + escapeHtml(country) + '"></div>' +
    '<div class="form-row"><label>总部</label><input type="text" name="company_headquarters" value="' + escapeHtml(hq) + '"></div>' +
    '<div class="form-row"><label><input type="checkbox" name="china_office" ' + (china ? 'checked' : '') + '> 有中国分公司或服务</label></div></div>' +
    '<div class="result-section"><h3>商用限制</h3>' +
    '<div class="form-row"><label><input type="checkbox" name="commercial_license_required" ' + (needLic ? 'checked' : '') + '> 需购买 License</label></div>' +
    '<div class="form-row"><label><input type="checkbox" name="free_for_commercial" ' + (freeComm ? 'checked' : '') + '> 允许免费商用</label></div>' +
    '<div class="form-row"><label>限制说明</label><input type="text" name="commercial_restrictions" value="' + escapeHtml(restr) + '"></div>' +
    '<div class="form-row"><label>用户限制</label><input type="text" name="user_limit" value="' + escapeHtml(userLimit) + '"></div>' +
    '<div class="form-row"><label>功能限制</label><input type="text" name="feature_restrictions" value="' + escapeHtml(featRestr) + '"></div></div>' +
    '<div class="result-section"><h3>可替代方案（JSON 数组）</h3>' +
    '<div class="form-row"><label>alternative_tools</label><textarea name="alternative_tools">' + escapeHtml(altsStr) + '</textarea></div></div>' +
    '<div class="kb-detail-actions">' +
    '<button type="submit" class="btn btn-sm">保存</button>' +
    '<button type="button" class="btn btn-sm" data-action="kb-cancel-edit" data-tool="' + escapeHtml(toolName) + '">取消</button>' +
    '</div></form></div>';
}

async function loadKbDetail(toolName) {
  var detailEl = document.getElementById('kbDetail');
  if (!toolName) {
    detailEl.innerHTML = '<p class="task-status" style="padding:16px">请从左侧选择工具</p>';
    return;
  }
  detailEl.innerHTML = '<span class="task-status">加载中…</span>';
  try {
    var res = await fetch(API_BASE + '/api/v1/knowledge-base/' + encodeURIComponent(toolName) + '/detail');
    if (!res.ok) throw new Error('加载详情失败: ' + (await res.text()) || res.status);
    var detail = await res.json();
    detailEl.innerHTML = renderKbDetail(detail);
  } catch (e) {
    detailEl.innerHTML = '<span style="color:var(--danger)">' + escapeHtml(e.message) + '</span>';
  }
}

async function handleKbAction(action, toolName, reportId, btn) {
  try {
    if (action === 'kb-create') {
      btn.disabled = true;
      var res = await fetch(API_BASE + '/api/v1/knowledge-base/' + encodeURIComponent(toolName) + '/create-from-report?report_id=' + encodeURIComponent(reportId), { method: 'POST' });
      if (!res.ok) throw new Error('加入工具信息库失败: ' + (await res.text()) || res.status);
      btn.textContent = '已加入工具信息库';
    } else if (action === 'kb-update') {
      btn.disabled = true;
      var res2 = await fetch(API_BASE + '/api/v1/knowledge-base/' + encodeURIComponent(toolName) + '/update-from-report?report_id=' + encodeURIComponent(reportId), { method: 'POST' });
      if (!res2.ok) throw new Error('更新工具信息库失败: ' + (await res2.text()) || res2.status);
      btn.textContent = '工具信息库已更新';
    } else if (action === 'kb-ignore' || action === 'kb-keep') {
      btn.textContent = action === 'kb-ignore' ? '已选择暂不保存' : '已选择保持不变';
      btn.disabled = true;
    }
  } catch (e) {
    alert(e.message || e);
    btn.disabled = false;
  }
}

async function deleteKbTool(toolName, btn) {
  if (!toolName) return;
  if (!confirm('确定从工具信息库中删除「' + toolName + '」？删除后不可恢复。')) return;
  if (btn) btn.disabled = true;
  try {
    var res = await fetch(API_BASE + '/api/v1/knowledge-base/' + encodeURIComponent(toolName), { method: 'DELETE' });
    if (!res.ok) throw new Error('删除失败: ' + (await res.text()) || res.status);
    kbEntriesCache = kbEntriesCache.filter(function(e) { return (e.tool_name || '') !== toolName; });
    applyKbFilter();
    if (kbSelectedTool === toolName) {
      kbSelectedTool = kbFilteredEntries.length > 0 ? kbFilteredEntries[0].tool_name : null;
      renderKbList();
      await loadKbDetail(kbSelectedTool);
    } else {
      renderKbList();
    }
  } catch (e) {
    alert(e.message || e);
  }
  if (btn) btn.disabled = false;
}

function initKbBrowse() {
  // 加载列表
  document.getElementById('kbLoadListBtn').onclick = async function() {
    var btn = this;
    var panel = document.getElementById('kbPanel');
    var listEl = document.getElementById('kbList');
    var detailEl = document.getElementById('kbDetail');
    btn.disabled = true;
    listEl.innerHTML = '<span class="task-status">加载中…</span>';
    detailEl.innerHTML = '';
    try {
      var res = await fetch(API_BASE + '/api/v1/knowledge-base?limit=1000&order_by=' + encodeURIComponent(kbOrderBy));
      if (!res.ok) throw new Error('加载列表失败: ' + (await res.text()) || res.status);
      var data = await res.json();
      kbEntriesCache = data.entries || [];
      document.getElementById('kbSearch').value = '';
      applyKbFilter();
      panel.style.display = 'flex';
      renderKbList();
      if (kbFilteredEntries.length > 0) {
        kbSelectedTool = kbFilteredEntries[0].tool_name;
        renderKbList();
        await loadKbDetail(kbSelectedTool);
      } else {
        kbSelectedTool = null;
        detailEl.innerHTML = '<p class="task-status" style="padding:16px">暂无工具信息库条目</p>';
      }
    } catch (e) {
      listEl.innerHTML = '<span style="color:var(--danger)">' + escapeHtml(e.message) + '</span>';
    }
    btn.disabled = false;
  };

  // 搜索筛选
  document.getElementById('kbSearch').oninput = function() {
    applyKbFilter();
    renderKbList();
    var stillInList = kbFilteredEntries.some(function(e) { return e.tool_name === kbSelectedTool; });
    if (!stillInList && kbFilteredEntries.length > 0) {
      kbSelectedTool = kbFilteredEntries[0].tool_name;
      renderKbList();
      loadKbDetail(kbSelectedTool);
    } else if (!stillInList) {
      kbSelectedTool = null;
      loadKbDetail(null);
    }
  };

  // 许可过滤
  document.getElementById('kbLicenseFilter').onchange = function() {
    kbLicenseFilter = this.value || 'all';
    applyKbFilter();
    renderKbList();
    var stillInList = kbFilteredEntries.some(function(e) { return e.tool_name === kbSelectedTool; });
    if (!stillInList && kbFilteredEntries.length > 0) {
      kbSelectedTool = kbFilteredEntries[0].tool_name;
      renderKbList();
      loadKbDetail(kbSelectedTool);
    } else if (!stillInList) {
      kbSelectedTool = null;
      loadKbDetail(null);
    }
  };

  // 列表点击
  document.getElementById('kbList').addEventListener('click', async function(evt) {
    var btn = evt.target.closest('.kb-list-item');
    if (!btn) return;
    var toolName = btn.getAttribute('data-tool');
    if (!toolName) return;
    kbSelectedTool = toolName;
    renderKbList();
    await loadKbDetail(toolName);
  });

  // 排序
  document.getElementById('kbOrder').onchange = function() {
    kbOrderBy = this.value || 'tool_name';
    document.getElementById('kbLoadListBtn').click();
  };

  // 导出 CSV
  document.getElementById('kbExportBtn').onclick = function() {
    if (!kbEntriesCache.length) {
      alert('请先加载工具信息库列表，再执行导出。');
      return;
    }
    var rows = [];
    rows.push(['工具名称', '许可/协议类型', '许可模式', '公司名称', '所属国家/地区', '最近更新时间']);
    var list = kbFilteredEntries.length ? kbFilteredEntries : kbEntriesCache;
    list.forEach(function(e) {
      var name = e.tool_name || '';
      var data = e.data || {};
      rows.push([name, data.license_type || '', data.license_mode || '', data.company_name || '', data.company_country || '', e.updated_at || (data.updated_at || '')]);
    });
    var csv = rows.map(function(row) { return row.map(csvEscape).join(','); }).join('\r\n');
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'tool-knowledge-base-list.csv';
    document.body.appendChild(a);
    a.click();
    setTimeout(function() { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1000);
  };

  // 全局委托：编辑/删除/知识库操作
  document.addEventListener('click', function(evt) {
    var target = evt.target.closest('[data-action]');
    if (!target) return;
    var action = target.getAttribute('data-action');
    if (!/^kb-/.test(action)) return;
    var tool = target.getAttribute('data-tool');
    var reportId = target.getAttribute('data-report-id');
    if (action === 'kb-delete') { deleteKbTool(tool, target); return; }
    if (action === 'kb-edit') {
      evt.preventDefault();
      (async function() {
        var detailEl = document.getElementById('kbDetail');
        detailEl.innerHTML = '<span class="task-status">加载中…</span>';
        try {
          var res = await fetch(API_BASE + '/api/v1/knowledge-base/' + encodeURIComponent(tool));
          if (!res.ok) throw new Error('加载失败: ' + (await res.text()) || res.status);
          var json = await res.json();
          kbEditFullData = json.data || {};
          detailEl.innerHTML = renderKbEditForm(json.tool_name, kbEditFullData);
        } catch (e) {
          detailEl.innerHTML = '<span style="color:var(--danger)">' + escapeHtml(e.message) + '</span>';
        }
      })();
      return;
    }
    if (action === 'kb-cancel-edit') { loadKbDetail(tool); return; }
    handleKbAction(action, tool, reportId, target);
  });

  // 编辑表单提交
  document.addEventListener('submit', function(evt) {
    if (evt.target.id !== 'kbEditForm') return;
    evt.preventDefault();
    var form = evt.target;
    var toolName = form.getAttribute('data-tool');
    if (!toolName) return;
    var formData = {
      license_type: form.license_type.value.trim() || null,
      license_version: form.license_version.value.trim() || null,
      license_mode: form.license_mode.value.trim() || null,
      company_name: form.company_name.value.trim() || null,
      company_country: form.company_country.value.trim() || null,
      company_headquarters: form.company_headquarters.value.trim() || null,
      china_office: form.china_office.checked,
      commercial_license_required: form.commercial_license_required.checked,
      free_for_commercial: form.free_for_commercial.checked,
      commercial_restrictions: form.commercial_restrictions.value.trim() || null,
      user_limit: form.user_limit.value.trim() || null,
      feature_restrictions: form.feature_restrictions.value.trim() || null
    };
    try {
      var altsStr = form.alternative_tools.value.trim();
      formData.alternative_tools = altsStr ? JSON.parse(altsStr) : [];
    } catch (_) {
      alert('可替代方案请输入合法 JSON 数组');
      return;
    }
    var data = Object.assign({}, kbEditFullData || {}, formData);
    (async function() {
      var btn = form.querySelector('button[type="submit"]');
      if (btn) btn.disabled = true;
      try {
        var res = await fetch(API_BASE + '/api/v1/knowledge-base/' + encodeURIComponent(toolName), {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('保存失败: ' + (await res.text()) || res.status);
        var idx = kbEntriesCache.findIndex(function(e) { return (e.tool_name || '') === toolName; });
        if (idx >= 0) kbEntriesCache[idx].data = data;
        renderKbList();
        await loadKbDetail(toolName);
      } catch (e) {
        alert(e.message || e);
      }
      if (btn) btn.disabled = false;
    })();
  });
}
