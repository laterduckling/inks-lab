// ═══════════════════════════════════════════════════════
// INK'S LAB — Parent Report Email Script
// Paste this entire file into Google Apps Script
// Setup instructions are at the bottom of this file
// ═══════════════════════════════════════════════════════

// >>> CHANGE THESE TO YOUR REAL EMAIL ADDRESSES <<<
const EMAILS = ['your@gmail.com', 'wife@gmail.com'];

// Receive session report from the app (POST webhook)
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    // Store session for weekly digest
    const store = PropertiesService.getScriptProperties();
    const sessions = JSON.parse(store.getProperty('sessions') || '[]');
    sessions.push({ ...data, receivedAt: new Date().toISOString() });
    // Keep last 50 sessions
    if (sessions.length > 50) sessions.splice(0, sessions.length - 50);
    store.setProperty('sessions', JSON.stringify(sessions));

    // Send immediate session email
    sendSessionEmail(data);

    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Immediate email after each session
function sendSessionEmail(data) {
  const lang = data.lang === 'FR' ? 'fr' : 'en';
  const date = new Date(data.date);
  const dateStr = date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  const flag = data.lang === 'FR' ? '\ud83c\uddeb\ud83c\uddf7' : '\ud83c\uddfa\ud83c\uddf8';

  const subject = `\ud83d\udc19 Ink's Lab \u2014 ${flag} ${data.subject || 'Homework'} (${dateStr})`;

  const completed = (data.completed || []).map(c => `  \u2705 ${c}`).join('\n');
  const coinsLine = data.minecoins != null ? `\u26cf\ufe0f Minecoins earned: +${data.coinsEarned} (total: ${data.minecoins})` : '';

  const body = `
Ink's Lab \u2014 Session Report
${'='.repeat(40)}

${flag} Language: ${data.lang === 'FR' ? 'French' : 'English'}
\ud83d\udcda Subject: ${data.subject || 'Homework'}
\u23f1\ufe0f Duration: ${data.minutes || '?'} minutes
\ud83d\udcdd Tasks: ${data.tasksCount || '?'}
\ud83d\udca1 Hints used: ${data.totalHints || 0}
${coinsLine}

${data.headline ? `\ud83d\udce3 ${data.headline}` : ''}

${completed ? `Completed:\n${completed}` : ''}

${data.shone ? `\u2b50 Shone at: ${data.shone}` : ''}
${data.struggled ? `\ud83d\udd04 Needs work: ${data.struggled}` : ''}
${data.tip ? `\ud83d\udca1 Tip: ${data.tip}` : ''}
${data.insight ? `\ud83e\udde0 Insight: ${data.insight}` : ''}

\ud83e\uddf1 Station: ${data.blocks || 0} / 30 blocks
\ud83c\udccf Cards collected: ${data.cardsCount || 0}
${'='.repeat(40)}
Sent automatically from Ink's Lab
`.trim();

  EMAILS.forEach(email => {
    MailApp.sendEmail({
      to: email,
      subject: subject,
      body: body
    });
  });
}

// Weekly digest — runs every Sunday via time trigger
function sendWeeklyDigest() {
  const store = PropertiesService.getScriptProperties();
  const allSessions = JSON.parse(store.getProperty('sessions') || '[]');

  // Filter to last 7 days
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const week = allSessions.filter(s => new Date(s.receivedAt || s.date).getTime() > weekAgo);

  if (week.length === 0) {
    EMAILS.forEach(email => {
      MailApp.sendEmail({
        to: email,
        subject: "\ud83d\udc19 Ink's Lab \u2014 Weekly Summary (no sessions this week)",
        body: "No homework sessions were completed this week.\n\nKeep exploring, little astronaut! \ud83d\ude80"
      });
    });
    return;
  }

  const totalMins = week.reduce((a, s) => a + (s.minutes || 0), 0);
  const totalHints = week.reduce((a, s) => a + (s.totalHints || 0), 0);
  const totalCoins = week.reduce((a, s) => a + (s.coinsEarned || 0), 0);
  const subjects = {};
  week.forEach(s => { if (s.subject) subjects[s.subject] = (subjects[s.subject] || 0) + 1; });
  const subjectList = Object.entries(subjects).map(([k, v]) => `  ${k}: ${v} session${v > 1 ? 's' : ''}`).join('\n');

  const hardSessions = week.filter(s => (s.avgHints || 0) > 2);
  const hardSubjects = {};
  hardSessions.forEach(s => { if (s.subject) hardSubjects[s.subject] = (hardSubjects[s.subject] || 0) + 1; });
  const hardestEntry = Object.entries(hardSubjects).sort((a, b) => b[1] - a[1])[0];

  const lastSession = week[week.length - 1];

  const body = `
Ink's Lab \u2014 Weekly Summary
${'='.repeat(40)}

\ud83d\udcc5 Sessions this week: ${week.length}
\u23f1\ufe0f Total time: ${totalMins} minutes
\ud83d\udca1 Total hints: ${totalHints}
\u26cf\ufe0f Minecoins earned this week: ${totalCoins}
\u26cf\ufe0f Minecoins balance: ${lastSession.minecoins || '?'}

Subjects:
${subjectList}

${hardestEntry ? `\u26a0\ufe0f Needs extra support: ${hardestEntry[0]} (${hardestEntry[1]} hard session${hardestEntry[1] > 1 ? 's' : ''})` : '\u2705 No major difficulty patterns this week!'}

\ud83e\uddf1 Station progress: ${lastSession.blocks || 0} / 30 blocks
\ud83c\udccf Cards collected: ${lastSession.cardsCount || 0}
${'='.repeat(40)}
Sent automatically from Ink's Lab
`.trim();

  EMAILS.forEach(email => {
    MailApp.sendEmail({
      to: email,
      subject: `\ud83d\udc19 Ink's Lab \u2014 Weekly Summary (${week.length} session${week.length > 1 ? 's' : ''})`,
      body: body
    });
  });
}

// Daily digest — runs Mon-Thu at 9pm via time trigger
function sendDailyDigest() {
  // Only run Mon-Thu (1=Mon, 4=Thu)
  const today = new Date().getDay();
  if (today === 0 || today === 5 || today === 6) return; // skip Fri/Sat/Sun

  const store = PropertiesService.getScriptProperties();
  const allSessions = JSON.parse(store.getProperty('sessions') || '[]');

  // Filter to today's sessions only
  const now = new Date();
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const todaySessions = allSessions.filter(s => new Date(s.receivedAt || s.date).getTime() >= startOfDay);

  const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

  if (todaySessions.length === 0) {
    EMAILS.forEach(email => {
      MailApp.sendEmail({
        to: email,
        subject: `\ud83d\udc19 Ink's Lab \u2014 ${dateStr} (no session today)`,
        body: `No homework session was completed today (${dateStr}).\n\nMaybe tomorrow! \ud83d\ude80`
      });
    });
    return;
  }

  const totalMins = todaySessions.reduce((a, s) => a + (s.minutes || 0), 0);
  const totalHints = todaySessions.reduce((a, s) => a + (s.totalHints || 0), 0);
  const totalCoins = todaySessions.reduce((a, s) => a + (s.coinsEarned || 0), 0);
  const lastSession = todaySessions[todaySessions.length - 1];

  const sessionDetails = todaySessions.map((s, i) => {
    const flag = s.lang === 'FR' ? '\ud83c\uddeb\ud83c\uddf7' : '\ud83c\uddfa\ud83c\uddf8';
    return `${flag} ${s.subject || 'Homework'} \u2014 ${s.minutes || '?'} min, ${s.totalHints || 0} hints, +${s.coinsEarned || 0} coins${s.headline ? '\n   ' + s.headline : ''}${s.struggled ? '\n   \ud83d\udd04 Needs work: ' + s.struggled : ''}${s.shone ? '\n   \u2b50 Shone at: ' + s.shone : ''}`;
  }).join('\n\n');

  const body = `
Ink's Lab \u2014 Daily Report (${dateStr})
${'='.repeat(40)}

Sessions today: ${todaySessions.length}
Total time: ${totalMins} minutes
Hints used: ${totalHints}
Minecoins earned: +${totalCoins} (balance: ${lastSession.minecoins || '?'})

${sessionDetails}

\ud83e\uddf1 Station: ${lastSession.blocks || 0} / 30 blocks
\ud83c\udccf Cards: ${lastSession.cardsCount || 0}
${'='.repeat(40)}
Sent automatically from Ink's Lab
`.trim();

  EMAILS.forEach(email => {
    MailApp.sendEmail({
      to: email,
      subject: `\ud83d\udc19 Ink's Lab \u2014 ${dateStr} (${todaySessions.length} session${todaySessions.length > 1 ? 's' : ''})`,
      body: body
    });
  });
}

// ═══════════════════════════════════════════════════════
// SETUP INSTRUCTIONS
// ═══════════════════════════════════════════════════════
//
// 1. Go to https://script.google.com
// 2. Click "+ New project"
// 3. Delete the default code and paste this entire file
// 4. IMPORTANT: Change the EMAILS array at the top to your real emails
// 5. Click "Deploy" > "New deployment"
// 6. Click the gear icon next to "Select type" > choose "Web app"
// 7. Set:
//    - Description: "Ink's Lab Reports"
//    - Execute as: "Me"
//    - Who has access: "Anyone"
// 8. Click "Deploy"
// 9. Click "Authorize access" and allow permissions
// 10. Copy the Web app URL — it looks like:
//     https://script.google.com/macros/s/XXXXX.../exec
// 11. That URL goes into the Ink's Lab app (I'll tell you where)
//
// For the daily digest (Mon-Thu 9pm):
// 12. In the Apps Script editor, click the clock icon (Triggers) on the left
// 13. Click "+ Add Trigger"
// 14. Set:
//     - Function: sendDailyDigest
//     - Event source: Time-driven
//     - Type: Day timer
//     - Time: 9pm to 10pm
// 15. Click Save
//
// For the weekly digest:
// 16. Click "+ Add Trigger" again
// 17. Set:
//     - Function: sendWeeklyDigest
//     - Event source: Time-driven
//     - Type: Week timer
//     - Day: Sunday
//     - Time: 6pm to 7pm (or whenever you want)
// 15. Click Save
//
// That's it! You'll get:
// - An email after every homework session (automatic)
// - A weekly summary every Sunday evening (automatic)
// ═══════════════════════════════════════════════════════
