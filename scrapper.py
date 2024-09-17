import streamlit as st
import pandas as pd
from linkedin_api import Linkedin
import json
from typing import List, Literal

# Secure credential storage
def save_credentials(username, password):
    st.session_state['linkedin_username'] = username
    st.session_state['linkedin_password'] = password

def load_credentials():
    return st.session_state.get('linkedin_username'), st.session_state.get('linkedin_password')

# Function to handle API calls
def execute_api_function(api, function_name, **kwargs):
    try:
        function = getattr(api, function_name)
        return function(**kwargs), None
    except Exception as e:
        return None, str(e)

# Function to create input fields based on parameter type
def create_input_field(param_name, param_type):
    if param_type == str:
        return st.text_input(f"{param_name}", key=f"input_{param_name}")
    elif param_type == int:
        return st.number_input(f"{param_name}", step=1, key=f"input_{param_name}")
    elif param_type == bool:
        return st.checkbox(f"{param_name}", key=f"input_{param_name}")
    elif param_type == List[str]:
        return st.text_input(f"{param_name} (comma-separated)", key=f"input_{param_name}")
    elif "Literal" in str(param_type):
        options = eval(str(param_type).split("Literal")[1])
        return st.selectbox(f"{param_name}", options, key=f"input_{param_name}")
    else:
        return st.text_input(f"{param_name}", key=f"input_{param_name}")

# Main app
def main():
    st.set_page_config(layout="wide")
    
    # Side panel
    with st.sidebar:
        st.title("LinkedIn Scraper")
        if 'linkedin_username' in st.session_state:
            st.success(f"Logged in as: {st.session_state['linkedin_username']}")
            if st.button("Logout", key="sidebar_logout"):
                del st.session_state['linkedin_username']
                del st.session_state['linkedin_password']
                st.session_state.page = 'welcome'
                st.success("Logged out successfully!")
                st.experimental_rerun()
        
        st.header("Navigation")
        if st.button("Home", key="sidebar_home"):
            st.session_state.page = 'welcome'
        if st.button("Login", key="sidebar_login"):
            st.session_state.page = 'login'
        if 'linkedin_username' in st.session_state:
            if st.button("API Functions", key="sidebar_api"):
                st.session_state.page = 'api_selection'
        
        st.header("About")
        st.info("This app allows you to scrape data from LinkedIn using various API functions.")

    # Main content
    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'

    if st.session_state.page == 'welcome':
        st.header("Welcome to LinkedIn Scraper")
        st.write("Instructions:")
        st.write("1. Log in with your LinkedIn credentials.")
        st.write("2. Choose an API function to use.")
        st.write("3. Fill in the required parameters.")
        st.write("4. View the results and optionally export to CSV.")
        if st.button("Get Started", key="welcome_get_started"):
            st.session_state.page = 'login'
            st.info("Redirecting to login page...")
            st.experimental_rerun()

    elif st.session_state.page == 'login':
        st.header("LinkedIn Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            if username and password:
                save_credentials(username, password)
                st.session_state.page = 'api_selection'
                st.success("Logged in successfully!")
                st.info("Redirecting to API selection...")
                st.experimental_rerun()
            else:
                st.error("Please enter both username and password.")

    elif st.session_state.page == 'api_selection':
        username, password = load_credentials()
        if not username or not password:
            st.error("Please log in first.")
            st.session_state.page = 'login'
            st.experimental_rerun()
        else:
            try:
                api = Linkedin(username, password)
                st.success("Connected to LinkedIn API successfully!")
            except Exception as e:
                st.error(f"Failed to connect to LinkedIn API: {str(e)}")
                st.info("Please try logging in again.")
                st.session_state.page = 'login'
                st.experimental_rerun()

            st.header("API Function Selection")
            
            api_functions = {
                "Get Profile": {
                    "function": "get_profile",
                    "params": {
                        "public_id": str,
                        "urn_id": str
                    }
                },
                "Search People": {
                    "function": "search_people",
                    "params": {
                        "keywords": str,
                        "connection_of": str,
                        "network_depths": List[Literal['F', 'S', 'O']],
                        "current_company": List[str],
                        "past_companies": List[str],
                        "nonprofit_interests": List[str],
                        "profile_languages": List[str],
                        "regions": List[str],
                        "industries": List[str],
                        "schools": List[str],
                        "include_private_profiles": bool,
                        "keyword_first_name": str,
                        "keyword_last_name": str,
                        "keyword_title": str,
                        "keyword_company": str,
                        "keyword_school": str,
                        "service_categories": List[str],
                        "network_depth": Literal['F', 'S', 'O'],
                        "title": str
                    }
                },
                # ... [other API functions remain the same]
            }
            
            selected_function = st.selectbox("Choose an API function", list(api_functions.keys()), key="function_select")
            function_info = api_functions[selected_function]
            
            st.subheader(f"Parameters for {selected_function}")
            
            params = {}
            for param_name, param_type in function_info["params"].items():
                param_value = create_input_field(param_name, param_type)
                if param_value:
                    if param_type == List[str]:
                        params[param_name] = [item.strip() for item in param_value.split(',') if item.strip()]
                    elif "Literal" in str(param_type):
                        params[param_name] = param_value
                    else:
                        params[param_name] = param_type(param_value)
            
            if st.button("Execute", key="execute_button"):
                with st.spinner("Executing API function..."):
                    result, error = execute_api_function(api, function_info["function"], **params)
                    if error:
                        st.error(f"Error executing API function: {error}")
                    else:
                        st.success("API function executed successfully!")
                        display_results(result)

def display_results(result):
    st.subheader("JSON Response")
    st.json(result)
    
    st.subheader("Tabular Data")
    try:
        df = pd.json_normalize(result)
        st.dataframe(df)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="linkedin_data.csv",
            mime="text/csv",
            key="download_csv"
        )
        st.success("Data processed successfully. You can now download the CSV.")
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.info("The JSON response may not be suitable for tabular representation.")

if __name__ == "__main__":
    main()