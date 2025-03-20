import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pandas as pd
import json
import os

# App title and configuration
st.set_page_config(page_title="AI Note Maker", page_icon="📝", layout="wide")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Main app header
st.title("📝 AI Note Maker")
st.markdown("Generate comprehensive, customized notes on any topic using AI")

# Sidebar for API key and settings
with st.sidebar:
    st.header("🔑 API Configuration")
    api_key = st.text_input("Enter your Gemini API Key", type="password")
    model_name = st.selectbox("Select AI Model", ["gemini-2.0-flash","gemini-2.0-flash-lite","gemini-2.0-pro-exp-02-05","gemini-2.0-flash-thinking-exp-01-21","gemini-1.5-pro", "gemini-1.5-flash","gemini-1.5-flash-8b"], index=0)
    
    st.header("📚 History")
    if st.button("Clear History"):
        st.session_state.history = []
        st.success("History cleared!")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("AI Note Maker helps you create detailed notes on any topic using Google's Gemini AI.")

# Function to generate list of AI tools
def generate_ai_tools():
    tools = [
        "Bullet Points",
        "Cornell Notes",
        "Mind Map Structure",
        "Flashcards",
        "Summary Notes",
        "Detailed Explanation",
        "Question & Answer Format",
        "Key Concepts & Definitions",
        "Timeline Format",
        "Comparative Analysis"
    ]
    
    categories = {
        "Note Formats": ["Bullet Points", "Cornell Notes", "Mind Map Structure", "Summary Notes", "Detailed Explanation"],
        "Study Aids": ["Flashcards", "Question & Answer Format", "Key Concepts & Definitions"],
        "Specialized": ["Timeline Format", "Comparative Analysis"]
    }
    
    return tools, categories

# Get all tools and categories
ai_tools, tool_categories = generate_ai_tools()

# Function to load prompt templates
@st.cache_data
def load_prompt_templates():
    templates = {
        "Bullet Points": "Create comprehensive bullet point notes on: {prompt}. Format with clear hierarchical structure (main points and sub-points) using bullet symbols. Make notes concise yet complete, covering all important aspects. Use appropriate spacing for readability.",
        
        "Cornell Notes": "Create Cornell-style notes on: {prompt}. Structure with three sections: 1) Right column (main notes area): detailed content with clear paragraphs and hierarchical organization, 2) Left column (cue column): key questions, terms, and concepts that align with the main notes, 3) Bottom section: concise summary of the entire topic. Use proper formatting and spacing.",
        
        "Mind Map Structure": "Create a text-based mind map structure on: {prompt}. Format with the core concept in the center, main branches using level 1 headings, sub-branches using level 2 headings, and leaf nodes using bullet points. Use indentation to show relationships between concepts. Include all important relationships and hierarchies.",
        
        "Flashcards": "Create a set of flashcards on: {prompt}. Format with 'Q:' for questions and 'A:' for answers, separating each flashcard with a divider line. Include comprehensive coverage of key facts, definitions, concepts, and their applications. Number each flashcard.",
        
        "Summary Notes": "Create concise summary notes on: {prompt}. Include only the most essential information, key concepts, and critical takeaways. Format with clear headings and short paragraphs. Ensure comprehensive coverage while maintaining brevity (maximum 1/3 the length of detailed notes).",
        
        "Detailed Explanation": "Create detailed explanatory notes on: {prompt}. Include thorough explanations of concepts, supporting evidence, examples, and applications. Structure with clear headings, subheadings, and logical flow. Use appropriate technical language while ensuring clarity.",
        
        "Question & Answer Format": "Create comprehensive Q&A format notes on: {prompt}. Format with clear questions followed by detailed answers. Cover all important aspects of the topic with questions ranging from basic understanding to advanced application. Group related questions together under appropriate headings.",
        
        "Key Concepts & Definitions": "Create a glossary of key concepts and definitions for: {prompt}. Format each entry with the term in bold followed by a comprehensive definition. Include examples where helpful. Organize alphabetically or by related concept groups with clear headings.",
        
        "Timeline Format": "Create chronological timeline notes on: {prompt}. Format with clear date/period indicators followed by detailed descriptions of events, developments, or phases. Include significant milestones, causes, and effects. Use appropriate headings for major eras or transitions.",
        
        "Comparative Analysis": "Create comparative analysis notes on: {prompt}. Structure with clear categories for comparison in the left column and entities being compared across the top. Include detailed points of comparison with similarities and differences clearly marked. Conclude with synthesis of key insights from the comparison."
    }
    return templates

# Function to generate content with AI
def generate_ai_content(prompt, api_key, model_name, temperature, detail_level):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        with st.spinner("🔮 AI is working its magic..."):
            # Adjust max tokens based on detail level
            max_tokens = {
                "Brief": 2048,
                "Standard": 4096, 
                "Comprehensive": 8192
            }
            
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_tokens[detail_level]
            }
            
            response = model.generate_content(prompt, generation_config=generation_config)
            return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Function to save content to history
def save_to_history(tool_name, topic, output):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history.insert(0, {"timestamp": timestamp, "tool": tool_name, "topic": topic, "output": output})
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]

# Function to export notes
def export_notes(content, format="txt"):
    if format == "txt":
        return content
    elif format == "md":
        return content  # Already in markdown format
    else:
        return content

# Main content area
templates = load_prompt_templates()

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Create New Notes")
    topic = st.text_area("Enter Topic", height=100, placeholder="Enter the topic you want to create notes for...")
    
with col2:
    st.header("Note Parameters")
    note_type = st.selectbox("Note Format", ai_tools)
    
    # Additional customization parameters
    detail_level = st.select_slider(
        "Detail Level",
        options=["Brief", "Standard", "Comprehensive"],
        value="Standard"
    )
    
    temperature = st.slider("Creativity Level", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
    
    education_level = st.selectbox(
        "Education Level",
        ["Elementary", "Middle School", "High School", "Undergraduate", "Graduate", "Professional"],
        index=3
    )

# Create formatted prompt with parameters
if topic:
    base_prompt = templates[note_type].format(prompt=topic)
    final_prompt = f"{base_prompt}\n\nAdditional parameters:\n- Detail level: {detail_level}\n- Education level: {education_level}"
    
    st.markdown("---")
    
    # Generate and display notes
    if st.button("Generate Notes"):
        if not api_key:
            st.error("Please enter your Gemini API key in the sidebar")
        else:
            output = generate_ai_content(final_prompt, api_key, model_name, temperature, detail_level)
            
            # Save to history
            save_to_history(note_type, topic, output)
            
            # Display results
            st.header(f"Notes on: {topic}")
            
            # Create tabs for viewing and exporting
            tab1, tab2 = st.tabs(["View Notes", "Export Options"])
            
            with tab1:
                st.markdown(output)
            
            with tab2:
                export_format = st.selectbox("Export Format", ["Text (.txt)", "Markdown (.md)"])
                format_extension = export_format.split('(')[1].replace(')', '').replace('.', '')
                
                export_content = export_notes(output, format_extension)
                st.download_button(
                    label="Download Notes",
                    data=export_content,
                    file_name=f"notes_{topic.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.{format_extension}",
                    mime="text/plain"
                )

# Display history
if st.session_state.history:
    st.markdown("---")
    st.header("Recent Notes")
    
    for i, item in enumerate(st.session_state.history[:5]):
        with st.expander(f"**{item['topic']}** ({item['tool']}) - {item['timestamp']}"):
            st.markdown(item['output'])
            
            # Add option to re-export
            format_extension = "txt"
            export_content = export_notes(item['output'], format_extension)
            st.download_button(
                label="Download These Notes",
                data=export_content,
                file_name=f"notes_{item['topic'].replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.{format_extension}",
                mime="text/plain",
                key=f"download_{i}"
            )
