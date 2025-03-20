import streamlit as st
import google.generativeai as genai
from datetime import datetime
import pandas as pd
import json
import os
import re

# App title and configuration
st.set_page_config(page_title="AI Note Maker", page_icon="📝", layout="wide")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'custom_templates' not in st.session_state:
    st.session_state.custom_templates = {}

# Main app header
st.title("📝 AI Note Maker")
st.markdown("Generate comprehensive, customized notes on any topic using AI")

# Sidebar for API key and settings
with st.sidebar:
    st.header("🔑 API Configuration")
    saved_api_key = st.text_input("Enter your Gemini API Key", value=st.session_state.api_key, type="password")
    if saved_api_key != st.session_state.api_key:
        st.session_state.api_key = saved_api_key
    
    model_name = st.selectbox("Select AI Model", 
                             ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-pro-exp-02-05", 
                              "gemini-2.0-flash-thinking-exp-01-21", "gemini-1.5-pro", 
                              "gemini-1.5-flash", "gemini-1.5-flash-8b"], 
                             index=0)
    
    # View options
    st.header("🔍 View Options")
    view_mode = st.radio("Select View", ["Standard", "Compact", "Focused"], index=0)
    
    # Theme settings
    st.header("🎨 Theme")
    theme_options = ["Light", "Dark", "Blue", "Green"]
    selected_theme = st.selectbox("Select Theme", theme_options, index=0)
    
    # History and Favorites tabs
    tab1, tab2 = st.tabs(["History", "Favorites"])
    
    with tab1:
        if st.button("Clear History"):
            st.session_state.history = []
            st.success("History cleared!")
        
        # Display compact history
        if st.session_state.history:
            for i, item in enumerate(st.session_state.history[:10]):
                st.caption(f"{i+1}. {item['topic']} ({item['tool']})")
    
    with tab2:
        # Display favorites
        if st.session_state.favorites:
            for i, item in enumerate(st.session_state.favorites):
                st.caption(f"{i+1}. {item['topic']} ({item['tool']})")
            
            if st.button("Clear Favorites"):
                st.session_state.favorites = []
                st.success("Favorites cleared!")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("AI Note Maker helps you create detailed notes on any topic using Google's Gemini AI.")
    st.markdown("v2.0 - Advanced Controls")

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
        "Comparative Analysis",
        "Exam Preparation",
        "Research Notes",
        "Case Study Analysis",
        "Custom Template"
    ]
    
    categories = {
        "Note Formats": ["Bullet Points", "Cornell Notes", "Mind Map Structure", "Summary Notes", "Detailed Explanation"],
        "Study Aids": ["Flashcards", "Question & Answer Format", "Key Concepts & Definitions", "Exam Preparation"],
        "Specialized": ["Timeline Format", "Comparative Analysis", "Research Notes", "Case Study Analysis"],
        "Custom": ["Custom Template"]
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
        
        "Comparative Analysis": "Create comparative analysis notes on: {prompt}. Structure with clear categories for comparison in the left column and entities being compared across the top. Include detailed points of comparison with similarities and differences clearly marked. Conclude with synthesis of key insights from the comparison.",
        
        "Exam Preparation": "Create comprehensive exam preparation notes on: {prompt}. Include key definitions, formulas, concepts, potential exam questions, and model answers. Format with clear sections for different question types and difficulty levels. Highlight common pitfalls and strategies for tackling complex problems.",
        
        "Research Notes": "Create detailed research notes on: {prompt}. Structure with clear sections for background, methodology, key findings, and implications. Include thorough analysis of current research, potential gaps, and future directions. Use appropriate citations and references format.",
        
        "Case Study Analysis": "Create a comprehensive case study analysis on: {prompt}. Structure with clear sections for background, key issues, stakeholder analysis, alternatives, recommendations, and implementation plan. Include detailed analysis of causes and effects, supported by evidence and reasoning."
    }
    return templates

# Function to generate content with AI
def generate_ai_content(prompt, api_key, model_name, temperature, detail_level, style_params):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        with st.spinner("🔮 AI is working its magic..."):
            # Adjust max tokens based on detail level
            max_tokens = {
                "Brief": 2048,
                "Standard": 4096, 
                "Comprehensive": 8192,
                "Expert": 12288
            }
            
            # Apply style adjustments to prompt
            style_prefix = f"Using {style_params['tone']} tone and {style_params['language_style']} language style, "
            enhanced_prompt = style_prefix + prompt
            
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_tokens[detail_level]
            }
            
            response = model.generate_content(enhanced_prompt, generation_config=generation_config)
            return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Function to save content to history
def save_to_history(tool_name, topic, output, favorite=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item = {"timestamp": timestamp, "tool": tool_name, "topic": topic, "output": output, "favorite": favorite}
    
    st.session_state.history.insert(0, item)
    if len(st.session_state.history) > 30:
        st.session_state.history = st.session_state.history[:30]
    
    if favorite:
        st.session_state.favorites.insert(0, item)
        if len(st.session_state.favorites) > 20:
            st.session_state.favorites = st.session_state.favorites[:20]

# Function to export notes
def export_notes(content, format="txt"):
    if format == "txt":
        return content
    elif format == "md":
        return content  # Already in markdown format
    elif format == "csv":
        # Convert to CSV if content is structured appropriately
        # This is a simple implementation and may need enhancement
        lines = content.split('\n')
        csv_lines = []
        for line in lines:
            # Replace markdown formatting and convert to CSV
            line = re.sub(r'^\s*[-*]', '', line).strip()
            if line:
                csv_lines.append(line)
        return '\n'.join(csv_lines)
    else:
        return content

# Main content area
templates = load_prompt_templates()

# Determine layout based on view mode
if view_mode == "Standard":
    col1, col2 = st.columns([2, 1])
elif view_mode == "Compact":
    col1, col2, col3 = st.columns([1, 1, 1])
else:  # Focused
    col1 = st
    col2 = st

# Topic and parameters input
if view_mode == "Standard" or view_mode == "Focused":
    with col1:
        st.header("Create New Notes")
        topic = st.text_area("Enter Topic", height=100, placeholder="Enter the topic you want to create notes for...")
        
    with col2:
        st.header("Note Parameters")
        note_type = st.selectbox("Note Format", ai_tools)
        
        # Show custom template field if selected
        if note_type == "Custom Template":
            template_name = st.text_input("Template Name", key="template_name")
            
            # Load existing template if available
            template_value = ""
            if template_name in st.session_state.custom_templates:
                template_value = st.session_state.custom_templates[template_name]
            
            custom_template = st.text_area("Custom Prompt Template", 
                                         value=template_value,
                                         height=150, 
                                         placeholder="Create {detail_level} notes on {prompt}. Use {education_level} language...")
            
            # Save template button
            if st.button("Save Template"):
                st.session_state.custom_templates[template_name] = custom_template
                st.success(f"Template '{template_name}' saved!")
        
        # Additional customization parameters
        detail_level = st.select_slider(
            "Detail Level",
            options=["Brief", "Standard", "Comprehensive", "Expert"],
            value="Standard"
        )
        
        # Advanced parameters
        with st.expander("Advanced Parameters"):
            temperature = st.slider("Creativity Level", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
            
            education_level = st.selectbox(
                "Education Level",
                ["Elementary", "Middle School", "High School", "Undergraduate", "Graduate", "Professional"],
                index=3
            )
            
            # Style parameters
            tone_options = ["Formal", "Casual", "Academic", "Enthusiastic", "Technical", "Simplified"]
            tone = st.selectbox("Tone", tone_options, index=0)
            
            language_style_options = ["Standard", "Creative", "Concise", "Elaborate", "Scientific", "Conversational"]
            language_style = st.selectbox("Language Style", language_style_options, index=0)
            
            # Collect style parameters
            style_params = {
                "tone": tone,
                "language_style": language_style
            }
else:  # Compact view
    with col1:
        st.header("Topic")
        topic = st.text_area("Enter Topic", height=80, placeholder="Enter topic...")
    
    with col2:
        st.header("Format")
        note_type = st.selectbox("Note Format", ai_tools)
        detail_level = st.select_slider("Detail", options=["Brief", "Standard", "Comprehensive", "Expert"], value="Standard")
    
    with col3:
        st.header("Style")
        tone = st.selectbox("Tone", ["Formal", "Casual", "Academic"], index=0)
        language_style = st.selectbox("Style", ["Standard", "Creative", "Concise"], index=0)
        temperature = st.slider("Creativity", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
        education_level = "Undergraduate"  # Default in compact view
        style_params = {"tone": tone, "language_style": language_style}

# Create formatted prompt with parameters
if topic:
    if note_type == "Custom Template" and "custom_template" in locals():
        base_prompt = custom_template.format(prompt=topic, detail_level=detail_level, education_level=education_level)
    else:
        base_prompt = templates[note_type].format(prompt=topic)
    
    final_prompt = f"{base_prompt}\n\nAdditional parameters:\n- Detail level: {detail_level}\n- Education level: {education_level}"
    
    st.markdown("---")
    
    # Generate and display notes
    if st.button("Generate Notes"):
        if not st.session_state.api_key:
            st.error("Please enter your Gemini API key in the sidebar")
        else:
            output = generate_ai_content(final_prompt, st.session_state.api_key, model_name, temperature, detail_level, style_params)
            
            # Save to history
            save_to_history(note_type, topic, output)
            
            # Display results
            st.header(f"Notes on: {topic}")
            
            # Create tabs for viewing and exporting
            tab1, tab2 = st.tabs(["View Notes", "Export Options"])
            
            with tab1:
                st.markdown(output)
                
                # Add to favorites option
                if st.button("⭐ Add to Favorites"):
                    save_to_history(note_type, topic, output, favorite=True)
                    st.success("Added to favorites!")
            
            with tab2:
                export_format = st.selectbox("Export Format", ["Text (.txt)", "Markdown (.md)", "CSV (.csv)"])
                format_extension = export_format.split('(')[1].replace(')', '').replace('.', '')
                
                export_content = export_notes(output, format_extension)
                
                st.download_button(
                    label="Download Notes",
                    data=export_content,
                    file_name=f"notes_{topic.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.{format_extension}",
                    mime="text/plain"
                )
                
                # Email option
                with st.expander("Email Notes"):
                    email_address = st.text_input("Email Address")
                    if st.button("Email Notes") and email_address:
                        st.success(f"Notes would be emailed to {email_address} (Email functionality not implemented in this demo)")

# Display history
if st.session_state.history and view_mode != "Focused":
    st.markdown("---")
    st.header("Recent Notes")
    
    for i, item in enumerate(st.session_state.history[:5]):
        with st.expander(f"**{item['topic']}** ({item['tool']}) - {item['timestamp']} {'⭐' if item.get('favorite', False) else ''}"):
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
            
            # Add option to create new notes based on these
            if st.button("Create New Notes Based on These", key=f"clone_{i}"):
                st.session_state.clone_notes = item['output']
                st.session_state.clone_topic = item['topic']
                st.experimental_rerun()

# Apply theme setting
if selected_theme != "Light":
    # This would typically be handled by custom CSS, but this is a placeholder
    st.markdown(f"<style>/* Custom {selected_theme} theme would be applied here */</style>", unsafe_allow_html=True)
