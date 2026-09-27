import streamlit as st
import openai
import google.generativeai as genai
from pypdf import PdfReader

# إعداد الشاشة والواجهة
st.set_page_config(page_title="AI Hub Pro - المنصة الموحدة", page_icon="🤖", layout="wide")
# ==========================================
# نظام حماية المنصة بكلمة سر
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 تسجيل الدخول إلى AI Hub Pro")
    password_input = st.text_input("أدخل كلمة السر للدخول:", type="password")
    
    if st.button("تسجيل الدخول"):
        # يمكنك تغيير كلمة السر (Wael2026) إلى أي كلمة سر تفضلها
        if password_input == "Wael&2026": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ كلمة السر غير صحيحة، حاول مرة أخرى.")
    st.stop() # إيقاف باقي الصفحة حتى يتم إدخال كلمة السر الصحيحة

st.title("🤖 منصة الذكاء الاصطناعي الموحدة (AI Hub Pro)")
st.caption("تطبيق شامل للمحادثة، تحليل الملفات، وتوليد الصور")

# الشريط الجانبي للإعدادات والمفاتيح
with st.sidebar:
    st.header("⚙️ الإعدادات والمفاتيح")
    
    # اختيار نوع المهمة
    task_mode = st.radio(
        "اختر نمط العمل:",
        ["💬 محادثة وتحليل ملفات", "🎨 توليد صور (DALL-E 3)"]
    )
    
    st.divider()
    
    if task_mode == "💬 محادثة وتحليل ملفات":
        selected_model = st.selectbox(
            "اختر النموذج للتحليل والإجابة:",
            ["Google Gemini 1.5", "ChatGPT (GPT-4o)"]
        )
    
    st.divider()
    
    openai_api_key = st.text_input("مفتاح OpenAI API Key:", type="password")
    gemini_api_key = st.text_input("مفتاح Gemini API Key:", type="password")

# دالة مساعدة لقراءة محتوى الملفات
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    elif uploaded_file.name.endswith('.txt'):
        return uploaded_file.getvalue().decode("utf-8")
    return ""

# ==========================================
# النمط الأول: المحادثة وتحليل الملفات
# ==========================================
if task_mode == "💬 محادثة وتحليل ملفات":
    
    # منطقة رفع الملفات
    st.subheader("📁 رفع مستند (اختياري)")
    uploaded_file = st.file_uploader("قم برفع ملف PDF أو TXT للتحليل أو السؤال عنه:", type=["pdf", "txt"])
    
    file_context = ""
    if uploaded_file:
        with st.spinner("جاري قراءة محتوى الملف..."):
            file_context = extract_text_from_file(uploaded_file)
            st.success(f"تمت قراءة الملف '{uploaded_file.name}' بنجاح!")

    # حفظ سجل المحادثة
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض المحادثات السابقة
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # استقبال مدخلات المستخدم
    if prompt := st.chat_input("اكتب سؤالك هنا (أو اسأل عن محتوى الملف المرفوع)..."):
        
        # تجهيز السؤال مع إضافة نص الملف كسياق في حال وجوده
        full_prompt_to_send = prompt
        if file_context:
            full_prompt_to_send = (
                f"إليك نص المستند المرفق:\n---بداية النص---\n{file_context[:12000]}\n---نهاية النص---\n\n"
                f"بناءً على المستند أعلاه، أجب عن التالي:\n{prompt}"
            )

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            try:
                # 1. استخدام Gemini
                if "Gemini" in selected_model:
                    if not gemini_api_key:
                        st.warning("⚠️ يرجى إدخال مفتاح Google Gemini API في الشريط الجانبي.")
                    else:
                        genai.configure(api_key=gemini_api_key)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        response = model.generate_content(full_prompt_to_send)
                        full_response = response.text

                # 2. استخدام ChatGPT
                elif "ChatGPT" in selected_model:
                    if not openai_api_key:
                        st.warning("⚠️ يرجى إدخال مفتاح OpenAI API في الشريط الجانبي.")
                    else:
                        client = openai.OpenAI(api_key=openai_api_key)
                        formatted_messages = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages[:-1]
                        ]
                        formatted_messages.append({"role": "user", "content": full_prompt_to_send})

                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=formatted_messages
                        )
                        full_response = response.choices[0].message.content

                # عرض الإجابة وحفظها
                if full_response:
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"حدث خطأ أثناء الاتصال بالخدمة: {str(e)}")

# ==========================================
# النمط الثاني: توليد الصور
# ==========================================
elif task_mode == "🎨 توليد صور (DALL-E 3)":
    st.subheader("🎨 إنشاء صور باستخدام نموذج DALL-E 3")
    st.write("اكتب وصفاً مفصلاً للصورة التي تريد إنشاءها:")
    
    image_prompt = st.text_area(
        "وصف الصورة:",
        placeholder="مثال: رائد فضاء يجلس في كافيه كلاسيكي على كوكب المريخ بأسلوب ألوان زيتية سينمائي..."
    )
    
    if st.button("توليد الصورة 🚀"):
        if not openai_api_key:
            st.warning("⚠️ ميزة توليد الصور تعتمد على OpenAI DALL-E 3، يرجى إدخال OpenAI API Key في الشريط الجانبي.")
        elif not image_prompt.strip():
            st.warning("⚠️ يرجى كتابة وصف للصورة أولاً.")
        else:
            with st.spinner("جاري تصميم الصورة... قد يستغرق ذلك بضع ثوانٍ"):
                try:
                    client = openai.OpenAI(api_key=openai_api_key)
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1,
                    )
                    image_url = response.data[0].url
                    
                    st.image(image_url, caption=image_prompt, use_container_width=True)
                    st.markdown(f"[🔗 اضغط هنا لعرض الصورة أو تحميلها بدقة كاملة]({image_url})")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء توليد الصورة: {str(e)}")