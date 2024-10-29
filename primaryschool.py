import requests
from requests.cookies import RequestsCookieJar
import streamlit as st
import pandas as pd
import streamlit as st
from streamlit_chat import message
import os
from openai import OpenAI



tab1, tab2, tab3,tab4 = st.tabs(["CCA Finder","LLM Ask School Info", "About Us", "Methodology"])

with tab1:
    st.header("CCA Finder")

    # Step 1: Read the CSV file into a pandas DataFrame
    df = pd.read_csv('data/CCA.csv')

    # Step 2: Get a list of unique data from the column `cca_generic_name`
    unique_school_section = df['school_section'].unique()
    unique_cca_names = df['cca_generic_name'].unique()
    # Step 3: Create a dropdown list from the unique `cca_generic_name` values
    selected_school_section = st.selectbox("Select a the level", unique_school_section)
    selected_cca = st.selectbox("Select a CCA", unique_cca_names)
    # Step 4: Filter the DataFrame to show `school_name` where `cca_generic_name` matches the selection
    filtered_df = df[(df['cca_generic_name'] == selected_cca) & (df['school_section'] == selected_school_section)]

    # Display the list of school names
    st.write("Schools offering the selected CCA:")
    st.write(filtered_df['school_name'].unique())
with tab2:
    st.header("LLM Ask School Info")
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})


with tab3:
    st.header("About Us")
    st.write("A detailed page outlining the project scope, objectives, data sources, and features.")
    st.subheader("Use Case 1 - CCA Finder", divider=True)
    st.write("Using Streamlit python to allow user quickly drill down in to the level (Primary, Secondary, JC) and choice of CCA, the system will return the list of school that provide the selected CCA")
    st.divider()
    st.subheader("Use Case 2 - Ask School General Information", divider=True)
    st.write("Using LLM to ask school related information, example you can ask where is Ai Tong School")
    st.divider()
    st.subheader("Data source", divider=True)
    st.write("""MOE (Ministry of Education)
List of all schools with details on:

General information of schools
Subjects offered
Co-curricular activities (CCAs)
MOE programmes
School Distinctive Programmes
All information is accurate as at 24 Mar 2021.""")
    st.write("https://data.gov.sg/datasets?topics=education&page=1&resultId=457")
with tab4:
    st.header("Methodology")
    st.write("""A comprehensive explanation of the data flows and implementation details.
A flowchart illustrating the process flow for each of the use cases in the application. For example, if the application has two main use cases: a) chat with information and b) intelligent search, each of these use cases should have its own flowchart.""")
# Streamlit app

st.stop()
# Create a session
session = requests.Session()

# Set the User-Agent
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
})

# Add cookies
cookies = RequestsCookieJar()
cookies.set('moe-custom#client_date', '30/07/2024', domain='www.moe.gov.sg', path='/')
cookies.set('rp_www.moe.gov.sg', '68f0583b18d679e337a059a19777a1f7', domain='www.moe.gov.sg', path='/')
cookies.set('AWSALB', 'rtgFXfjCp7uv4Q1WdQyWQVPvobfmIB1/m8shZagBTrAANsmVaXj5QMmLjAlE8YAGczjs0d7DgnajRjqPXdZKzAHbJZ81oSZQPtLnO9CVxyJuKBlaehdEC79ZXnYT', domain='www.moe.gov.sg', path='/')
cookies.set('ASP.NET_SessionId', 'nyqu2y5j44ksrsw3eyaejuvu', domain='www.moe.gov.sg', path='/')
session.cookies.update(cookies)

# Set headers
headers = {
    "authority": "www.moe.gov.sg",
    "method": "POST",
    "path": "/api/v1/vacanciesAndBalloting/getAllResult",
    "scheme": "https",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,es;q=0.6,zh-TW;q=0.5",
    "origin": "https://www.moe.gov.sg",
    "priority": "u=1, i",
    "referer": "https://www.moe.gov.sg/primary/p1-registration/vacancies-and-balloting",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin"
}

# Make the POST request
response = session.post('https://www.moe.gov.sg/api/v1/vacanciesAndBalloting/getAllResult', headers=headers)

# Print the response
print(response.status_code)
print(response.text)

df = pd.DataFrame(response.json()[0]["school_list"])
df['avail'] = df['avail'].astype(int)
df['applicant'] = df['applicant'].astype(int)
df['total'] = df['total'].astype(int)

# Filter DataFrame
schools_of_interest = ["Greendale Primary School", "Mee Toh School", "Horizon Primary School"]
filtered_df = df[df['title'].isin(schools_of_interest)][['title', 'avail', 'applicant','area']]


st.write(filtered_df)

schools_of_interest = ["St. Hilda's Primary School", "Gongshang Primary School"]
filtered_df = df[df['title'].isin(schools_of_interest)][['title', 'avail', 'applicant','area']]
grouped_df = df.groupby('area').sum().reset_index()
grouped_df['lack'] = grouped_df['applicant']-grouped_df['avail']
st.write(grouped_df)
st.write(filtered_df)
