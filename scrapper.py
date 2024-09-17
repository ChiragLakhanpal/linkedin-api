import streamlit as st
import pandas as pd
from linkedin_api import Linkedin
from typing import List, get_args, Literal
import ast

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
    elif hasattr(param_type, "__origin__") and param_type.__origin__ == Literal:
        options = get_args(param_type)
        return st.selectbox(f"{param_name}", options, key=f"input_{param_name}")
    elif hasattr(param_type, "__origin__") and param_type.__origin__ == List:
        if hasattr(param_type.__args__[0], "__origin__") and param_type.__args__[0].__origin__ == Literal:
            options = get_args(param_type.__args__[0])
            return st.multiselect(f"{param_name}", options, key=f"input_{param_name}")
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
                st.rerun()
        
        st.header("Navigation")
        if st.button("Single Search", key="sidebar_ss"):
            st.session_state.page = 'single_search'
        if st.button("Bulk Search", key="sidebar_bs"):
            st.session_state.page = 'bulk_search'
        
        st.header("About")
        st.info("This app allows you to scrape data from LinkedIn using various API functions.")

    # Main content
    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'

    if st.session_state.page == 'welcome':
        display_welcome_page()

    elif st.session_state.page == 'login':
        display_login_page()

    elif st.session_state.page == 'single_search':
        display_single_search_page()

    elif st.session_state.page == 'bulk_search':
        display_bulk_search_page()

def display_welcome_page():
    st.header("Welcome to LinkedIn Scraper")
    st.write("Instructions:")
    st.write("1. Log in with your LinkedIn credentials.")
    st.write("2. Choose between Single Search or Bulk Search.")
    st.write("3. Fill in the required parameters.")
    st.write("4. View the results and optionally export to CSV.")
    if st.button("Get Started", key="welcome_get_started"):
        st.session_state.page = 'login'
        st.info("Redirecting to login page...")
        st.rerun()

def display_login_page():
    st.header("LinkedIn Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_button"):
        if username and password:
            save_credentials(username, password)
            st.session_state.page = 'single_search'
            st.success("Logged in successfully!")
            st.info("Redirecting to Single Search...")
            st.rerun()
        else:
            st.error("Please enter both username and password.")

def initialize_linkedin_api(username, password):
    try:
        api = Linkedin(username, password)
        # Test the connection by trying to get the user's own profile
        api.get_user_profile()
        return api, None
    except LinkedinError as e:
        if 'unauthorized' in str(e).lower():
            return None, "Invalid credentials. Please check your username and password."
        else:
            return None, f"LinkedIn API error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def display_single_search_page():
    st.header("Single Search")
    username, password = load_credentials()
    if not username or not password:
        st.error("Please log in first.")
        st.session_state.page = 'login'
        st.rerun()
    else:
        api, error = initialize_linkedin_api(username, password)
        if api:
            st.success("Connected to LinkedIn API successfully!")
            display_api_function_selection(api)
        else:
            st.error(f"Failed to connect to LinkedIn API: {error}")
            st.info("Please try logging in again.")
            st.session_state.page = 'login'
            st.rerun()

def display_bulk_search_page():
    st.header("Bulk Search")
    st.write("Bulk search functionality is not implemented yet.")

def display_api_function_selection(api):
    st.subheader("API Function Selection")
    
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
            "contact_interests": List[str],
            "service_categories": List[str],
            "include_private_profiles": bool,
            "keyword_first_name": str,
            "keyword_last_name": str,
            "keyword_title": str,
            "keyword_company": str,
            "keyword_school": str,
            "network_depth": Literal['F', 'S', 'O'],
            "title": str
        }
    },
    "Get Company": {
        "function": "get_company",
        "params": {
            "public_id": str
        }
    },
    "Get Company Updates": {
        "function": "get_company_updates",
        "params": {
            "public_id": str,
            "urn_id": str,
            "max_results": int
        }
    },
    "Get Conversation": {
        "function": "get_conversation",
        "params": {
            "conversation_urn_id": str
        }
    },
    "Get Conversation Details": {
        "function": "get_conversation_details",
        "params": {
            "profile_urn_id": str
        }
    },
    "Get Conversations": {
        "function": "get_conversations",
        "params": {}
    },
    "Get Current Profile Views": {
        "function": "get_current_profile_views",
        "params": {}
    },
    "Get Feed Posts": {
        "function": "get_feed_posts",
        "params": {
            "limit": int,
            "offset": int,
            "exclude_promoted_posts": bool
        }
    },
    "Get Invitations": {
        "function": "get_invitations",
        "params": {
            "start": int,
            "limit": int
        }
    },
    "Get Job": {
        "function": "get_job",
        "params": {
            "job_id": str
        }
    },
    "Get Job Skills": {
        "function": "get_job_skills",
        "params": {
            "job_id": str
        }
    },
    "Get Post Comments": {
        "function": "get_post_comments",
        "params": {
            "post_urn": str,
            "comment_count": int
        }
    },
    "Get Post Reactions": {
        "function": "get_post_reactions",
        "params": {
            "urn_id": str,
            "max_results": int
        }
    },
    "Get Profile Connections": {
        "function": "get_profile_connections",
        "params": {
            "urn_id": str
        }
    },
    "Get Profile Contact Info": {
        "function": "get_profile_contact_info",
        "params": {
            "public_id": str,
            "urn_id": str
        }
    },
    "Get Profile Experiences": {
        "function": "get_profile_experiences",
        "params": {
            "urn_id": str
        }
    },
    "Get Profile Member Badges": {
        "function": "get_profile_member_badges",
        "params": {
            "public_profile_id": str
        }
    },
    "Get Profile Network Info": {
        "function": "get_profile_network_info",
        "params": {
            "public_profile_id": str
        }
    },
    "Get Profile Posts": {
        "function": "get_profile_posts",
        "params": {
            "public_id": str,
            "urn_id": str,
            "post_count": int
        }
    },
    "Get Profile Privacy Settings": {
        "function": "get_profile_privacy_settings",
        "params": {
            "public_profile_id": str
        }
    },
    "Get Profile Skills": {
        "function": "get_profile_skills",
        "params": {
            "public_id": str,
            "urn_id": str
        }
    },
    "Get Profile Updates": {
        "function": "get_profile_updates",
        "params": {
            "public_id": str,
            "urn_id": str,
            "max_results": int
        }
    },
    "Get School": {
        "function": "get_school",
        "params": {
            "public_id": str
        }
    },
    "Get User Profile": {
        "function": "get_user_profile",
        "params": {
            "use_cache": bool
        }
    },
    "Search Companies": {
        "function": "search_companies",
        "params": {
            "keywords": List[str]
        }
    },
    "Search Jobs": {
        "function": "search_jobs",
        "params": {
            "keywords": str,
            "companies": List[str],
            "experience": List[Literal['1', '2', '3', '4', '5', '6']],
            "job_type": List[Literal['F', 'C', 'P', 'T', 'I', 'V', 'O']],
            "job_title": List[str],
            "industries": List[str],
            "location_name": str,
            "remote": List[Literal['1', '2', '3']],
            "listed_at": int,
            "distance": int,
            "limit": int,
            "offset": int
        }
    },
    "Add Connection": {
        "function": "add_connection",
        "params": {
            "profile_public_id": str,
            "message": str,
            "profile_urn": str
        }
    },
    "Remove Connection": {
        "function": "remove_connection",
        "params": {
            "public_profile_id": str
        }
    },
    "Follow Company": {
        "function": "follow_company",
        "params": {
            "following_state_urn": str,
            "following": bool
        }
    },
    "Unfollow Entity": {
        "function": "unfollow_entity",
        "params": {
            "urn_id": str
        }
    },
    "React to Post": {
        "function": "react_to_post",
        "params": {
            "post_urn_id": str,
            "reaction_type": Literal['LIKE', 'PRAISE', 'APPRECIATION', 'EMPATHY', 'INTEREST', 'ENTERTAINMENT']
        }
    },
    "Send Message": {
        "function": "send_message",
        "params": {
            "message_body": str,
            "conversation_urn_id": str,
            "recipients": List[str]
        }
    },
    "Mark Conversation as Seen": {
        "function": "mark_conversation_as_seen",
        "params": {
            "conversation_urn_id": str
        }
    },
    "Reply Invitation": {
        "function": "reply_invitation",
        "params": {
            "invitation_entity_urn": str,
            "invitation_shared_secret": str,
            "action": Literal['accept', 'reject']
        }
    }
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
