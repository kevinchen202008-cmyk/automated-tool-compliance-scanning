/**
 * 合规扫描模块
 * Compliance scan tab logic
 */

function renderResult(report) {
  var toolName = (report.tool && report.tool.name) || '未知工具';
  var lic = report.license_info || {};
  var comp = report.company_info || {};
  var comm = report.commercial_restrictions || {};
  var alts = report.alternative_tools || [];
  var kbUpdate = report.knowledge_base_update || {};
  var ds = report.data_source || {};
  var ai = !!ds.ai_analysis;
  var kb = !!ds.knowledge_base;
  var sourceLabel = ai && kb ? '混合' : ai ? '本次 AI' : kb ? '工具信息库' : '无';
  var sourceClass = ai && kb ? 'mixed' : ai ? 'ai' : kb ? 'kb' : '';
  var sourceHtml = '<div class="data-source-badge' + (sourceClass ? ' ' + sourceClass : '') + '">数据来源：<span>' + escapeHtml(sourceLabel) + '</span></div>';

  var sectionsHtml = renderComplianceSections(lic, comp, comm, alts);

  // 知识库操作提示
  var kbHtml = '';
  if (kbUpdate && kbUpdate.available) {
    if (kbUpdate.action === 'pending_creation') {
      kbHtml = '<div class="kb-banner new">' +
        '<div>发现新工具，本次 AI 分析结果尚未写入工具信息库。</div>' +
        '<div class="kb-actions">' +
        '<button class="btn btn-sm" data-action="kb-create" data-tool="' + escapeHtml(toolName) + '" data-report-id="' + (report.compliance_report && report.compliance_report.id) + '">将本次结果加入工具信息库</button>' +
        '<button class="btn btn-sm" data-action="kb-ignore" data-tool="' + escapeHtml(toolName) + '">暂不保存，只查看本次结果</button>' +
        '</div></div>';
    } else if (kbUpdate.action === 'diff_available') {
      var summary = kbUpdate.summary || ('发现 ' + (kbUpdate.change_count || 0) + ' 处差异');
      var changes = kbUpdate.changes || [];
      var changeList = changes.slice(0, 5).map(function(c) {
        return '<li>' + escapeHtml(c.field_label || c.field || '') + '：' +
          escapeHtml(String(c.old_value ?? '（原无）')) + ' → ' +
          escapeHtml(String(c.new_value ?? '（新无）')) + '</li>';
      }).join('');
      if (!changeList) changeList = '<li>当前工具信息库记录与本次 AI 分析无显著差异。</li>';
      kbHtml = '<div class="kb-banner diff">' +
        '<div>工具信息库中已存在该工具记录。</div>' +
        '<div style="margin-top:6px;font-size:11px;color:var(--muted)">差异说明：左侧为<strong>工具信息库当前值</strong>，右侧为<strong>本次 AI 分析结果</strong>；（原无）/（新无）表示该侧无值。</div>' +
        '<div>' + escapeHtml(summary) + '</div>' +
        '<ul style="margin:6px 0 0 16px;padding:0;font-size:12px;">' + changeList + '</ul>' +
        (kbUpdate.has_changes ? (
          '<div class="kb-actions">' +
          '<button class="btn btn-sm" data-action="kb-update" data-tool="' + escapeHtml(toolName) + '" data-report-id="' + (report.compliance_report && report.compliance_report.id) + '">用本次 AI 结果更新工具信息库差异</button>' +
          '<button class="btn btn-sm" data-action="kb-keep" data-tool="' + escapeHtml(toolName) + '">保持工具信息库不变</button>' +
          '</div>'
        ) : '') +
        '</div>';
    }
  }

  return '<div class="result-card">' +
    '<h2>' + escapeHtml(toolName) + '</h2>' +
    sourceHtml + sectionsHtml +
    (kbHtml ? '<div class="result-section">' + kbHtml + '</div>' : '') +
    '</div>';
}

function initScan() {
  document.getElementById('startBtn').onclick = async function() {
    var raw = document.getElementById('tools').value.trim();
    if (!raw) { alert('请输入至少一个工具名称'); return; }
    var tools = raw.split(/[\n,]+/).map(function(s) { return s.trim(); }).filter(Boolean);
    if (!tools.length) { alert('请输入至少一个工具名称'); return; }

    var btn = this;
    btn.disabled = true;
    document.getElementById('progressCard').style.display = 'block';
    document.getElementById('taskList').innerHTML = '';
    document.getElementById('resultContainer').innerHTML = '';

    try {
      var batchRes = await fetch(API_BASE + '/api/v1/tools/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tools: tools })
      });
      if (!batchRes.ok) throw new Error('创建工具失败: ' + (await batchRes.text()) || batchRes.status);
      var batch = await batchRes.json();
      var toolIds = batch.tools.map(function(t) { return t.id; });

      var scanRes = await fetch(API_BASE + '/api/v1/scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_ids: toolIds })
      });
      if (!scanRes.ok) throw new Error('启动扫描失败: ' + (await scanRes.text()) || scanRes.status);
      var scan = await scanRes.json();
      var tasks = scan.tasks || [];
      var reportIds = {};
      var fetchedReports = {};

      function renderTasks() {
        document.getElementById('taskList').innerHTML = tasks.map(function(t) {
          var statusText = t.status === 'completed' ? '已完成' : t.status === 'failed' ? '失败' : '扫描中...';
          return '<div class="task-item ' + (t.status === 'completed' ? 'done' : t.status === 'failed' ? 'error' : 'pending') + '">' +
            '<span class="task-name">' + escapeHtml(t.tool_name) + '</span>' +
            '<span class="task-status">' + statusText + '</span></div>';
        }).join('');
      }
      renderTasks();

      var doneCount = 0;
      var interval = setInterval(async function() {
        for (var i = 0; i < tasks.length; i++) {
          var t = tasks[i];
          if (t.status === 'completed' || t.status === 'failed') continue;
          try {
            var stRes = await fetch(API_BASE + '/api/v1/scan/status/' + t.tool_id);
            if (!stRes.ok) continue;
            var st = await stRes.json();
            t.status = st.status;
            if (st.result && st.result.report_id) reportIds[t.tool_id] = st.result.report_id;
            if (t.status === 'completed') doneCount++;
            if (t.status === 'failed') doneCount++;
          } catch (_) {}
        }
        renderTasks();

        for (var tid in reportIds) {
          if (fetchedReports[tid]) continue;
          var rid = reportIds[tid];
          try {
            var rRes = await fetch(API_BASE + '/api/v1/reports/' + rid);
            if (!rRes.ok) continue;
            var report = await rRes.json();
            fetchedReports[tid] = true;
            document.getElementById('resultContainer').insertAdjacentHTML('beforeend', renderResult(report));
          } catch (_) {}
        }

        if (doneCount >= tasks.length) {
          clearInterval(interval);
          for (var tid2 in reportIds) {
            if (fetchedReports[tid2]) continue;
            var rid2 = reportIds[tid2];
            try {
              var rRes2 = await fetch(API_BASE + '/api/v1/reports/' + rid2);
              if (!rRes2.ok) continue;
              var report2 = await rRes2.json();
              document.getElementById('resultContainer').insertAdjacentHTML('beforeend', renderResult(report2));
            } catch (_) {}
            fetchedReports[tid2] = true;
          }
        }
      }, 2000);
    } catch (e) {
      document.getElementById('taskList').innerHTML = '<div class="task-item error">错误: ' + escapeHtml(e.message) + '</div>';
    }
    btn.disabled = false;
  };
}
