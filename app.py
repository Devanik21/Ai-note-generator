import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import re
import markdown # For HTML export
import random

# App title and configuration
st.set_page_config(page_title="AI Note Maker", page_icon="📝", layout="wide")

# Constants for selectbox options
DETAIL_LEVEL_OPTIONS = ["Brief", "Standard", "Comprehensive", "Expert"]
TONE_OPTIONS = ["Formal", "Casual", "Academic", "Enthusiastic", "Technical", "Simplified"]
LANGUAGE_STYLE_OPTIONS = ["Standard", "Creative", "Concise", "Elaborate", "Scientific", "Conversational"]

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'custom_templates' not in st.session_state:
    st.session_state.custom_templates = {}
if 'user_knowledge_level' not in st.session_state:
    st.session_state.user_knowledge_level = {}
if 'spaced_repetition' not in st.session_state:
    st.session_state.spaced_repetition = []
if 'quiz_scores' not in st.session_state:
    st.session_state.quiz_scores = []
if 'default_detail_level' not in st.session_state:
    st.session_state.default_detail_level = "Standard"
if 'default_tone' not in st.session_state:
    st.session_state.default_tone = "Formal"
if 'default_language_style' not in st.session_state:
    st.session_state.default_language_style = "Standard"
if 'topic_suggestions' not in st.session_state:
    st.session_state.topic_suggestions = []

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
                             ["gemini-2.0-flash", "gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-preview-03-25", "gemini-2.0-flash-lite", "gemini-2.0-pro-exp-02-05",
                              "gemini-2.0-flash-thinking-exp-01-21", "gemini-1.5-pro",
                              "gemini-1.5-flash", "gemini-1.5-flash-8b"],
                             index=0)
    
    st.header("⚙️ User Preferences")
    pref_detail_level = st.selectbox(
        "Default Detail Level",
        options=DETAIL_LEVEL_OPTIONS,
        index=DETAIL_LEVEL_OPTIONS.index(st.session_state.default_detail_level)
    )
    if pref_detail_level != st.session_state.default_detail_level:
        st.session_state.default_detail_level = pref_detail_level
        st.rerun()

    pref_tone = st.selectbox(
        "Default Tone",
        options=TONE_OPTIONS,
        index=TONE_OPTIONS.index(st.session_state.default_tone)
    )
    if pref_tone != st.session_state.default_tone:
        st.session_state.default_tone = pref_tone
        st.rerun()

    pref_language_style = st.selectbox(
        "Default Language Style",
        options=LANGUAGE_STYLE_OPTIONS,
        index=LANGUAGE_STYLE_OPTIONS.index(st.session_state.default_language_style)
    )
    if pref_language_style != st.session_state.default_language_style:
        st.session_state.default_language_style = pref_language_style
        st.rerun()

    # Theme settings
    st.header("🎨 Theme")
    theme_options = ["Light", "Dark", "Blue", "Green"]
    selected_theme = st.selectbox("Select Theme", theme_options, index=0)
    
    # History and Favorites tabs
    tab1, tab2, tab3 = st.tabs(["History", "Favorites", "Learning"])
    
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
    
    with tab3:
        # Display learning data
        st.caption("Knowledge Levels:")
        if st.session_state.user_knowledge_level:
            for topic, level in st.session_state.user_knowledge_level.items():
                st.caption(f"{topic}: {level}/5")
        
        st.caption("Upcoming Flashcards:")
        due_cards = [card for card in st.session_state.spaced_repetition 
                    if card['next_review'] <= datetime.now()]
        st.caption(f"{len(due_cards)} cards due for review")
        
        st.caption("Quiz Performance:")
        if st.session_state.quiz_scores:
            avg_score = sum(score['score'] for score in st.session_state.quiz_scores) / len(st.session_state.quiz_scores)
            st.caption(f"Average Score: {avg_score:.1f}%")

        st.markdown("---")
        st.subheader("🚀 Topic Exploration")
        exploration_interest = st.text_input("Interest to explore related topics:", key="exploration_interest_input")
        if st.button("Suggest Related Topics"):
            if not st.session_state.api_key:
                st.error("API key is required for topic suggestion.")
            elif not exploration_interest:
                st.warning("Please enter an interest to get suggestions.")
            else:
                with st.spinner("AI is brainstorming..."):
                    # This is a placeholder. In a real scenario, you'd call the AI.
                    # prompt = f"Suggest 3-5 related academic topics for further study based on the interest: '{exploration_interest}'. Provide a brief (1-sentence) explanation for each suggestion."
                    # suggestions_text = generate_ai_content(prompt, st.session_state.api_key, model_name, 0.7, "Brief", {"tone": "Creative", "language_style": "Concise"})
                    # st.session_state.topic_suggestions = suggestions_text.split('\n') # Process appropriately
                    st.session_state.topic_suggestions = [
                        f"Exploring sub-field A of {exploration_interest}",
                        f"The history of {exploration_interest}",
                        f"Future trends in {exploration_interest}"
                    ]
                st.success("Suggestions generated!")

        if st.session_state.get('topic_suggestions'):
            st.markdown("**Suggested Topics:**")
            for suggestion in st.session_state.topic_suggestions:
                st.caption(f"- {suggestion}")

        st.markdown("---")
        st.subheader("📈 Advanced Analytics")
        notes_this_week = 0
        one_week_ago = datetime.now() - timedelta(days=7)
        for item in st.session_state.history:
            try:
                item_timestamp = datetime.strptime(item['timestamp'], "%Y-%m-%d %H:%M:%S")
                if item_timestamp > one_week_ago:
                    notes_this_week += 1
            except ValueError:
                pass # Ignore items with unexpected timestamp format
        st.metric("Notes Generated (Last 7 Days)", notes_this_week)

        if st.session_state.history:
            from collections import Counter
            tool_counts = Counter(item['tool'] for item in st.session_state.history)
            most_common_tool, most_common_count = tool_counts.most_common(1)[0] if tool_counts else ("N/A", 0)
            st.metric("Most Used Note Format", f"{most_common_tool} ({most_common_count} times)")
        
        focus_areas = [topic for topic, level in st.session_state.user_knowledge_level.items() if level < 3]
        st.caption(f"Learning Focus Areas (Knowledge < 3/5): {len(focus_areas)}")
        for area in focus_areas[:3]: # Display top 3
            st.caption(f"- {area} (Level: {st.session_state.user_knowledge_level[area]}/5)")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("AI Note Maker helps you create detailed notes on any topic using Google's Gemini AI.")
    st.markdown("v3.0 - Smart Learning Features")

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
        "Deep research",
        "Case Study Analysis",
        "Custom Template"
    ]
    
    categories = {
        "Note Formats": ["Bullet Points", "Cornell Notes","Mind Map Structure", "Summary Notes", "Detailed Explanation"],
        "Study Aids": ["Flashcards", "Question & Answer Format", "Key Concepts & Definitions", "Exam Preparation"],
        "Specialized": ["Timeline Format", "Comparative Analysis", "Deep research", "Case Study Analysis"],
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
        
        "Comprehensive Quiz": "Generate a comprehensive quiz on: {prompt}. Include a mix of multiple choice questions (MCQs), short answer, and true/false questions with a total of 30 questions. Ensure a range of difficulty levels. For MCQs, provide four options with one correct answer clearly marked. Group questions by subtopics if applicable. Include an answer key at the end.",
    
        
        "Mind Map Structure": "Create a text-based mind map structure on: {prompt}. Format with the core concept in the center, main branches using level 1 headings, sub-branches using level 2 headings, and leaf nodes using bullet points. Use indentation to show relationships between concepts. Include all important relationships and hierarchies.",
        
        "Flashcards": "Create a set of flashcards on: {prompt}. Format with 'Q:' for questions and 'A:' for answers, separating each flashcard with a divider line. Include comprehensive coverage of key facts, definitions, concepts, and their applications. Number each flashcard.",
        
        "Summary Notes": "Create concise summary notes on: {prompt}. Include only the most essential information, key concepts, and critical takeaways. Format with clear headings and short paragraphs. Ensure comprehensive coverage while maintaining brevity (maximum 1/3 the length of detailed notes).",
        
        "Detailed Explanation": "Create detailed explanatory notes on: {prompt}. Include thorough explanations of concepts, supporting evidence, examples, and applications. Structure with clear headings, subheadings, and logical flow. Use appropriate technical language while ensuring clarity.",
        
        "Question & Answer Format": "Create comprehensive Q&A format notes on: {prompt}. Format with clear questions followed by detailed answers. Cover all important aspects of the topic with questions ranging from basic understanding to advanced application. Group related questions together under appropriate headings.",
        
        "Key Concepts & Definitions": "Create a glossary of key concepts and definitions for: {prompt}. Format each entry with the term in bold followed by a comprehensive definition. Include examples where helpful. Organize alphabetically or by related concept groups with clear headings.",
        
        "Timeline Format": "Create chronological timeline notes on: {prompt}. Format with clear date/period indicators followed by detailed descriptions of events, developments, or phases. Include significant milestones, causes, and effects. Use appropriate headings for major eras or transitions.",
        
        "Comparative Analysis": "Create comparative analysis notes on: {prompt}. Structure with clear categories for comparison in the left column and entities being compared across the top. Include detailed points of comparison with similarities and differences clearly marked. Conclude with synthesis of key insights from the comparison.",
        
        "Exam Preparation": "Create comprehensive exam preparation notes on: {prompt}. Include key definitions, formulas, concepts, potential exam questions, and model answers. Format with clear sections for different question types and difficulty levels. Highlight common pitfalls and strategies for tackling complex problems.",
        
        "Deep research": """
You are a high-level research assistant writing in-depth academic responses. 
Structure the output as a formal article (~8000 tokens) with:
1. Executive Summary  
2. Introduction  
3. History & Evolution  
4. Concepts & Frameworks  
5. Current State  
6. Challenges  
7. Applications  
8. Comparisons  
9. Future Outlook  
10. Conclusion  
11. References (Optional)

Query:
\"\"\"{user_prompt}\"\"\"
""",

        "Case Study Analysis": """
You are a high-level research assistant writing comprehensive academic case study analyses. 
Structure the response as a formal case study (~8000 tokens) with:
1. Executive Summary  
2. Introduction & Background  
3. History & Context  
4. Key Issues  
5. Stakeholder Analysis  
6. Root Cause Analysis  
7. Strategic Alternatives  
8. Recommendation  
9. Implementation Plan  
10. Challenges & Risk Mitigation  
11. Conclusion  
12. References (Optional)

Query:
\"\"\"{user_prompt}\"\"\"
"""

       }
    
    # New templates for enhanced features
    templates.update({
        "Auto-Summary": "Provide a concise 3-paragraph summary of the following notes, highlighting only the most critical concepts and takeaways: {content}",
        
        "Refinement": "Refine the following notes on '{topic}' to make them {refinement_type}. Maintain the original structure but improve the content based on the refinement request: {content}",
        
        "Adaptive Content": "Create {detail_level} notes on {prompt} specifically tailored for someone with a knowledge level of {knowledge_level}/5 in this subject. Adjust complexity, depth, and examples accordingly.",
        
        "Spaced Repetition Cards": "Based on the following notes, create 5-10 spaced repetition flashcards covering the most important concepts that would be suitable for long-term memorization: {content}",
        
        "Quiz Generation": "Create a 5-question quiz with multiple-choice answers based on the following notes. Include 4 options per question with only one correct answer. Format with the question followed by options labeled A, B, C, D, and mark the correct answer at the end: {content}"
    })
    
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
                "Expert": 8192
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
        # The content from Gemini is often already markdown-like.
        return content
    elif format == "csv":
        lines = content.split('\n')
        csv_output_lines = []
        for line in lines:
            # Remove common markdown list/block prefixes
            cleaned_line = re.sub(r'^\s*[-*#>]+\s*', '', line).strip()
            if cleaned_line: # Only process non-empty lines
                # Escape double quotes
                cleaned_line_csv = cleaned_line.replace('"', '""')
                # Enclose in double quotes if it contains a comma, a double quote, or needs it
                if ',' in cleaned_line_csv or '"' in cleaned_line_csv or ' ' in cleaned_line_csv or '\n' in cleaned_line_csv:
                    csv_output_lines.append(f'"{cleaned_line_csv}"')
                else:
                    csv_output_lines.append(cleaned_line_csv)
        return '\n'.join(csv_output_lines)
    elif format == "html":
        # Convert markdown content to HTML
        html_body = markdown.markdown(content, extensions=['fenced_code', 'tables', 'extra'])
        html_full = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; color: #333; }}
        h1, h2, h3, h4, h5, h6 {{ color: #1a1a1a; margin-top: 1.5em; margin-bottom: 0.5em; }}
        p {{ margin-bottom: 1em; }}
        ul, ol {{ padding-left: 20px; margin-bottom: 1em; }}
        li {{ margin-bottom: 0.25em; }}
        code {{ background-color: #f0f0f0; padding: 0.2em 0.4em; margin: 0; font-size: 85%; border-radius: 3px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;}}
        pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        pre code {{ background-color: transparent; padding: 0; margin: 0; font-size: inherit; border-radius: 0; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; border: 1px solid #ddd; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f9f9f9; }}
        blockquote {{ border-left: 4px solid #ccc; padding-left: 10px; color: #555; margin-left: 0; margin-right: 0; font-style: italic;}}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""
        return html_full
    else:
        return content

# New function for AI-powered summarization
def summarize_notes(content, api_key, model_name):
    templates = load_prompt_templates()
    prompt = templates["Auto-Summary"].format(content=content)
    
    summary = generate_ai_content(
        prompt, 
        api_key, 
        model_name, 
        temperature=0.3, 
        detail_level="Brief",
        style_params={"tone": "Concise", "language_style": "Standard"}
    )
    
    return summary

# New function for adaptive refinement
def refine_notes(content, topic, refinement_type, api_key, model_name):
    templates = load_prompt_templates()
    prompt = templates["Refinement"].format(
        content=content,
        topic=topic,
        refinement_type=refinement_type
    )
    
    refined = generate_ai_content(
        prompt, 
        api_key, 
        model_name, 
        temperature=0.5, 
        detail_level="Standard",
        style_params={"tone": "Academic", "language_style": "Standard"}
    )
    
    return refined


# Function for deep search
def deep_search_notes(query, content, api_key, model_name):
    prompt = f"Given the following notes content, perform a deep semantic search for '{query}'. Return the most relevant sections that answer or relate to this query, along with brief explanations of why they're relevant:\n\n{content}"
    
    results = generate_ai_content(
        prompt, 
        api_key, 
        model_name, 
        temperature=0.3, 
        detail_level="Standard",
        style_params={"tone": "Analytical", "language_style": "Concise"}
    )
    
    return results


# New function for generating quiz from notes
def generate_quiz(content, api_key, model_name):
    templates = load_prompt_templates()
    prompt = f"Create a 20 -question quiz with multiple-choice answers based on the following notes. " \
             f"Include 4 options per question with only one correct answer. " \
             f"Format with the question followed by options labeled A, B, C, D, and mark the correct answer at the end:\n\n{content}"
    
    quiz = generate_ai_content(
        prompt, 
        api_key, 
        model_name, 
        temperature=0.7, 
        detail_level="Standard",
        style_params={"tone": "Enthusiastic", "language_style": "Conversational"}
    )
    
    return quiz

# New function to create spaced repetition cards
def create_spaced_repetition(content, topic, api_key, model_name):
    templates = load_prompt_templates()
    prompt = templates["Spaced Repetition Cards"].format(content=content)
    
    cards_text = generate_ai_content(
        prompt, 
        api_key, 
        model_name, 
        temperature=0.5, 
        detail_level="Standard",
        style_params={"tone": "Academic", "language_style": "Concise"}
    )
    
    # Process raw text into cards
    cards = []
    raw_cards = cards_text.split("---")
    
    for card_text in raw_cards:
        if "Q:" in card_text and "A:" in card_text:
            question = re.search(r"Q:(.*?)A:", card_text, re.DOTALL).group(1).strip()
            answer = re.search(r"A:(.*)", card_text, re.DOTALL).group(1).strip()
            
            # Create card with spaced repetition metadata
            card = {
                "topic": topic,
                "question": question,
                "answer": answer,
                "created": datetime.now(),
                "next_review": datetime.now() + timedelta(days=1),
                "ease_factor": 2.5,
                "interval": 1,
                "repetitions": 0
            }
            
            cards.append(card)
    
    # Add to session state
    for card in cards:
        st.session_state.spaced_repetition.append(card)
    
    return len(cards)

# New function to process quiz answers and calculate score
def grade_quiz(quiz_text, user_answers):
    # Extract correct answers from quiz text
    correct_answers = []
    questions = quiz_text.split("\n\n")
    
    for q in questions:
        if "Correct answer:" in q:
            correct = re.search(r"Correct answer: ([A-D])", q).group(1)
            correct_answers.append(correct)
    
    # Calculate score
    if len(correct_answers) != len(user_answers):
        return 0
    
    score = sum(1 for correct, user in zip(correct_answers, user_answers) if correct == user)
    percentage = (score / len(correct_answers)) * 100
    
    # Record score in history
    st.session_state.quiz_scores.append({
        "timestamp": datetime.now(),
        "score": percentage,
        "total_questions": len(correct_answers)
    })
    
    return percentage
# Main content area
templates = load_prompt_templates()

# Use standard layout
col1, col2 = st.columns([2, 1])

# Topic and parameters input
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
        options=DETAIL_LEVEL_OPTIONS,
        value=st.session_state.default_detail_level  # Use preference
    )
    
    # Advanced parameters
    with st.expander("Advanced Parameters"):
        temperature = st.slider("Creativity Level", min_value=0.1, max_value=1.0, value=0.7, step=0.1)
        
        education_level = st.selectbox(
            "Education Level",
            ["Elementary", "Middle School", "High School", "Undergraduate", "Graduate", "Professional"],
            index=3
        )
        
        # Style parameters using preferences as default
        tone = st.selectbox("Tone", TONE_OPTIONS, index=TONE_OPTIONS.index(st.session_state.default_tone))
        
        language_style = st.selectbox("Language Style", LANGUAGE_STYLE_OPTIONS, index=LANGUAGE_STYLE_OPTIONS.index(st.session_state.default_language_style))
        
        # NEW: Knowledge level for adaptive learning
        if topic:
            # Set default knowledge level or retrieve existing
            if topic in st.session_state.user_knowledge_level:
                default_knowledge = st.session_state.user_knowledge_level[topic]
            else:
                default_knowledge = 3
                
            knowledge_level = st.slider(
                "Your Knowledge Level on This Topic", 
                min_value=1, 
                max_value=5, 
                value=default_knowledge,
                help="1=Beginner, 5=Expert"
            )
            
            # Save knowledge level
            st.session_state.user_knowledge_level[topic] = knowledge_level
        
        # Collect style parameters
        style_params = {
            "tone": tone,
            "language_style": language_style
        }

# Create formatted prompt with parameters
if topic:
    if note_type == "Custom Template" and "custom_template" in locals():
        base_prompt = custom_template.format(prompt=topic, detail_level=detail_level, education_level=education_level)
    else:
        # NEW: Use adaptive content template if knowledge level is set
        if topic in st.session_state.user_knowledge_level:
            knowledge_level = st.session_state.user_knowledge_level[topic]
            base_prompt = templates["Adaptive Content"].format(
                prompt=topic, 
                detail_level=detail_level, 
                knowledge_level=knowledge_level
            )
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
            
            # Store generated notes in session state for later use
            st.session_state.output = output
            
            # Display results
            st.header(f"Notes on: {topic}")
            
            
            tab1,  tab4 = st.tabs(["View Notes" ,"Export Options"])
         
            with tab1:
                st.markdown(output)
                
                # Add to favorites option
                if st.button("⭐ Add to Favorites"):
                    save_to_history(note_type, topic, output, favorite=True)
                    st.success("Added to favorites!")
            









            

            
            

            with tab4: # Export Options Tab
                # Inject Flashcard CSS if not already done (though it's for a different section,
                # good to have CSS injections managed)
                if 'flashcard_css_injected' not in st.session_state:
                    # Define FLASHCARD_CSS as shown in the explanation above
                    FLASHCARD_CSS = """
                    <style>
                    .flashcard-container {
                        margin-bottom: 20px;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.35);
                    }
                    .flashcard-question {
                        background: linear-gradient(135deg, #1D2B64, #4A00E0);
                        color: #f0f0f0;
                        padding: 20px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        font-size: 1.1em;
                    }
                    .flashcard-question p { margin: 0; line-height: 1.5; }
                    .flashcard-question strong { color: #ffffff; font-weight: 600; }
                    .flashcard-answer-content {
                        background-color: #283040;
                        color: #e0e0e0;
                        padding: 15px 20px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        border-top: 1px solid #4A00E0;
                    }
                    </style>
                    """
                    st.markdown(FLASHCARD_CSS, unsafe_allow_html=True)
                    st.session_state.flashcard_css_injected = True

                st.subheader("💾 Download Notes")
                export_options = ["Text (.txt)", "Markdown (.md)", "CSV (.csv)", "HTML (.html)"]
                export_format_selected = st.selectbox("Select Export Format", export_options)
                
                # Determine format_extension and mime_type based on selection
                if export_format_selected == "Text (.txt)":
                    format_extension = "txt"
                    mime_type = "text/plain"
                elif export_format_selected == "Markdown (.md)":
                    format_extension = "md"
                    mime_type = "text/markdown"
                elif export_format_selected == "CSV (.csv)":
                    format_extension = "csv"
                    mime_type = "text/csv"
                elif export_format_selected == "HTML (.html)":
                    format_extension = "html"
                    mime_type = "text/html"
                else: # Default fallback
                    format_extension = "txt"
                    mime_type = "text/plain"
                
                export_content = export_notes(output, format_extension)
                
                st.download_button(
                    label=f"Download as .{format_extension}",
                    data=export_content,
                    file_name=f"notes_{topic.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.{format_extension}",
                    mime=mime_type
                )
                
                st.markdown("---")

                # Feature 1: Copy to Clipboard
                st.subheader("📋 Copy to Clipboard")
                st.caption("Use the copy icon in the top right of the code box below to copy the raw notes.")
                st.code(output, language="markdown")

                st.markdown("---")

                # Feature 2: Note Statistics
                st.subheader("📊 Note Statistics")
                word_count = len(output.split())
                char_count = len(output)
                col_stat1, col_stat2 = st.columns(2)
                with col_stat1:
                    st.metric(label="Word Count", value=word_count)
                with col_stat2:
                    st.metric(label="Character Count", value=char_count)

# Display history
if st.session_state.history:
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
                st.rerun()
            
            # NEW: Quick enhancement options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Quick Summary", key=f"summary_{i}"):
                    summary = summarize_notes(item['output'], st.session_state.api_key, model_name)
                    st.markdown("### Summary")
                    st.markdown(summary)
            with col2:
                if st.button("🎮 Quick Quiz", key=f"quiz_{i}"):
                    quiz = generate_quiz(item['output'], st.session_state.api_key, model_name)
                    st.markdown("### Quiz")
                    st.markdown(quiz)

# NEW: Display due flashcards for spaced repetition
if st.session_state.spaced_repetition:
    due_cards = [card for card in st.session_state.spaced_repetition 
                if card['next_review'] <= datetime.now()]
    
    if due_cards:
        st.markdown("---")
        st.header(f"📆 Flashcards Due for Review ({len(due_cards)})")
        
        # Ensure CSS is injected for flashcards
        if 'flashcard_css_injected' not in st.session_state:
            # FLASHCARD_CSS should be defined as shown in the prompt's explanation
            # For brevity, assuming FLASHCARD_CSS is defined globally or accessible here
            st.markdown(FLASHCARD_CSS, unsafe_allow_html=True)
            st.session_state.flashcard_css_injected = True

        # Show one card at a time
        if 'current_card_index' not in st.session_state:
            st.session_state.current_card_index = 0
        
        if st.session_state.current_card_index < len(due_cards):
            card = due_cards[st.session_state.current_card_index]

            # Styled Flashcard
            question_html = f"""
            <div class="flashcard-question">
                <p><small>Topic: {card['topic']}</small></p>
                <p><strong>❓ Question:</strong> {card['question']}</p>
            </div>
            """
            
            st.markdown(f"<div class='flashcard-container'>{question_html}", unsafe_allow_html=True)
            
            with st.expander("💡 Show Answer"):
                st.markdown(f"<div class='flashcard-answer-content'>{card['answer']}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True) # Close flashcard-container
                
            # Rate difficulty buttons
            col1, col2, col3, col4 = st.columns(4)
                
            with col1:
                if st.button("😕 Hard"):
                    # Update card using SuperMemo SM-2 algorithm
                    if card['repetitions'] == 0:
                        card['interval'] = 1
                    else:
                        card['ease_factor'] = max(1.3, card['ease_factor'] - 0.2)
                        card['interval'] = max(1, card['interval'] * card['ease_factor'])
                    
                    card['repetitions'] = 0
                    card['next_review'] = datetime.now() + timedelta(days=card['interval'])
                    st.session_state.current_card_index += 1
                    st.rerun()
            
            with col2:
                if st.button("🙂 Okay"):
                    # Update card using SuperMemo SM-2 algorithm
                    if card['repetitions'] == 0:
                        card['interval'] = 1
                    else:
                        card['interval'] = card['interval'] * card['ease_factor']
                    
                    card['repetitions'] += 1
                    card['next_review'] = datetime.now() + timedelta(days=card['interval'])
                    st.session_state.current_card_index += 1
                    st.rerun()
            
            with col3:
                if st.button("😀 Easy"):
                    # Update card using SuperMemo SM-2 algorithm
                    if card['repetitions'] == 0:
                        card['interval'] = 2
                    else:
                        card['ease_factor'] = min(2.5, card['ease_factor'] + 0.1)
                        card['interval'] = card['interval'] * card['ease_factor']
                    
                    card['repetitions'] += 1
                    card['next_review'] = datetime.now() + timedelta(days=card['interval'])
                    st.session_state.current_card_index += 1
                    st.rerun()
            
            with col4:
                if st.button("Skip"):
                    st.session_state.current_card_index += 1
                    st.rerun()
        else:
            st.success("No more cards due for review today!")
            st.session_state.current_card_index = 0

# Flashcard Statistics
if st.session_state.spaced_repetition:
    st.markdown("---")
    st.header("📈 Flashcard Statistics") # Changed emoji for variety
    
    total_cards = len(st.session_state.spaced_repetition)
    due_today = len([card for card in st.session_state.spaced_repetition 
                     if card['next_review'] <= datetime.now()])
    st.write(f"Total flashcards: {total_cards}")
    st.write(f"Cards due today: {due_today}")
    
    # Cards by topic
    topics = set(card['topic'] for card in st.session_state.spaced_repetition)
    for topic in topics:
        topic_cards = [card for card in st.session_state.spaced_repetition if card['topic'] == topic]
        st.write(f"{topic}: {len(topic_cards)} cards")
        
    # Average ease factor
    if total_cards > 0:
        avg_ease = sum(card['ease_factor'] for card in st.session_state.spaced_repetition) / total_cards
        st.write(f"Average ease factor: {avg_ease:.2f}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and Gemini AI")
