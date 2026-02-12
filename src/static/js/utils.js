/**
 * 公共工具函数
 * Shared utility functions
 */

var API_BASE = '';

function escapeHtml(s) {
  if (s == null) return '';
  var div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function csvEscape(value) {
  if (value == null) return '';
  var s = String(value).replace(/"/g, '""');
  return /[",\r\n]/.test(s) ? ('"' + s + '"') : s;
}

/**
 * 渲染许可证/公司/商用限制/替代方案的公共 HTML 片段
 */
function renderComplianceSections(lic, comp, comm, alts) {
  lic = lic || {};
  comp = comp || {};
  comm = comm || {};
  alts = alts || [];

  var chinaText = comp.china_office ? '<span class="china-yes">\u221a \u6709\u4e2d\u56fd\u5206\u516c\u53f8\u6216\u670d\u52a1</span>' : '\u65e0';
  var needLicense = comm.commercial_license_required === true;
  var freeCommercial = comm.free_for_commercial === true;
  var needLicenseHtml = needLicense ? '<span class="no">\u662f</span>' : '<span class="yes">\u5426</span>';
  var freeCommercialHtml = freeCommercial ? '<span class="yes">\u662f</span>' : '<span class="no">\u5426</span>';

  var altHtml = '';
  for (var i = 0; i < alts.length; i++) {
    var a = alts[i];
    var name = a.name || '\u672a\u547d\u540d';
    var typeLicense = [a.type, a.license].filter(Boolean).join(' | \u8bb8\u53ef\u8bc1: ') || '\u5f00\u6e90';
    var adv = a.advantages || '';
    var scene = a.use_case || a.use_scenario || '';
    altHtml += '<div class="alt-block"><h4>' + escapeHtml(name) + '</h4>' +
      '<div class="meta">' + escapeHtml(typeLicense) + '</div>' +
      (adv ? '<div class="desc"><strong>\u4f18\u52bf\uff1a</strong>' + escapeHtml(adv) + '</div>' : '') +
      (scene ? '<div class="desc" style="margin-top:6px"><strong>\u9002\u7528\u573a\u666f\uff1a</strong>' + escapeHtml(scene) + '</div>' : '') +
      '</div>';
  }
  if (!altHtml) altHtml = '<div class="desc" style="color:var(--muted)">\u6682\u65e0\u66ff\u4ee3\u65b9\u6848</div>';

  return '<div class="result-section">' +
    '<h3>\u4f7f\u7528\u8bb8\u53ef/\u5f00\u6e90\u534f\u8bae</h3>' +
    '<div class="row"><span class="label">\u7c7b\u578b\uff1a</span>' + escapeHtml(lic.license_type || '\u672a\u77e5') + '</div>' +
    '<div class="row"><span class="label">\u7248\u672c\uff1a</span>' + escapeHtml(lic.license_version || '\u2014') + '</div>' +
    '<div class="row"><span class="label">\u6a21\u5f0f\uff1a</span>' + escapeHtml(lic.license_mode || '\u2014') + '</div>' +
    '</div>' +
    '<div class="result-section">' +
    '<h3>\u516c\u53f8\u4fe1\u606f</h3>' +
    '<div class="row"><span class="label">\u516c\u53f8\u540d\u79f0\uff1a</span>' + escapeHtml(comp.company_name || '\u2014') + '</div>' +
    '<div class="row"><span class="label">\u6240\u5c5e\u56fd\u5bb6\uff1a</span>' + escapeHtml(comp.company_country || '\u2014') + '</div>' +
    '<div class="row"><span class="label">\u603b\u90e8\uff1a</span>' + escapeHtml(comp.company_headquarters || '\u2014') + '</div>' +
    '<div class="row"><span class="label">\u4e2d\u56fd\u670d\u52a1\uff1a</span>' + chinaText + '</div>' +
    '</div>' +
    '<div class="result-section">' +
    '<h3>\u5546\u7528\u7528\u6237\u4f7f\u7528\u9650\u5236</h3>' +
    '<div class="row"><span class="label">\u9700\u8d2d\u4e70License\uff1a</span>' + needLicenseHtml + '</div>' +
    '<div class="row"><span class="label">\u5141\u8bb8\u514d\u8d39\u5546\u7528\uff1a</span>' + freeCommercialHtml + '</div>' +
    (comm.restrictions ? '<div class="row"><span class="label">\u9650\u5236\u8bf4\u660e\uff1a</span>' + escapeHtml(comm.restrictions) + '</div>' : '') +
    (comm.user_limit ? '<div class="row"><span class="label">\u7528\u6237\u9650\u5236\uff1a</span>' + escapeHtml(comm.user_limit) + '</div>' : '') +
    (comm.feature_restrictions ? '<div class="row"><span class="label">\u529f\u80fd\u9650\u5236\uff1a</span>' + escapeHtml(comm.feature_restrictions) + '</div>' : '') +
    '</div>' +
    '<div class="result-section">' +
    '<h3>\u53ef\u66ff\u4ee3\u65b9\u6848</h3>' + altHtml +
    '</div>';
}
