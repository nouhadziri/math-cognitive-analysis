import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

def load_data():
    with open('data.json', 'r') as f:
        return json.load(f)

def analyze_domains(data):
    domain_counts = {}
    for example in data['examples']:
        domain = example.get('domain', 'Unknown')
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    return domain_counts

def analyze_skills(data):
    skill_counts = {}
    skill_definitions = {}
    skill_examples = {}
    
    for example in data['examples']:
        for solution in example['solutions'].values():
            for skill in solution.get('skills', []):
                skill_name = skill['name']
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
                if skill_name not in skill_definitions:
                    skill_definitions[skill_name] = skill['definition']
                if skill_name not in skill_examples:
                    skill_examples[skill_name] = []
                skill_examples[skill_name].append({
                    'text': skill['spans'][0]['text'],
                    'explanation': skill['spans'][0]['explanation']
                })
    
    return skill_counts, skill_definitions, skill_examples

def create_domain_chart(domain_stats):
    df = pd.DataFrame(list(domain_stats.items()), columns=['Domain', 'Count'])
    fig = go.Figure(data=[
        go.Bar(
            x=df['Domain'],
            y=df['Count'],
            text=df['Count'],
            textposition='auto',
            marker_color='rgb(55, 83, 109)'
        )
    ])
    
    fig.update_layout(
        title='Distribution of Mathematical Domains',
        xaxis_title='Domain',
        yaxis_title='Number of Problems',
        template='plotly_white'
    )
    
    return fig

def create_skills_chart(skill_stats):
    df = pd.DataFrame(list(skill_stats.items()), columns=['Skill', 'Count'])
    df = df.sort_values('Count', ascending=True)
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['Count'],
            y=df['Skill'],
            orientation='h',
            text=df['Count'],
            textposition='auto',
            marker_color='rgb(26, 118, 255)'
        )
    ])
    
    fig.update_layout(
        title='Cognitive Skills Distribution',
        xaxis_title='Frequency',
        yaxis_title='Skill',
        height=800,
        template='plotly_white'
    )
    
    return fig

def generate_domain_table(domain_stats):
    html = """
    <div class="table-container">
        <h2>Mathematical Domains Summary</h2>
        <table>
            <tr>
                <th>Domain</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
    """
    
    total = sum(domain_stats.values())
    for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        html += f"""
            <tr>
                <td>{domain}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
        """
    
    html += """
        </table>
    </div>
    """
    return html

def generate_skills_table(skill_stats, skill_definitions, skill_examples):
    html = """
    <div class="table-container">
        <h2>Cognitive Skills Summary</h2>
        <table>
            <tr>
                <th>Skill</th>
                <th>Count</th>
                <th>Percentage</th>
                <th>Definition</th>
                <th>Example Evidence</th>
            </tr>
    """
    
    total = sum(skill_stats.values())
    for skill, count in sorted(skill_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        definition = skill_definitions[skill]
        example = skill_examples[skill][0] if skill_examples[skill] else {'text': 'No example available', 'explanation': ''}
        
        html += f"""
            <tr>
                <td><strong>{skill}</strong></td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
                <td>{definition}</td>
                <td>
                    <div class="evidence">
                        <p><strong>Text:</strong> {example['text']}</p>
                        <p><strong>Explanation:</strong> {example['explanation']}</p>
                    </div>
                </td>
            </tr>
        """
    
    html += """
        </table>
    </div>
    """
    return html

def generate_html_report(data, domain_stats, skill_stats, skill_definitions, skill_examples):
    # Create docs directory if it doesn't exist
    if not os.path.exists('docs'):
        os.makedirs('docs')
    
    # Generate domain chart
    domain_fig = create_domain_chart(domain_stats)
    domain_chart_html = domain_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # Generate tables
    domain_table_html = generate_domain_table(domain_stats)
    skills_table_html = generate_skills_table(skill_stats, skill_definitions, skill_examples)
    
    # Generate skills chart
    skills_fig = create_skills_chart(skill_stats)
    skills_chart_html = skills_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Math Cognitive Analysis</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .chart-container {{
                margin: 20px 0;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .table-container {{
                margin: 20px 0;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            .evidence {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
            }}
            .skills-section {{
                margin-top: 40px;
            }}
            .skill-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .skill-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .skill-name {{
                font-size: 1.2em;
                font-weight: bold;
                color: #2c3e50;
            }}
            .skill-count {{
                background: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.9em;
            }}
            .skill-definition {{
                color: #666;
                margin: 10px 0;
            }}
            .examples {{
                margin-top: 15px;
            }}
            .example {{
                background: #f8f9fa;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .example-text {{
                font-style: italic;
            }}
            .example-explanation {{
                color: #666;
                margin-top: 5px;
            }}
            h1, h2 {{
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Math Cognitive Analysis</h1>
            
            <div class="chart-container">
                <h2>Mathematical Domains Distribution</h2>
                {domain_chart_html}
            </div>
            
            {domain_table_html}
            
            <div class="chart-container">
                <h2>Cognitive Skills Distribution</h2>
                {skills_chart_html}
            </div>
            
            {skills_table_html}
            
            <div class="skills-section">
                <h2>Detailed Skill Analysis</h2>
                {generate_skills_html(skill_stats, skill_definitions, skill_examples)}
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write to file
    with open('docs/index.html', 'w') as f:
        f.write(html_content)

def generate_skills_html(skill_stats, skill_definitions, skill_examples):
    html = ""
    for skill, count in sorted(skill_stats.items(), key=lambda x: x[1], reverse=True):
        html += f"""
        <div class="skill-card">
            <div class="skill-header">
                <span class="skill-name">{skill}</span>
                <span class="skill-count">Used {count} times</span>
            </div>
            <div class="skill-definition">
                {skill_definitions[skill]}
            </div>
            <div class="examples">
                <h3>Examples:</h3>
                {generate_examples_html(skill_examples[skill])}
            </div>
        </div>
        """
    return html

def generate_examples_html(examples):
    html = ""
    for example in examples[:3]:  # Show first 3 examples
        html += f"""
        <div class="example">
            <div class="example-text">"{example['text']}"</div>
            <div class="example-explanation">{example['explanation']}</div>
        </div>
        """
    return html

def main():
    print("Loading data...")
    data = load_data()
    
    print("Analyzing domains...")
    domain_stats = analyze_domains(data)
    
    print("Analyzing skills...")
    skill_stats, skill_definitions, skill_examples = analyze_skills(data)
    
    print("Generating visualizations...")
    generate_html_report(data, domain_stats, skill_stats, skill_definitions, skill_examples)
    
    print("Done! Check docs/index.html for the results.")

if __name__ == "__main__":
    main() 