# library imports
import re
import socket
import platform
from datetime import datetime, timedelta
import streamlit as st
from streamlit_lottie import st_lottie
from streamlit_js_eval import streamlit_js_eval
import streamlit.components.v1 as components
import base64
from google import genai
from deep_translator import GoogleTranslator
import re
import time
from mistralai import Mistral
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# custom
import utils
import webscraper
import automatic_email

region_code= '&gl=US&ceid=US:en'
toggle_topic= False

api_key_gemini = st.secrets["API_KEY_GEMINI"]
api_key_mistral = st.secrets["API_KEY_MISTRAL"]
email_notification= st.secrets["EMAIL_NOTIFICATION"]
email_pwd = st.secrets["EMAIL_PASSWORD"]

if email_notification:
    #automatic_email.send_email("glimpsethrough98@gmail.com", "glimpsethrough98@gmail.com", body, pwd= email_pwd)
    # Define scope
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Authenticate using the JSON key file
    #creds = ServiceAccountCredentials.from_json_keyfile_name('GT_user_data.json', scope)
    #client = gspread.authorize(creds)

    creds_dict = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace('\\n', '\n'),  # Fix newline issues
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    }

    # Authenticate using the credentials dictionary
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

def render_page(topics):
    """Streamlit UI using CSS, Javascript and HTML"""

    # Inject custom CSS for professional button styling
    st.markdown(
        """
        <style>
        div.stButton > button {
            background: linear-gradient(to bottom, midnightblue, transparent);
            color: white;
            font-size: 14px;
            font-weight: bold;
            border: none;
            border-radius: 15px; /* Rounded edges with a 15px radius */
            padding: 15px 25px;
            width: 100%; /* Ensure full width for seamless joining */
            transition: background-color 0.3s ease, color 0.3s ease;
            margin: 0px; /* Remove spacing */
            white-space: nowrap; /* Prevents text from wrapping onto multiple lines */
            overflow-wrap: normal; /* Default behavior; avoids forcing breaks */
        }

        div.stButton > button:hover {
            background: linear-gradient(
                to bottom,
                transparent, 
                transparent, 
                transparent, 
                transparent, 
                transparent, 
                transparent,
                transparent, 
                darkorange
            );
            color: khaki; /* Midnightblue text */
        }

        div.stColumn {
            padding: 0px !important; /* Ensure columns have no padding */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    selected_topic = None
    cols = st.columns(len(topics), gap="small")  # Ensure no gap between buttons
    for i, topic in enumerate(topics):
        with cols[i]:  
            if st.button(topic):
                selected_topic = topic  
    
    return selected_topic

def SetBackground(main_bg):
    '''
    A function to unpack an image from root folder and set as bg.
 
    Returns
    -------
    The background.
    '''
    custom_css = """
    <style>
        header { 
            background-color: #0E0143 !important;
            height: 40px;
        }
    </style>
    """
    # set bg name
    main_bg_ext = "png"
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
    
    st.markdown(custom_css, unsafe_allow_html=True)

# Streamlit layout
st.set_page_config(page_title="News Dashboard", layout="wide", page_icon="graphics/enhance3.ico")
SetBackground('graphics/wwdc-glowing-violet-3840x2160-19118.png')
page_width = streamlit_js_eval(js_expressions='window.innerWidth', key='WIDTH',  want_output = True)

try:
    if page_width and page_width <= st.secrets["screen_size"]:
        st.title("Unsupported Device Display Resolution :(")
        st.write("")
        st.markdown(f'<p style="color:red;">This application is currently optimized for desktop use only. For the best experience, please access it through a desktop browser.</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:red;">Width: {page_width} px</p>', unsafe_allow_html=True)
        try:
            hostname = socket.gethostname()
            os_info = platform.system() + " " + platform.release()
            if email_notification:
                #automatic_email.send_bug_report("glimpsethrough98@gmail.com", "telang.sarvesh98@gmail.com", body, pwd= email_pwd)
                # Open the Google Sheet and select the worksheet
                sh_error = client.open('error_bug_report').worksheet('Sheet1')

                # Define row data
                host_name= hostname
                time_of_request= datetime.now().isoformat()
                os_info= os_info
                error_log= f"Unsupported Device Display Resolution. Tried with Width:{page_width}"

                # Append data
                row_err = [host_name, time_of_request, os_info, error_log]
                sh_error.append_row(row_err)
        except:
            pass
    else:
        count=0
        # User Input
        topics= ["Top Stories⚡", "Technology", "Automobile", "AI", "Stock market", "Sports", "Finance", "Entertainment", "Science", "Politics", "Lifestyle", "Soccer", "Cricket", "F1"]
        region_list= {'World':'&hl=en','USA':'&hl=en&gl=US&ceid=US:en', 'GER':'&hl=de&gl=DE&ceid=DE:de', 'IND (eng)':'&hl=en&gl=IN&ceid=IN:en', 'IND (hindi)':'&hl=hi&gl=IN&ceid=IN:hi', 'UK':'&hl=en&gl=GB&ceid=GB:en', 'AUS':'&hl=en&gl=AU&ceid=AU:en', 'CAN':'&hl=en&gl=CA&ceid=CA:en', 'FRA':'&hl=fr&gl=FR&ceid=FR:fr', 'ESP':'&hl=es&gl=ES&ceid=ES:es', 'ITA':'&hl=it&gl=IT&ceid=IT:it', 'NL':'&hl=nl&gl=NL&ceid=NL:nl', 'PT':'&hl=pt-PT&gl=PT&ceid=PT:pt-PT', 'BRA':'&hl=pt-BR&gl=BR&ceid=BR:pt-BR', 'RUS':'&hl=ru&gl=RU&ceid=RU:ru', 'CHN':'&hl=zh-CN&gl=CN&ceid=CN:zh-CN', 'JPN':'&hl=ja&gl=JP&ceid=JP:ja'}
        custom = False
        isresponse= False
        isdefault= False
        prompt= None

        # Apply custom CSS to make dropdowns transparent and align them horizontally
        st.markdown("""
            <style>
                div[data-testid="stSelectbox"] {
                    background: transparent !important;
                    display: inline-block;
                    padding-right: 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        selected_topic = render_page(topics)

        news_count= 10
        sources_count = 4
        region= list(region_list.keys())[0]
        region_code= '&hl=en'
        client_code=0

        client1 = genai.Client(api_key= api_key_gemini)
        client2 = Mistral(api_key=api_key_mistral)
        lottie_animation2 = utils.get("graphics/Scene-1.json")

        col1_image, col2_title, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17, col18 = st.columns([1,5,1,1,1,1,1,1,1,1,0.5,0.5,0.5, 0.5, 0.5, 0.5, 0.5, 0.5])  # Adjust ratio as needed
        with col2_title:
            st.markdown(
                "<h1 style='font-size: 44px;'>Glimpse Through</h1>", 
                unsafe_allow_html=True
            )
            st.markdown(
                "<h1 style='font-size: 14px; text-align: right; margin-top: -30px; margin-bottom: -250px; margin-right: 60px; color: #d4c0fc'>A Smart Global News Curator✨</h1>", 
                unsafe_allow_html=True
            )


        with col1_image:
            #st.image("enhance3.png", width=85)
            st_lottie(lottie_animation2, speed=1, reverse=True, height=80, loop=True, quality="high", key="logo")

        st.markdown(
            """
            <style>
                /* Target the dropdown box */
                div[data-baseweb="select"] > div {
                    background-color: rgba(25, 46, 87, 1) !important; /* Change this to your preferred color */
                    color: lavender !important;
                }

                /* Target the dropdown options */
                ul {
                    background-color: rgba(25, 46, 87, 0.3) !important;
                }

                /* Target the dropdown text */
                div[data-baseweb="select"] * {
                    color: lavender !important;
                    font-size: 14px !important; /* Set font size */
                }

                /* Global font size for all text */
                body, div, span, input, textarea, select, option {
                    font-size: 14px !important; /* Apply font size globally */
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        hide_elements = """
                <style>
                    div[data-testid="stSliderTickBarMin"],
                    div[data-testid="stSliderTickBarMax"] {
                        display: none;
                    }
                </style>
        """
        st.markdown(
            """
            <style>
            div[data-testid="stForm"] {
                background-color: rgba(0, 0, 0, 0.2); /* Light gray background */
                border: 0.5px solid violet; /* Optional border color */
                border-radius: 20px; /* Rounded corners */
                padding: 20px; /* Add space inside the form */
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1); /* Optional shadow for depth */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(hide_elements, unsafe_allow_html=True)

        main_col = st.columns([1.3, 0.7])

        with main_col[0]:
            # Create a form and define columns inside it
            with st.form(key="selection_form"):
                # First row with input widgets and sliders
                col1, col2, col3, col4, col5 = st.columns([2.5, 0.7, 1, 0.7, 0.7])
                
                with col1:
                    custom_selected_topic = st.text_input(
                        "Search",
                        value= "",
                        placeholder="Enter custom topic or news category...",
                        key="custom_topic"
                    )

                with col2:
                    region = st.selectbox("Select Region:", list(region_list.keys()), key="region")
                    region_code = region_list[region]

                with col3:
                    sources_count = st.slider(
                        "News Sources Count:",
                        min_value=1,
                        max_value=10,
                        value=4,
                        key="sources_count"
                    )

                with col4:
                    news_count = st.slider(
                        "News Count:",
                        min_value=1,
                        max_value=15,
                        value=10,
                        key="news_count"
                    )

                with col5:
                    isprioritize = st.checkbox("Prioritize Topic-specific Sources", key="specialized_toggle", value= False)

                # Second row dedicated for the submit button
                button_col, empty1, empty2 = st.columns([1, 2, 1])
                with button_col:
                    submit_button = st.form_submit_button("Apply Selection")

            st.markdown(
                """
                <style>
                .info-button {
                    display: inline-block;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    background-color: white;
                    color: black;
                    text-align: center;
                    font-weight: bold;
                    line-height: 24px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }

                .info-button:hover {
                    background-color: #2980b9;
                }

                .tooltip {
                    display: none;
                    position: absolute;
                    background: white;
                    color: midnightblue;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 15px;
                    box-shadow: 2px 2px 1px rgba(0, 0, 0, 0.2);
                    top: 0; /* Aligns the tooltip vertically */
                    left: 35px; /* Adjust to position it horizontally next to the button */
                    white-space: nowrap; /* Prevents the text from wrapping */
                }

                .info-container {
                    position: relative; /* Ensure positioning works relative to this container */
                    display: inline-block; /* Keeps the button and tooltip together */
                }

                .info-container:hover .tooltip {
                    display: block;
                }
                </style>

                <div class="info-container">
                    <div class="info-button">i</div>
                    <div class="tooltip">How it works: Select News Category → Apply Filters (Optional) → Uses AI to extract top news sources → Scrapes headlines of latest articles from Google News (Publicly Available Search Results) → Summarizes major news</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if "loading_complete" not in st.session_state:
            st.session_state.loading_complete = False

        progress_text = "Loading..."
        my_bar = st.progress(0, text=progress_text)

        if custom_selected_topic and selected_topic== None:
            lottie_animation1 = utils.get("graphics/Animation_9.json")
            ht= 430
        else:
            lottie_animation1 = utils.get("graphics/Animation_7.json")
            ht= 280

        loading_placeholder = st.empty()

        if not st.session_state.loading_complete:
            with loading_placeholder:
                # Set the background to white and apply the animation
                st_lottie(lottie_animation1, speed=1, reverse=True, height=ht, loop=True, quality="high", key="loading")

        if 'hl=en' in region_code:
            isenglish= True
        else:
            isenglish= False

        if custom_selected_topic and custom_selected_topic != "" and selected_topic== None:
            if not isenglish:
                translator = GoogleTranslator(source='auto', target='en')
                custom_selected_topic = translator.translate(custom_selected_topic)
            topic = custom_selected_topic
        elif selected_topic:
            topic = selected_topic
        else:
            if isenglish: 
                topic= topics[0]
            else:
                topic= topics[1]
        
        for percent_complete in range(0, 10):
            time.sleep(0.01)
            my_bar.progress(percent_complete + 1, text=progress_text)

        if topic== "Top Stories⚡":
            prompt= None
            isdefault = True
            display_text= f"Exploring the latest global headlines... 🌍"
        else:
            isdefault= False
            prompt= f"List the top {sources_count} news sources in {region} that are most relevant to {topic}."
            if isprioritize:
                prompt+= f"Prioritize sources that are specifically renowned for covering {topic} over general sources."
            display_text= f"Searching for the top {sources_count} news sources in {region} that are most relevant to {topic}...🔍"

        for percent_complete in range(10, 20):
            time.sleep(0.01)
            my_bar.progress(percent_complete + 1, text=progress_text)
        
        if prompt:
            for percent_complete in range(20, 30):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)
            try:
                response = client1.models.generate_content(
                    model="gemini-2.0-flash",
                    contents= prompt+ "Provide only their names without any category-specific suffixes such as '- Sports'."
                )
                client_code=1
                if response.text and response.text.strip():  # Check if response is non-empty
                    isresponse= True
                    extract_response = re.findall(r"\d+\.\s+(.+)", response.text)
                    words_list = response.text.replace("Response:", "").split()
                    answer = utils.group_sentences(words_list)
                else:
                    print("Please wait.. Response is empty. Retrying...")
                    time.sleep(2)  # Wait for 2 seconds before retrying

            except Exception as e:
                print("Error in extracting response from client 1:")
                print(e)
                print("Retrying with client2:")
                try:
                    # Example chat completion request
                    response2 = client2.chat.complete(
                        model="mistral-large-latest",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt+ "Provide only their names without any category-specific suffixes such as '- Sports'.",
                            },
                        ]
                    )
                    client_code=2

                    response_text= response2.choices[0].message.content

                    if response_text:
                        isresponse= True
                        print("Response has content:")
                        extract_response = re.findall(r"\d+\.\s+(.+)", response_text)
                        words_list = response_text.replace("Response:", "").split()
                        answer = utils.group_sentences(words_list)
                    else:
                        print("Please wait.. Response is empty. Retrying...")
                        time.sleep(2)  # Wait for 2 seconds before retrying
                except:
                    print("Error in extracting response from client 2:")
                    raise RuntimeError("Error retrieving response from API")
            for percent_complete in range(30, 40):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)
        else:
            for percent_complete in range(20, 40):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)
            isresponse= True
            client_code=3
            defaults = {
                'World': ['The New York Times', 'The Guardian', 'DW News', 'Moneycontrol', 
                        'Bloomberg', 'TechCrunch', 'Reuters', 'BBC', 'The Verge', 'WION'],
                
                'USA': ['The New York Times', 'CNN', 'Fox News', 'The Washington Post', 
                        'USA Today', 'The Wall Street Journal', 'NBC News', 
                        'CBS News', 'ABC News', 'Reuters'],
                
                'GER': ['Bild.de', 'Die Welt', 'Frankfurter Allgemeine Zeitung', 'Zeit Online',
                        'Süddeutsche Zeitung', 'Spiegel Online', 'Focus Online', 'Tagesschau', 'Handelsblatt', 'n-tv'],
                
                'IND (eng)': ['The Economic Times', 'The Times of India', 'Moneycontrol', 'Hindustan Times', 'India Today', 'The Indian Express', 'NDTV', 
                            'The Hindu', 'Zee News', 'News18'],
                
                'IND (hindi)': ['Dainik Bhaskar', 'Moneycontrol', 'Amar Ujala', 'Navbharat Times', 
                                'Dainik Jagran', 'Patrika', 'Punjab Kesari', 
                                'Rajasthan Patrika', 'Jagran Josh', 'Zee News Hindi'],
                
                'UK': ['BBC News', 'The Guardian', 'The Independent', 'The Telegraph', 
                    'Sky News', 'Daily Mail', 'Evening Standard', 'Financial Times', 
                    'The Times', 'Metro'],
                
                'AUS': ['ABC News Australia', 'The Sydney Morning Herald', 'The Australian', 
                        '9News', 'The Age', 'The Guardian Australia', 'news.com.au', 
                        'SBS News', 'Herald Sun', 'Sky News Australia'],
                
                'CAN': ['CBC News', 'The Globe and Mail', 'CTV News', 'National Post', 
                        'Toronto Star', 'Global News', 'Maclean’s', 'The Toronto Sun', 
                        'The Huffington Post Canada', 'Financial Post'],
                
                'FRA': ['Le Monde', 'Le Figaro', 'France 24', 'Libération', 
                        'L’Express', 'Le Parisien', 'BFM TV', 'RFI', 
                        'La Croix', 'Challenges'],
                
                'ESP': ['El País', 'El Mundo', 'ABC España', 'La Vanguardia', 
                        'El Confidencial', '20 Minutos', 'OK Diario', 
                        'La Razón', 'Europa Press', 'Cadena SER'],
                
                'ITA': ['Corriere della Sera', 'La Repubblica', 'Il Sole 24 Ore', 'ANSA', 
                        'La Stampa', 'Il Giornale', 'Rai News', 'Tgcom24', 
                        'Il Fatto Quotidiano', 'AGI'],
                
                'NL': ['De Telegraaf', 'Algemeen Dagblad', 'de Volkskrant', 'NRC Handelsblad', 
                    'Het Parool', 'RTL Nieuws', 'NOS', 'Trouw', 
                    'BNR Nieuwsradio', 'Het Financieele Dagblad'],
                
                'PT': ['Público', 'Diário de Notícias', 'Expresso', 'Correio da Manhã', 
                    'Jornal de Notícias', 'RTP Notícias', 'Observador', 'SIC Notícias', 
                    'TVI24', 'O Jogo'],
                
                'BRA': ['Folha de S.Paulo', 'O Globo', 'Estadão', 'G1', 
                        'UOL Notícias', 'Veja', 'R7', 'Correio Braziliense', 
                        'Terra', 'Jornal do Brasil'],
                
                'RUS': ['RT', 'TASS', 'RIA Novosti', 'Kommersant', 
                        'Izvestia', 'Lenta.ru', 'Vedomosti', 'Sputnik News', 
                        'Argumenty i Fakty', 'Fontanka'],
                
                'CHN': ['Xinhua', 'People’s Daily', 'Global Times', 'China Daily', 
                        'Sina News', 'Phoenix TV', 'The Paper', 'Caixin', 
                        'South China Morning Post', 'China News Service'],
                
                'JPN': ['NHK News', 'Asahi Shimbun', 'Yomiuri Shimbun', 'Mainichi Shimbun', 
                        'Nikkei Asia', 'The Japan Times', 'Kyodo News', 'Jiji Press', 
                        'Fuji News Network', 'Tokyo Shimbun']
            }
            selected_region_defaults = defaults.get(region, ['The New York Times', 'The Guardian', 'DW News', 'Moneycontrol', 
                        'Bloomberg', 'TechCrunch', 'Reuters', 'BBC', 'The Verge', 'WION'])
            extract_response = selected_region_defaults[:sources_count]
            for percent_complete in range(40, 60):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)

        try:
            hostname = socket.gethostname()
            os_info = platform.system() + " " + platform.release()
            body = f"""\
            time: {datetime.now()}
            host_name: {hostname}
            os_info: {os_info}
            client_code: {client_code}
            """
            if email_notification:
                # Open the Google Sheet and select the worksheet
                sh = client.open('user_run_request').worksheet('Sheet1')

                # Define row data
                host_name= hostname
                time_of_request= datetime.now().isoformat()
                os_info= os_info
                client_code= client_code
                # Append data
                row = [host_name, time_of_request, os_info, client_code, topic, region, sources_count, news_count, isprioritize]
                sh.append_row(row)
        
        except Exception as e2:
            print("Error in saving user data: ", e2)

        if isresponse and extract_response:
            output_lines = []

            if prompt:
                output_lines.append("Topic: " + topic)
                output_lines.append("Region: " + region)
                output_lines.append(display_text)
                output_lines.append("Response: ")
                output_lines.extend(answer)
                output_lines.append(f"Extracting recent news updates...")
                output_lines.append(f"Please wait... ⏳")
            
            else:
                output_lines.append("Topic: " + topic)
                output_lines.append("Region: "+ region)
                output_lines.append(display_text)
                output_lines.append("Connecting to sources...")
                output_lines.append("Fetching news articles...")
                output_lines.append(f"Please wait... ⏳")
            
            for percent_complete in range(40, 60):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)

            # Convert output_lines to list items
            lines_html = "".join(f"<li style='opacity: 0; margin: 5px 0;'>{line}</li>" for line in output_lines)

            # HTML block with JavaScript for line-by-line animation
            html_code = f"""
            <div id="animated-text" style="
                height: 150px;
                overflow-y: auto;
                background-color: transparent;
                color: lavender;
                padding: 10px;
                font-family: Verdana;
                font-size: 14px;
            ">

                <ul style="list-style-type: none; padding: 0; margin: 0;">
                    {lines_html}
                </ul>
            </div>

            <style>
                /* Scrollbar for Webkit browsers (Chrome, Edge, Safari) */
                #animated-text::-webkit-scrollbar {{
                    width: 8px; /* Width of the scrollbar */
                }}

                #animated-text::-webkit-scrollbar-track {{
                    background: transparent; /* Grey background (track/slot) */
                    border-radius: 5px;
                }}

                #animated-text::-webkit-scrollbar-thumb {{
                    background: white; /* White scrollbar handle */
                    border-radius: 5px;
                }}

                /* Scrollbar for Firefox */
                #animated-text {{
                    scrollbar-color: transparent; /* Thumb color and track color */
                }}
            </style>

            <script>
                const container = document.getElementById("animated-text");
                const lines = container.querySelectorAll("li");
                let index = 0;

                function displayNextLine() {{
                    if (index < lines.length) {{
                        let line = lines[index];
                        let opacity = 0;
                        line.style.opacity = opacity;

                        // Gradual fade-in effect
                        const interval = setInterval(() => {{
                            if (opacity >= 1) {{
                                clearInterval(interval);
                            }} else {{
                                opacity += 0.05;
                                line.style.opacity = opacity;
                            }}
                        }}, 50);

                        index++;

                        // Smooth incremental scroll
                        setTimeout(() => {{
                            let targetScroll = container.scrollTop + line.clientHeight;
                            smoothScroll(container, targetScroll);
                        }}, 400);  

                        setTimeout(displayNextLine, 700); // Delay before showing the next line
                    }}
                }}

                function smoothScroll(element, target) {{
                    let start = element.scrollTop;
                    let change = target - start;
                    let startTime = performance.now();
                    let duration = 300; // Scroll speed (ms)

                    function animateScroll(currentTime) {{
                        let elapsedTime = currentTime - startTime;
                        let progress = Math.min(elapsedTime / duration, 1);
                        element.scrollTop = start + change * progress;

                        if (progress < 1) {{
                            requestAnimationFrame(animateScroll);
                        }}
                    }}

                    requestAnimationFrame(animateScroll);
                }}

                displayNextLine();
            </script>
            """  
            with main_col[1]:
                # Render the animated text in Streamlit
                st.components.v1.html(html_code, height=200)

            news_df_sorted=[]
            for medium in extract_response:
                df= webscraper.ScrapData(topic= topic, news_medium=medium, domain="https://news.google.com/", count=news_count, region=region_code, isenglish=isenglish, isdefault= isdefault) 
                news_df_sorted.append(df)
            
            for percent_complete in range(60, 90):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)

            st.session_state.loading_complete = True

            # Combine all titles into a single list
            all_news = []
            for df in news_df_sorted:
                all_news.extend(df['Title'].tolist())  # Extract titles from each dataframe

            # Join the titles into a single block of text, separated by new lines
            combined_titles = "\n".join(all_news)

            print(news_df_sorted[0].columns)

            try:
                response_ticker = client1.models.generate_content(
                    model="gemini-2.0-flash",
                    contents= f"Summarize the key points and provide important highlights based on the following news titles:\n{combined_titles}"
                )
                if response_ticker.text and response_ticker.text.strip():
                    ticker= response_ticker.text
                else:
                    ticker=""
            except:
                try:
                    response_ticker = client2.chat.complete(
                        model="mistral-large-latest",
                        messages=[
                            {
                                "role": "user",
                                "content": "Summarize the key points and provide important highlights based on the following news titles:\n"+combined_titles,
                            },
                        ]
                    )

                    response_ticker_text= response_ticker.choices[0].message.content

                    if response_ticker_text:
                        ticker= response_ticker_text
                    else:
                        ticker=""
                except:
                    ticker=""
            
            for percent_complete in range(90, 100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)

            time.sleep(1)
            my_bar.empty()

            loading_placeholder.empty()
            text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ticker)
            scroll_text = text.replace('*', '|')

            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    #scroll-container {{
                        width: 100%;
                        overflow: hidden;
                        background-color: rgba(25, 46, 87, 0.4);
                        border-top: 2px solid white;
                        border-bottom: 2px solid white;
                        position: relative;
                    }}

                    #scroll-text {{
                        display: inline-block;
                        white-space: nowrap;
                        color: white;
                        font-size: 18px;
                        font-family: Verdana;
                        position: relative;
                        left: 100%;
                        cursor: pointer;
                    }}

                    #summary-block {{
                        position: absolute;
                        left: 0;
                        margin-left: -5px;
                        top: 50%;
                        transform: translateY(-50%) skewX(-10deg);
                        background-color: rgba(255, 0, 0, 0.7);
                        color: white;
                        padding: 10px;
                        font-size: 18px;
                        font-weight: bold;
                        font-family: Verdana;
                        z-index: 10;
                        transform-origin: left center;
                    }}
                </style>
            </head>
            <body>
                <div id="scroll-container">
                    <div id="summary-block">Summary</div>
                    <div id="scroll-text">{scroll_text}</div>
                </div>
                
                <script>
                    let scrollText = document.getElementById('scroll-text');
                    let scrollSpeed = 1;
                    let paused = false;

                    function scrollTextLeft() {{
                        if (paused) return;

                        if (scrollText.getBoundingClientRect().right <= 0) {{
                            scrollText.style.left = '100%';
                        }} else {{
                            scrollText.style.left = (parseInt(scrollText.style.left, 10) - scrollSpeed) + 'px';
                        }}
                    }}

                    scrollText.style.position = 'relative';
                    scrollText.style.left = '100%';
                    let intervalID = setInterval(scrollTextLeft, 10);

                    scrollText.addEventListener('mouseover', () => {{
                        paused = true;
                    }});
                    scrollText.addEventListener('mouseout', () => {{
                        paused = false;
                    }});
                </script>
            </body>
            </html>
            """
            components.html(html_code, height=60)

            # Custom CSS for horizontal scrolling with fixed blocks
            scroll_item_height = news_count*35  # For example, 215vh. You may change this value dynamically.

            zoom= -0.002*news_count + 1.04

            st.markdown(
                f"""
                <style>
                /* Global Reset */
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: Verdana;
                }}
                
                html, body {{
                    width: 100%;
                    height: 100%;
                    overflow: hidden; /* Prevents overflow */
                    margin: 0;
                }}

                /* Ensure the main content takes the full screen */
                main {{
                    height: 90vh;  /* Full viewport height */
                    width: 90vw;   /* Full viewport width */
                    display: flex;
                    overflow: hidden;
                }}

                /* Section containing the scrollable content */
                .wrap {{
                    display: flex;
                    height: 100%;
                    width: 100%;   /* Ensure it takes the full width */
                    overflow: hidden;  /* Prevents horizontal scroll */
                }}

                /* The section for scrolling */
                .scroll-container {{
                    display: flex;
                    flex-wrap: nowrap;
                    justify-content: flex-start;
                    overflow-x: scroll;
                    height: 100%;
                    gap: 12px;
                    padding: 40px;
                    scroll-behavior: smooth;
                    width: 150%;
                }}

                /* Each news article block inside scroll */
                .scroll-item {{
                    min-width: 25vw;  /* Decrease size to fit more columns */
                    max-width: 75vw;  /* Prevent items from becoming too wide */
                    height: {scroll_item_height}vh;  /* Dynamic height: change scroll_item_height to adjust */
                    background: linear-gradient(to bottom, 
                        rgba(255, 255, 255, 0.98) 0%,   
                        rgba(255, 240, 220, 0.3) 30%,  
                        rgba(255, 225, 200, 0.1) 60%,  
                        rgba(255, 210, 180, 0.6) 90%,  
                        rgba(255, 200, 160, 0.9) 100%
                    );
                    padding: 24px;
                    border-radius: 15px;
                    text-align: center;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease;
                    flex-shrink: 0; /* Prevents shrinking when zooming */
                }}

                /* Hover effect for zooming */
                .scroll-item:hover {{
                    transform: scale({zoom});
                    background-color: white !important;
                    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
                }}

                /* Styling for navigation blocks */
                .blocks {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 100;
                    pointer-events: none;
                }}

                /* Adjust position of blocks */
                .block {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 4rem;
                    height: 100%;
                    background: #a19a8f;
                    z-index: 100;
                    padding: 2rem 1.25rem;
                    display: flex;
                    align-items: center;
                    flex-direction: column;
                    justify-content: space-between;
                    pointer-events: auto;
                    cursor: pointer;
                    border-left: 0.2rem solid #000;
                    font-weight: 500;
                }}

                /* Adjusted block positions */
                .block[data-block-section="1"].init {{ left: calc(100vw - 16rem); }}
                .block[data-block-section="2"].init {{ left: calc(100vw - 12rem); }}
                .block[data-block-section="3"].init {{ left: calc(100vw - 8rem); }}
                .block[data-block-section="4"].init {{ left: calc(100vw - 4rem); }}

                .block.fixed {{ left: 4rem; }}

                /* Block title styling */
                .block__title {{
                    position: relative;
                    white-space: nowrap;
                    transform: rotate(-90deg) translate(-50%);
                    text-align: right;
                }}

                .block__number, .block__title {{
                    text-transform: uppercase;
                    font-size: 1.6rem;
                    line-height: 0.9rem;
                    color: #000;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

            try:
                # Check if all DataFrames have a valid 'Medium' value at index 0
                for df in news_df_sorted:
                    _ = df.loc[0, 'Medium']  # Try accessing 'Medium' column at index 0
            except (KeyError, IndexError):
                # If an error occurs, update all DataFrames
                for df in news_df_sorted:
                    df['Medium'] = df['Medium'].astype(object)
                    df.loc[0, 'Medium'] = 'https://img.icons8.com/?size=100&id=p1yIKD1Sjsp1&format=png&color=000000'
                    df.loc[0, 'Source'] = 'Sorry, no results found.. Please try a different search term!'

            if sources_count >= 1:
                news_content0 = "<div class='news-container'>"

                for index, row in news_df_sorted[0].iterrows():
                    news_content0 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 40px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content0+= "</div>"

            if sources_count >= 2:
                news_content1 = "<div class='news-container'>"

                for index, row in news_df_sorted[1].iterrows():
                    news_content1 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content1+= "</div>"

            if sources_count >= 3:
                news_content2 = "<div class='news-container'>"

                for index, row in news_df_sorted[2].iterrows():
                    news_content2 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content2+= "</div>"

            if sources_count >= 4:
                news_content3 = "<div class='news-container'>"

                for index, row in news_df_sorted[3].iterrows():
                    news_content3 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content3 += "</div>"

            if sources_count >= 5:
                news_content4 = "<div class='news-container'>"

                for index, row in news_df_sorted[4].iterrows():
                    news_content4 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content4 += "</div>"

            if sources_count >= 6:
                news_content5 = "<div class='news-container'>"

                for index, row in news_df_sorted[5].iterrows():
                    news_content5 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content5 += "</div>"

            if sources_count >= 7:
                news_content6 = "<div class='news-container'>"

                for index, row in news_df_sorted[6].iterrows():
                    news_content6 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content6 += "</div>"

            if sources_count >= 8:
                news_content7 = "<div class='news-container'>"

                for index, row in news_df_sorted[7].iterrows():
                    news_content7 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content7 += "</div>"

            if sources_count >= 9:
                news_content8 = "<div class='news-container'>"

                for index, row in news_df_sorted[8].iterrows():
                    news_content8 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                        <div style="position: absolute; bottom: 3px; left: 50px; width: 25%; height: 1px; background-color: black;"></div>
                    </div>
                    """
                news_content8 += "</div>"

            if sources_count >= 10:
                news_content9 = "<div class='news-container'>"

                for index, row in news_df_sorted[9].iterrows():
                    news_content9 += f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; position: relative;">
                        <div style="flex: 1; padding-bottom: 8px;">
                            <p>
                                <a href="{row['Link']}" target="_blank" style="font-size: 16px; font-weight: bold; text-decoration: none; color: black;">
                                    {row['Title']}
                                </a>
                                <br>
                                <span style="font-size: 10px; color: gray;">{row['Source']} | {row['Author']} | {row['Time']}</span>
                            </p>
                        </div>
                        <div style="flex-shrink: 0; margin-left: 15px;">
                            <img src="{row['Thumbnail']}" alt="Thumbnail" style="width: 185px; height: auto; border-radius: 5px;">
                        </div>
                    </div>
                    """
                news_content9 += "</div>"


            if sources_count==10:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[4]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[4]['Source'][0]}</p>
                                {news_content4}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[5]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[5]['Source'][0]}</p>
                                {news_content5}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[6]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[6]['Source'][0]}</p>
                                {news_content6}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[7]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[7]['Source'][0]}</p>
                                {news_content7}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[8]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[8]['Source'][0]}</p>
                                {news_content8}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[9]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[9]['Source'][0]}</p>
                                {news_content9}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==9:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[4]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[4]['Source'][0]}</p>
                                {news_content4}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[5]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[5]['Source'][0]}</p>
                                {news_content5}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[6]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[6]['Source'][0]}</p>
                                {news_content6}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[7]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[7]['Source'][0]}</p>
                                {news_content7}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[8]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[8]['Source'][0]}</p>
                                {news_content8}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==8:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[4]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[4]['Source'][0]}</p>
                                {news_content4}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[5]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[5]['Source'][0]}</p>
                                {news_content5}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[6]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[6]['Source'][0]}</p>
                                {news_content6}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[7]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[7]['Source'][0]}</p>
                                {news_content7}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==7:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[4]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[4]['Source'][0]}</p>
                                {news_content4}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[5]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[5]['Source'][0]}</p>
                                {news_content5}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[6]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[6]['Source'][0]}</p>
                                {news_content6}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==6:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[4]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[4]['Source'][0]}</p>
                                {news_content4}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[5]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[5]['Source'][0]}</p>
                                {news_content5}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==5:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[4]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[4]['Source'][0]}</p>
                                {news_content4}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==4:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[3]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[3]['Source'][0]}</p>
                                {news_content3}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==3:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[2]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[2]['Source'][0]}</p>
                                {news_content2}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==2:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[1]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[1]['Source'][0]}</p>
                                {news_content1}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if sources_count==1:
                st.markdown(
                    f"""
                    <div class="main">
                        <div class="scroll-container">
                            <div class="scroll-item" style="width: 200px; white-space: normal; overflow-wrap: break-word;">
                                <img src="{news_df_sorted[0]['Medium'][0]}" alt="News Image" style="width: 20%; border-radius: 10px;">
                                <p style="font-size: 14px; font-weight: bold; color: #555; margin-top: 5px; text-align: center;">{news_df_sorted[0]['Source'][0]}</p>
                                {news_content0}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.session_state.loading_complete = False

        st.markdown(
            """
            <style>
            .bottom-right {
                position: absolute;
                bottom: -120px;
                right: 0px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                margin: 5px; /* Optional spacing */
            }
            </style>
            <p class='bottom-right'>Image by <a href='https://4kwallpapers.com/abstract/wwdc-glowing-violet-19118.html' style='color: lightblue; text-decoration: none;'>4kwallpapers.com</a></p>
            """,
            unsafe_allow_html=True
        )

except Exception as e1:
    st.title("Server Error... Please try again after sometime :(")
    st.write("")
    st.markdown(f'<p style="color:red;">Details: {e1}</p>', unsafe_allow_html=True)

    error_log = traceback.format_exc()
    
    try:
        hostname = socket.gethostname()
        os_info = platform.system() + " " + platform.release()
        body = f"""\
        time: {datetime.now()}
        host_name: {hostname}
        os_info: {os_info}
        error_log: {error_log}
        """
        if email_notification:
            #automatic_email.send_bug_report("glimpsethrough98@gmail.com", "telang.sarvesh98@gmail.com", body, pwd= email_pwd)
            # Open the Google Sheet and select the worksheet
            sh_error = client.open('error_bug_report').worksheet('Sheet1')

            # Define row data
            host_name= hostname
            time_of_request= datetime.now().isoformat()
            os_info= os_info
            client_code= client_code
            error_log= error_log

            # Append data
            row_err = [host_name, time_of_request, os_info, error_log, client_code, topic, region, sources_count, news_count, isprioritize]
            sh_error.append_row(row_err)
    except:
        pass

    lottie_animation3 = utils.get("graphics/Animation_10.json")
    st_lottie(lottie_animation3, speed=1, reverse=True, height=700, loop=True, quality="high", key="logo1")
    