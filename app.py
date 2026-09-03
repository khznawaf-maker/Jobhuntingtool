"""
Luluty Job Hunting Tool
Run:  python -m streamlit run app.py
"""

import base64, io, json, os, random, re, time
from collections import Counter
from datetime import datetime, timedelta

import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Luluty Job Hunting Tool", page_icon="🐸", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "employers.json")
JOBCACHE = os.path.join(HERE, "jobcache.json")

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept": "text/html,application/json,*/*",
}
CACHE_HOURS = 12
MIN_DELAY, MAX_DELAY = 1.5, 4.0

HYPE = [
    "Good job Luluty! 💚", "I'm proud of you 🌸", "You're doing well, beautiful ✨",
    "Look at you go 🐸", "Future data analyst incoming 📊",
    "Taibah's finest 🎓", "You got this, habibti 💅", "Keep cooking Luluty 🔥",
    "Your CV is about to eat 😤", "Recruiters aren't ready 💫",
    "Smartest girl in Medina 🧠", "One click closer 💼",
]

# ═══════════════════════════════════════ style
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family:'Space Grotesk',sans-serif; }
.hero{
  background:linear-gradient(135deg,#6EE7B7 0%,#3B82F6 40%,#A855F7 75%,#EC4899 100%);
  background-size:300% 300%; animation:flow 9s ease infinite;
  border-radius:26px; padding:22px 28px; margin-bottom:6px;
  box-shadow:0 12px 34px rgba(168,85,247,.34);
}
@keyframes flow{0%{background-position:0% 50%}50%{background-position:100% 50%}
100%{background-position:0% 50%}}
.hero h1{color:#fff;margin:0;font-size:2.3rem;letter-spacing:-1.4px}
.hero p{color:#F0FDF4;margin:5px 0 0;font-size:.95rem}
.jobcard{border:2px solid #E5E7EB;border-radius:18px;padding:15px 18px;
  margin-bottom:11px;background:#fff;transition:.15s}
.jobcard:hover{border-color:#A855F7;transform:translateY(-2px)}
.badge{display:inline-block;padding:3px 11px;border-radius:999px;
  font-size:.71rem;font-weight:700;margin:2px 4px 2px 0}
.b-green{background:#DCFCE7;color:#166534}
.b-blue{background:#DBEAFE;color:#1E40AF}
.b-pink{background:#FCE7F3;color:#9D174D}
.b-gray{background:#F3F4F6;color:#374151}
.b-amber{background:#FEF3C7;color:#92400E}
.stButton>button{border-radius:14px;font-weight:700;border:2px solid #111;
  box-shadow:3px 3px 0 #111}
.stButton>button:hover{transform:translate(1px,1px);box-shadow:2px 2px 0 #111}
</style>
""", unsafe_allow_html=True)

# ── header GIF (falls back to emoji if frog.gif is missing)
try:
    _g = base64.b64encode(open(os.path.join(HERE, "frog.gif"), "rb").read()).decode()
    FROG = f'<img src="data:image/gif;base64,{_g}" width="66" style="border-radius:14px">'
except Exception:
    FROG = '<div style="font-size:3rem">🐸</div>'

st.markdown(f"""
<div class="hero"><div style="display:flex;align-items:center;gap:16px">
{FROG}<div><h1>Luluty Job Hunting Tool</h1>
<p>scrape · match · fix the CV · sort some balls 🫧</p></div></div></div>
""", unsafe_allow_html=True)

# ── live rotating encouragement
_hype_js = json.dumps(HYPE)
components.html(f"""
<div id="hb" style="text-align:center;font-family:'Space Grotesk',system-ui;
 font-size:1.24rem;font-weight:700;padding:12px;background:#FFF1F7;
 border:2px dashed #EC4899;border-radius:18px;color:#9D174D;
 transition:opacity .45s">{HYPE[0]}</div>
<script>
const H={_hype_js};let i=0;const el=document.getElementById('hb');
setInterval(()=>{{
  el.style.opacity=0;
  setTimeout(()=>{{i=(i+1)%H.length;el.textContent=H[i];el.style.opacity=1;}},450);
}},5800);
</script>
""", height=70)

# ═══════════════════════════════════════ data
SAUDI_CITIES = {
    "Riyadh":["riyadh","الرياض"], "Jeddah":["jeddah","jedda","جدة"],
    "Medina":["medina","madinah","medinah","المدينة"],
    "Mecca":["mecca","makkah","مكة"], "Dammam":["dammam","الدمام"],
    "Khobar":["khobar","الخبر"], "Dhahran":["dhahran","الظهران"],
    "Jubail":["jubail","الجبيل"], "Yanbu":["yanbu","ينبع"],
    "Tabuk":["tabuk","تبوك"], "Abha":["abha","أبها"], "NEOM":["neom","نيوم"],
    "AlUla":["alula","al ula","العلا"], "Qassim":["qassim","buraidah","القصيم"],
    "Hail":["hail","حائل"], "Jazan":["jazan","jizan","جازان"],
    "Al-Ahsa":["ahsa","hofuf","الأحساء"], "Taif":["taif","الطائف"],
}
SAUDI_GENERIC = ["saudi","ksa","k.s.a","السعودية","المملكة"]

CANDIDATE_SLUGS = [
    "tabby","tamara","foodics","salla","unifonic","lean","nana","jahez","zid",
    "hyperpay","geidea","mrsool","sary","neom","redseaglobal","roshn","qiddiya",
    "diriyah","pif","alula","careem","noon","talabat","kitopi","bayut",
    "accenture","deloitte","sap","oracle","cisco","ericsson","nokia","siemens",
    "schneiderelectric","honeywell","ibm","databricks","snowflake","palantir",
    "servicenow","mongodb","elastic","gitlab","cyberani","zenhr","alinma",
]
PROBES = {
    "lever":"https://api.lever.co/v0/postings/{s}?mode=json",
    "greenhouse":"https://boards-api.greenhouse.io/v1/boards/{s}/jobs",
    "ashby":"https://api.ashbyhq.com/posting-api/job-board/{s}",
    "recruitee":"https://{s}.recruitee.com/api/offers/",
    "workable":"https://apply.workable.com/api/v1/widget/accounts/{s}",
    "smartr":"https://api.smartrecruiters.com/v1/companies/{s}/postings",
}
GOV_ENTITIES = {
    "ZATCA":"https://zatca.gov.sa/en/Careers/Pages/default.aspx",
    "SDAIA":"https://sdaia.gov.sa/en/Contact/Pages/JoinUs.aspx",
    "SAMA":"https://www.sama.gov.sa/en-US/Careers/Pages/default.aspx",
    "GOSI":"https://www.gosi.gov.sa/en/Careers",
    "Monsha'at":"https://www.monshaat.gov.sa/en/careers",
    "CMA":"https://cma.org.sa/en/AboutUs/Careers/Pages/default.aspx",
    "GASTAT":"https://www.stats.gov.sa/en/careers",
    "DGA":"https://dga.gov.sa/en/careers",
    "NCA":"https://nca.gov.sa/en/careers/",
    "SFDA":"https://www.sfda.gov.sa/en/careers",
    "Saudi Post SPL":"https://splonline.com.sa/en/careers/",
    "KAUST":"https://www.kaust.edu.sa/en/careers",
    "SIDF":"https://www.sidf.gov.sa/en/Careers",
    "Saudi EXIM":"https://saudiexim.gov.sa/en/careers",
    "MISA":"https://misa.gov.sa/en/careers/",
    "RCRC":"https://www.rcrc.gov.sa/en/careers",
    "Elm":"https://elm.sa/en/careers",
    "NDMC":"https://www.ndmc.gov.sa/en/careers",
    "TGA":"https://tga.gov.sa/en/careers",
    "Mawani":"https://mawani.gov.sa/en/careers",
}

STOPWORDS = set("""
a an the and or of to in for with on at by from as is are was were be been being
i me my we our you your he she it they them this that these those will would can
could should have has had do does did not no so if then than there here what which
who whom when where why how all any both each few more most other some such only own
same too very just don now up out about into over after before under again
year years month months day days work working works experience skills team teams
role responsibilities requirements ability strong good excellent using use used
new job company across within including etc via per able support
""".split())

SENIOR = ["senior","sr.","staff ","principal","lead ","head of","manager",
          "director","vp ","chief","architect","expert","10+","8+ years"," iii"]
JUNIOR = ["junior","graduate","entry","intern","trainee","associate","fresh",
          "0-2","1-2","analyst program","rotational","tamheer","co-op",
          "cooperative","new grad"]

DEGREE_FIELDS = {
    "computer information systems":["information system","computer information",
        "management information","mis","business systems","systems analysis"],
    "computer science":["computer science","software engineering","informatics"],
    "data science":["data science","data analytics","statistics","machine learning"],
    "business":["business administration","management","marketing","finance"],
    "engineering":["electrical engineering","mechanical","civil","industrial",
                   "telecommunication","network engineering"],
    "accounting":["accounting","audit"],
}

WEAK_VERBS = {
    "responsible for":"Led","worked on":"Delivered","helped":"Supported",
    "assisted":"Supported","did":"Executed","made":"Built",
    "was part of":"Contributed to","handled":"Managed","took care of":"Managed",
    "involved in":"Drove","participated in":"Contributed to",
}


def tokens(t):
    ws = re.findall(r"[a-zA-Z][a-zA-Z+#.\-]{1,}", (t or "").lower())
    return [w.strip(".-") for w in ws if w not in STOPWORDS and len(w) > 2]

def strip_html(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>"," ", s or "", flags=re.S|re.I)
    s = re.sub(r"<[^>]+>"," ", s)
    for a,b in [("&amp;","&"),("&nbsp;"," "),("&#39;","'"),("&quot;",'"')]:
        s = s.replace(a,b)
    return re.sub(r"\s+"," ", s).strip()

def build_profile(text, top_n=60):
    ws = tokens(text)
    prof = {t:c for t,c in Counter(ws).most_common(top_n)}
    for t,c in Counter(f"{a} {b}" for a,b in zip(ws,ws[1:])).most_common(top_n//2):
        if c > 1:
            prof[t] = c*2
    return prof

def detect_field(text):
    low = (text or "").lower()
    sc = {f: sum(low.count(k) for k in kws) for f,kws in DEGREE_FIELDS.items()}
    best = max(sc, key=sc.get)
    return (best, DEGREE_FIELDS[best]) if sc[best] > 0 else (None, [])

def read_upload(f):
    n, data = f.name.lower(), f.read()
    if n.endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    if n.endswith(".docx"):
        import docx
        return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")


# ═══════════════════════════════════════ polite fetching
def polite_sleep(): time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

def get(url, timeout=20):
    try:
        r = requests.get(url, timeout=timeout, headers=UA)
        if r.status_code == 429:
            time.sleep(60); return None
        return r if r.status_code == 200 else None
    except requests.RequestException:
        return None

def load_cache():
    if os.path.exists(JOBCACHE):
        try: return json.load(open(JOBCACHE, encoding="utf-8"))
        except Exception: pass
    return {}

def save_cache(c):
    try: json.dump(c, open(JOBCACHE,"w",encoding="utf-8"))
    except Exception: pass

def cache_fresh(e):
    try:
        return datetime.now()-datetime.fromisoformat(e["ts"]) < timedelta(hours=CACHE_HOURS)
    except Exception:
        return False

def probe(slug):
    for ats,tpl in PROBES.items():
        r = get(tpl.format(s=slug), timeout=10)
        if r:
            try: d = r.json()
            except Exception: continue
            if isinstance(d,list) and d: return ats
            if isinstance(d,dict):
                for k in ("jobs","offers","content","results"):
                    if d.get(k): return ats
        time.sleep(0.4)
    return None

def fetch_ats(slug, ats):
    out = []
    try:
        if ats=="lever":
            r=get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            for j in (r.json() if r else []):
                out.append({"title":j.get("text",""),
                    "location":(j.get("categories") or {}).get("location",""),
                    "url":j.get("hostedUrl",""),
                    "desc":strip_html(j.get("descriptionPlain") or "")})
        elif ats=="greenhouse":
            r=get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
            for j in (r.json().get("jobs",[]) if r else []):
                out.append({"title":j.get("title",""),
                    "location":(j.get("location") or {}).get("name",""),
                    "url":j.get("absolute_url",""),
                    "desc":strip_html(j.get("content",""))})
        elif ats=="ashby":
            r=get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
            for j in (r.json().get("jobs",[]) if r else []):
                out.append({"title":j.get("title",""),"location":j.get("location",""),
                    "url":j.get("jobUrl",""),
                    "desc":strip_html(j.get("descriptionPlain",""))})
        elif ats=="recruitee":
            r=get(f"https://{slug}.recruitee.com/api/offers/")
            for j in (r.json().get("offers",[]) if r else []):
                out.append({"title":j.get("title",""),"location":j.get("location",""),
                    "url":j.get("careers_url",""),
                    "desc":strip_html(j.get("description",""))})
        elif ats=="workable":
            r=get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
            for j in (r.json().get("jobs",[]) if r else []):
                out.append({"title":j.get("title",""),
                    "location":j.get("location") or j.get("city",""),
                    "url":j.get("url",""),"desc":strip_html(j.get("description",""))})
        elif ats=="smartr":
            r=get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100")
            for j in (r.json().get("content",[]) if r else []):
                loc=j.get("location") or {}
                out.append({"title":j.get("name",""),
                    "location":f"{loc.get('city','')} {loc.get('country','')}".strip(),
                    "url":j.get("ref") or j.get("applyUrl",""),"desc":""})
    except Exception:
        pass
    for j in out: j["company"]=slug
    return out

JOB_WORD = re.compile(r"(analyst|engineer|specialist|officer|developer|consultant|"
    r"coordinator|administrator|architect|scientist|technician|associate|intern|"
    r"trainee|graduate|advisor|auditor|designer|researcher)", re.I)

def fetch_gov(name, url):
    r = get(url)
    if not r: return []
    out, seen = [], set()
    for c in re.findall(r"<(?:a|li|h[2-4])[^>]*>(.*?)</(?:a|li|h[2-4])>",
                        r.text, flags=re.S|re.I):
        t = strip_html(c)
        if 6 < len(t) < 90 and JOB_WORD.search(t) and t.lower() not in seen:
            seen.add(t.lower())
            out.append({"title":t,"location":"Saudi Arabia","url":url,
                        "desc":"","company":name})
    return out[:40]

def fetch_jobspy(term, cities, all_saudi):
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return [], "JobSpy not installed — run: pip install -U python-jobspy"
    loc = "Saudi Arabia" if all_saudi else f"{cities[0]}, Saudi Arabia"
    try:
        df = scrape_jobs(site_name=["indeed","bayt"], search_term=term,
                         location=loc, results_wanted=25, hours_old=168,
                         country_indeed="Saudi Arabia")
        return [{"title":str(r.get("title") or ""),
                 "location":str(r.get("location") or ""),
                 "url":str(r.get("job_url") or ""),
                 "desc":str(r.get("description") or "")[:4000],
                 "company":str(r.get("company") or "board")}
                for _,r in df.iterrows()], None
    except Exception as e:
        return [], f"JobSpy error: {e}"


def loc_ok(loc, chosen, all_saudi, keep_blank):
    l = (loc or "").lower().strip()
    if not l: return keep_blank
    if all_saudi:
        return (any(g in l for g in SAUDI_GENERIC)
                or any(k in l for c in SAUDI_CITIES.values() for k in c))
    return any(k in l for city in chosen for k in SAUDI_CITIES[city])

def score(job, prof, entry_only, field_kws):
    tl = job["title"].lower()
    if entry_only and any(m in tl for m in SENIOR): return 0, []
    hay = f"{tl} {job.get('desc','').lower()}"
    pts, hits = 0, []
    for term,w in prof.items():
        if term in hay:
            pts += w*(4 if term in tl else 1)
            if term in tl or w>=3: hits.append(term)
    for kw in field_kws:
        if kw in hay: pts += 20; hits.append(kw)
    if entry_only and any(m in tl for m in JUNIOR): pts += 25
    return pts, sorted(set(hits), key=len, reverse=True)[:8]


# ═══════════════════════════════════════ CV parsing / tailoring
SECTION_HEADS = ["education","skills","technical skills","soft skills",
                 "certification","certifications","experience","projects",
                 "summary","professional summary"]

def parse_cv(text):
    lines = [l.rstrip() for l in text.split("\n")]
    cv = {"name":"", "headline":"", "contact":"", "sections":{}}

    for l in lines[:6]:
        s = l.strip()
        if s and s.isupper() and len(s.split()) <= 5 and not cv["name"]:
            cv["name"] = s
        elif s and not cv["headline"] and cv["name"] and len(s) < 70:
            cv["headline"] = s
    if not cv["name"]:
        cv["name"] = next((l.strip() for l in lines if l.strip()), "YOUR NAME")

    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    phone = re.search(r"(\+?966[\d\s-]{7,}|0?5\d[\d\s-]{6,})", text)
    cv["contact"] = " | ".join(filter(None, [
        email.group(0) if email else "",
        phone.group(0).strip() if phone else "",
        "Saudi Arabia"]))

    cur, buf = "header", []
    for l in lines:
        low = l.strip().lower()
        matched = next((h for h in SECTION_HEADS
                        if low == h or low.startswith(h)), None)
        if matched and len(l.strip()) < 40:
            cv["sections"].setdefault(cur, []).extend(buf)
            cur, buf = matched, []
        else:
            if l.strip(): buf.append(l.strip())
    cv["sections"].setdefault(cur, []).extend(buf)
    return cv

def extract_bullets(lines):
    out = []
    for l in lines:
        m = re.match(r"^[-•·▪*]\s*(.+)$", l.strip())
        if m: out.append(m.group(1).strip())
        elif len(l.strip()) > 45 and l.strip()[0].isupper(): out.append(l.strip())
    return out

def jd_keywords(jd, n=30):
    ws = tokens(jd)
    uni = Counter(ws)
    bi = Counter(f"{a} {b}" for a,b in zip(ws,ws[1:]))
    out = [t for t,c in bi.most_common(n) if c > 1]
    out += [t for t,c in uni.most_common(n*2) if t not in " ".join(out)]
    return out[:n]

def jd_title(jd):
    m = re.search(r"(?:job title|position|role)\s*[:\-]\s*(.{3,60})", jd, re.I)
    if m: return m.group(1).strip().title()
    for l in jd.split("\n")[:6]:
        s = l.strip()
        if 6 < len(s) < 60 and JOB_WORD.search(s):
            return s.title()
    return "Target Role"

def tailor_bullet(b, kws):
    new = b
    for weak, strong in WEAK_VERBS.items():
        if new.lower().startswith(weak):
            new = strong + new[len(weak):]; break
        if weak in new.lower():
            new = re.sub(weak, strong.lower(), new, count=1, flags=re.I)
    hit = [k for k in kws if k in new.lower()]
    return new, hit

def build_tailored(cv, jd, target_title):
    kws = jd_keywords(jd)
    out = {"title": target_title, "keywords": kws}

    skills_lines = (cv["sections"].get("skills",[]) +
                    cv["sections"].get("technical skills",[]) +
                    cv["sections"].get("soft skills",[]))
    skills = []
    for l in skills_lines:
        for part in re.split(r"[,\u2022•|]", l):
            p = part.strip()
            if 2 < len(p) < 45: skills.append(p)
    ranked = sorted(set(skills),
                    key=lambda s: -sum(1 for k in kws if k in s.lower()))
    out["skills"] = ranked

    exp_lines = cv["sections"].get("experience", [])
    bullets = extract_bullets(exp_lines)
    tailored = []
    for b in bullets:
        nb, hits = tailor_bullet(b, kws)
        tailored.append({"text": nb, "hits": hits,
                         "score": len(hits) + (1 if re.search(r"\d", nb) else 0)})
    tailored.sort(key=lambda x: -x["score"])
    out["bullets"] = tailored
    out["gaps"] = [k for k in kws
                   if k not in " ".join(skills + bullets).lower()][:12]
    out["summary"] = (
        f"{cv.get('headline') or 'Graduate'} seeking a {target_title} role. "
        f"Hands-on with {', '.join(ranked[:3]) if ranked else 'core tools'}. "
        f"[Add one measurable achievement here.]")
    out["education"] = cv["sections"].get("education", [])
    out["certs"] = cv["sections"].get("certification", []) + \
                   cv["sections"].get("certifications", [])
    out["experience_raw"] = exp_lines
    return out


def make_docx(cv, t):
    import docx
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    d = docx.Document()
    for s in d.sections:
        s.top_margin = s.bottom_margin = Pt(36)
        s.left_margin = s.right_margin = Pt(46)
    n = d.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(10.5)

    h = d.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(cv["name"]); r.bold = True; r.font.size = Pt(19)
    sub = d.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(t["title"]).font.size = Pt(11.5)
    c = d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.add_run(cv["contact"]).font.size = Pt(9.5)

    def head(txt):
        p = d.add_paragraph(); p.space_before = Pt(11); p.space_after = Pt(2)
        rr = p.add_run(txt.upper()); rr.bold = True; rr.font.size = Pt(11)
        rr.font.color.rgb = RGBColor(0x1F,0x2A,0x44)

    head("Professional Summary"); d.add_paragraph(t["summary"])
    head("Education")
    for l in t["education"]: d.add_paragraph(l)
    head("Skills")
    if t["skills"]: d.add_paragraph(" • ".join(t["skills"][:16]))
    head("Experience")
    for l in t["experience_raw"]:
        if not re.match(r"^[-•·▪*]", l.strip()): d.add_paragraph(l)
    for b in t["bullets"]:
        d.add_paragraph(b["text"], style="List Bullet")
    if t["certs"]:
        head("Certifications")
        for l in t["certs"]: d.add_paragraph(l)

    buf = io.BytesIO(); d.save(buf); buf.seek(0)
    return buf.getvalue()


def make_pdf(cv, t):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                    ListFlowable, ListItem, HRFlowable)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=14*mm,
                            bottomMargin=14*mm, leftMargin=16*mm, rightMargin=16*mm)
    ss = getSampleStyleSheet()
    nm = ParagraphStyle("nm", parent=ss["Title"], fontSize=19, spaceAfter=2)
    rl = ParagraphStyle("rl", parent=ss["Normal"], fontSize=11.5,
                        alignment=1, spaceAfter=2)
    ct = ParagraphStyle("ct", parent=ss["Normal"], fontSize=9,
                        alignment=1, textColor=colors.grey, spaceAfter=8)
    hd = ParagraphStyle("hd", parent=ss["Heading2"], fontSize=11,
                        spaceBefore=9, spaceAfter=3,
                        textColor=colors.HexColor("#1F2A44"))
    bd = ParagraphStyle("bd", parent=ss["Normal"], fontSize=10, leading=13.5)

    def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;")

    f = [Paragraph(esc(cv["name"]), nm), Paragraph(esc(t["title"]), rl),
         Paragraph(esc(cv["contact"]), ct),
         HRFlowable(width="100%", color=colors.HexColor("#CBD5E1")),
         Paragraph("PROFESSIONAL SUMMARY", hd), Paragraph(esc(t["summary"]), bd)]

    f.append(Paragraph("EDUCATION", hd))
    for l in t["education"]: f.append(Paragraph(esc(l), bd))
    if t["skills"]:
        f.append(Paragraph("SKILLS", hd))
        f.append(Paragraph(esc(" • ".join(t["skills"][:16])), bd))
    f.append(Paragraph("EXPERIENCE", hd))
    for l in t["experience_raw"]:
        if not re.match(r"^[-•·▪*]", l.strip()):
            f.append(Paragraph(f"<b>{esc(l)}</b>", bd))
    if t["bullets"]:
        f.append(ListFlowable(
            [ListItem(Paragraph(esc(b["text"]), bd), leftIndent=10)
             for b in t["bullets"]], bulletType="bullet", start="•", leftIndent=12))
    if t["certs"]:
        f.append(Paragraph("CERTIFICATIONS", hd))
        for l in t["certs"]: f.append(Paragraph(esc(l), bd))

    doc.build(f); buf.seek(0)
    return buf.getvalue()


# ═══════════════════════════════════════ sidebar
with st.sidebar:
    st.markdown("### 📍 where")
    all_saudi = st.checkbox("All of Saudi Arabia", value=True)
    chosen = [] if all_saudi else st.multiselect("Cities", list(SAUDI_CITIES),
                                                 default=["Riyadh","Medina"])
    keep_blank = st.checkbox("Include unlisted locations", value=False)

    st.markdown("### 🎓 level")
    level = st.radio("Show", ["Entry level", "Experienced"], index=0)
    entry_only = level == "Entry level"

    st.markdown("### 🔌 sources")
    use_private = st.checkbox("Company ATS boards", value=True)
    use_gov = st.checkbox("Government portals", value=True)
    use_boards = st.checkbox("Indeed + Bayt", value=True,
                             help="LinkedIn excluded — it blocks hard.")
    min_score = st.slider("Min match score", 0, 120, 15)
    st.markdown("---")
    st.caption(f"Polite mode · {MIN_DELAY}–{MAX_DELAY}s delays · "
               f"{CACHE_HOURS}h cache · auto back-off on 429")


# ═══════════════════════════════════════ game
GAME_HTML = """
<div style="font-family:system-ui;text-align:center;padding:2px">
 <div style="display:flex;justify-content:center;gap:14px;margin-bottom:6px;
      font-weight:700;font-size:.8rem;color:#374151">
   <span id="lvl">lvl 1/5</span><span id="mv">moves 0</span><span id="stars"></span>
 </div>
 <div id="tubes" style="display:flex;gap:9px;justify-content:center;
      align-items:flex-end;height:146px"></div>
 <div id="msg" style="margin-top:6px;font-size:.95rem;font-weight:800;
      min-height:20px"></div>
 <button id="rst" style="margin-top:2px;padding:5px 14px;border-radius:10px;
   border:2px solid #111;background:#FDE68A;font-weight:700;cursor:pointer;
   font-size:.76rem;box-shadow:2px 2px 0 #111">restart</button>
</div>
<style>
.tube{width:33px;border:3px solid #111;border-top:none;border-radius:0 0 17px 17px;
 display:flex;flex-direction:column-reverse;align-items:center;padding-bottom:4px;
 gap:2px;cursor:pointer;background:#fff;
 transition:transform .18s cubic-bezier(.34,1.56,.64,1)}
.tube.sel{transform:translateY(-10px)}
.ball{width:23px;height:21px;border-radius:50%;border:2px solid rgba(0,0,0,.22);
 animation:drop .22s cubic-bezier(.34,1.56,.64,1)}
@keyframes drop{from{transform:translateY(-16px);opacity:.4}
to{transform:translateY(0);opacity:1}}
</style>
<script>
const C=['#EF4444','#3B82F6','#22C55E','#EAB308','#A855F7','#EC4899'];
const L=[{c:2,e:1,h:3},{c:3,e:1,h:3},{c:4,e:2,h:4},{c:5,e:2,h:4},{c:6,e:2,h:4}];
let lvl=0,tubes=[],sel=null,moves=0,stars=0,cap=4,lock=false;
const $=id=>document.getElementById(id);

function build(){
  const s=L[lvl];cap=s.h;let b=[];
  for(let c=0;c<s.c;c++)for(let k=0;k<s.h;k++)b.push(c);
  for(let i=b.length-1;i>0;i--){const j=0|Math.random()*(i+1);[b[i],b[j]]=[b[j],b[i]];}
  tubes=[];
  for(let t=0;t<s.c;t++)tubes.push(b.slice(t*s.h,(t+1)*s.h));
  for(let e=0;e<s.e;e++)tubes.push([]);
  moves=0;sel=null;lock=false;$('msg').textContent='';draw();
}
const won=()=>tubes.every(t=>!t.length||(t.length===cap&&t.every(x=>x===t[0])));

function draw(){
  const box=$('tubes');box.innerHTML='';
  $('lvl').textContent='lvl '+(lvl+1)+'/5';
  $('mv').textContent='moves '+moves;
  $('stars').textContent='⭐'.repeat(stars);
  tubes.forEach((t,i)=>{
    const d=document.createElement('div');
    d.className='tube'+(sel===i?' sel':'');
    d.style.height=(cap*25+8)+'px';
    t.forEach(c=>{const e=document.createElement('div');
      e.className='ball';e.style.background=C[c];d.appendChild(e);});
    d.onclick=()=>{
      if(lock)return;
      if(sel===null){if(t.length)sel=i;}
      else if(sel===i){sel=null;}
      else{
        const f=tubes[sel],o=tubes[i];
        if(f.length&&o.length<cap&&(!o.length||o[o.length-1]===f[f.length-1])){
          o.push(f.pop());moves++;
        }
        sel=null;
        if(won()){
          lock=true;
          if(lvl<4){
            $('msg').innerHTML='<span style="color:#059669">clear! 🫧</span>';
            stars++;lvl++;setTimeout(build,750);draw();return;
          }
          stars=5;
          $('msg').innerHTML='<div style="font-size:1.2rem">⭐⭐⭐⭐⭐</div>'+
            '<div style="color:#DB2777;font-size:1.02rem">GOOD GIRL LULUTY!</div>';
          draw();return;
        }
      }
      draw();
    };
    box.appendChild(d);
  });
}
$('rst').onclick=build;build();
</script>
"""

# ═══════════════════════════════════════ tabs
t_search, t_cv = st.tabs(["🔎 Find jobs", "📝 CV lab"])
profile, cv_text, field, field_kws, label = None, "", None, [], ""

with t_search:
    left, right = st.columns([5, 3])

    with left:
        m1, m2, m3 = st.tabs(["Upload CV", "Paste JD", "Keywords"])
        with m1:
            up = st.file_uploader("Drop the CV", type=["pdf","docx","txt"],
                                  key="cvsearch")
            if up:
                cv_text = read_upload(up)
                st.session_state["cv_text"] = cv_text
                profile, label = build_profile(cv_text), "cv"
                field, field_kws = detect_field(cv_text)
                st.success(f"Parsed {len(cv_text):,} chars")
                if field:
                    st.info(f"Field: **{field.title()}** — matching jobs get +20")
                st.markdown("".join(f'<span class="badge b-blue">{k}</span>'
                            for k in list(profile)[:12]), unsafe_allow_html=True)
        with m2:
            jd = st.text_area("Paste the job description", height=170)
            if jd.strip():
                profile, label = build_profile(jd), "jd"
                st.session_state["jd_text"] = jd
        with m3:
            kw = st.text_input("Titles / keywords",
                "data analyst, business analyst, information systems, database")
            if kw.strip() and not profile:
                profile = {t.strip().lower():5 for t in kw.split(",") if t.strip()}
                label = "keywords"

        go = st.button("🐸  LET'S GOOO", type="primary", use_container_width=True)

    with right:
        st.markdown("##### 🫧 ball sort — play while it scans")
        components.html(GAME_HTML, height=250)

    if go:
        if not profile:
            st.error("Give me a CV, a JD, or keywords first."); st.stop()
        if not all_saudi and not chosen:
            st.error("Pick a city."); st.stop()

        employers = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
        jobcache = load_cache()
        results, dead, notes = [], [], []
        bar, status = st.progress(0.0), st.empty()

        if use_private:
            if not employers:
                status.info("First run — probing company APIs. Go sort some balls.")
                for i,slug in enumerate(CANDIDATE_SLUGS):
                    a = probe(slug)
                    if a: employers[slug]=a
                    bar.progress((i+1)/len(CANDIDATE_SLUGS)*0.4)
                    polite_sleep()
                json.dump(employers, open(CACHE,"w"), indent=2)
            items = list(employers.items())
            for i,(slug,ats) in enumerate(items):
                k=f"ats:{slug}"
                if k in jobcache and cache_fresh(jobcache[k]):
                    jobs=jobcache[k]["jobs"]; status.write(f"📦 {slug} (cached)")
                else:
                    status.write(f"🌐 {slug}…")
                    jobs=fetch_ats(slug,ats)
                    jobcache[k]={"ts":datetime.now().isoformat(),"jobs":jobs}
                    polite_sleep()
                for j in jobs:
                    if loc_ok(j["location"],chosen,all_saudi,keep_blank):
                        p,h=score(j,profile,entry_only,field_kws)
                        if p>=min_score:
                            j["score"],j["matched"],j["src"]=p,", ".join(h),"ATS"
                            results.append(j)
                bar.progress(0.4+(i+1)/max(len(items),1)*0.25)

        if use_gov:
            items=list(GOV_ENTITIES.items())
            for i,(name,url) in enumerate(items):
                k=f"gov:{name}"
                if k in jobcache and cache_fresh(jobcache[k]):
                    jobs=jobcache[k]["jobs"]
                else:
                    status.write(f"🏛 {name}…")
                    jobs=fetch_gov(name,url)
                    jobcache[k]={"ts":datetime.now().isoformat(),"jobs":jobs}
                    polite_sleep()
                if not jobs: dead.append(name)
                for j in jobs:
                    p,h=score(j,profile,entry_only,field_kws)
                    if p>=min_score:
                        j["score"],j["matched"],j["src"]=p,", ".join(h),"GOV"
                        results.append(j)
                bar.progress(0.65+(i+1)/len(items)*0.2)

        if use_boards:
            term=list(profile)[0]
            status.write("🔍 Indeed + Bayt…")
            jobs,err=fetch_jobspy(term, chosen or ["Riyadh"], all_saudi)
            if err: notes.append(err)
            for j in jobs:
                if loc_ok(j["location"],chosen,all_saudi,True):
                    p,h=score(j,profile,entry_only,field_kws)
                    if p>=min_score:
                        j["score"],j["matched"],j["src"]=p,", ".join(h),"BOARD"
                        results.append(j)
            bar.progress(0.95)

        save_cache(jobcache); bar.progress(1.0); status.empty()

        seen,uniq=set(),[]
        for j in sorted(results,key=lambda x:-x["score"]):
            if j["url"] not in seen: seen.add(j["url"]); uniq.append(j)
        st.session_state["results"]=uniq

        st.markdown(f"## 🎯 {len(uniq)} matches — {random.choice(HYPE)}")
        if not uniq:
            st.warning("Nothing. Lower min score, add cities, or try 'Experienced'.")

        for j in uniq:
            bd={"ATS":"b-green","GOV":"b-blue","BOARD":"b-pink"}[j["src"]]
            chips="".join(f'<span class="badge b-gray">{m}</span>'
                          for m in j["matched"].split(", ") if m)
            st.markdown(f"""<div class="jobcard">
              <div style="display:flex;justify-content:space-between">
                <div style="flex:1">
                  <div style="font-size:1.1rem;font-weight:700">{j['title']}</div>
                  <div style="color:#6B7280;font-size:.85rem;margin:3px 0 7px">
                    {j['company']} · {j['location'] or 'n/a'}
                    <span class="badge {bd}">{j['src']}</span></div>
                  {chips}</div>
                <div style="font-size:1.55rem;font-weight:700;color:#A855F7">
                  {j['score']}</div></div>
              <div style="margin-top:8px"><a href="{j['url']}" target="_blank"
                style="font-weight:700;color:#3B82F6">open posting ↗</a></div>
            </div>""", unsafe_allow_html=True)

        if uniq:
            import csv as _csv
            b=io.StringIO(); w=_csv.writer(b)
            w.writerow(["score","source","company","title","location","matched","url"])
            for j in uniq:
                w.writerow([j["score"],j["src"],j["company"],j["title"],
                            j["location"],j["matched"],j["url"]])
            st.download_button("⬇ CSV", b.getvalue(),
                f"luluty_{datetime.now():%Y-%m-%d}.csv","text/csv")
        if dead:
            st.info("No readable listings from: "+", ".join(dead)+
                    " — JavaScript-rendered or login-walled. Open manually.")
        for n in notes: st.warning(n)


# ═══════════════════════════════════════ CV LAB
with t_cv:
    st.markdown("### 📝 CV lab — tailor the CV to one job")
    st.caption("Reorders skills, strengthens verbs, surfaces the JD's language, "
               "and exports a single-column ATS-safe file. It will not invent "
               "experience — fabrications fail at interview and employers verify.")

    c1, c2 = st.columns(2)
    with c1:
        u2 = st.file_uploader("CV", type=["pdf","docx","txt"], key="cvlab")
        if u2:
            st.session_state["cv_text"] = read_upload(u2)
        text = st.session_state.get("cv_text","")
        if text: st.success(f"Loaded — {len(text):,} chars")
    with c2:
        target_jd = st.text_area("Paste the job description you're applying to",
                                 height=190, key="tjd")

    if text and target_jd.strip():
        cv = parse_cv(text)
        title = st.text_input("Target job title (appears under the name)",
                              jd_title(target_jd))
        t = build_tailored(cv, target_jd, title)

        st.markdown("#### Skills — JD matches first")
        st.markdown("".join(
            f'<span class="badge {"b-green" if any(k in s.lower() for k in t["keywords"]) else "b-gray"}">{s}</span>'
            for s in t["skills"][:20]), unsafe_allow_html=True)

        st.markdown("#### Experience bullets — strongest match first")
        for b in t["bullets"]:
            tag = (f'<span class="badge b-amber">{len(b["hits"])} JD hits</span>'
                   if b["hits"] else '<span class="badge b-gray">no match</span>')
            st.markdown(f'<div style="margin-bottom:7px">{tag} {b["text"]}</div>',
                        unsafe_allow_html=True)

        if t["gaps"]:
            st.markdown("#### ⚠ JD terms missing from the CV")
            st.caption("Add only what's genuinely true.")
            st.markdown("".join(f'<span class="badge b-pink">{g}</span>'
                        for g in t["gaps"]), unsafe_allow_html=True)

        st.markdown("#### Summary line — edit before sending")
        t["summary"] = st.text_area("Summary", t["summary"], height=80)

        st.markdown("#### 📥 Download")
        d1, d2 = st.columns(2)
        safe = re.sub(r"\W+","_", title)[:30]
        try:
            d1.download_button("⬇ Word (.docx)", make_docx(cv, t), f"CV_{safe}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True)
        except Exception as e:
            d1.error(f"DOCX failed: {e}")
        try:
            d2.download_button("⬇ PDF", make_pdf(cv, t), f"CV_{safe}.pdf",
                "application/pdf", use_container_width=True)
        except Exception as e:
            d2.error(f"PDF failed — pip install reportlab ({e})")

        with st.expander("Before sending"):
            st.markdown("""
- Read every bullet. If a rephrase changed the meaning, fix it.
- Add real numbers where gaps were flagged — how many queries, events, reports.
- Match the job title exactly as the posting writes it.
- Send **.docx** unless the portal demands PDF.
- One page for entry level.
            """)
    else:
        st.info("Load a CV and paste a JD to generate a tailored version.")