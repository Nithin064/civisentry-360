import os, json
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title='CiviSentry 360', page_icon='🛡️', layout='wide', initial_sidebar_state='expanded')

# ---------- Data and knowledge ----------
DATA_FILE = Path(__file__).parent / 'civisentry_simulated_data.csv'
KNOWLEDGE = {
    'possible_fall': ('FALL RESPONSE', 'Ensure scene safety. Check whether the worker responds. Notify the site supervisor. Initiate emergency response. Avoid unnecessary movement of a potentially injured worker.'),
    'heat_stress': ('HEAT-STRESS GUIDANCE', 'During hot conditions, provide water, shade and recovery periods. Monitor weakness, dizziness, confusion and unusual fatigue. Notify the supervisor before resuming heavy work.'),
    'ppe_gap': ('PPE GUIDANCE', 'Workers need task-appropriate PPE. Work at height requires suitable fall-protection equipment and supervisor verification before work begins.'),
    'waterlogging': ('SITE HOUSEKEEPING', 'Inspect access routes and excavation edges after rainfall. Isolate electrical hazards and remove standing water before allowing normal work.'),
    'normal': ('ROUTINE MONITORING', 'Maintain hydration, PPE and scheduled supervisor checks. Continue monitoring the worker and active site zone.')
}

def load_data():
    if DATA_FILE.exists(): return pd.read_csv(DATA_FILE, parse_dates=['timestamp'])
    return pd.DataFrame()

from civisentry_core import classify

def risk_from_values(temp, duration, tilt, acceleration):
    result = classify(temp, 65, tilt, acceleration, duration)
    return result.score, result.level, result.event

def retrieve(event): return KNOWLEDGE.get(event, KNOWLEDGE['normal'])

def local_response(event, temp, duration, zone):
    title, evidence = retrieve(event)
    responses = {
        'possible_fall': ('Possible fall detected. Make the area safe, verify worker response, notify the supervisor and initiate the site emergency procedure.', 'விழும் அபாயம் கண்டறியப்பட்டது. சுற்றுப்புறத்தைப் பாதுகாப்பாக்கி, பணியாளரின் நிலையைச் சரிபார்த்து, மேற்பார்வையாளருக்குத் தெரிவிக்கவும்.'),
        'heat_stress': (f'High heat-stress risk detected at {temp:.0f}°C after {duration:.0f} minutes. Move the worker to shade, provide water and allow recovery before heavy work.', 'அதிக வெப்ப அழுத்த அபாயம் கண்டறியப்பட்டது. நிழலுக்குச் சென்று தண்ணீர் குடித்து ஓய்வு எடுக்கவும்.'),
        'ppe_gap': ('PPE gap detected. Stop the relevant task until the required protective equipment is verified by the supervisor.', 'பாதுகாப்பு உபகரணக் குறைபாடு கண்டறியப்பட்டது. தேவையான உபகரணங்கள் சரிபார்க்கப்படும் வரை பணியை நிறுத்தவும்.'),
        'waterlogging': ('Waterlogging risk detected. Inspect access routes, excavation edges and electrical hazards before work continues.', 'நீர் தேக்கம் கண்டறியப்பட்டது. பணி தொடரும் முன் பாதைகள், அகழி விளிம்புகள் மற்றும் மின் அபாயங்களைச் சரிபார்க்கவும்.'),
        'normal': ('Worker condition appears normal. Continue work with planned hydration, PPE and supervisor checks.', 'பணியாளரின் நிலை சாதாரணமாக உள்ளது. தண்ணீர், PPE மற்றும் மேற்பார்வையாளர் சரிபார்ப்பைத் தொடர்ந்து பின்பற்றவும்.')
    }
    en, ta = responses.get(event, responses['normal'])
    return en, ta, title, evidence

def llm_response(event, temp, duration, zone, evidence):
    """Optional Gemini integration. Falls back to a grounded response if no key is configured."""
    key = os.getenv('GEMINI_API_KEY') or st.secrets.get('GEMINI_API_KEY', None)
    if not key: return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f'''You are CiviSentry 360, a construction safety copilot for Tamil Nadu.\nEvent: {event}\nTemperature: {temp} C\nWork duration: {duration} minutes\nZone: {zone}\nRetrieved safety evidence: {evidence}\nReturn concise English supervisor action, a short Tamil worker instruction, and one sentence explaining the evidence. Do not diagnose illness, invent laws, or claim field validation.'''
        return model.generate_content(prompt).text
    except Exception as e:
        return f'Live LLM unavailable; grounded offline fallback used. ({type(e).__name__})'

# ---------- Theme ----------
st.markdown('''<style>
/* CiviSentry 360 accessible projector-first theme */
:root{--navy:#0b1f35;--blue:#1464a5;--cyan:#007f86;--ink:#10253d;--muted:#526b83;--line:#d7e3ee;--surface:#ffffff;--soft:#f3f7fb;--red:#b42332;--amber:#9a6500;--green:#087443}
[data-testid="stAppViewContainer"]{background:#f4f7fb;color:var(--ink)}
[data-testid="stHeader"]{background:rgba(244,247,251,.92)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1f35,#123b5d);border-right:1px solid #1c5277}
[data-testid="stSidebar"] *{color:#f5fbff!important}
[data-testid="stSidebar"] .stCaption{color:#c4d7e5!important}
.block-container{max-width:1450px;padding-top:2.2rem;padding-bottom:3rem}
h1,h2,h3{color:var(--navy)!important;letter-spacing:-.02em}
.stMarkdown p,.stMarkdown li,.stCaption{color:var(--ink)}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:14px;padding:15px 17px;box-shadow:0 4px 14px rgba(16,37,61,.06)}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-weight:650}
[data-testid="stMetricValue"]{color:var(--navy)!important;font-weight:800}
[data-testid="stMetricDelta"]{font-weight:700}
.kpi{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 4px 14px rgba(16,37,61,.06)}
.kpi small{color:var(--muted)}.kpi b{font-size:28px;color:var(--navy);display:block;margin:5px 0}.muted{color:var(--muted)}
.stButton>button{border-radius:9px;border:1px solid #9bb9cf;background:#fff;color:var(--navy);font-weight:700;min-height:2.5rem}
.stButton>button:hover{border-color:var(--blue);color:var(--blue);background:#eef7ff}
[data-testid="stAlert"]{border-radius:10px}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:10px}
div[data-baseweb="tab-list"]{gap:8px}button[data-baseweb="tab"]{font-weight:700}
.notice{padding:12px;border-radius:10px;background:#fff5d6;border:1px solid #e5bd55;color:#6d4b00}
</style>''', unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.markdown('## 🛡️ CiviSentry 360')
st.sidebar.caption('Construction Safety & Site Intelligence')
page = st.sidebar.radio('Navigation', ['Overview','Worker Safety','Environment','Site Zones','AI Copilot','Simulator','Dataset'], index=0)
st.sidebar.divider()
st.sidebar.warning('SIMULATION MODE')
st.sidebar.caption('Synthetic telemetry is used for prototype validation. It is not field-measured or medically validated.')
st.sidebar.caption('Designed for Tamil Nadu construction contexts.')

st.title('CiviSentry 360')
st.caption('Multimodal AI construction safety and site intelligence platform • REC-AIX 2026')

_df = load_data()

# ---------- Overview ----------
if page == 'Overview':
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown('<div class="kpi"><small>Active workers</small><b>24</b><span class="muted">Monitored today</span></div>', unsafe_allow_html=True)
    c2.markdown('<div class="kpi"><small>Site risk index</small><b>74/100</b><span class="muted">High attention</span></div>', unsafe_allow_html=True)
    c3.markdown('<div class="kpi"><small>Open alerts</small><b>03</b><span class="muted">2 need action</span></div>', unsafe_allow_html=True)
    c4.markdown('<div class="kpi"><small>PPE compliance</small><b>86%</b><span class="muted">+7% this week</span></div>', unsafe_allow_html=True)
    st.subheader('Site risk overview')
    left,right = st.columns([1.3,1])
    with left:
        st.metric('Overall site risk', '74 / 100', 'HIGH')
        st.progress(.74)
        st.warning('Primary drivers: heat exposure and scaffolding PPE gap.')
        if not _df.empty:
            chart = _df.groupby('event', as_index=False)['risk_score'].mean().sort_values('risk_score', ascending=False)
            st.bar_chart(chart.set_index('event'))
    with right:
        st.markdown('### Live alert queue')
        st.error('🔴 Possible fall · TN-CW-014 · Scaffolding')
        st.warning('🟡 Heat-stress risk · TN-CW-009 · Concrete')
        st.warning('🟡 Harness missing · TN-CW-021 · Scaffolding')
        st.markdown('### Today’s AI insight')
        st.info('Highest combined risk occurs between 11:00 and 14:00. Reschedule heavy manual work and increase hydration checks.')

# ---------- Worker ----------
elif page == 'Worker Safety':
    st.subheader('Worker safety monitor')
    scenario = st.selectbox('Select simulated scenario', ['Normal work','Heat-stress risk','Possible fall'])
    vals = {'Normal work':(30,22,4,1.0,'normal'),'Heat-stress risk':(39,96,8,1.1,'heat_stress'),'Possible fall':(31,110,68,3.8,'possible_fall')}[scenario]
    temp,duration,tilt,acc,event = vals
    score,level,detected = risk_from_values(temp,duration,tilt,acc)
    a,b,c,d = st.columns(4)
    a.metric('Temperature',f'{temp} °C'); b.metric('Work duration',f'{duration} min'); c.metric('Foot tilt',f'{tilt}°'); d.metric('Acceleration',f'{acc} g')
    st.metric('Risk score',f'{score}/100',level)
    st.progress(score/100)
    en,ta,title,evidence = local_response(event,temp,duration,'Scaffolding')
    st.subheader(f'{level}: {title}')
    st.error(en) if score >= 81 else st.warning(en) if score >= 61 else st.success(en)
    st.markdown(f'### Tamil worker instruction\n{ta}')
    st.caption('In final hardware integration, these values can come from an IMU, temperature sensor and pressure sensor. Current values are simulated.')

# ---------- Environment ----------
elif page == 'Environment':
    st.subheader('Environment and heat-risk intelligence')
    a,b,c,d = st.columns(4); a.metric('Temperature','39°C'); b.metric('Humidity','72%'); c.metric('Heat index','46°C','High'); d.metric('Waterlogging','No')
    st.warning('High heat exposure window: 11:00–14:00')
    if not _df.empty:
        hourly = _df.copy(); hourly['hour'] = hourly.timestamp.dt.hour
        st.line_chart(hourly.groupby('hour')['temperature_c'].mean())
    st.info('AI recommendation: move high-intensity outdoor work to before 11:00 or after 16:00; keep water and shaded recovery space near the active zone.')
    st.markdown('**Tamil:** கடுமையான வெளிப்புற பணிகளை காலை 11 மணிக்கு முன் அல்லது மாலை 4 மணிக்குப் பிறகு திட்டமிடவும்.')

# ---------- Zones ----------
elif page == 'Site Zones':
    st.subheader('Construction site zones')
    zones = pd.DataFrame({'Zone':['A · Excavation','B · Scaffolding','C · Concrete','D · Materials'],'Risk score':[62,94,25,71],'Primary risk':['Edge protection','Harness gap','Heat exposure','Trip hazard'],'Action':['Inspect barricade','Verify harness before work','Hydration checks','Clear pathway']})
    st.dataframe(zones, use_container_width=True, hide_index=True)
    st.error('Zone B: CRITICAL — verify harness and barricade before work.')
    st.warning('Zone D: HIGH — move steel away from worker pathway.')
    st.info('Zone A: inspect excavation edge protection after rainfall.')

# ---------- Copilot ----------
elif page == 'AI Copilot':
    st.subheader('CiviSentry AI Copilot')
    event_label = st.selectbox('Detected event', ['possible_fall','heat_stress','ppe_gap','waterlogging','normal'])
    zone = st.selectbox('Site zone',['Scaffolding','Excavation','Concrete','Materials'])
    temp = st.number_input('Temperature °C', 20.0, 50.0, 39.0)
    duration = st.number_input('Work duration (minutes)', 0, 240, 96)
    en,ta,title,evidence = local_response(event_label,temp,duration,zone)
    st.markdown(f'**Retrieved source:** `{title}`')
    st.info(evidence)
    live = llm_response(event_label,temp,duration,zone,evidence)
    if live:
        st.success('Live LLM response generated using GEMINI_API_KEY')
        st.write(live)
    else:
        st.markdown('### Grounded fallback recommendation')
        st.write(en)
        st.markdown('### Tamil worker instruction')
        st.markdown(f'### {ta}')
        st.caption('To enable live LLM generation, add GEMINI_API_KEY in deployment secrets. The fallback is intentionally retained for offline reliability.')

# ---------- Simulator ----------
elif page == 'Simulator':
    st.subheader('What-if risk simulator')
    a,b,c,d = st.columns(4)
    temp = a.slider('Temperature °C',25,45,39); duration=b.slider('Work duration (min)',0,180,110); tilt=c.slider('Foot tilt °',0,90,68); acc=d.slider('Acceleration (g)',0.5,4.5,3.8)
    score,level,event = risk_from_values(temp,duration,tilt,acc)
    st.metric('Risk engine result',f'{score}/100',f'{level} · {event}')
    st.progress(score/100)
    en,ta,title,evidence = local_response(event,temp,duration,'Scaffolding')
    st.write(en); st.markdown(f'**Tamil:** {ta}'); st.info(f'RAG evidence: {evidence}')
    st.caption('Synthetic values are used to validate the workflow; they are not claimed as live measurements.')

# ---------- Dataset ----------
elif page == 'Dataset':
    st.subheader('Synthetic telemetry dataset')
    st.caption('48 rows created for prototype validation. Download and inspect the data used by this dashboard.')
    st.download_button('Download CSV', _df.to_csv(index=False).encode('utf-8'), 'civisentry_simulated_data.csv', 'text/csv')
    st.dataframe(_df, use_container_width=True, hide_index=True)

st.divider(); st.caption('CiviSentry 360 is an early-stage decision-support prototype. It does not replace a qualified safety officer, emergency service or medical assessment.')
