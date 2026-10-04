import os, re, io, json
import streamlit as st
import pandas as pd

st.set_page_config(page_title='AI SEO Product Description Generator', page_icon='🛍️', layout='wide')

st.markdown('''<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.stApp {background:#f2f8fa; color:#163b48;}
section[data-testid="stSidebar"] {background:#e1f1ed; border-right:1px solid #b8d8d5;}
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {color:#163b48;}
h1, h2, h3 {color:#12536a;}
.hero {padding:1.2rem 1.4rem; border-radius:12px; background:linear-gradient(115deg,#dceefa 0%,#e1f3ed 72%,#fbe9e6 100%); border:1px solid #c2dfe0; border-left:4px solid #e6a9a4; margin-bottom:1rem;}
.hero h1 {margin:0 0 .25rem 0; color:#12536a;}
.small {color:#315765; font-size:.92rem;}
.card {padding:1rem; border:1px solid #b8d8d5; border-radius:8px; background:#ffffff;}
[data-testid="stWidgetLabel"] p, [role="radiogroup"] label, [role="radiogroup"] label p {color:#194c5b; font-weight:600;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {color:#315765;}
[data-baseweb="input"] > div, [data-baseweb="textarea"] > div, [data-baseweb="select"] > div {background:#ffffff; border-color:#78aeb4;}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] [role="combobox"] {color:#163b48;}
[data-baseweb="input"] input:disabled, [data-baseweb="textarea"] textarea:disabled {color:#3d5963; -webkit-text-fill-color:#3d5963; opacity:1;}
[data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="popover"] ul {background:#ffffff; color:#163b48;}
[data-baseweb="popover"] [role="option"], [data-baseweb="menu"] li {color:#163b48;}
[data-testid="stAlert"], [data-testid="stAlert"] p {color:#163b48;}
[data-testid="stCode"] pre, [data-testid="stCode"] code, [data-testid="stCode"] code span {background:#e4f4f6; color:#00758a; font-weight:700;}
div.stButton > button:not([kind="primary"]), [data-testid="stDownloadButton"] button {background:#e1f1ed; border:1px solid #78aeb4; color:#12536a;}
div.stButton > button:not([kind="primary"]):hover, [data-testid="stDownloadButton"] button:hover {background:#d1e9e4; border-color:#528f98; color:#103e51;}
div[data-testid="stMetric"] {background:#e1f1ed; border:1px solid #b8d8d5; border-radius:8px; padding:.75rem;}
div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {color:#12536a;}
div.stButton > button[kind="primary"] {background:#126c78; border:1px solid #0f5967; color:#ffffff; font-weight:700;}
div.stButton > button[kind="primary"]:hover {background:#0e5967; border-color:#0b4855; color:#ffffff;}
div.stButton > button:focus {outline:3px solid #e6a9a4; outline-offset:2px;}
hr {border-color:#bfd9da;}
</style>''', unsafe_allow_html=True)

DEFAULT_PROMPT = '''You are an SEO product copywriter for an e-commerce catalog.
Use ONLY the product information supplied below. Never invent or infer any factual detail.

PRODUCT INPUT
Product ID: {product_id}
Product Name: {product_name}
Category: {category}
Price (INR): {price_inr}
Key Attributes: {key_attributes}
Target Customer: {target_customer}

TASK
1. Write an SEO-friendly product description of approximately 60 words.
2. Generate exactly 5 concise bullet points.
3. Create one SEO-friendly meta title of no more than 60 characters.
4. Use the product name naturally and use relevant supplied attributes without keyword stuffing.
5. Write for the stated target customer.
6. Preserve supplied numbers, units and specifications exactly.
7. If a fact is not explicitly provided, omit it rather than guessing.
8. Do not make unsupported medical, safety, quality, superiority or performance claims.

OUTPUT FORMAT
DESCRIPTION:
...

KEY FEATURES:
- ...
- ...
- ...
- ...
- ...

META TITLE:
...'''

@st.cache_data
def load_products(path='T47_SEO_Product_Description_Generator_COMPLETE.xlsx'):
    return pd.read_excel(path, sheet_name='Selected_Products')

try:
    products = load_products()
except Exception:
    products = pd.DataFrame(columns=['product_id','product_name','category','price_inr','key_attributes','target_customer'])

def parse_attributes(s):
    attrs=[]
    for part in str(s).split(';'):
        part=part.strip()
        if not part: continue
        bits=part.split(' ',1)
        attrs.append((bits[0], bits[1] if len(bits)>1 else ''))
    return attrs

def demo_generate(p):
    attrs=parse_attributes(p['key_attributes'])
    phrases=[f"{k.replace('_',' ')} {v}" for k,v in attrs]
    desc=(f"{p['product_name']} is designed for {str(p['target_customer']).lower()}, with "
          + ', '.join(phrases[:3]) + '. '
          + (f"It also includes {phrases[3]}. " if len(phrases)>3 else '')
          + f"Priced at ₹{p['price_inr']}, this {str(p['category']).lower()} product presents the supplied specifications in a clear, customer-friendly format. "
          + "The content uses only the provided product information.")
    bullets=[f"{k.replace('_',' ').capitalize()}: {v}" for k,v in attrs]
    bullets.extend([
        f"Target customer: {p['target_customer']}",
        f"Category: {p['category']}",
        f"Price: ₹{p['price_inr']}",
        f"Product: {p['product_name']}",
        f"Product ID: {p['product_id']}",
    ])
    bullets=bullets[:5]
    title=f"{p['product_name']} | {', '.join(v for k,v in attrs[:2])}"[:60]
    return {'description':desc,'bullets':bullets,'meta_title':title,'raw':''}

def gemini_generate(p, api_key, prompt_template):
    from google import genai
    client=genai.Client(api_key=api_key)
    prompt=prompt_template.format(**{k:str(p[k]) for k in ['product_id','product_name','category','price_inr','key_attributes','target_customer']})
    response=client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    text=response.text or ''
    desc=re.search(r'DESCRIPTION:\s*(.*?)(?:\n\s*KEY FEATURES:|\n\s*META TITLE:|$)',text,re.S|re.I)
    bullets=re.search(r'KEY FEATURES:\s*(.*?)(?:\n\s*META TITLE:|$)',text,re.S|re.I)
    meta=re.search(r'META TITLE:\s*(.*)',text,re.S|re.I)
    d=desc.group(1).strip() if desc else text.strip()
    b=[]
    if bullets:
        b=[re.sub(r'^[-•*]\s*','',x.strip()) for x in bullets.group(1).splitlines() if x.strip()]
    b=(b+['']*5)[:5]
    t=meta.group(1).strip().splitlines()[0] if meta else ''
    return {'description':d,'bullets':b,'meta_title':t,'raw':text}

def validate(p, result):
    source=str(p['key_attributes']).lower()
    combined=(result['description']+' '+' '.join(result['bullets'])+' '+result['meta_title']).lower()
    attrs=parse_attributes(p['key_attributes'])
    matched=sum(1 for k,v in attrs if v.lower() in combined)
    unsupported=[]
    # Lightweight warning heuristic: factual numeric tokens in output not present in source.
    nums=set(re.findall(r'\b\d+(?:\.\d+)?\b',combined))
    srcnums=set(re.findall(r'\b\d+(?:\.\d+)?\b',source))
    for n in sorted(nums-srcnums):
        unsupported.append(n)
    return {
        'word_count':len(result['description'].split()),
        'meta_chars':len(result['meta_title']),
        'bullet_count':sum(bool(x.strip()) for x in result['bullets']),
        'attribute_matches':f'{matched}/{len(attrs)}',
        'numeric_warnings':', '.join(sorted(unsupported)) if unsupported else 'None',
        'status':'Review' if unsupported else 'Pre-check passed'
    }

st.markdown('<div class="hero"><h1>🛍️ AI SEO Product Description Generator</h1><div class="small">Generate a ~60-word description, exactly 5 feature bullets and an SEO meta title — while checking output against source attributes.</div></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header('⚙️ Generator settings')
    mode=st.radio('Generation mode',['Demo mode','Gemini API'],index=0)
    if mode=='Gemini API':
        api_key=st.text_input('Gemini API key',type='password',help='Use a key from Google AI Studio. Do not hard-code it into the app.')
    else:
        api_key=''
    st.caption('Demo mode works without an API key. Gemini mode uses the same master prompt stored in the workbook.')
    prompt_override=st.text_area('Master prompt',DEFAULT_PROMPT,height=300)

if products.empty:
    st.error('Selected_Products sheet could not be loaded. Keep the Excel workbook in the same folder as app.py.')
    st.stop()

# Inputs
st.subheader('1. Select or enter a product')
left,right=st.columns([1.4,1])
with left:
    choice=st.selectbox('Product from the 50-product sample',products['product_id'].tolist())
    p=products.loc[products['product_id']==choice].iloc[0].to_dict()
    st.text_input('Product name',value=str(p['product_name']),disabled=True)
    st.text_input('Category',value=str(p['category']),disabled=True)
with right:
    st.number_input('Price (₹)',value=int(p['price_inr']),disabled=True)
    st.text_input('Target customer',value=str(p['target_customer']),disabled=True)
    st.text_area('Key attributes',value=str(p['key_attributes']),height=90,disabled=True)

if st.button('✨ Generate SEO Content',type='primary',use_container_width=True):
    try:
        with st.spinner('Generating and validating content...'):
            if mode=='Gemini API':
                if not api_key:
                    st.warning('Enter a Gemini API key or switch to Demo mode.')
                    st.stop()
                result=gemini_generate(p,api_key,prompt_override)
                genmode='Gemini API'
            else:
                result=demo_generate(p)
                genmode='Demo/template mode'
            checks=validate(p,result)
            st.session_state['last']={'product':p,'result':result,'checks':checks,'mode':genmode}
    except Exception as e:
        st.error(f'Generation failed: {e}')

if 'last' in st.session_state:
    data=st.session_state['last']; r=data['result']; c=data['checks']
    st.divider(); st.subheader('2. Generated content')
    st.caption(f"Mode: {data['mode']} • Product ID: {data['product']['product_id']}")
    st.markdown('**📝 Description**')
    st.write(r['description'])
    st.markdown('**⭐ Key Features**')
    for x in r['bullets']:
        st.markdown(f'- {x}')
    st.markdown('**🔍 Meta Title**')
    st.code(r['meta_title'])

    st.subheader('3. Validation')
    a,b,d,e=st.columns(4)
    a.metric('Description words',c['word_count'])
    b.metric('Meta characters',c['meta_chars'])
    d.metric('Bullets',c['bullet_count'])
    e.metric('Attribute matches',c['attribute_matches'])
    if c['numeric_warnings']=='None': st.success('Pre-check: no numeric values were detected that are absent from the source attributes. Human verification is still required.')
    else: st.warning('Numeric values needing review: '+c['numeric_warnings'])
    st.info('This validation is a screening aid, not a substitute for the required human fact-check.')

    record={
        'product_id':data['product']['product_id'], 'product_name':data['product']['product_name'],
        'category':data['product']['category'], 'price_inr':data['product']['price_inr'],
        'target_customer':data['product']['target_customer'], 'description':r['description'],
        'bullet_1':r['bullets'][0], 'bullet_2':r['bullets'][1], 'bullet_3':r['bullets'][2],
        'bullet_4':r['bullets'][3], 'bullet_5':r['bullets'][4], 'meta_title':r['meta_title'],
        'description_word_count':c['word_count'], 'meta_title_char_count':c['meta_chars'],
        'bullet_count':c['bullet_count'], 'generation_mode':data['mode'], 'final_status':'Human review required'
    }
    df=pd.DataFrame([record])
    st.download_button('⬇️ Export this product as CSV',df.to_csv(index=False).encode('utf-8'),file_name=f"{data['product']['product_id']}_seo_output.csv",mime='text/csv')

