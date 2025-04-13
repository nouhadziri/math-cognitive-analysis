import os
import json
import re
import ast
from collections import defaultdict, Counter
import pandas as pd
from anthropic import Anthropic
import time
from tqdm import tqdm
import random
import argparse
from datasets import load_dataset

# Parse command line arguments
parser = argparse.ArgumentParser(description='Analyze cognitive skills in mathematical solutions')
parser.add_argument('--api-key', required=True, help='Anthropic API key')
args = parser.parse_args()

# Configuration
API_KEY = args.api_key  # Get API key from command line
TOTAL_EXAMPLES = 3  # Analyze only one example
OUTPUT_DIR = "new_cognitive_analysis_results"
MODEL = "claude-3-7-sonnet-20250219"

# Initialize Anthropic client
client = Anthropic(api_key=API_KEY)

# Define the domains from the provided images
DOMAINS = [
    "Geometry", "Number theory", "Combinatorics", "Real functions", 
    "Biology", "Complex functions", "Quantum theory", "Field theory",
    "Calculus of variations", "Difference equations", "Electromagnetic theory",
    "Group theory", "Linear algebra", "Probability theory", "Algebraic systems",
    "Mechanics", "Thermodynamics", "Differential equations", "Computer science",
    "Numerical analysis", "Calculus", "Algebraic structures", "Astronomy", "Other"
]

# Domain keywords for classification
DOMAIN_KEYWORDS = {
    "Geometry": ["geometry", "triangle", "circle", "angle", "area", "volume", "polygon", "euclidean"],
    "Number theory": ["number theory", "prime", "divisibility", "sequence", "integer", "divisor", "gcd", "modular"],
    "Combinatorics": ["combinatorics", "permutation", "combination", "counting", "binomial", "factorial"],
    "Real functions": ["real function", "continuous", "differentiable", "trigonometry"],
    "Complex functions": ["complex function", "analytic", "holomorphic", "contour"],
    "Group theory": ["group theory", "isomorphism", "homomorphism", "abelian", "subgroup"],
    "Linear algebra": ["linear algebra", "matrix", "vector", "eigenvalue", "determinant", "span", "basis"],
    "Probability theory": ["probability", "random", "expected value", "variance", "distribution"],
    "Differential equations": ["differential equation", "ODE", "PDE", "boundary value"],
    "Calculus": ["calculus", "derivative", "integral", "limit", "series", "taylor"],
    "Algebraic systems": ["ring", "field", "group", "algebra", "abstract"],
    "Computer science": ["algorithm", "complexity", "programming", "graph theory", "data structure"]
}

def extract_metadata(example):
    """Extract and parse metadata from an example"""
    if 'metadata' not in example or not example['metadata']:
        return {}
    
    try:
        # Try to parse as a dictionary if it's a string
        if isinstance(example['metadata'], str):
            return ast.literal_eval(example['metadata'])
        return example['metadata']
    except (SyntaxError, ValueError):
        # If parsing fails, return empty dict
        return {}

def classify_to_domain(example, metadata, problem_text):
    """Classify the problem to one of the main domains"""
    # First check explicit domain in metadata
    if metadata and 'domain' in metadata and isinstance(metadata['domain'], list) and metadata['domain']:
        domain_path = metadata['domain'][0].lower()
        for domain in DOMAINS:
            if domain.lower() in domain_path:
                return domain
    
    # Next, try keyword matching
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in problem_text.lower() for keyword in keywords):
            return domain
    
    # Final attempt: check for mathematical symbols and expressions specific to domains
    if re.search(r'\bmatrix\b|det\(|determinant|eigenvalue', problem_text, re.IGNORECASE):
        return "Linear algebra"
    elif re.search(r'\btriangle\b|\bangle\b|\bcircle\b|\bsquare\b', problem_text, re.IGNORECASE):
        return "Geometry"
    elif re.search(r'\bprime\b|\bgcd\b|\blcm\b|\bmodulo\b', problem_text, re.IGNORECASE):
        return "Number theory"
    elif re.search(r'\bderivative\b|\bintegral\b|\blimit\b', problem_text, re.IGNORECASE):
        return "Calculus"
    
    return "Other"

def get_problem_text(example):
    """Extract problem text from various possible fields"""
    # Try different field names that might contain the problem
    field_names = ['question', 'problem']
    
    for field in field_names:
        if field in example and example[field]:
            return example[field]
    
    # If no specific field found, check if there's metadata with problem
    metadata = extract_metadata(example)
    if metadata and 'problem' in metadata:
        return metadata['problem']
    
    return ""

def analyze_thinking_trajectory(problem, thinking_trajectory, domain, trajectory_type):
    """Use Claude to analyze the cognitive skills in a thinking trajectory and generate a comprehensive analysis file"""
    system_prompt = """You are an expert in mathematical cognition and problem-solving. Your task is to analyze a thinking trajectory for a mathematical problem and identify the cognitive skills and strategies the solver is using.

For each cognitive skill you identify, you must:
1. Provide a clear definition of the skill
2. Cite specific spans of text from the trajectory that demonstrate this skill
3. For each span, provide:
   - The exact start position (character index) in the solution text
   - The exact end position (character index) in the solution text
   - The text content of the span
   - An explanation of why this span demonstrates the skill

Format your response in a structured way that can be easily parsed:

1. Start with your analysis of cognitive skills
2. End with a "SUMMARY_START" and list the most important skills
3. Then "SUMMARY_END"
"""

    user_prompt = f"""Mathematical Problem: 
{problem}

Domain: {domain}

Thinking Trajectory ({trajectory_type}):
{thinking_trajectory}

Please provide a comprehensive analysis following this structure:

1. Analyze the cognitive skills demonstrated, where for each skill:
   - Name the skill between tags <skill> and </skill>
   - Define the skill between tags <definition> and </definition>
   - For each span of text that demonstrates this skill:
     * Provide the exact start position between tags <start> and </start>
     * Provide the exact end position between tags <end> and </end>
     * Provide the text content between tags <text> and </text>
     * Explain why this span shows the skill between tags <explanation> and </explanation>
2. Finally, provide a summary between SUMMARY_START and SUMMARY_END tags listing the 3-5 most important cognitive skills demonstrated
"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,  # Increased to ensure we get the complete analysis
            temperature=0.6,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Error analyzing thinking trajectory: {e}")
        time.sleep(5)  # Wait in case of rate limiting
        return None

def extract_skills_from_analysis(analysis):
    """Extract the identified cognitive skills and their spans from Claude's analysis"""
    if not analysis:
        return {'skills': [], 'descriptions': {}, 'spans': {}}
    
    skills = []
    descriptions = {}
    spans = {}
    
    # Extract skills and their spans
    skill_pattern = r'<skill>(.*?)</skill>\s*<definition>(.*?)</definition>(.*?)(?=<skill>|SUMMARY_START)'
    skill_matches = re.findall(skill_pattern, analysis, re.DOTALL)
    
    for skill_match in skill_matches:
        skill_name = skill_match[0].strip()
        skill_def = skill_match[1].strip()
        skill_content = skill_match[2].strip()
        
        if skill_name:
            skills.append(skill_name)
            descriptions[skill_name] = skill_def
            
            # Extract spans for this skill
            span_pattern = r'<start>(.*?)</start>\s*<end>(.*?)</end>\s*<text>(.*?)</text>\s*<explanation>(.*?)</explanation>'
            span_matches = re.findall(span_pattern, skill_content, re.DOTALL)
            
            spans[skill_name] = []
            for start, end, text, explanation in span_matches:
                spans[skill_name].append({
                    'start': int(start.strip()),
                    'end': int(end.strip()),
                    'text': text.strip(),
                    'explanation': explanation.strip()
                })
    
    # Extract top skills from the summary section
    top_skills = []
    summary_match = re.search(r'SUMMARY_START(.*?)SUMMARY_END', analysis, re.DOTALL)
    
    if summary_match:
        summary_text = summary_match.group(1)
        list_items = re.findall(r'(?:\d+\.\s*|\-\s*|\*\s*)([^•\n]+)', summary_text)
        
        for item in list_items:
            skill_match = re.match(r'([A-Za-z\s]+(?:reasoning|thinking|analysis|manipulation|recognition|construction|verification|chaining|setting|satisfaction|solving|processing|representation))(?:\s*[:]\s*|\s*[-]\s*|\s*–\s*)?', item)
            if skill_match:
                top_skill = skill_match.group(1).strip()
                if top_skill and top_skill not in top_skills:
                    top_skills.append(top_skill)
    
    return {
        'skills': list(set(skills)),  # Remove duplicates
        'top_skills': top_skills,
        'descriptions': descriptions,
        'spans': spans
    }

def save_enhanced_analysis(problem_id, analysis_text, output_dir, trajectory_type, problem_text, thinking_trajectory, domain):
    """Save the enhanced analysis with problem and solution to a file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Extract summary from analysis text
    summary_match = re.search(r'SUMMARY_START(.*?)SUMMARY_END', analysis_text, re.DOTALL)
    
    # Remove any existing problem and solution sections from the analysis text
    analysis_text = re.sub(r'PROBLEM_START.*?PROBLEM_END', '', analysis_text, flags=re.DOTALL)
    analysis_text = re.sub(r'SOLUTION_START.*?SOLUTION_END', '', analysis_text, flags=re.DOTALL)
    
    # Create the enhanced analysis content with problem and solution added by us
    enhanced_content = f"""Problem:
{problem_text}

Domain: {domain}

Solution Trajectory ({trajectory_type}):
{thinking_trajectory}

Analysis:
{analysis_text}

Summary of Key Skills:
{summary_match.group(1).strip() if summary_match else 'Not found'}
"""
    
    # Save to file
    output_file = os.path.join(output_dir, f'example_{problem_id}_{trajectory_type}_analysis.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    return output_file

def analyze_cognitive_skills():
    """Analyze cognitive skills in the dataset"""
    print("Loading dataset...")
    dataset = load_dataset("simplescaling/s1K-1.1")
    print(f"Dataset loaded successfully with {len(dataset['train'])} examples")
    
    # Print available columns
    print("\nAvailable columns in dataset:")
    print(dataset['train'].column_names)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "analyses"), exist_ok=True)
    
    # Define trajectory columns with correct names from dataset
    trajectory_columns = {
        'groundtruth': 'solution',
        'gemini': 'gemini_thinking_trajectory',
        'deepseek': 'deepseek_thinking_trajectory'
    }
    
    # Process examples
    print(f"\nAnalyzing {TOTAL_EXAMPLES} examples...")
    for i in range(TOTAL_EXAMPLES):
        print(f"\nProcessing example {i+1}/{TOTAL_EXAMPLES}")
        example = dataset['train'][i]
        
        # Print example structure for debugging
        print("\nExample structure:")
        for key in example.keys():
            print(f"- {key}: {type(example[key])}")
        
        # Get problem text
        problem_text = get_problem_text(example)
        if not problem_text:
            print(f"Skipping example {i} - no problem text found")
            continue
            
        print(f"\nProblem text found ({len(problem_text)} chars)")
        
        # Get metadata and classify domain
        metadata = extract_metadata(example)
        domain = classify_to_domain(example, metadata, problem_text)
        print(f"Domain: {domain}")
        
        # Analyze each trajectory type
        for trajectory_type, column in trajectory_columns.items():
            print(f"\nAnalyzing {trajectory_type} trajectory...")
            print(f"Looking for column: {column}")
            
            if column not in example:
                print(f"Column {column} not found in example. Available columns are: {list(example.keys())}")
                continue
                
            trajectory = example[column]
            if not trajectory:
                print(f"No {trajectory_type} trajectory found (empty)")
                continue
                
            print(f"Found {trajectory_type} trajectory ({len(str(trajectory))} chars)")
            
            # Get analysis from Claude
            analysis = analyze_thinking_trajectory(problem_text, trajectory, domain, trajectory_type)
            if not analysis:
                print(f"Failed to get analysis for {trajectory_type}")
                continue
                
            # Save analysis with problem and solution added by us
            output_file = save_enhanced_analysis(i, analysis, os.path.join(OUTPUT_DIR, "analyses"), trajectory_type, problem_text, trajectory, domain)
            print(f"Saved analysis to {output_file}")
            
            # Add a small delay between API calls
            time.sleep(1)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    analyze_cognitive_skills() 