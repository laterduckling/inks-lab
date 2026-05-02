// ═══════════════════════════════════════════════════════
// INK'S WORLD — Parent Report Email Script
// Paste this entire file into Google Apps Script
// Setup instructions are at the bottom of this file
// ═══════════════════════════════════════════════════════

// >>> CHANGE THESE TO YOUR REAL EMAIL ADDRESSES <<<
const EMAILS = ['your@gmail.com', 'wife@gmail.com'];

// >>> TEACHER EMAILS (weekly report, one per language) <<<
const TEACHER_EN = ''; // English teacher email (leave empty to skip)
const TEACHER_FR = ''; // French teacher email (leave empty to skip)
// While testing, you can set these to your own email

// Receive session report OR profile backup from the app (POST webhook)
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const store = PropertiesService.getScriptProperties();

    // Profile backup — store latest snapshot of Jules's progress.
    // The app POSTs this after every completed mission so the data
    // survives device wipes and iOS ITP storage purges.
    //
    // The payload is AES-GCM encrypted on the client: we just store
    // the opaque blob. We can't read it. If you lose the password,
    // the backup is unrecoverable (by design).
    if (data && data.type === 'backup') {
      store.setProperty('latestBackup', JSON.stringify({
        type: 'backup',
        savedAt: data.savedAt || Date.now(),
        envelope: data.envelope || null,   // new encrypted format
        profile: data.profile || null      // legacy plaintext (pre-encryption)
      }));
      return ContentService.createTextOutput(JSON.stringify({ ok: true, kind: 'backup' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // Session report (default) — store for digests + send immediate email.
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

// Serve latest profile backup (GET ?action=restore)
function doGet(e) {
  try {
    const action = e && e.parameter && e.parameter.action;
    if (action === 'restore') {
      const store = PropertiesService.getScriptProperties();
      const raw = store.getProperty('latestBackup');
      if (!raw) {
        return ContentService.createTextOutput(JSON.stringify({ ok: false, reason: 'no-backup' }))
          .setMimeType(ContentService.MimeType.JSON);
      }
      return ContentService.createTextOutput(raw)
        .setMimeType(ContentService.MimeType.JSON);
    }
    return ContentService.createTextOutput(JSON.stringify({ ok: true, status: "Ink's World webhook live" }))
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

  const subject = `\ud83d\udc19 Ink's World \u00b7 Parents \u2014 ${flag} ${data.subject || 'Homework'} (${dateStr})`;

  const completed = (data.completed || []).map(c => `  \u2705 ${c}`).join('\n');
  const coinsLine = data.minecoins != null ? `\u26cf\ufe0f Minecoins earned: +${data.coinsEarned} (total: ${data.minecoins})` : '';

  const body = `
Ink's World \u2014 Session Report
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

\ud83d\udc19 Crew progress: ${data.blocks || 0} verified session${(data.blocks || 0) === 1 ? '' : 's'} (Colossal Squid unlocks at 120)
${'='.repeat(40)}
Sent automatically from Ink's World
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
        subject: "\ud83d\udc19 Ink's World \u00b7 Parents \u2014 Weekly Summary (no sessions this week)",
        body:
          "No homework sessions were completed this week.\n\n"
          + "If it's a holiday week, Jules can still earn crew unlocks via the \ud83d\udcf7 Practice Sheet path on weekends \u2014 a photo of any exercise book counts and unlocks the Dragon-Fire octopus on completion.\n\n"
          + "Keep exploring! \ud83d\udc19"
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
Ink's World \u2014 Weekly Summary
${'='.repeat(40)}

\ud83d\udcc5 Sessions this week: ${week.length}
\u23f1\ufe0f Total time: ${totalMins} minutes
\ud83d\udca1 Total hints: ${totalHints}
\u26cf\ufe0f Minecoins earned this week: ${totalCoins}
\u26cf\ufe0f Minecoins balance: ${lastSession.minecoins || '?'}

Subjects:
${subjectList}

${hardestEntry ? `\u26a0\ufe0f Needs extra support: ${hardestEntry[0]} (${hardestEntry[1]} hard session${hardestEntry[1] > 1 ? 's' : ''})` : '\u2705 No major difficulty patterns this week!'}

\ud83d\udc19 Crew progress: ${lastSession.blocks || 0} verified session${(lastSession.blocks || 0) === 1 ? '' : 's'} (Colossal Squid unlocks at 120)
${'='.repeat(40)}
Sent automatically from Ink's World
`.trim();

  EMAILS.forEach(email => {
    MailApp.sendEmail({
      to: email,
      subject: `\ud83d\udc19 Ink's World \u00b7 Parents \u2014 Weekly Summary (${week.length} session${week.length > 1 ? 's' : ''})`,
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
        subject: `\ud83d\udc19 Ink's World \u00b7 Parents \u2014 ${dateStr} (no session today)`,
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
Ink's World \u2014 Daily Report (${dateStr})
${'='.repeat(40)}

Sessions today: ${todaySessions.length}
Total time: ${totalMins} minutes
Hints used: ${totalHints}
Minecoins earned: +${totalCoins} (balance: ${lastSession.minecoins || '?'})

${sessionDetails}

\ud83d\udc19 Crew progress: ${lastSession.blocks || 0} verified session${(lastSession.blocks || 0) === 1 ? '' : 's'} (Colossal Squid unlocks at 120)
${'='.repeat(40)}
Sent automatically from Ink's World
`.trim();

  EMAILS.forEach(email => {
    MailApp.sendEmail({
      to: email,
      subject: `\ud83d\udc19 Ink's World \u00b7 Parents \u2014 ${dateStr} (${todaySessions.length} session${todaySessions.length > 1 ? 's' : ''})`,
      body: body
    });
  });
}

// Teacher weekly digest — runs every Friday via time trigger
// Sends separate reports to EN and FR teachers with only their relevant sessions
function sendTeacherDigest() {
  const store = PropertiesService.getScriptProperties();
  const allSessions = JSON.parse(store.getProperty('sessions') || '[]');

  // Filter to last 7 days
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const week = allSessions.filter(s => new Date(s.receivedAt || s.date).getTime() > weekAgo);

  // Split by language
  const enSessions = week.filter(s => s.lang === 'EN');
  const frSessions = week.filter(s => s.lang === 'FR');

  // Send to teachers (if configured) AND to parents for visibility into
  // exactly what the teacher receives. Subjects make the audience explicit
  // (🎓 Teacher Report on these vs · Parents on the parent-only emails),
  // so duplicates are easy to identify at a glance.
  if (TEACHER_EN && enSessions.length > 0) {
    sendTeacherEmail(TEACHER_EN, 'English', enSessions);
  }
  if (TEACHER_FR && frSessions.length > 0) {
    sendTeacherEmail(TEACHER_FR, 'French', frSessions);
  }
  if (enSessions.length > 0 || frSessions.length > 0) {
    EMAILS.forEach(email => {
      if (enSessions.length > 0) sendTeacherEmail(email, 'English', enSessions);
      if (frSessions.length > 0) sendTeacherEmail(email, 'French', frSessions);
    });
  }
}

function sendTeacherEmail(email, language, sessions) {
  const totalMins = sessions.reduce((a, s) => a + (s.minutes || 0), 0);
  const totalHints = sessions.reduce((a, s) => a + (s.totalHints || 0), 0);
  const flag = language === 'French' ? '\ud83c\uddeb\ud83c\uddf7' : '\ud83c\uddfa\ud83c\uddf8';

  const sessionDetails = sessions.map(s => {
    const d = new Date(s.date || s.receivedAt);
    const dateStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const difficulty = (s.avgHints || 0) > 2 ? 'Needed extra support' : (s.avgHints || 0) > 1 ? 'Some difficulty' : 'Comfortable';

    // Task-level detail if available
    let taskLines = '';
    if (s.teacherTasks && s.teacherTasks.length > 0) {
      taskLines = s.teacherTasks.map(t =>
        `      - ${t.task}: ${t.result} (${t.hintsUsed || 0} hint${(t.hintsUsed || 0) !== 1 ? 's' : ''})`
      ).join('\n');
    }

    return `  ${dateStr} \u2014 ${s.subject || 'Homework'} (${s.minutes || '?'} min, ${difficulty})` +
      (s.shone ? `\n    Strength: ${s.shone}` : '') +
      (s.struggled ? `\n    Needs work: ${s.struggled}` : '') +
      (taskLines ? `\n    Exercises:\n${taskLines}` : '');
  }).join('\n\n');

  // Identify patterns
  const hardSessions = sessions.filter(s => (s.avgHints || 0) > 2);
  const subjects = {};
  sessions.forEach(s => { if (s.subject) subjects[s.subject] = (subjects[s.subject] || 0) + 1; });

  const body = `
Ink's World \u2014 Weekly Teacher Report
${flag} ${language} Sessions
${'='.repeat(50)}

Student: Jules
Week: ${new Date(Date.now() - 7*24*60*60*1000).toLocaleDateString('en-US', {month:'short',day:'numeric'})} \u2013 ${new Date().toLocaleDateString('en-US', {month:'short',day:'numeric'})}
Sessions this week: ${sessions.length}
Total study time: ${totalMins} minutes
Total hints used: ${totalHints}

${'─'.repeat(50)}
SESSION DETAILS
${'─'.repeat(50)}

${sessionDetails}

${'─'.repeat(50)}
PATTERNS & OBSERVATIONS
${'─'.repeat(50)}

${hardSessions.length > 0
  ? `Areas needing support: ${hardSessions.map(s => s.subject).filter((v,i,a) => a.indexOf(v) === i).join(', ')} (${hardSessions.length} session${hardSessions.length > 1 ? 's' : ''} with extra difficulty)`
  : 'No major difficulty patterns this week.'}

Subjects covered: ${Object.entries(subjects).map(([k,v]) => `${k} (${v}x)`).join(', ')}

${'='.repeat(50)}
This report is generated automatically by Ink's World,
a homework companion app used at home.
For questions, please contact Jules's parents.
`.trim();

  MailApp.sendEmail({
    to: email,
    subject: `\ud83c\udf93 Teacher Report ${flag} \u2014 Jules's ${language} Homework (week of ${new Date().toLocaleDateString('en-US', {month:'short',day:'numeric'})})`,
    body: body
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
//    - Description: "Ink's World Reports"
//    - Execute as: "Me"
//    - Who has access: "Anyone"
// 8. Click "Deploy"
// 9. Click "Authorize access" and allow permissions
// 10. Copy the Web app URL — it looks like:
//     https://script.google.com/macros/s/XXXXX.../exec
// 11. That URL goes into the Ink's World app (I'll tell you where)
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
// For the teacher weekly report:
// 18. Click "+ Add Trigger" again
// 19. Set:
//     - Function: sendTeacherDigest
//     - Event source: Time-driven
//     - Type: Week timer
//     - Day: Friday
//     - Time: 6pm to 7pm
// 20. Click Save
// 21. Set TEACHER_EN and TEACHER_FR at the top to real teacher emails
//     (or your own emails for testing)
//
// That's it! You'll get:
// - An email after every homework session (automatic)
// - A weekly summary every Sunday evening (automatic)
// - Teacher reports every Friday (split by language)
//
// ─────────────────────────────────────────────
// UPGRADING AN EXISTING DEPLOYMENT (backup/restore)
// ─────────────────────────────────────────────
// If you already had the script deployed and are pasting this new
// version over the old one, you MUST redeploy so the new doGet /
// backup handling takes effect. Apps Script serves the version that
// was live at deploy time — saving the editor is not enough.
//
// Steps:
//   1. Replace the old code with this file and hit Save (cmd+S).
//   2. Click "Deploy" > "Manage deployments".
//   3. Next to your existing deployment, click the pencil (Edit).
//   4. Under "Version", choose "New version" and give it a note
//      (e.g. "add backup/restore").
//   5. Click Deploy. The URL stays the same, so the app keeps
//      working — no change needed inside Ink's World.
//
// What this adds:
// - doPost now accepts `{type:'backup', profile:{...}}` and stores
//   the latest snapshot in ScriptProperties ("latestBackup").
// - doGet answers `?action=restore` with the latest backup JSON, so
//   the app can self-heal if iOS wipes localStorage after 7 days.
// ═══════════════════════════════════════════════════════
