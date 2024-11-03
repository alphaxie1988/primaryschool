import streamlit as st
from streamlit_chat import message
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os
import graphviz

load_dotenv()
st.set_page_config(
    page_title="Primay School",
    page_icon="📖",
    )

st.logo("logobig.png", icon_image="logosmall.png",size='large')
@st.cache_data
def loadData():

    school_info_df = pd.read_csv('data/generalInformation.csv')
    school_info_df = school_info_df[school_info_df['mainlevel_code'] == "PRIMARY"]

    ccadf = pd.read_csv('data/CCA.csv')
    ccadf = ccadf[ccadf['school_name'].isin(school_info_df['school_name'])]
    ccadf =  ccadf[['school_name','cca_generic_name']]
    ccadf_pivot = ccadf.pivot_table(
    index=["school_name"],
    columns="cca_generic_name",
    aggfunc=lambda x: 'Yes',
    fill_value='No').reset_index()
    ccadf_pivot.columns = [
        f"CCA: {col}" if col not in ["school_name"] else col 
        for col in ccadf_pivot.columns
    ]

 
    subjectdf = pd.read_csv('data/subjectsOffered.csv')
    subjectdf = subjectdf[subjectdf['school_name'].isin(school_info_df['school_name'])]
    subjectdf =  subjectdf[['school_name','subject_desc']]
    subjectdf_pivot = subjectdf.pivot_table(
    index=["school_name"],
    columns="subject_desc",
    aggfunc=lambda x: 'Yes',
    fill_value='No').reset_index()
    subjectdf_pivot.columns = [
        f"subject offered: {col}" if col not in ["school_name"] else col 
        for col in subjectdf_pivot.columns
    ]

    popularitydf = pd.read_csv('data/popularity.csv')
    popularitydf = popularitydf[popularitydf['school_name'].isin(school_info_df['school_name'])]
    popularitydf =  popularitydf[['school_name','popularity']]
   


    school_info_df = pd.merge(school_info_df, ccadf_pivot, on="school_name", how="left")
    school_info_df = pd.merge(school_info_df, subjectdf_pivot, on="school_name", how="left")
    school_info_df = pd.merge(school_info_df, popularitydf, on="school_name", how="left")

    school_info_df = school_info_df.fillna("No")
    return school_info_df
@st.cache_data
def get_school_info(school_data, query,previousContext):
            # Find the school name mentioned in the query
            school_name = []
            for name in school_data["school_name"]:
                if name.lower() in query.lower():
                    school_name.append(name)

            if len(school_name) >= 1:
                # Get relevant row from the DataFrame
                context = ""
                for school in school_name:
                    context += "\nInformation about "+school+"\n"
                    school_info = school_data[school_data["school_name"] == school].to_dict(orient="records")[0]
                # Format school information as context
                    context += "\n".join([f"{key}: {value}" for key, value in school_info.items() if pd.notna(value)])
                st.write("🛜 Context Passed to LLM")
                #st.write(context)
                return context
            else:
                return previousContext
            
def app():
    if "context" not in st.session_state:
        st.session_state.context = ""
    def Compare_School():
        st.header("Compare School")
            # Sample options list
        school_data = loadData()
        # Step 3: Create a dropdown list from the unique `cca_generic_name` values

        options = school_data["school_name"]

        # Dropdown 1
        selection_1 = st.selectbox("Select option 1:", options, key="dropdown_1")

        # Dropdown 2
        selection_2 = st.selectbox("Select option 2:", options, key="dropdown_2")
        # Check if selections are different
        if selection_1 == selection_2:
            st.warning("Please select two different school.")
            # Disable the submit button if selections are the same
            submit_button = st.button("Compare the two Schools", disabled=True)
        else:
            # Enable the submit button if selections are different
            submit_button = st.button("Compare the two Schools")

        if submit_button:
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            if "openai_model" not in st.session_state:
                st.session_state["openai_model"] = "gpt-4o-mini"
            st.success(f"You selected {selection_1} and {selection_2}.")
            context = ""
            context += "\nInformation about "+selection_1+"\n"
            school_info = school_data[school_data["school_name"] == selection_1].to_dict(orient="records")[0]
            # Format school information as context
            context += "\n".join([f"{key}: {value}" for key, value in school_info.items() if pd.notna(value)])
            context += "\nInformation about "+selection_2+"\n"
            school_info = school_data[school_data["school_name"] == selection_2].to_dict(orient="records")[0]
            # Format school information as context
            context += "\n".join([f"{key}: {value}" for key, value in school_info.items() if pd.notna(value)])
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": "system", "content": f"Use the following school information as context:\n\n{context}"},
                {"role": "user", "content": "Can you come out with the comprehensive comparison based of the two schools? If possible give a conclusion on which is a better school and why. Note that the popularity score is calculated based on number of applicant in phase 2B divided by the amount of vacancy in Phase 2B. The higher number mean more popular"}],
                stream=True,
            )
            response = st.write_stream(stream)
            if response:
                with st.expander("Disclaimer"):
                    st.write("""**IMPORTANT NOTICE**: This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

Furthermore, please be aware that the large language model may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

Always consult with qualified professionals for accurate and personalized advice.""")

    def LLM_Ask_School_Info():
        st.header("LLM Ask School Info")
        rag = st.checkbox("Use RAG",True)
        # Sample data loading (replace with your actual data file)
        school_data = loadData()
        school_data["school_name"] = school_data["school_name"].str.replace('SCHOOL', '',case=False).str.strip()
        #st.dataframe(school_data)
        # Function to retrieve school information based on query
        
        # Set up OpenAI client
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

        if prompt := st.chat_input("Where is Mee Toh School?"):
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get additional context for RAG
            if rag:
                st.session_state.context = get_school_info(school_data, prompt,st.session_state.context)
            else:
                st.session_state.context = ""
        
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                # Include context as an inline message for the assistant's response without saving it in the session state
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": "system", "content": f"Use the following school information as context:\n\n{st.session_state.context}, please only reply if question is related to the context."},
                        *st.session_state.messages  # Append user and assistant messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
        if len(st.session_state.messages) == 0:
            st.info("Try asking: Where is Mee Toh and who is the princiapl of the school? What mother tongue does it provide? Does it have Choir as CCA?")
        else:
            with st.expander("Disclaimer"):
                st.write("""**IMPORTANT NOTICE**: This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

Furthermore, please be aware that the large language model may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

Always consult with qualified professionals for accurate and personalized advice.""")
    def CCA_Finder():
        st.header("CCA Finder")

        # Step 1: Read the CSV file into a pandas DataFrame
        df = pd.read_csv('data/CCA.csv')
    

        # Step 2: Get a list of unique data from the column `cca_generic_name`
        unique_cca_names = df['cca_generic_name'].unique()
        # Step 3: Create a dropdown list from the unique `cca_generic_name` values
        selected_cca = st.selectbox("Select a CCA", unique_cca_names)
        # Step 4: Filter the DataFrame to show `school_name` where `cca_generic_name` matches the selection
        filtered_df = df[(df['cca_generic_name'] == selected_cca) & (df['school_section'] == 'PRIMARY')]

        # Display the list of school names
        st.write("Schools offering the selected CCA:")
        st.write(filtered_df['school_name'].unique())

    def About_Us():
        st.header("About Us")
        st.write("This application is done by Xie Jianlong from CSIT. For feedback please email me at xie_jl@csit.gov.sg")
        st.subheader("Use Case 1 - Compare School", divider=True)
        st.write("This tool allows you to select two Singapore Primary School and do a detailed analytics on the school.")
        st.write("This use case uses canned prompt approach by passing user selected information as context for the LLM to make analysis")
        st.write("Currently The canned Prompt is")
        st.info("Can you come out with the comprehensive comparison based of the two schools? If possible give a conclusion on which is a better school and why. Note that the popularity score is calculated based on number of applicant in phase 2B divided by the amount of vacancy in Phase 2B. The higher number mean more popular")
        school_data = loadData()
        st.info(get_school_info(school_data,"Mee Toh School",""))
        
        st.divider()
        st.subheader("Use Case 2 - Ask School General Information", divider=True)
        st.write("""Using LLM to ask school related information, example you can ask where is Mee Toh School
                \nUsing openAI gpt-4o-mini model LLM there is alot of hallucination. The system uses curated data MOE via data.gov.sg.
                \nWhen user post a question eg where is Mee Toh Primary School?
                \nThe program will do a Simple RAG by getting the context from the data.
                \n\nResponse Before RAG
                """)
        st.image("meetoh1.png")
        st.write("Response after RAG")
        st.image("meetoh2.png")
        st.image("meetoh3.png",caption="Actual Location of Mee Toh", width=450)
        st.write("As you can see before RAG the address was very vague. Sometime it might even give wrong answer. The LLM also can answer more definitive after RAG")
        st.divider()
        st.subheader("Use Case 3 - CCA Finder", divider=True)
        st.write("Using Streamlit python to allow user quickly drill down in to the level (Primary, Secondary, JC) and choice of CCA, the system will return the list of school that provide the selected CCA")
        st.divider()
        st.subheader("Data source", divider=True)
        st.write("""MOE (Ministry of Education)
    List of all schools with details on:
```
General information of schools ✅
Subjects offered ✅
Co-curricular activities (CCAs) ✅
MOE programmes ❌
School Distinctive Programmes ❌
```""")
        st.write("All information is accurate as at 24 Mar 2021.")
        st.write("https://data.gov.sg/datasets?topics=education&page=1&resultId=457")
        st.divider()
        st.write("""Primary 1 Registration 2024 Data
```
    List of all schools with the vacancy and applicant in phase 2B 2024 ✅
```
""")        
        st.write("https://mathnuggets.sg/best-primary-schools-in-singapore/")
    def Methodology():
        st.header("Methodology")
        st.write("""A comprehensive explanation of the data flows and implementation details.
    A flowchart illustrating the process flow for each of the use cases in the application. For example, if the application has two main use cases: a) chat with information and b) intelligent search, each of these use cases should have its own flowchart.""")
        st.divider()
        st.subheader("Use Case 1 - Compare School", divider=True)
        graph = graphviz.Digraph()
        graph.edge("School Popularity via mathnuggets.sg", "Data Loader")
        graph.edge("School Data via data.gov.sg", "Data Loader")
        graph.edge("Data Loader", "Pandas DataFrame")
        graph.edge("Pandas DataFrame", "Merge CCA/Subject/General Information Tables")
        graph.edge("Merge CCA/Subject/General Information Tables", "User Select Two Schools")
        graph.edge("User Select Two Schools","Parse Information of the Two Schools as Context")
        graph.edge("Parse Information of the Two Schools as Context","Display the LLM Response")
        st.graphviz_chart(graph)
        st.subheader("Use Case 2 - Ask School General Information", divider=True)
        # Create a graphlib graph object
        graph = graphviz.Digraph()
        graph.edge("School Popularity via mathnuggets.sg", "Data Loader")
        graph.edge("School Data via data.gov.sg", "Data Loader")
        graph.edge("Data Loader", "Pandas DataFrame")
        graph.edge("Pandas DataFrame", "Merge CCA/Subject/General Information Tables")
        graph.edge("Merge CCA/Subject/General Information Tables", "User Submit Query")
        graph.edge("User Submit Query","Is Rag Enabled")
        graph.edge("Is Rag Enabled","If School name appears in User Submitted Query","Yes")
        graph.edge("If School name appears in User Submitted Query","Perform RAG","Yes")
        graph.edge("Is Rag Enabled","Use blank Context","No")
        graph.edge("If School name appears in User Submitted Query","Is there Existing Context",'No')
        graph.edge("Is there Existing Context","Use Existing Context","Yes")
        graph.edge("Is there Existing Context","Use blank Context","No")
        graph.edge("Use Existing Context","Set Context")
        graph.edge("Perform RAG","Get data from Dataframe convert to String")
        graph.edge("Get data from Dataframe convert to String","Set Context")
        graph.edge("Use blank Context","Set Context")
        st.graphviz_chart(graph)
        
        st.divider()
        st.subheader("Use Case 3 - CCA Finder", divider=True)
        graph = graphviz.Digraph()
        graph.edge("School CCA Data via data.gov.sg", "Data Loader")
        graph.edge("Data Loader", "Pandas DataFrame")
        graph.edge("Pandas DataFrame","User Select CCA")
        graph.edge("User Select CCA","Display a list of School Match Condition")
        st.graphviz_chart(graph)


    pg = st.navigation([st.Page(Compare_School), st.Page(LLM_Ask_School_Info),st.Page(CCA_Finder), st.Page(About_Us), st.Page(Methodology)])
    pg.run()


# Define the hardcoded password
correct_password = os.environ.get("password")

# Initialize session state to store whether access has been granted
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Create a placeholder for the password input box
placeholder = st.empty()

# Check if the user is authenticated
if not st.session_state.authenticated:
    # Show password input inside the placeholder
    password = placeholder.text_input("Enter password:", type="password")

    if password:
        # Verify if the password is correct
        if password == correct_password:
            st.session_state.authenticated = True  # Set authentication state
            placeholder.empty()  # Clear the password input box
            app()
        else:
            st.error("Incorrect password. Please try again.")
            st.stop()  # Stop execution if the password is incorrect
else:
    # Content that shows after successful authentication
    app()
