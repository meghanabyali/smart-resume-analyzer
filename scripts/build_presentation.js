/*
 * Builds deliverables/Smart_Resume_Analyzer_Presentation.pptx
 *
 *   npm install pptxgenjs@3.12.0      (once, anywhere on NODE_PATH)
 *   node scripts/build_presentation.js
 *
 * Numbers on the results/testing slides come from the recorded runs in docs/testing.md.
 * Screenshots in deliverables/screenshots/ are real captures of the running application.
 */
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const SHOTS = path.join(ROOT, "deliverables", "screenshots");
const OUT = path.join(ROOT, "deliverables", "Smart_Resume_Analyzer_Presentation.pptx");

// Brand palette shared with the web app (navy dominant, violet accent).
const THEME = {
  name: "Smart Resume Analyzer",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2033", lt1: "FFFFFF", dk2: "14213D", lt2: "EEF1FB",
    accent1: "3A56D4", accent2: "7048E8", accent3: "1A7F37", accent4: "B35C00",
    accent5: "C92A2A", accent6: "2A78D6", hlink: "3A56D4", folHlink: "7048E8",
  },
};
const K = {
  navy: "14213D", ink: "1B2033", ink2: "52586E", muted: "6B7189", white: "FFFFFF", tint: "EEF1FB",
  blue: "3A56D4", violet: "7048E8", series: "2A78D6", good: "1A7F37", warn: "B35C00", bad: "C92A2A",
  line: "D0D5E6", softViolet: "B9A8F5",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Smart Resume Analyzer with AI-Based Feedback";
pres.subject = "AI Capstone Project";
pres.author = "Capstone project team";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

const W = 13.333;
const M = 0.6; // margin

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "DARK",
  background: { color: K.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.3, w: W - 2 * M, h: 1.6, fontSize: 44, align: "left",
      bold: true, color: K.white, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.05, w: W - 2 * M, h: 1.4, fontSize: 20,
      color: "CADCFC", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: K.white },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.4, w: W - 2 * M, h: 0.9, fontSize: 36,
      bold: true, color: K.navy, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Smart Resume Analyzer · AI Capstone", options: { x: M, y: 7.0, w: 6, h: 0.3, fontSize: 10,
      color: K.muted, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: K.muted, align: "right" },
});

// ---------------------------------------------------------------- helpers
let section = "";
function slide(master, title, sec) {
  if (sec && sec !== section) { pres.addSection({ title: sec }); section = sec; }
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
const T = (s, text, o) => s.addText(text, { isTextBox: true, fontFace: THEME.bodyFontFace, color: K.ink, ...o });
const shadow = () => ({ type: "outer", color: "14213D", opacity: 0.12, blur: 6, offset: 2, angle: 90 });

function card(s, x, y, w, h, opts = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: opts.fill || K.white },
    line: { color: opts.line || K.line, width: 0.75 }, shadow: opts.noShadow ? undefined : shadow(),
    objectName: opts.name });
}
function badge(s, x, y, label, color = K.violet, d = 0.5) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color } });
  T(s, String(label), { x, y, w: d, h: d, fontSize: d > 0.45 ? 16 : 12, bold: true, color: K.white, align: "center",
    valign: "middle", margin: 0 });
}
function bullets(items, size = 16) {
  return items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1,
    paraSpaceAfter: 8, fontSize: size } }));
}

// ================================================================ 1. Title
{
  const s = slide("DARK", "Smart Resume Analyzer with AI-Based Feedback", "Introduction");
  s.addText("Artificial Intelligence Capstone Project · Explainable rule-based AI + NLP for resume screening",
    { placeholder: "body" });
  ["PDF / DOCX parsing", "Resume score /100", "Estimated ATS score", "Smart feedback", "Dashboard & PDF report"]
    .forEach((t, i) => {
      const x = M + i * 2.43;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.7, w: 2.25, h: 0.6, rectRadius: 0.3,
        fill: { color: "22315A" }, line: { color: "3A4A78" } });
      T(s, t, { x, y: 5.7, w: 2.25, h: 0.6, fontSize: 13, color: K.white, align: "center", valign: "middle", margin: 0 });
    });
  s.addNotes("Introduce the project: an AI-powered web app that evaluates student resumes against industry hiring standards and explains every score.");
}

// ================================================================ 2. Introduction
{
  const s = slide("CONTENT", "Why resumes need AI-assisted feedback", "Introduction");
  T(s, bullets([
    "Recruiters and Applicant Tracking Systems (ATS) screen most applications before a human reads them in detail",
    "Screening relies on recognisable sections, parseable text and role-specific keywords",
    "Students rarely get feedback that explains what is missing and why it matters",
    "This project simulates the screening logic used by HR-tech platforms – transparently",
  ], 18), { x: M, y: 1.6, w: 7.2, h: 4.6, valign: "top" });
  card(s, 8.4, 1.6, 4.3, 4.6, { fill: K.tint, noShadow: true });
  T(s, "Industry applications", { x: 8.7, y: 1.8, w: 3.8, h: 0.5, fontSize: 18, bold: true, color: K.navy, margin: 0 });
  ["Resume screening systems", "ATS software", "Recruitment automation tools", "Career guidance platforms"]
    .forEach((t, i) => {
      badge(s, 8.7, 2.5 + i * 0.9, i + 1, K.blue, 0.45);
      T(s, t, { x: 9.3, y: 2.5 + i * 0.9, w: 3.3, h: 0.45, fontSize: 15, valign: "middle", margin: 0 });
    });
  s.addNotes("Explain the context: ATS and keyword screening, and the gap in actionable feedback for students.");
}

// ================================================================ 3. Problem statement / existing problem
{
  const s = slide("CONTENT", "Problem statement", "Introduction");
  T(s, "Many students create resumes without understanding:", { x: M, y: 1.45, w: 12, h: 0.5, fontSize: 18, color: K.ink2, margin: 0 });
  const items = [
    ["ATS requirements", "Unparseable layouts and non-standard headings hide content"],
    ["Industry-relevant skills", "Role skills are missing or buried in paragraphs"],
    ["Formatting standards", "No bullets, wrong length, missing sections"],
    ["Keyword optimisation", "Skills are not phrased the way job descriptions phrase them"],
    ["Role-specific expectations", "One generic resume is used for every role"],
  ];
  items.forEach(([h, d], i) => {
    const x = M + i * 2.46, y = 2.2;
    card(s, x, y, 2.26, 3.3);
    badge(s, x + 0.25, y + 0.3, i + 1, K.violet);
    T(s, h, { x: x + 0.25, y: y + 1.0, w: 1.85, h: 0.8, fontSize: 16, bold: true, color: K.navy, margin: 0, valign: "top" });
    T(s, d, { x: x + 0.25, y: y + 1.85, w: 1.85, h: 1.3, fontSize: 13, color: K.ink2, margin: 0, valign: "top" });
  });
  T(s, "Existing problem: generic resume checkers give a single opaque number, or need paid AI APIs, and rarely explain the evidence behind a score.",
    { x: M, y: 5.85, w: W - 2 * M, h: 0.8, fontSize: 15, italic: true, color: K.ink2, margin: 0 });
}

// ================================================================ 4. Objectives
{
  const s = slide("CONTENT", "Project objectives", "Introduction");
  const obj = ["Upload resumes in PDF or DOCX format", "Extract and process resume content", "Generate resume scores",
    "Check ATS compatibility", "Analyze role-based skills", "Receive smart improvement suggestions",
    "View analysis results on a dashboard"];
  obj.forEach((t, i) => {
    const col = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4;
    const x = M + col * 6.2, y = 1.6 + row * 1.2;
    card(s, x, y, 5.9, 0.95, { noShadow: true, fill: K.tint, line: K.tint });
    badge(s, x + 0.25, y + 0.22, i + 1, K.navy);
    T(s, t, { x: x + 0.95, y, w: 4.8, h: 0.95, fontSize: 17, valign: "middle", margin: 0 });
  });
  T(s, "All seven objectives are implemented as working, tested features.", { x: 6.8, y: 5.25, w: 5.9, h: 0.9,
    fontSize: 15, italic: true, color: K.violet, margin: 0, valign: "middle" });
}

// ================================================================ 5. Proposed solution
{
  const s = slide("CONTENT", "Proposed solution", "Solution");
  T(s, bullets([
    "Flask web application: upload a resume, pick a target role, get a dashboard in seconds",
    "Explainable rule-based AI: every point awarded is backed by evidence from the resume",
    "Basic NLP with spaCy and NLTK – no deep learning, no LLMs, no paid APIs",
    "Four target roles: Data Analyst, Web Developer, AI Engineer, Cloud Engineer",
    "Privacy-first: private links, one-click delete, automatic retention purge",
  ], 17), { x: M, y: 1.6, w: 6.3, h: 4.9, valign: "top" });
  s.addImage({ path: path.join(SHOTS, "home.png"), x: 7.2, y: 1.6, w: 5.5, h: 3.385, altText: "Home page of the Smart Resume Analyzer" });
  s.addShape(pres.shapes.RECTANGLE, { x: 7.2, y: 1.6, w: 5.5, h: 3.385, fill: { type: "none" }, line: { color: K.line, width: 0.75 } });
  T(s, "Home page (live application screenshot)", { x: 7.2, y: 5.1, w: 5.5, h: 0.35, fontSize: 11, color: K.muted, margin: 0 });
}

// ================================================================ 6. Architecture
{
  const s = slide("CONTENT", "System architecture", "Solution");
  const box = (x, y, w, h, title, sub, fill, color = K.white) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.1, fill: { color: fill }, line: { color: fill } });
    T(s, [{ text: title, options: { bold: true, fontSize: 15, breakLine: true } }, { text: sub, options: { fontSize: 12 } }],
      { x: x + 0.1, y, w: w - 0.2, h, color, align: "center", valign: "middle", margin: 0 });
  };
  const arrow = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, { x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color: K.muted, width: 1.5, endArrowType: "triangle" } });

  box(M, 1.55, W - 2 * M, 0.85, "Browser", "Bootstrap 5 · Chart.js · upload.js / dashboard.js", K.tint, K.navy);
  arrow(W / 2, 2.4, W / 2, 2.75);
  box(M, 2.75, W - 2 * M, 0.75, "Flask routes", "main · upload · analysis · report  (HTML pages + JSON API)", K.blue);
  arrow(W / 2, 3.5, W / 2, 3.85);
  const svc = [["Module 1", "file_handler · resume_parser · text_preprocessor · section_extractor"],
    ["Module 2", "resume_scorer"], ["Module 3", "skill_matcher · ats_analyzer"], ["Module 4", "feedback_engine"],
    ["Module 5", "report_generator"]];
  const sw = (W - 2 * M - 4 * 0.2) / 5;
  svc.forEach(([t, d], i) => box(M + i * (sw + 0.2), 3.85, sw, 1.35, t, d, K.navy));
  arrow(W / 2, 5.2, W / 2, 5.55);
  box(M, 5.55, 6.0, 0.9, "SQLAlchemy models → SQLite / MySQL", "resumes ─< analyses ─< feedback", K.violet);
  box(M + 6.3, 5.55, W - 2 * M - 6.3, 0.9, "Reference data (JSON)", "job_roles.json · skill_keywords.json", K.tint, K.navy);
  s.addNotes("Layered design: thin Flask controllers, services independent of HTTP (unit-testable), ORM models, JSON-configurable rules. analysis_pipeline orchestrates the services.");
}

// ================================================================ 7. Workflow
{
  const s = slide("CONTENT", "Project workflow", "Solution");
  const steps = ["User uploads resume", "System extracts resume text", "Resume data is processed",
    "Resume score is calculated", "ATS keyword matching", "Suggestions are generated", "Dashboard displays analysis"];
  const bw = 1.58, gap = 0.16;
  steps.forEach((t, i) => {
    const x = M + i * (bw + gap), y = 2.2;
    card(s, x, y, bw, 2.2, { fill: i % 2 ? K.white : K.tint });
    badge(s, x + bw / 2 - 0.27, y + 0.25, i + 1, i < 3 ? K.blue : i < 6 ? K.violet : K.navy, 0.54);
    T(s, t, { x: x + 0.1, y: y + 0.95, w: bw - 0.2, h: 1.1, fontSize: 14, bold: true, color: K.navy, align: "center", valign: "top", margin: 0 });
  });
  [["Module 1", 0, 3], ["Modules 2–4", 3, 6], ["Module 5", 6, 7]].forEach(([lbl, a, b]) => {
    const x = M + a * (bw + gap), w = (b - a) * (bw + gap) - gap;
    s.addShape(pres.shapes.LINE, { x, y: 4.75, w, h: 0, line: { color: K.line, width: 1.5 } });
    T(s, lbl, { x, y: 4.85, w, h: 0.4, fontSize: 13, color: K.muted, align: "center", margin: 0 });
  });
  T(s, "Each run is stored (resume → analysis → feedback) and the dashboard and PDF report are always rendered from the stored record.",
    { x: M, y: 5.7, w: W - 2 * M, h: 0.6, fontSize: 15, color: K.ink2, margin: 0 });
}

// ================================================================ 8. Five modules
{
  const s = slide("CONTENT", "Five project modules", "Implementation");
  const mods = [
    ["Resume Upload & Parsing", "Extension + magic-byte + size checks · PyMuPDF / python-docx · scanned, encrypted and corrupt files rejected · sections, contact, education, projects extracted"],
    ["Resume Score Analyzer", "Six independent functions: structure 20, skills 20, education 15, projects 15, contact 15, completeness 15 – each with evidence and gaps"],
    ["ATS Keyword Checker", "4 roles · ~75 skills with aliases · boundary-safe phrase matching · 60/20/20 estimated ATS score · skill-gap list"],
    ["Smart Feedback System", "9 rule generators · category, priority, problem, evidence, recommendation, reason · de-duplicated and sorted"],
    ["Dashboard & Report", "Score rings, Chart.js bars, skill badges, priority filter · printable page · ReportLab PDF"],
  ];
  mods.forEach(([h, d], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const w = 3.85, x = M + col * (w + 0.3) + (row === 1 ? (w + 0.3) / 2 : 0), y = 1.55 + row * 2.65;
    card(s, x, y, w, 2.4);
    badge(s, x + 0.25, y + 0.25, i + 1, K.violet);
    T(s, h, { x: x + 0.9, y: y + 0.25, w: w - 1.05, h: 0.5, fontSize: 17, bold: true, color: K.navy, valign: "middle", margin: 0 });
    T(s, d, { x: x + 0.25, y: y + 0.9, w: w - 0.45, h: 1.4, fontSize: 13, color: K.ink2, valign: "top", margin: 0 });
  });
}

// ================================================================ 9. Technology stack
{
  const s = slide("CONTENT", "Technology stack", "Implementation");
  const stack = [
    ["Frontend", "HTML5, CSS3, JavaScript, Bootstrap 5, Jinja2, Chart.js"],
    ["Backend", "Python 3.11, Flask, Flask-SQLAlchemy"],
    ["AI / NLP", "spaCy en_core_web_sm, NLTK, regular expressions"],
    ["Documents", "PyMuPDF (PDF), python-docx (DOCX), ReportLab (report)"],
    ["Database", "SQLite (MySQL/PostgreSQL-ready via SQLAlchemy)"],
    ["Testing", "pytest + Flask test client (62 tests)"],
    ["Deployment", "Gunicorn, Render blueprint, health endpoint"],
  ];
  const rows = stack.map(([a, b], i) => [
    { text: a, options: { bold: true, color: K.navy, fill: { color: i % 2 ? K.white : K.tint } } },
    { text: b, options: { color: K.ink, fill: { color: i % 2 ? K.white : K.tint } } },
  ]);
  s.addTable(rows, { x: M, y: 1.6, w: 8.2, colW: [2.2, 6.0], fontSize: 16, rowH: 0.62, valign: "middle",
    border: { type: "solid", color: K.line, pt: 0.75 }, margin: [0, 0.15, 0, 0.15] });
  card(s, 9.2, 1.6, 3.5, 4.34, { fill: K.navy, line: K.navy, noShadow: true });
  T(s, [{ text: "Deliberately excluded", options: { bold: true, fontSize: 17, breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },
    ...bullets(["Deep learning models", "LLM training", "Complex recommendation engines", "Enterprise authentication",
      "Large-scale cloud architecture"], 14)],
    { x: 9.45, y: 1.8, w: 3.05, h: 4.0, color: K.white, valign: "top", margin: 0 });
}

// ================================================================ 10. AI/NLP implementation
{
  const s = slide("CONTENT", "AI and NLP implementation", "Implementation");
  const cols = [
    ["Preprocessing", ["Unicode/ligature/bullet normalisation", "NLTK RegexpTokenizer keeps C++, C#, Node.js, CI/CD",
      "NLTK stopwords + resume boilerplate", "spaCy lemmatisation"]],
    ["Information extraction", ["~110 heading synonyms → 10 sections", "Regex: email, phone, URLs, degrees, grades, metrics",
      "spaCy NER for the candidate name", "Action verbs and quantified outcomes"]],
    ["Keyword analysis", ["Alias dictionary (JS → JavaScript, GCP → Google Cloud)",
      "Boundaries: Java ≠ JavaScript, SQL ≠ MySQL", "Context rule: 'ML' needs ML context nearby",
      "NLTK FreqDist + bigrams, spaCy noun chunks"]],
  ];
  cols.forEach(([h, items], i) => {
    const x = M + i * 4.1;
    card(s, x, 1.6, 3.85, 3.6);
    T(s, h, { x: x + 0.3, y: 1.8, w: 3.3, h: 0.5, fontSize: 18, bold: true, color: K.violet, margin: 0 });
    T(s, bullets(items, 14), { x: x + 0.3, y: 2.4, w: 3.35, h: 2.7, valign: "top", margin: 0 });
  });
  T(s, "Decision layer: weighted rule-based scoring + 9 recommendation generators, so every output is explainable.",
    { x: M, y: 5.5, w: W - 2 * M, h: 0.5, fontSize: 15, italic: true, color: K.ink2, margin: 0 });
}

// ================================================================ 11. Scoring model (native chart)
{
  const s = slide("CONTENT", "Scoring model", "Implementation");
  s.addChart(pres.charts.BAR, [{ name: "Max points", labels: ["Structure", "Skills", "Education", "Projects", "Contact", "Completeness"],
    values: [20, 20, 15, 15, 15, 15] }], {
    x: M, y: 1.5, w: 6.6, h: 4.9, barDir: "bar", chartColors: [K.series], showValue: true, dataLabelPosition: "outEnd",
    dataLabelColor: K.ink, dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt", showLegend: false, showTitle: true,
    title: "Resume score: maximum points per parameter (total 100)", titleFontSize: 14, titleColor: K.navy, titleFontFace: "+mn-lt",
    catAxisLabelColor: K.ink2, valAxisLabelColor: K.ink2, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, valAxisMaxVal: 25, valGridLine: { color: "E3E6F0", size: 0.75 },
    catGridLine: { style: "none" }, catAxisOrientation: "maxMin", barGapWidthPct: 60,
  });
  card(s, 7.6, 1.5, 5.1, 2.35, { fill: K.tint, noShadow: true, line: K.tint });
  T(s, [{ text: "Estimated ATS score", options: { bold: true, fontSize: 18, color: K.navy, breakLine: true } },
    { text: "60% role keyword coverage", options: { fontSize: 15, breakLine: true } },
    { text: "20% parseability (text layer, layout, encoding)", options: { fontSize: 15, breakLine: true } },
    { text: "20% structural compatibility (headings, contact, length, bullets)", options: { fontSize: 15 } }],
    { x: 7.85, y: 1.65, w: 4.7, h: 2.1, valign: "top", margin: 0 });
  card(s, 7.6, 4.05, 5.1, 2.35, { noShadow: true });
  T(s, [{ text: "Score categories (application-defined)", options: { bold: true, fontSize: 16, color: K.navy, breakLine: true } },
    { text: "85–100  Excellent", options: { fontSize: 15, color: K.good, breakLine: true } },
    { text: "70–84  Good", options: { fontSize: 15, color: K.blue, breakLine: true } },
    { text: "50–69  Needs Improvement", options: { fontSize: 15, color: K.warn, breakLine: true } },
    { text: "0–49  Significant Improvement Needed", options: { fontSize: 15, color: K.bad } }],
    { x: 7.85, y: 4.2, w: 4.7, h: 2.1, valign: "top", margin: 0 });
}

// ================================================================ 12. Screenshots
{
  const s = slide("CONTENT", "Application screenshots", "Results");
  s.addImage({ path: path.join(SHOTS, "dashboard.png"), x: M, y: 1.45, w: 6.8, h: 5.23, altText: "Analysis dashboard" });
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: 1.45, w: 6.8, h: 5.23, fill: { type: "none" }, line: { color: K.line, width: 0.75 } });
  s.addImage({ path: path.join(SHOTS, "upload.png"), x: 7.65, y: 1.45, w: 5.05, h: 3.885, altText: "Upload page" });
  s.addShape(pres.shapes.RECTANGLE, { x: 7.65, y: 1.45, w: 5.05, h: 3.885, fill: { type: "none" }, line: { color: K.line, width: 0.75 } });
  T(s, [{ text: "Left: analysis dashboard (resume score, ATS score, parameter chart, skill gap).", options: { breakLine: true } },
    { text: "Right: upload page with drag-and-drop and role selection." }],
    { x: 7.65, y: 5.5, w: 5.05, h: 1.1, fontSize: 13, color: K.ink2, valign: "top", margin: 0 });
}

// ================================================================ 13. Results (native chart)
{
  const s = slide("CONTENT", "Results on the synthetic sample dataset", "Results");
  const labels = ["DA strong", "AI strong", "Web strong", "Cloud average", "DA average", "Web incomplete", "Cloud incomplete", "AI poorly structured"];
  s.addChart(pres.charts.BAR, [
    { name: "Resume score", labels, values: [99, 96, 95, 82, 66, 52, 38, 25] },
    { name: "Estimated ATS score", labels, values: [100, 100, 100, 67, 50, 45, 30, 52] },
  ], {
    x: M, y: 1.45, w: 8.4, h: 5.2, barDir: "col", barGrouping: "clustered", chartColors: [K.series, "EB6834"],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10, dataLabelColor: K.ink, dataLabelFontFace: "+mn-lt",
    showLegend: true, legendPos: "t", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: K.ink2,
    catAxisLabelColor: K.ink2, valAxisLabelColor: K.ink2, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valAxisMinVal: 0, valAxisMaxVal: 120, valAxisMajorUnit: 20,
    valGridLine: { color: "E3E6F0", size: 0.75 }, catGridLine: { style: "none" }, barGapWidthPct: 50,
  });
  card(s, 9.3, 1.45, 3.4, 5.2, { fill: K.tint, noShadow: true, line: K.tint });
  T(s, [{ text: "What the results show", options: { bold: true, fontSize: 17, color: K.navy, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    ...bullets(["Scores rank samples in the intended quality order",
      "The poorly structured resume has many AI keywords (ATS 52) but no structure (resume score 25) – the two scores measure different things",
      "Strong samples trigger no improvement rules; weak ones get 15–20 targeted suggestions"], 13)],
    { x: 9.5, y: 1.65, w: 3.05, h: 4.9, valign: "top", margin: 0 });
  s.addNotes("Numbers recorded with scripts/seed_data.py --samples on 17 Nov 2026 (docs/testing.md). DA = Data Analyst.");
}

// ================================================================ 14. Testing
{
  const s = slide("CONTENT", "Testing and validation", "Results");
  card(s, M, 1.6, 3.6, 2.4, { fill: K.navy, line: K.navy, noShadow: true });
  T(s, "62", { x: M, y: 1.7, w: 3.6, h: 1.4, fontSize: 66, bold: true, color: K.white, align: "center", valign: "middle", margin: 0 });
  T(s, "automated tests passed", { x: M, y: 3.1, w: 3.6, h: 0.5, fontSize: 16, color: "CADCFC", align: "center", margin: 0 });
  const rows = [["Suite", "Tests", "Focus"],
    ["test_parser.py", "17", "validation, extraction, NLP, info extraction"],
    ["test_scoring.py", "14", "bounds, sums, determinism, explanations"],
    ["test_ats.py", "9", "aliases, false positives, role changes, formula"],
    ["test_feedback.py", "7", "rules fire only when relevant, priorities"],
    ["test_routes.py", "15", "API, errors, security, end-to-end, delete"]];
  s.addTable(rows.map((r, i) => r.map((c) => ({ text: c, options: i === 0 ? { bold: true, color: K.white, fill: { color: K.blue } }
    : { color: K.ink, fill: { color: i % 2 ? K.white : K.tint } } }))),
    { x: 4.6, y: 1.6, w: 8.1, colW: [2.2, 0.9, 5.0], fontSize: 14, rowH: 0.5, valign: "middle",
      border: { type: "solid", color: K.line, pt: 0.75 }, margin: [0, 0.12, 0, 0.12] });
  T(s, bullets(["End-to-end test: upload → extract → analyse → store → dashboard → PDF report (PDF text verified)",
    "Manual UI checks at 1300, 768 and 576 px using headless Edge screenshots"], 14),
    { x: M, y: 4.85, w: W - 2 * M, h: 1.3, valign: "top", margin: 0 });
}

// ================================================================ 15. Limitations & future scope
{
  const s = slide("CONTENT", "Limitations and future scope", "Conclusion");
  const two = (x, title, items, color) => {
    card(s, x, 1.6, 5.85, 3.9);
    T(s, title, { x: x + 0.3, y: 1.8, w: 5.3, h: 0.5, fontSize: 20, bold: true, color, margin: 0 });
    T(s, bullets(items, 15), { x: x + 0.3, y: 2.45, w: 5.3, h: 2.9, valign: "top", margin: 0 });
  };
  two(M, "Limitations", ["Rule-based heuristics can misread very creative layouts", "No OCR – scanned PDFs are rejected with a message",
    "English-only keyword dictionaries; unlisted synonyms are missed", "ATS score is an estimate, not a vendor score",
    "No user accounts – access relies on private links"], K.bad);
  two(M + 6.25, "Future scope", ["Paste a real job description and extract its keywords", "OCR for scanned resumes (e.g. Tesseract)",
    "More roles and editable dictionaries from an admin page", "Side-by-side comparison of resume versions",
    "Optional login to keep an analysis history"], K.good);
}

// ================================================================ 16. Conclusion
{
  const s = slide("DARK", "Conclusion", "Conclusion");
  s.addText("A working, tested and explainable resume analyzer covering all five modules: evaluation, ATS keyword analysis, skill-gap identification, smart feedback and dashboard reporting.",
    { placeholder: "body" });
  T(s, "Thank you · Questions?", { x: M, y: 5.8, w: 8, h: 0.6, fontSize: 22, bold: true, color: K.softViolet, margin: 0 });
}

pres.writeFile({ fileName: OUT }).then(async (file) => {
  try {
    // Optional: write THEME colours into the theme part (helper from the deck-building toolkit, if available).
    const helper = process.env.APPLY_THEME_JS;
    if (helper) { await require(helper).applyTheme(file, THEME); }
  } catch (e) { console.warn("Theme colours not applied:", e.message); }
  console.log("wrote", file);
});
