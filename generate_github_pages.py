import json
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import os

def load_data():
    with open('data.json', 'r') as f:
        return json.load(f)

def analyze_domains(data):
    domain_stats = defaultdict(int)
    for example in data['examples']:
        domain = example.get('domain', 'Unknown')
        domain_stats[domain] += 1
    return domain_stats

def analyze_skills(data):
    skill_stats = defaultdict(int)
    skill_definitions = {}
    skill_examples = defaultdict(list)
    
    for example in data['examples']:
        for solution_type, solution in example['solutions'].items():
            if 'skills' in solution:
                for skill in solution['skills']:
                    skill_name = skill['name']
                    skill_stats[skill_name] += 1
                    if skill_name not in skill_definitions:
                        skill_definitions[skill_name] = skill['definition']
                    if 'spans' in skill:
                        skill_examples[skill_name].extend(skill['spans'])
    
    return skill_stats, skill_definitions, skill_examples

def generate_domain_table(domain_stats):
    html = """
    <h2>Top Mathematical Domains</h2>
    <table>
        <tr>
            <th>Domain</th>
            <th>Count</th>
        </tr>
    """
    
    for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True):
        html += f"""
        <tr>
            <td>{domain}</td>
            <td>{count}</td>
        </tr>
        """
    
    html += "</table>"
    return html

def generate_skills_table(skill_stats, skill_definitions, skill_examples):
    html = """
    <h2>Top Cognitive Skills</h2>
    <table>
        <tr>
            <th>Skill</th>
            <th>Count</th>
            <th>Percentage</th>
            <th>Definition</th>
            <th>Evidence</th>
            <th>Math Example</th>
        </tr>
    """
    
    total_skills = sum(skill_stats.values())
    
    for skill_name, count in sorted(skill_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_skills) * 100
        definition = skill_definitions.get(skill_name, "No definition available")
        
        # Get example evidence
        evidence = "No evidence provided."
        if skill_name in skill_examples and skill_examples[skill_name]:
            example = skill_examples[skill_name][0]
            evidence = f"""
            <div class="evidence">
                <p><strong>Text:</strong> {example['text']}</p>
                <p><strong>Explanation:</strong> {example['explanation']}</p>
            </div>
            """
        
        html += f"""
        <tr>
            <td><strong>{skill_name}</strong></td>
            <td>{count}</td>
            <td>{percentage:.1f}%</td>
            <td>{definition}</td>
            <td>{evidence}</td>
            <td>Example problem here</td>
        </tr>
        """
    
    html += "</table>"
    return html

def generate_html_report(data, domain_stats, skill_stats, skill_definitions, skill_examples):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cognitive Skills in Mathematical Problem Solving</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .evidence {
                background-color: #f9f9f9;
                padding: 10px;
                margin: 5px 0;
                border-radius: 3px;
            }
            h1, h2 {
                color: #333;
            }
            h1 {
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <h1>Cognitive Skills in Mathematical Problem Solving</h1>
    """
    
    # Add domain statistics
    html_content += generate_domain_table(domain_stats)
    
    # Add skill statistics
    html_content += generate_skills_table(skill_stats, skill_definitions, skill_examples)
    
    html_content += """
    </body>
    </html>
    """
    
    # Create docs directory if it doesn't exist
    if not os.path.exists('docs'):
        os.makedirs('docs')
    
    # Save the HTML file
    with open('docs/index.html', 'w') as f:
        f.write(html_content)

def main():
    data = load_data()
    
    # Analyze data
    domain_stats = analyze_domains(data)
    skill_stats, skill_definitions, skill_examples = analyze_skills(data)
    
    # Generate HTML report
    generate_html_report(data, domain_stats, skill_stats, skill_definitions, skill_examples)
    
    print("GitHub Pages site generated! Check the docs/index.html file.")

if __name__ == "__main__":
    main() 