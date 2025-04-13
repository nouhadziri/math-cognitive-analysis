import os
import json
import re

def parse_analysis_file(file_path):
    """Parse an analysis file and extract problem, domain, solution, and skills"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract problem
    problem_match = re.search(r'Problem:\n(.*?)\n\nDomain:', content, re.DOTALL)
    problem = problem_match.group(1).strip() if problem_match else ""
    
    # Extract domain
    domain_match = re.search(r'Domain: (.*?)\n', content)
    domain = domain_match.group(1).strip() if domain_match else ""
    
    # Extract solution trajectory
    solution_match = re.search(r'Solution Trajectory \(.*?\):\n(.*?)\n\nAnalysis:', content, re.DOTALL)
    solution = solution_match.group(1).strip() if solution_match else ""
    
    # Extract skills
    skills = []
    skill_pattern = r'<skill>(.*?)</skill>\s*<definition>(.*?)</definition>(.*?)(?=<skill>|SUMMARY_START)'
    skill_matches = re.findall(skill_pattern, content, re.DOTALL)
    
    for skill_match in skill_matches:
        skill_name = skill_match[0].strip()
        skill_def = skill_match[1].strip()
        skill_content = skill_match[2].strip()
        
        # Extract spans for this skill
        spans = []
        span_pattern = r'<start>(.*?)</start>\s*<end>(.*?)</end>\s*<text>(.*?)</text>\s*<explanation>(.*?)</explanation>'
        span_matches = re.findall(span_pattern, skill_content, re.DOTALL)
        
        for start, end, text, explanation in span_matches:
            spans.append({
                'start': int(start.strip()),
                'end': int(end.strip()),
                'text': text.strip(),
                'explanation': explanation.strip()
            })
        
        skills.append({
            'name': skill_name,
            'definition': skill_def,
            'spans': spans
        })
    
    return {
        'problem': problem,
        'domain': domain,
        'solution': solution,
        'skills': skills
    }

def main():
    # Directory containing analysis files
    analyses_dir = "new_cognitive_analysis_results/analyses"
    
    # Initialize data structure
    data = {
        'examples': []
    }
    
    # Get all analysis files
    files = [f for f in os.listdir(analyses_dir) if f.endswith('_analysis.txt')]
    
    # Group files by example number
    example_files = {}
    for file in files:
        # Extract example number and type (e.g., "example_0_groundtruth")
        match = re.match(r'example_(\d+)_(.*?)_analysis\.txt', file)
        if match:
            example_num = int(match.group(1))
            example_type = match.group(2)
            
            if example_num not in example_files:
                example_files[example_num] = {}
            
            example_files[example_num][example_type] = os.path.join(analyses_dir, file)
    
    # Process each example
    for example_num in sorted(example_files.keys()):
        example_data = {
            'id': example_num,
            'solutions': {}
        }
        
        # Process each solution type for this example
        for solution_type, file_path in example_files[example_num].items():
            analysis_data = parse_analysis_file(file_path)
            
            # For the first solution type, store problem and domain
            if not example_data.get('problem'):
                example_data['problem'] = analysis_data['problem']
                example_data['domain'] = analysis_data['domain']
            
            # Store solution data
            example_data['solutions'][solution_type] = {
                'trajectory': analysis_data['solution'],
                'skills': analysis_data['skills']
            }
        
        data['examples'].append(example_data)
    
    # Save to data.json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main() 