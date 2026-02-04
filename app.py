import streamlit as st
import requests
import json

# PAGE SETUP
st.set_page_config(page_title="SEO Agent", page_icon="🚀", layout="wide")
st.title("🚀 SEO Strategist & Auditor")

# SIDEBAR (Credentials)
with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("Agent URL", placeholder="https://...langchain.com")
    api_key = st.text_input("API Key", type="password")
    st.info("Enter the URL and Key provided by your developer.")

# CHAT INTERFACE
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# INPUT HANDLING
if prompt := st.chat_input("Ask the SEO Agent..."):
    if not api_url or not api_key:
        st.error("🚨 Please enter the Agent URL and API Key in the sidebar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # CALL THE AGENT
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # We assume the standard LangGraph Cloud endpoint structure
        target_endpoint = api_url.rstrip("/") + "/runs/stream"
        
        payload = {
            "assistant_id": "seo_agent", 
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "stream_mode": "values"
        }
        
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}

        try:
            with requests.post(target_endpoint, json=payload, headers=headers, stream=True) as response:
                if response.status_code != 200:
                    st.error(f"Error {response.status_code}: {response.text}")
                else:
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data: "):
                                data_str = decoded.replace("data: ", "")
                                try:
                                    data = json.loads(data_str)
                                    # Look for the AI's response in the messages list
                                    if "messages" in data and len(data["messages"]) > 0:
                                        last_msg = data["messages"][-1]
                                        if last_msg["type"] == "ai":
                                            full_response = last_msg["content"]
                                            message_placeholder.markdown(full_response + "▌")
                                except:
                                    pass
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Connection Failed: {e}")
