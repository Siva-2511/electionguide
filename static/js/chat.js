'use strict';

// ── Country Quick Facts ────────────────────────────────────────────────────
const FACTS_DATA = {
  india: {
    title: '🇮🇳 India · தமிழ் தேர்தல் · भारत चुनाव — Quick Facts',
    facts: [
      ['Conducted by', 'Election Commission of India'],
      ['Min Voting Age', '18 years'],
      ['Total Voters', '969 Million'],
      ['Voting Method', 'EVM + VVPAT'],
      ['TN 2026 Result', 'May 4, 2026'],
      ['Voter Portal', '<a href="https://voters.eci.gov.in" target="_blank" rel="noopener noreferrer">voters.eci.gov.in</a>'],
      ['ECI Website', '<a href="https://www.eci.gov.in" target="_blank" rel="noopener noreferrer">eci.gov.in</a>'],
    ]
  },
  us: {
    title: '🇺🇸 United States — Quick Facts',
    facts: [
      ['Conducted by', 'Federal Election Commission (FEC)'],
      ['Min Voting Age', '18 years'],
      ['Eligible Voters', '~240 Million'],
      ['Voting System', 'First Past The Post'],
      ['Next Election', 'November 2026 (Midterms)'],
      ['Register at', '<a href="https://vote.gov" target="_blank" rel="noopener noreferrer">vote.gov</a>'],
      ['Official Site', '<a href="https://www.fec.gov" target="_blank" rel="noopener noreferrer">fec.gov</a>'],
    ]
  },
  uk: {
    title: '🇬🇧 United Kingdom — Quick Facts',
    facts: [
      ['Conducted by', 'Electoral Commission'],
      ['Min Voting Age', '18 years'],
      ['Total Seats', '650 (House of Commons)'],
      ['Voting System', 'First Past The Post'],
      ['Last Election', 'July 4, 2024'],
      ['Next Election', '~2029'],
      ['Register at', '<a href="https://gov.uk/register-to-vote" target="_blank" rel="noopener noreferrer">gov.uk/register-to-vote</a>'],
    ]
  },
  australia: {
    title: '🇦🇺 Australia — Quick Facts',
    facts: [
      ['Conducted by', 'Australian Electoral Commission'],
      ['Min Voting Age', '18 years'],
      ['Voting', '⚠️ Compulsory (fine: AUD $20)'],
      ['Voting System', 'Preferential'],
      ['Total Seats', '151 (House of Reps)'],
      ['Last Election', 'May 3, 2025'],
      ['Enrol at', '<a href="https://aec.gov.au" target="_blank" rel="noopener noreferrer">aec.gov.au</a>'],
    ]
  },
  canada: {
    title: '🇨🇦 Canada — Quick Facts',
    facts: [
      ['Conducted by', 'Elections Canada'],
      ['Min Voting Age', '18 years'],
      ['Total Seats', '343 (House of Commons)'],
      ['Voting System', 'First Past The Post'],
      ['Last Election', 'April 28, 2025'],
      ['Next Election', '~2029'],
      ['Register at', '<a href="https://elections.ca" target="_blank" rel="noopener noreferrer">elections.ca</a>'],
    ]
  }
};

const COUNTRIES = {
  india: {
    flag: '🇮🇳', label: 'India',
    title: 'India Elections · தமிழ் தேர்தல் · भारत चुनाव',
    sub: 'Election Commission of India (ECI) · eci.gov.in · Non-partisan guide',
    chatSub: 'வணக்கம்! Namaste! 🙏 Helping you navigate Indian elections.',
    eligDesc: 'Enter your age to check if you can vote in India.',
    timelineUrl: '/timeline?country=india',
    electionDefault: { day: '2029-04-01', name: 'India General Election' },
    welcome: [
      "வணக்கம்! Namaste! 🙏 I'm ElectionGuide, your India election assistant.",
      "I can help you with:",
      "✅ Voter eligibility (18+) · 📝 ECI voter registration · 🗳️ EVM voting · 📅 Election schedule",
      "Visit eci.gov.in to register. What would you like to know?"
    ],
    bodyClass: 'country-india',
    showCitizen: false,
  },
  us: {
    flag: '🇺🇸', label: 'United States',
    title: 'United States Elections',
    sub: 'Powered by Google Civic Information API · Non-partisan guide',
    chatSub: 'Helping you navigate US elections. Ask me anything!',
    eligDesc: 'Enter your age to check if you can vote in the US.',
    timelineUrl: '/timeline?country=us',
    electionDefault: { day: '2026-11-03', name: 'US Election Day 2026' },
    welcome: [
      "Hello! I'm ElectionGuide, your non-partisan US election assistant.",
      "I can help you with:",
      "✅ Voter eligibility · 📝 Registration at vote.gov · 📍 Polling locations · 📅 Election dates",
      "What would you like to know?"
    ],
    bodyClass: 'country-us',
    showCitizen: true,
  },
  uk: {
    flag: '🇬🇧', label: 'United Kingdom',
    title: 'United Kingdom Elections',
    sub: 'Electoral Commission · electoralcommission.org.uk',
    chatSub: 'Helping you navigate UK elections.',
    eligDesc: 'Enter your age to check if you can vote in the UK.',
    timelineUrl: '/timeline?country=uk',
    electionDefault: { day: '2029-05-01', name: 'UK General Election 2029' },
    welcome: [
      "Hello! I'm ElectionGuide, your UK election assistant.",
      "I can help you with registration (gov.uk/register-to-vote), voting eligibility, and polling stations.",
      "What would you like to know?"
    ],
    bodyClass: 'country-uk',
    showCitizen: true,
  },
  australia: {
    flag: '🇦🇺', label: 'Australia',
    title: 'Australian Elections',
    sub: 'Australian Electoral Commission (AEC) · aec.gov.au',
    chatSub: 'Helping you navigate Australian elections. Voting is compulsory!',
    eligDesc: 'Enter your age to check if you can vote in Australia.',
    timelineUrl: '/timeline?country=australia',
    electionDefault: { day: '2028-05-01', name: 'Australian Federal Election 2028' },
    welcome: [
      "G'day! I'm ElectionGuide, your Australia election assistant.",
      "Voting in Australia is compulsory for citizens 18+. Enrol at aec.gov.au.",
      "What would you like to know?"
    ],
    bodyClass: 'country-aus',
    showCitizen: true,
  },
  canada: {
    flag: '🇨🇦', label: 'Canada',
    title: 'Canadian Elections',
    sub: 'Elections Canada · elections.ca',
    chatSub: 'Helping you navigate Canadian elections.',
    eligDesc: 'Enter your age to check if you can vote in Canada.',
    timelineUrl: '/timeline?country=canada',
    electionDefault: { day: '2029-10-01', name: 'Canadian Federal Election 2029' },
    welcome: [
      "Hello! I'm ElectionGuide, your Canada election assistant.",
      "I can help you with voter registration (elections.ca) and voting information.",
      "What would you like to know?"
    ],
    bodyClass: 'country-can',
    showCitizen: true,
  },
};

// ── State ──────────────────────────────────────────────────────────────────
const state = { country: 'india', isLoading: false, electionDay: '', electionName: '' };

// ── DOM Refs ───────────────────────────────────────────────────────────────
const chatForm        = document.getElementById('chat-form');
const chatInput       = document.getElementById('chat-input');
const chatMessages    = document.getElementById('chat-messages');
const addressInput    = document.getElementById('address-input');
const eligibilityForm = document.getElementById('eligibility-form');
const eligResult      = document.getElementById('eligibility-result');
const checklistBtn    = document.getElementById('btn-get-checklist');
const checklistResult = document.getElementById('checklist-result');
const reminderBtn     = document.getElementById('btn-add-reminder');
const reminderResult  = document.getElementById('reminder-result');
const voterStatus     = document.getElementById('voter-status');
const bannerFlag      = document.getElementById('banner-flag');
const bannerTitle     = document.getElementById('banner-title');
const bannerSub       = document.getElementById('banner-subtitle');
const countryBanner   = document.getElementById('country-banner');
const chatSubtitle    = document.getElementById('chat-subtitle');
const eligDesc        = document.getElementById('elig-desc');
const infoPanel       = document.getElementById('india-info-panel');
const citizenGroup    = document.getElementById('citizen-group');
const navTimeline     = document.getElementById('nav-timeline');
const btnTimeline     = document.getElementById('btn-view-timeline');

// ── Country Switch ─────────────────────────────────────────────────────────
function switchCountry(country) {
  if (!COUNTRIES[country]) return;
  state.country = country;
  const cfg = COUNTRIES[country];

  // Update body class for CSS variable switching
  document.body.className = cfg.bodyClass;

  // Update all tabs
  document.querySelectorAll('.ctab').forEach(btn => {
    const isActive = btn.dataset.country === country;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive.toString());
  });

  // Banner
  if (bannerFlag) {
    bannerFlag.textContent = cfg.flag;
    bannerFlag.style.animation = 'none';
    requestAnimationFrame(() => { bannerFlag.style.animation = 'fadeUp .4s ease'; });
  }
  if (bannerTitle) bannerTitle.textContent = cfg.title;
  if (bannerSub) bannerSub.textContent = cfg.sub;

  // Chat
  if (chatSubtitle) chatSubtitle.textContent = cfg.chatSub;
  if (eligDesc) eligDesc.textContent = cfg.eligDesc;

  // Citizenship field — hide for India (citizenship ≡ registration check)
  if (citizenGroup) citizenGroup.style.display = cfg.showCitizen ? '' : 'none';

  // Timeline links
  if (navTimeline) navTimeline.href = cfg.timelineUrl;
  if (btnTimeline) btnTimeline.href = cfg.timelineUrl;

  // Info panel — show for ALL countries with correct facts
  if (infoPanel) {
    const fd = FACTS_DATA[country];
    if (fd) {
      const titleEl = document.getElementById('facts-title');
      const gridEl = document.getElementById('facts-grid');
      if (titleEl) titleEl.textContent = fd.title;
      if (gridEl) {
        gridEl.innerHTML = fd.facts.map(([label, val]) =>
          `<div class="fact-item"><span class="fact-label">${label}</span><span class="fact-val">${val}</span></div>`
        ).join('');
      }
    }
    infoPanel.style.display = '';
  }

  // Redraw chart for this country
  if (typeof window.drawCountryChart === 'function') {
    window.drawCountryChart(country);
  }

  // Reset chat with welcome message
  chatMessages.innerHTML = '';
  addWelcome(cfg.welcome, cfg.flag);

  // Reset election defaults
  state.electionDay = cfg.electionDefault.day;
  state.electionName = cfg.electionDefault.name;
}

// ── Init country tabs ──────────────────────────────────────────────────────
document.querySelectorAll('.ctab').forEach(btn => {
  btn.addEventListener('click', () => {
    switchCountry(btn.dataset.country);
    // Close mobile menu if open
    const mob = document.getElementById('nav-mobile-menu');
    if (mob && !mob.classList.contains('hidden')) {
      mob.classList.add('hidden');
      const hb = document.getElementById('nav-hamburger');
      if (hb) hb.setAttribute('aria-expanded', 'false');
    }
  });
});

// ── Helpers ────────────────────────────────────────────────────────────────
function esc(t) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(t));
  return d.innerHTML;
}

function formatReply(text) {
  if (!text) return '';
  if (text.includes('•')) {
    const items = text.split('\n').filter(l => l.trim())
      .map(l => `<li>${esc(l.replace(/^•\s*/, '').trim())}</li>`).join('');
    return `<ul>${items}</ul>`;
  }
  if (/^\d+\./.test(text.trim())) {
    const items = text.split('\n').filter(l => l.trim())
      .map(l => `<li>${esc(l.replace(/^\d+\.\s*/, ''))}</li>`).join('');
    return `<ol>${items}</ol>`;
  }
  return text.split('\n').filter(l => l.trim()).map(l => `<p>${esc(l)}</p>`).join('');
}

function scrollBottom() { chatMessages.scrollTop = chatMessages.scrollHeight; }

// ── Message Rendering ──────────────────────────────────────────────────────
function makeMsg(role, html) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
  wrap.setAttribute('role', 'article');
  wrap.setAttribute('aria-label', `${role === 'user' ? 'Your' : 'Assistant'} message`);

  const av = document.createElement('div');
  av.className = 'message-avatar';
  av.setAttribute('aria-hidden', 'true');
  av.textContent = role === 'user' ? '👤' : COUNTRIES[state.country]?.flag || '🗳️';

  const ct = document.createElement('div');
  ct.className = 'message-content';
  ct.innerHTML = html;

  wrap.appendChild(av);
  wrap.appendChild(ct);
  chatMessages.appendChild(wrap);
  scrollBottom();
  return wrap;
}

function addWelcome(lines, flag) {
  const html = lines.map(l => `<p>${esc(l)}</p>`).join('');
  makeMsg('bot', html);
}

function addUser(msg) { makeMsg('user', `<p>${esc(msg)}</p>`); }
function addBot(text) { makeMsg('bot', formatReply(text)); }

function addLoading() {
  const wrap = makeMsg('bot', '<div class="typing-dots" aria-hidden="true"><span></span><span></span><span></span></div>');
  wrap.id = 'loading-msg';
}
function removeLoading() { const el = document.getElementById('loading-msg'); if (el) el.remove(); }

// ── Chat ───────────────────────────────────────────────────────────────────
async function sendMessage(msg) {
  if (state.isLoading || !msg.trim()) return;
  state.isLoading = true;
  chatInput.disabled = true;
  document.getElementById('btn-send').disabled = true;

  addUser(msg);
  addLoading();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: msg.trim(),
        address: addressInput?.value.trim() || '',
        country: state.country,
        lang: 'en',
      }),
    });
    const data = await res.json();
    removeLoading();

    if (data.success && data.data?.reply) {
      addBot(data.data.reply);
      if (data.data.election_day) {
        state.electionDay = data.data.election_day;
        state.electionName = data.data.election_info?.election_name || state.electionName;
      }
    } else {
      addBot(data.error || 'I could not process that. Please try again.');
    }
  } catch (_) {
    removeLoading();
    addBot('Connection issue. Please check your network and try again.');
  } finally {
    state.isLoading = false;
    chatInput.disabled = false;
    chatInput.value = '';
    document.getElementById('btn-send').disabled = false;
    chatInput.focus();
  }
}

if (chatForm) {
  chatForm.addEventListener('submit', e => {
    e.preventDefault();
    const m = chatInput.value.trim();
    if (m) sendMessage(m);
  });
}

// ── Eligibility ────────────────────────────────────────────────────────────
if (eligibilityForm) {
  eligibilityForm.addEventListener('submit', async e => {
    e.preventDefault();
    const age = document.getElementById('age-input').value;
    const citizen = (document.querySelector('input[name="citizen"]:checked')?.value === 'yes') ?? true;
    eligResult.className = 'result-box';
    eligResult.classList.remove('hidden');
    eligResult.textContent = 'Checking…';
    try {
      const res = await fetch('/eligibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ age: parseInt(age, 10), citizen, country: state.country }),
      });
      const data = await res.json();
      if (data.success && data.data) {
        const d = data.data;
        eligResult.classList.add(d.eligible ? 'success' : 'error');
        eligResult.innerHTML = `<strong>${d.eligible ? '✅ Eligible to vote!' : '❌ Not eligible yet'}</strong><br/>${esc(d.reason || '')}<br/><em>${esc(d.next_step || '')}</em>`;
      } else {
        eligResult.classList.add('error');
        eligResult.textContent = data.error || 'Invalid input.';
      }
    } catch (_) { eligResult.classList.add('error'); eligResult.textContent = 'Try again.'; }
  });
}

// ── Checklist ──────────────────────────────────────────────────────────────
if (checklistBtn) {
  checklistBtn.addEventListener('click', async () => {
    const status = voterStatus?.value || 'unregistered';
    checklistResult.classList.remove('hidden');
    checklistResult.innerHTML = '<p>Loading…</p>';
    try {
      const res = await fetch('/checklist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, country: state.country }),
      });
      const data = await res.json();
      if (data.success && data.data?.steps) {
        const html = data.data.steps.map(s => `
          <div class="checklist-step" role="listitem">
            <div class="step-num">${s.step}</div>
            <div class="step-body"><div class="step-title">${esc(s.title)}</div><div class="step-desc">${esc(s.description)}</div></div>
          </div>`).join('');
        checklistResult.innerHTML = `<div role="list">${html}</div>`;
      } else { checklistResult.innerHTML = '<p>Could not load. Please try again.</p>'; }
    } catch (_) { checklistResult.innerHTML = '<p>Could not load. Please try again.</p>'; }
  });
}

// ── Reminder ───────────────────────────────────────────────────────────────
if (reminderBtn) {
  reminderBtn.addEventListener('click', async () => {
    reminderResult.className = 'result-box';
    reminderResult.classList.remove('hidden');
    reminderResult.textContent = 'Adding reminder…';
    try {
      const res = await fetch('/reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ election_day: state.electionDay, election_name: state.electionName }),
      });
      const data = await res.json();
      if (data.success) { 
        reminderResult.classList.add('success'); 
        reminderResult.innerHTML = `✅ Reminder successfully added to your <a href="${data.data.link}" target="_blank" style="color:white; text-decoration:underline;">Google Calendar</a>!`; 
      }
      else { 
        reminderResult.classList.add('error'); 
        reminderResult.textContent = data.error || 'Sign in first to add a reminder.'; 
      }
    } catch (_) { reminderResult.classList.add('error'); reminderResult.textContent = 'Could not add reminder.'; }
  });
}

// ── Init ───────────────────────────────────────────────────────────────────
switchCountry('india');
