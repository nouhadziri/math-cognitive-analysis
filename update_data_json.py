import json
import os
from collections import defaultdict
import re

def load_data():
    with open('data.json', 'r') as f:
        return json.load(f)

def load_analysis_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract problem ID and model from filename
    match = re.match(r'example_(\d+)_(\w+)_analysis\.txt', os.path.basename(file_path))
    if not match:
        return None
    
    problem_id = int(match.group(1))
    model = match.group(2)
    
    # Parse the analysis content
    sections = content.split('\n\n')
    analysis = {
        'problem_text': sections[0].split('Problem Text:')[1].strip(),
        'domain': sections[1].split('Domain:')[1].strip(),
        'trajectory': sections[2].split('Solution Trajectory:')[1].strip(),
        'skills': []
    }
    
    # Parse skills
    skills_section = sections[3].split('Cognitive Skills Analysis:')[1].strip()
    skill_blocks = skills_section.split('\n\n')
    
    for block in skill_blocks:
        if not block.strip():
            continue
            
        lines = block.split('\n')
        skill = {
            'name': lines[0].split(':')[1].strip(),
            'definition': lines[1].split(':')[1].strip(),
            'spans': []
        }
        
        # Parse spans
        span_text = '\n'.join(lines[2:])
        span_blocks = span_text.split('Evidence:')
        
        for span_block in span_blocks[1:]:
            if not span_block.strip():
                continue
                
            lines = span_block.strip().split('\n')
            span = {
                'start': int(lines[0].split(':')[1].strip()),
                'end': int(lines[1].split(':')[1].strip()),
                'text': lines[2].split(':')[1].strip(),
                'explanation': lines[3].split(':')[1].strip()
            }
            skill['spans'].append(span)
        
        analysis['skills'].append(skill)
    
    return problem_id, model, analysis

def update_data_json():
    # Load existing data
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    # Create a mapping of problem IDs to their indices
    problem_id_to_idx = {example['id']: idx for idx, example in enumerate(data['examples'])}
    
    # Process new analysis files
    analysis_dir = 'new_cognitive_analysis_results/analyses'
    for filename in os.listdir(analysis_dir):
        if not filename.endswith('_analysis.txt'):
            continue
            
        result = load_analysis_file(os.path.join(analysis_dir, filename))
        if not result:
            continue
            
        problem_id, model, analysis = result
        
        # Update the corresponding example in data.json
        if problem_id in problem_id_to_idx:
            idx = problem_id_to_idx[problem_id]
            if 'solutions' not in data['examples'][idx]:
                data['examples'][idx]['solutions'] = {}
            data['examples'][idx]['solutions'][model] = {
                'trajectory': analysis['trajectory'],
                'skills': analysis['skills']
            }
    
    # Save updated data
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Updated data.json with new analyses")

def generate_statistics(data):
    # Initialize counters
    domain_stats = defaultdict(int)
    skill_stats = defaultdict(int)
    skill_definitions = {}
    skill_examples = defaultdict(list)
    
    # Process each example
    for example in data['examples']:
        if 'solutions' not in example:
            continue
            
        for model, solution in example['solutions'].items():
            # Count domains
            domain = solution.get('domain', 'Unknown')
            domain_stats[domain] += 1
            
            # Process skills
            for skill in solution.get('skills', []):
                skill_name = skill['name']
                skill_stats[skill_name] += 1
                skill_definitions[skill_name] = skill['definition']
                
                # Add example
                skill_examples[skill_name].append({
                    'problem_id': example['id'],
                    'model': model,
                    'spans': skill['spans']
                })
    
    # Save statistics
    stats = {
        'domains': dict(domain_stats),
        'skills': {
            'counts': dict(skill_stats),
            'definitions': skill_definitions,
            'examples': dict(skill_examples)
        }
    }
    
    with open('statistics.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats

def main():
    print("Updating data.json with new analyses...")
    update_data_json()
    
    print("Generating statistics...")
    data = load_data()
    stats = generate_statistics(data)
    
    print("\nStatistics Summary:")
    print("\nDomains:")
    for domain, count in stats['domains'].items():
        print(f"{domain}: {count}")
    
    print("\nTop Skills:")
    sorted_skills = sorted(stats['skills']['counts'].items(), key=lambda x: x[1], reverse=True)
    for skill, count in sorted_skills[:10]:
        print(f"{skill}: {count}")
    
    print("\nDone! Updated data.json and generated statistics.json")

if __name__ == "__main__":
    main() 