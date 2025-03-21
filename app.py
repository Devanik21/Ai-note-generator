import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import pandas as pd
import json
import os
import re
import random

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
if 'user_knowledge_level' not in st.session_state:
    st.session_state.user_knowledge_level = {}
if 'spaced_repetition' not in st.session_state:
    st.session_state.spaced_repetition = []
if 'quiz_scores' not in st.session_state:
    st.session_state.quiz_scores = []

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

# New function for generating quiz from notes
def generate_quiz(content, api_key, model_name):
    templates = load_prompt_templates()
    prompt = templates["Quiz Generation"].format(content=content)
    
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
            
            # Display results
            st.header(f"Notes on: {topic}")
            
            # Create tabs for viewing, enhancement, learning, and exporting
            tab1, tab2, tab3, tab4 = st.tabs(["View Notes", "Enhance Notes", "Learn", "Export Options"])
            
            with tab1:
                st.markdown(output)
                
                # Add to favorites option
                if st.button("⭐ Add to Favorites"):
                    save_to_history(note_type, topic, output, favorite=True)
                    st.success("Added to favorites!")
            
            with tab2:
                # NEW: AI-Powered Summarization & Refinement
                st.subheader("🧠 AI Enhancement Tools")
                
                # Auto-summarization
                if st.button("📝 Generate Summary"):
                    summary = summarize_notes(output, st.session_state.api_key, model_name)
                    st.markdown("### Summary")
                    st.markdown(summary)
                    
                # Adaptive refinement
                refinement_type = st.selectbox(
                    "Refinement Type",
                    ["clearer", "more concise", "more detailed", "simpler", "more technical", "more examples"]
                )
                
                if st.button("🔄 Refine Notes"):
                    refined = refine_notes(output, topic, refinement_type, st.session_state.api_key, model_name)
                    st.markdown("### Refined Notes")
                    st.markdown(refined)
                    
                    # Option to replace original notes with refined version
                    if st.button("Save Refined Version"):
                        save_to_history(note_type, topic, refined)
                        st.success("Refined notes saved to history!")
            
            with tab3:
                # NEW: Smart Personalized Learning
                st.subheader("📚 Learning Tools")
                
                # Spaced repetition
                if st.button("🔄 Create Flashcards for Spaced Repetition"):
                    card_count = create_spaced_repetition(output, topic, st.session_state.api_key, model_name)
                    st.success(f"Created {card_count} flashcards for spaced repetition!")
                    
                    # Show flashcards preview
                    if card_count > 0:
                        st.markdown("### Flashcard Preview")
                        for i, card in enumerate(st.session_state.spaced_repetition[-card_count:]):
                            with st.expander(f"Card {i+1}"):
                                st.markdown(f"**Q:** {card['question']}")
                                with st.expander("Show Answer"):
                                    st.markdown(f"**A:** {card['answer']}")
                
                # Quiz creation
                if st.button("🎮 Generate Quiz"):
                    quiz = generate_quiz(output, st.session_state.api_key, model_name)
                    st.session_state.current_quiz = quiz
                    st.markdown("### Quiz")
                    
                    # Process quiz text to display as form
                    questions = quiz.split("\n\n")
                    user_answers = []
                    
                    for i, q in enumerate(questions):
                        if q and "A)" in q:
                            st.markdown(q.split("Correct answer:")[0])  # Show question without answer
                            answer = st.radio(f"Question {i+1}", ["A", "B", "C", "D"], key=f"q_{i}")
                            user_answers.append(answer)
                    
                    if user_answers and st.button("Submit Quiz"):
                        score = grade_quiz(quiz, user_answers)
                        st.success(f"Your score: {score:.1f}%")
                        
                        # Update knowledge level based on quiz performance
                        if topic in st.session_state.user_knowledge_level:
                            current_level = st.session_state.user_knowledge_level[topic]
                            # Adjust level based on score
                            if score > 90:
                                st.session_state.user_knowledge_level[topic] = min(5, current_level + 0.5)
                            elif score < 60:
                                st.session_state.user_knowledge_level[topic] = max(1, current_level - 0.5)
                            
                            st.info(f"Knowledge level updated to: {st.session_state.user_knowledge_level[topic]}/5")
            
            with tab4:
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
        
        # Show one card at a time
        if 'current_card_index' not in st.session_state:
            st.session_state.current_card_index = 0
        
        if st.session_state.current_card_index < len(due_cards):
            card = due_cards[st.session_state.current_card_index]
            
            st.markdown(f"**Topic:** {card['topic']}")
            st.markdown(f"**Question:** {card['question']}")
            
            with st.expander("Show Answer"):
                st.markdown(card['answer'])
                
                # Rate difficulty
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

# Apply theme setting
if selected_theme != "Light":
    st.markdown(f"<style>/* Custom {selected_theme} theme would be applied here */</style>", unsafe_allow_html=True)

# Final Message
st.markdown("---")
st.markdown("### Thank You for Using AI Note Maker 🚀")
