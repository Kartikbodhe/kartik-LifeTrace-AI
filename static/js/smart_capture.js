/**
 * LifeTrace AI — Smart Capture Component
 * Fast natural language parser preview & confirm flow
 */

document.addEventListener('DOMContentLoaded', () => {
  const inputEl = document.getElementById('smartInput');
  const analyzeBtn = document.getElementById('smartAnalyzeBtn');
  const previewContainer = document.getElementById('smartPreviewContainer');
  const previewCard = document.getElementById('smartPreviewCard');
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

  if (!inputEl || !analyzeBtn || !previewContainer) return;

  // Example chip click helper
  window.useExample = function(text) {
    inputEl.value = text;
    analyzeText();
  };

  analyzeBtn.addEventListener('click', analyzeText);

  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      analyzeText();
    }
  });

  function analyzeText() {
    const text = inputEl.value.trim();
    if (!text) return;

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';

    fetch('/smart-capture/parse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || ''
      },
      body: JSON.stringify({ text: text })
    })
      .then(res => res.json())
      .then(res => {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '✨ Analyze & Preview';

        if (res.success && res.data) {
          renderPreview(res.data);
        } else {
          alert(res.error || 'Unable to parse input.');
        }
      })
      .catch(err => {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '✨ Analyze & Preview';
        console.error('Smart capture error:', err);
      });
  }

  function renderPreview(data) {
    previewContainer.style.display = 'block';

    const type = data.type || 'task';
    const isPayment = type === 'payment';
    const isPromise = type === 'promise';
    const isMemory = type === 'memory';

    let extraFieldsHtml = '';

    if (isPayment) {
      extraFieldsHtml = `
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Person Name</label>
            <input type="text" name="person_name" class="form-control" value="${escapeHtml(data.person_name || 'Rahul')}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Amount (₹)</label>
            <input type="number" step="0.01" name="amount" class="form-control" value="${escapeHtml(data.amount || '0.00')}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Type</label>
            <select name="transaction_type" class="form-control">
              <option value="LENT" ${data.transaction_type === 'LENT' ? 'selected' : ''}>Money Lent (to someone)</option>
              <option value="BORROWED" ${data.transaction_type === 'BORROWED' ? 'selected' : ''}>Money Borrowed (from someone)</option>
            </select>
          </div>
        </div>
      `;
    } else if (isPromise) {
      extraFieldsHtml = `
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Person or Organization</label>
            <input type="text" name="person_or_org" class="form-control" value="${escapeHtml(data.person_or_org || 'Collaborator')}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Priority</label>
            <select name="priority" class="form-control">
              <option value="Low" ${data.priority === 'Low' ? 'selected' : ''}>Low</option>
              <option value="Medium" ${data.priority === 'Medium' || !data.priority ? 'selected' : ''}>Medium</option>
              <option value="High" ${data.priority === 'High' ? 'selected' : ''}>High</option>
            </select>
          </div>
        </div>
      `;
    } else if (type === 'task') {
      extraFieldsHtml = `
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Priority</label>
            <select name="priority" class="form-control">
              <option value="Low" ${data.priority === 'Low' ? 'selected' : ''}>Low</option>
              <option value="Medium" ${data.priority === 'Medium' || !data.priority ? 'selected' : ''}>Medium</option>
              <option value="High" ${data.priority === 'High' ? 'selected' : ''}>High</option>
            </select>
          </div>
          <div class="form-group" style="display: flex; align-items: flex-end; padding-bottom: 0.5rem;">
            <label class="form-check">
              <input type="checkbox" name="create_reminder" value="1" checked>
              <span>Schedule in-app reminder for due date</span>
            </label>
          </div>
        </div>
      `;
    }

    const html = `
      <form action="/smart-capture/confirm" method="POST">
        <input type="hidden" name="csrf_token" value="${csrfToken || ''}">
        <input type="hidden" name="type" value="${type}">

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.75rem;">
          <div>
            <span class="badge" style="background: rgba(99,102,241,0.2); color: #a5b4fc; font-size: 0.8rem; text-transform: uppercase;">
              Detected Intent: ${type}
            </span>
            <span style="font-size: 0.75rem; color: var(--text-faint); margin-left: 0.5rem;">
              Confidence: ${Math.round((data.confidence || 0.8) * 100)}%
            </span>
          </div>
          <span style="font-size: 0.72rem; color: var(--text-faint); background: rgba(255,255,255,0.04); padding: 0.2rem 0.5rem; border-radius: 4px;">
            ${escapeHtml(data.engine || 'Pattern Engine')}
          </span>
        </div>

        <div class="form-group">
          <label class="form-label">Title / Main Objective</label>
          <input type="text" name="title" class="form-control" value="${escapeHtml(data.title || '')}" required>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Category</label>
            <input type="text" name="category" class="form-control" value="${escapeHtml(data.category || 'General')}">
          </div>
          <div class="form-group">
            <label class="form-label">Suggested Date & Time</label>
            <input type="text" name="date" class="form-control" value="${escapeHtml(data.suggested_datetime || data.suggested_date || '')}" placeholder="YYYY-MM-DD HH:MM">
          </div>
        </div>

        ${extraFieldsHtml}

        <div class="form-group">
          <label class="form-label">Details / Original Expression</label>
          <textarea name="description" class="form-control" rows="2">${escapeHtml(data.description || data.raw_input || '')}</textarea>
        </div>

        <div style="display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="document.getElementById('smartPreviewContainer').style.display='none'">Cancel</button>
          <button type="submit" class="btn btn-primary">✅ Confirm & Save to LifeTrace</button>
        </div>
      </form>
    `;

    previewCard.innerHTML = html;
    previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
});
