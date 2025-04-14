import json
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
import seaborn as sns

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

def analyze_skills_per_domain_and_model(data):
    domain_model_skills = {'groundtruth': {}, 'gemini': {}, 'deepseek': {}}
    models = ['groundtruth', 'gemini', 'deepseek']
    
    for example in data['examples']:
        domain = example.get('domain', 'Unknown')
        for model in models:
            if model in example['solutions']:
                if domain not in domain_model_skills[model]:
                    domain_model_skills[model][domain] = 0
                if 'skills' in example['solutions'][model]:
                    domain_model_skills[model][domain] += len(example['solutions'][model]['skills'])
    
    return domain_model_skills

def plot_domain_stats(domain_stats):
    plt.figure(figsize=(12, 6))
    domains = list(domain_stats.keys())
    counts = list(domain_stats.values())
    
    plt.bar(domains, counts)
    plt.xticks(rotation=45, ha='right')
    plt.title('Number of Problems by Mathematical Domain')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('domain_stats.png')
    plt.close()

def plot_skill_stats(data):
    # Create a dictionary to store skill counts per domain
    domain_skill_counts = {}
    total_skills_per_domain = {}
    
    for example in data['examples']:
        domain = example.get('domain', 'Unknown')
        if domain not in domain_skill_counts:
            domain_skill_counts[domain] = {}
            total_skills_per_domain[domain] = 0
        
        # Count skills for each model
        for model in ['groundtruth', 'gemini', 'deepseek']:
            if model in example['solutions'] and 'skills' in example['solutions'][model]:
                skills = example['solutions'][model]['skills']
                total_skills_per_domain[domain] += len(skills)
                for skill in skills:
                    skill_name = skill['name']
                    if skill_name not in domain_skill_counts[domain]:
                        domain_skill_counts[domain][skill_name] = 0
                    domain_skill_counts[domain][skill_name] += 1
    
    # Get all unique skills and domains
    all_skills = sorted(set().union(*[set(d.keys()) for d in domain_skill_counts.values()]))
    all_domains = sorted(domain_skill_counts.keys())
    
    # Create a matrix for the heatmap
    heatmap_data = np.zeros((len(all_skills), len(all_domains)))
    
    # Fill the matrix with percentages
    for i, skill in enumerate(all_skills):
        for j, domain in enumerate(all_domains):
            if total_skills_per_domain[domain] > 0:
                count = domain_skill_counts[domain].get(skill, 0)
                heatmap_data[i, j] = (count / total_skills_per_domain[domain]) * 100
    
    # Create the heatmap
    plt.figure(figsize=(15, 10))
    sns.heatmap(heatmap_data, 
                annot=True, 
                fmt='.1f',
                cmap='YlOrRd',
                xticklabels=all_domains,
                yticklabels=all_skills,
                cbar_kws={'label': 'Percentage of Skills Used'})
    
    plt.title('Skill Usage Distribution by Domain')
    plt.xlabel('Mathematical Domain')
    plt.ylabel('Cognitive Skill')
    plt.tight_layout()
    plt.savefig('skill_stats.png')
    plt.close()

def plot_skills_per_domain_and_model(domain_model_skills):
    plt.figure(figsize=(15, 8))
    
    models = ['groundtruth', 'gemini', 'deepseek']
    domains = sorted(set().union(*[set(d.keys()) for d in domain_model_skills.values()]))
    
    x = np.arange(len(domains))
    width = 0.25
    
    for i, model in enumerate(models):
        counts = [domain_model_skills[model].get(domain, 0) for domain in domains]
        plt.bar(x + i*width, counts, width, label=model)
    
    plt.xlabel('Mathematical Domain')
    plt.ylabel('Number of Skills')
    plt.title('Skills Distribution by Domain and Model')
    plt.xticks(x + width, domains, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig('skills_per_domain_model.png')
    plt.close()

def generate_html_report(data, domain_stats, skill_stats, skill_definitions, skill_examples, domain_model_skills):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cognitive Skills Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .section { margin-bottom: 30px; }
            .skill-card { 
                border: 1px solid #ddd; 
                padding: 15px; 
                margin-bottom: 15px; 
                border-radius: 5px;
            }
            .skill-name { 
                font-weight: bold; 
                font-size: 1.2em; 
                margin-bottom: 10px;
            }
            .skill-definition { 
                margin-bottom: 10px; 
                color: #555;
            }
            .example { 
                background-color: #f5f5f5; 
                padding: 10px; 
                margin: 5px 0; 
                border-radius: 3px;
            }
            .toggle-button { 
                background-color: #4CAF50; 
                color: white; 
                padding: 5px 10px; 
                border: none; 
                border-radius: 3px; 
                cursor: pointer;
            }
            .hidden { display: none; }
            .domain-stats { margin-bottom: 20px; }
            .skill-stats { margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>Cognitive Skills Analysis Report</h1>
        
        <div class="section domain-stats">
            <h2>Domain Statistics</h2>
            <img src="domain_stats.png" alt="Domain Statistics">
        </div>
        
        <div class="section skill-stats">
            <h2>Skill Statistics</h2>
            <img src="skill_stats.png" alt="Skill Statistics">
        </div>
        
        <div class="section">
            <h2>Skills Distribution by Domain and Model</h2>
            <img src="skills_per_domain_model.png" alt="Skills per Domain and Model">
        </div>
        
        <div class="section">
            <h2>Detailed Skill Analysis</h2>
    """
    
    for skill_name, count in sorted(skill_stats.items(), key=lambda x: x[1], reverse=True):
        html_content += f"""
            <div class="skill-card">
                <div class="skill-name">{skill_name} (Used {count} times)</div>
                <div class="skill-definition">{skill_definitions[skill_name]}</div>
                <button class="toggle-button" onclick="toggleExamples('{skill_name}')">Show Examples</button>
                <div id="{skill_name}-examples" class="hidden">
                    <h3>Examples:</h3>
        """
        
        for example in skill_examples[skill_name][:3]:  # Show up to 3 examples
            html_content += f"""
                    <div class="example">
                        <p><strong>Text:</strong> {example['text']}</p>
                        <p><strong>Explanation:</strong> {example['explanation']}</p>
                    </div>
            """
        
        html_content += """
                </div>
            </div>
        """
    
    html_content += """
        </div>
        
        <script>
            function toggleExamples(skillName) {
                const examplesDiv = document.getElementById(skillName + '-examples');
                const button = examplesDiv.previousElementSibling;
                
                if (examplesDiv.classList.contains('hidden')) {
                    examplesDiv.classList.remove('hidden');
                    button.textContent = 'Hide Examples';
                } else {
                    examplesDiv.classList.add('hidden');
                    button.textContent = 'Show Examples';
                }
            }
        </script>
    </body>
    </html>
    """
    
    with open('skills_report.html', 'w') as f:
        f.write(html_content)

def main():
    data = load_data()
    
    # Analyze data
    domain_stats = analyze_domains(data)
    skill_stats, skill_definitions, skill_examples = analyze_skills(data)
    domain_model_skills = analyze_skills_per_domain_and_model(data)
    
    # Generate visualizations
    plot_domain_stats(domain_stats)
    plot_skill_stats(data)
    plot_skills_per_domain_and_model(domain_model_skills)
    
    # Generate HTML report
    generate_html_report(data, domain_stats, skill_stats, skill_definitions, skill_examples, domain_model_skills)
    
    print("Analysis complete! Check the following files:")
    print("- domain_stats.png: Distribution of problems by domain")
    print("- skill_stats.png: Frequency of cognitive skills")
    print("- skills_per_domain_model.png: Skills distribution by domain and model")
    print("- skills_report.html: Detailed analysis with examples")

if __name__ == "__main__":
    main() 