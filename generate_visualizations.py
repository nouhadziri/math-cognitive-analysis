import json
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import os
import re

def load_data():
    """Load data from new_data.json"""
    print("Loading data from new_data.json...")
    with open('new_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_domains(data):
    """Analyze domains from data"""
    domain_counts = {}
    for example in data['examples']:
        domain = example.get('domain', 'Unknown')
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    return domain_counts

def analyze_skills(data, model='deepseek'):
    """Analyze skills for a specific model"""
    skill_counts = {}
    skill_definitions = {}
    skill_examples = {}
    
    for example in data['examples']:
        if model in example['solutions']:
            solution = example['solutions'][model]
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

def analyze_skills_per_domain_and_model(data):
    """Analyze cognitive skills distribution across domains and models."""
    domain_model_skills = {}
    
    for example in data['examples']:
        domain = example.get('domain', 'Unknown')
        if domain not in domain_model_skills:
            domain_model_skills[domain] = {'groundtruth': {}, 'gemini': {}, 'deepseek': {}}
        
        for model, solution in example['solutions'].items():
            for skill in solution.get('skills', []):
                skill_name = skill['name']
                domain_model_skills[domain][model][skill_name] = domain_model_skills[domain][model].get(skill_name, 0) + 1
    
    return domain_model_skills

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

def create_skills_chart(skill_stats, model_name):
    """Create a skills distribution chart for a specific model"""
    df = pd.DataFrame(list(skill_stats.items()), columns=['Skill', 'Count'])
    df = df.sort_values('Count', ascending=True)
    
    # Get top 15 skills
    df = df.tail(15)
    
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
        title=f'Top 15 Cognitive Skills Distribution ({model_name})',
        xaxis_title='Frequency',
        yaxis_title='Skill',
        height=800,
        template='plotly_white'
    )
    
    return fig

def create_skills_per_domain_chart(domain_model_skills, model='deepseek'):
    """Create a chart showing top 10 skills per domain for a specific model."""
    # Prepare data for plotting
    domains = list(domain_model_skills.keys())
    
    # Create subplots for each domain
    fig = make_subplots(
        rows=len(domains), 
        cols=1,
        subplot_titles=[f"Top Skills in {domain}" for domain in domains],
        vertical_spacing=0.05  # Reduced from 0.1 to 0.05
    )
    
    # Add traces for each domain
    for i, domain in enumerate(domains, 1):
        # Get skills and counts for the specified model
        skills_counts = list(domain_model_skills[domain][model].items())
        
        # Sort by count and get top 10
        top_skills = sorted(skills_counts, key=lambda x: x[1], reverse=True)[:10]
        skills = [skill[0] for skill in top_skills]
        counts = [skill[1] for skill in top_skills]
        
        fig.add_trace(
            go.Bar(
                x=skills,
                y=counts,
                name=domain,
                text=counts,
                textposition='auto',
                marker_color='rgb(55, 83, 109)'
            ),
            row=i,
            col=1
        )
        
        # Update x-axis for better readability
        fig.update_xaxes(tickangle=45, row=i, col=1)
    
    # Update layout
    fig.update_layout(
        title=f'Top 10 Skills by Domain ({model})',
        height=300 * len(domains),
        template='plotly_white',
        showlegend=False,
        margin=dict(t=100, b=100)  # Add more margin for rotated labels
    )
    
    return fig

def create_domain_skills_heatmap(domain_model_skills):
    """Create a heatmap showing skills distribution across domains."""
    # Get all unique skills and their total counts across all domains and models
    skill_counts = {}
    for domain_data in domain_model_skills.values():
        for model_data in domain_data.values():
            for skill, count in model_data.items():
                skill_counts[skill] = skill_counts.get(skill, 0) + count
    
    # Get top 15 skills by total count
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_skill_names = [skill for skill, _ in top_skills]
    
    # Create a matrix for the heatmap
    domains = list(domain_model_skills.keys())
    heatmap_data = []
    
    for domain in domains:
        row = []
        for skill in top_skill_names:
            # Sum the skill count across all models for this domain
            skill_count = sum(
                domain_model_skills[domain][model].get(skill, 0)
                for model in ['groundtruth', 'gemini', 'deepseek']
            )
            row.append(skill_count)
        heatmap_data.append(row)
    
    # Create the heatmap with custom colorscale
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=top_skill_names,
        y=domains,
        colorscale=[
            [0, 'white'],  # Zero values will be white
            [0.1, 'rgb(230, 230, 230)'],  # Very low values
            [0.3, 'rgb(200, 200, 200)'],  # Low values
            [0.5, 'rgb(170, 170, 170)'],  # Medium values
            [0.7, 'rgb(140, 140, 140)'],  # High values
            [1.0, 'rgb(110, 110, 110)']   # Very high values
        ],
        text=[[str(val) if val > 0 else '' for val in row] for row in heatmap_data],
        texttemplate="%{text}",
        textfont={"size": 10, "color": "black"},
        hoverongaps=False,
        showscale=True,
        zmin=0,  # Set minimum value to 0
        zmax=max(max(row) for row in heatmap_data)  # Set maximum to the highest value
    ))
    
    fig.update_layout(
        title='Top 15 Skills Distribution Across Domains',
        xaxis_title='Cognitive Skills',
        yaxis_title='Mathematical Domains',
        height=400,
        template='plotly_white',
        margin=dict(l=50, r=50, t=50, b=100)  # Add more bottom margin for rotated labels
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)
    
    return fig

def create_top_skills_per_domain_chart(domain_model_skills):
    """Create a chart showing top 10 skills for each domain."""
    # Get domains
    domains = list(domain_model_skills.keys())
    
    # Create subplots for each domain
    fig = make_subplots(
        rows=len(domains), 
        cols=1,
        subplot_titles=[f"Top Skills in {domain}" for domain in domains],
        vertical_spacing=0.05  # Reduced from 0.1 to 0.05
    )
    
    # For each domain, create a bar plot of top skills
    for i, domain in enumerate(domains, 1):
        # Get total skill counts across all models
        domain_skills = {}
        for model in ['groundtruth', 'gemini', 'deepseek']:
            for skill, count in domain_model_skills[domain][model].items():
                domain_skills[skill] = domain_skills.get(skill, 0) + count
        
        # Sort by count and get top 10
        top_skills = sorted(domain_skills.items(), key=lambda x: x[1], reverse=True)[:10]
        skills = [skill[0] for skill in top_skills]
        counts = [skill[1] for skill in top_skills]
        
        if not top_skills:
            continue
            
        # Create bar plot for this domain
        fig.add_trace(
            go.Bar(
                x=skills,
                y=counts,
                name=domain,
                text=counts,
                textposition='auto',
                marker_color='rgb(55, 83, 109)'
            ),
            row=i,
            col=1
        )
        
        # Update x-axis labels for better readability
        fig.update_xaxes(tickangle=45, row=i, col=1)
    
    # Update layout
    fig.update_layout(
        title='Top 10 Skills by Domain (All Models Combined)',
        height=300 * len(domains),
        template='plotly_white',
        showlegend=False,
        margin=dict(t=100, b=100)  # Add more margin for rotated labels
    )
    
    return fig

def create_top_skills_chart(domain_model_skills):
    """Create a chart showing top 10 skills across all domains and models."""
    # Aggregate skills across all domains and models
    total_skills = {}
    for domain in domain_model_skills:
        for model in ['groundtruth', 'gemini', 'deepseek']:
            for skill, count in domain_model_skills[domain][model].items():
                total_skills[skill] = total_skills.get(skill, 0) + count
    
    # Get top 10 skills
    top_skills = sorted(total_skills.items(), key=lambda x: x[1], reverse=True)[:10]
    skills = [skill[0] for skill in top_skills]
    counts = [skill[1] for skill in top_skills]
    
    # Create the figure
    fig = go.Figure(data=[
        go.Bar(
            x=skills,
            y=counts,
            text=counts,
            textposition='auto',
            marker_color='rgb(55, 83, 109)'
        )
    ])
    
    # Update layout
    fig.update_layout(
        title='Top 10 Cognitive Skills Across All Domains',
        xaxis_title='Skill',
        yaxis_title='Total Count',
        template='plotly_white',
        showlegend=False,
        margin=dict(t=100, b=100),  # Add more margin for rotated labels
        height=600,
        width=1000
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)
    
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

def generate_html_report(data, domain_stats, model_skill_stats, domain_model_skills):
    """Generate an HTML report with all visualizations and tables."""
    # Create plots directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Create charts
    domain_chart = create_domain_chart(domain_stats)
    
    # Generate domain table
    domain_table = generate_domain_table(domain_stats)
    
    # Generate skills tables for each model
    skills_tables = {}
    for model in ['groundtruth', 'gemini', 'deepseek']:
        skill_stats, skill_definitions, skill_examples = analyze_skills(data, model)
        skills_tables[model] = generate_skills_table(skill_stats, skill_definitions, skill_examples)
    
    # Create the HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cognitive Skills Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .plot {{ margin: 20px 0; }}
            table {{ border-collapse: collapse; margin: 20px 0; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f5f5f5; }}
            .collapsible {{ cursor: pointer; }}
            .content {{ display: none; }}
        </style>
        <script>
            function toggleContent(id) {{
                var content = document.getElementById(id);
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            }}
        </script>
    </head>
    <body>
        <h1>Cognitive Skills Analysis Report</h1>
        
        <h2>Domain Distribution</h2>
        <div class="plot">
            {domain_chart.to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        {domain_table}
        
        <h2>Skills Analysis by Model</h2>
        
        <h3>Ground Truth</h3>
        <div class="plot">
            {create_skills_chart(model_skill_stats['groundtruth'], 'Ground Truth').to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        <div class="plot">
            {create_skills_per_domain_chart(domain_model_skills, 'groundtruth').to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        {skills_tables['groundtruth']}
        
        <h3>Gemini</h3>
        <div class="plot">
            {create_skills_chart(model_skill_stats['gemini'], 'Gemini').to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        <div class="plot">
            {create_skills_per_domain_chart(domain_model_skills, 'gemini').to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        {skills_tables['gemini']}
        
        <h3>Deepseek</h3>
        <div class="plot">
            {create_skills_chart(model_skill_stats['deepseek'], 'Deepseek').to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        <div class="plot">
            {create_skills_per_domain_chart(domain_model_skills, 'deepseek').to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
        {skills_tables['deepseek']}
        
        <h2>Combined Analysis</h2>
        <div class="plot">
            {create_top_skills_per_domain_chart(domain_model_skills).to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
    </body>
    </html>
    """
    
    # Save the HTML report
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

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

def create_skills_comparison_chart(model_skill_stats):
    """Create a side-by-side comparison of top 15 skills across all models."""
    # Get top 15 skills from each model
    all_skills = set()
    for model_stats in model_skill_stats.values():
        top_skills = sorted(model_stats.items(), key=lambda x: x[1], reverse=True)[:15]
        all_skills.update(skill for skill, _ in top_skills)
    
    # Create traces for each model
    traces = []
    models = ['groundtruth', 'gemini', 'deepseek']
    model_names = {'groundtruth': 'Ground Truth', 'gemini': 'Gemini', 'deepseek': 'Deepseek'}
    colors = {'groundtruth': 'rgb(55, 83, 109)', 'gemini': 'rgb(26, 118, 255)', 'deepseek': 'rgb(78, 121, 167)'}
    
    for model in models:
        skills_data = []
        for skill in all_skills:
            count = model_skill_stats[model].get(skill, 0)
            skills_data.append((skill, count))
        
        # Sort by count for this model
        skills_data.sort(key=lambda x: x[1], reverse=True)
        skills_data = skills_data[:15]  # Keep top 15
        
        traces.append(go.Bar(
            name=model_names[model],
            x=[skill[0] for skill in skills_data],
            y=[skill[1] for skill in skills_data],
            text=[skill[1] for skill in skills_data],
            textposition='auto',
            marker_color=colors[model]
        ))
    
    # Create figure
    fig = go.Figure(data=traces)
    
    # Update layout
    fig.update_layout(
        title='Top 15 Cognitive Skills Comparison Across Models',
        xaxis_title='Skill',
        yaxis_title='Count',
        barmode='group',
        height=600,
        width=1200,
        template='plotly_white',
        xaxis_tickangle=45,
        margin=dict(t=100, b=100)  # Add more margin for rotated labels
    )
    
    return fig

def create_combined_skills_distribution_chart(model_skill_stats):
    """Create a single figure with three subplots showing skills distribution for each model."""
    # Create subplots
    fig = make_subplots(
        rows=1, 
        cols=3,
        subplot_titles=['Ground Truth', 'Gemini', 'Deepseek'],
        horizontal_spacing=0.1
    )
    
    # Define colors for each model
    colors = {
        'groundtruth': 'rgb(55, 83, 109)',
        'gemini': 'rgb(26, 118, 255)',
        'deepseek': 'rgb(78, 121, 167)'
    }
    
    # Add traces for each model
    for i, model in enumerate(['groundtruth', 'gemini', 'deepseek'], 1):
        # Get top 15 skills for this model
        top_skills = sorted(model_skill_stats[model].items(), key=lambda x: x[1], reverse=True)[:15]
        skills = [skill[0] for skill in top_skills]
        counts = [skill[1] for skill in top_skills]
        
        fig.add_trace(
            go.Bar(
                x=counts,
                y=skills,
                orientation='h',
                text=counts,
                textposition='auto',
                marker_color=colors[model],
                name=model
            ),
            row=1,
            col=i
        )
        
        # Update x-axis for better readability
        fig.update_xaxes(title_text='Count', row=1, col=i)
        fig.update_yaxes(title_text='Skill', row=1, col=i)
    
    # Update layout
    fig.update_layout(
        title='Top 15 Cognitive Skills Distribution by Model',
        height=800,
        width=1500,
        template='plotly_white',
        showlegend=False,
        margin=dict(t=100, b=100)  # Add more margin for rotated labels
    )
    
    return fig

def main():
    print("Loading data...")
    data = load_data()
    
    print("Analyzing domains...")
    domain_stats = analyze_domains(data)
    
    print("Analyzing skills per domain and model...")
    domain_model_skills = analyze_skills_per_domain_and_model(data)
    
    # Analyze skills for each model
    model_skill_stats = {}
    for model in ['groundtruth', 'gemini', 'deepseek']:
        skill_stats, _, _ = analyze_skills(data, model)
        model_skill_stats[model] = skill_stats
    
    print("Generating visualizations...")
    
    # Create and save domain distribution plot
    print("Saving domain distribution plot...")
    domain_chart = create_domain_chart(domain_stats)
    domain_chart.write_html('plots/domain_distribution.html')
    domain_chart.write_image('plots/domain_distribution.png')
    
    # Create and save skills distribution plots for each model
    for model in ['groundtruth', 'gemini', 'deepseek']:
        print(f"Saving skills distribution plot for {model}...")
        skills_chart = create_skills_chart(model_skill_stats[model], model)
        skills_chart.write_html(f'plots/skills_distribution_{model}.html')
        skills_chart.write_image(f'plots/skills_distribution_{model}.png')
    
    # Create and save combined skills distribution plot
    print("Saving combined skills distribution plot...")
    combined_chart = create_combined_skills_distribution_chart(model_skill_stats)
    combined_chart.write_html('plots/combined_skills_distribution.html')
    combined_chart.write_image('plots/combined_skills_distribution.png')
    
    # Create and save skills comparison plot
    print("Saving skills comparison plot...")
    comparison_chart = create_skills_comparison_chart(model_skill_stats)
    comparison_chart.write_html('plots/skills_comparison.html')
    comparison_chart.write_image('plots/skills_comparison.png')
    
    # Create and save skills per domain plots for each model
    for model in ['groundtruth', 'gemini', 'deepseek']:
        print(f"Saving skills per domain plot for {model}...")
        skills_per_domain_chart = create_skills_per_domain_chart(domain_model_skills, model)
        skills_per_domain_chart.write_html(f'plots/skills_per_domain_{model}.html')
        skills_per_domain_chart.write_image(f'plots/skills_per_domain_{model}.png')
    
    # Create and save top skills per domain plot
    print("Saving top skills per domain plot...")
    top_skills_fig = create_top_skills_per_domain_chart(domain_model_skills)
    top_skills_fig.write_html('plots/top_skills_per_domain.html')
    top_skills_fig.write_image('plots/top_skills_per_domain.png')
    
    # Generate HTML report
    print("Generating HTML report...")
    generate_html_report(data, domain_stats, model_skill_stats, domain_model_skills)
    
    print("Done! Check:")
    print("- plots/domain_distribution.png (and .html)")
    for model in ['groundtruth', 'gemini', 'deepseek']:
        print(f"- plots/skills_distribution_{model}.png (and .html)")
        print(f"- plots/skills_per_domain_{model}.png (and .html)")
    print("- plots/combined_skills_distribution.png (and .html)")
    print("- plots/skills_comparison.png (and .html)")
    print("- plots/top_skills_per_domain.png (and .html)")
    print("- docs/index.html")

if __name__ == "__main__":
    main() 