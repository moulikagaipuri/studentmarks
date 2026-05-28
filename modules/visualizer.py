import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set seaborn theme style for rich aesthetics
sns.set_theme(style="white")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'DejaVu Sans', 'Arial', 'sans-serif']

# Premium Colors
COLOR_PALETTE = {
    'high': '#10B981',       # Emerald
    'medium': '#F59E0B',     # Amber
    'low': '#EF4444',        # Rose
    'primary': '#6366F1',     # Indigo
    'secondary': '#06B6D4',   # Cyan
    'dark_blue': '#1E3A8A',   # Deep Slate Blue
    'background': '#F8FAFC',  # Cool Slate Gray
    'grid': '#E2E8F0'         # Soft Grid Gray
}

def get_evaluated_dataframe(df):
    """
    Helper function to filter out students who do not have marks computed yet.
    Ensures columns Mid1, Mid2, and Average are strictly numeric.
    """
    if df.empty:
        return pd.DataFrame()
    # Filter rows where Average is not empty, NaN, or None
    df_eval = df[df['Average'].notna() & (df['Average'].apply(lambda x: str(x).strip() not in ["", "nan", "None"]))].copy()
    if not df_eval.empty:
        df_eval['Mid1'] = pd.to_numeric(df_eval['Mid1'])
        df_eval['Mid2'] = pd.to_numeric(df_eval['Mid2'])
        df_eval['Average'] = pd.to_numeric(df_eval['Average'])
    return df_eval

def plot_performance_distribution(df):
    """
    Plots a gorgeous donut chart showing the distribution of student performance categories.
    """
    df_eval = get_evaluated_dataframe(df)
    fig, ax = plt.subplots(figsize=(6, 5), facecolor='none')
    
    if df_eval.empty:
        ax.text(0.5, 0.5, "No Graded Student Data Available", ha='center', va='center', fontsize=12, color='#94A3B8', weight='bold')
        ax.axis('off')
        return fig

    counts = df_eval['Performance_Category'].value_counts()
    
    # Align categories exactly for color mapping
    categories = ['High Performance', 'Medium Performance', 'Low Performance']
    counts_aligned = [counts.get(cat, 0) for cat in categories]
    
    # Filter out categories with 0 students to keep the chart clean
    active_labels = []
    active_sizes = []
    active_colors = []
    
    color_map = {
        'High Performance': COLOR_PALETTE['high'],
        'Medium Performance': COLOR_PALETTE['medium'],
        'Low Performance': COLOR_PALETTE['low']
    }
    
    for cat, size in zip(categories, counts_aligned):
        if size > 0:
            active_labels.append(f"{cat} ({size})")
            active_sizes.append(size)
            active_colors.append(color_map[cat])

    if not active_sizes:
        ax.text(0.5, 0.5, "No Performance Metrics Computed", ha='center', va='center', fontsize=12, color='#94A3B8', weight='bold')
        ax.axis('off')
        return fig

    # Donut Chart
    wedges, texts, autotexts = ax.pie(
        active_sizes, 
        labels=active_labels, 
        colors=active_colors, 
        autopct='%1.1f%%', 
        startangle=140, 
        pctdistance=0.75,
        textprops=dict(color="#1E293B", weight="bold", size=10),
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=3) # Creates donut hole
    )
    
    # Style percentages inside wedges
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_size(10)
        
    ax.set_title("Overall Performance Distribution", fontsize=13, weight="bold", pad=20, color="#0F172A")
    return fig

def plot_mid_comparison_scatter(df):
    """
    Plots a highly stylized scatter plot comparing Mid 1 and Mid 2 marks,
    colored by their final performance category.
    """
    df_eval = get_evaluated_dataframe(df)
    fig, ax = plt.subplots(figsize=(7, 5), facecolor='none')
    
    if df_eval.empty:
        ax.text(0.5, 0.5, "No Graded Student Data Available", ha='center', va='center', fontsize=12, color='#94A3B8', weight='bold')
        ax.axis('off')
        return fig

    color_map = {
        'High Performance': COLOR_PALETTE['high'],
        'Medium Performance': COLOR_PALETTE['medium'],
        'Low Performance': COLOR_PALETTE['low']
    }
    
    sns.scatterplot(
        data=df_eval, 
        x='Mid1', 
        y='Mid2', 
        hue='Performance_Category', 
        palette=color_map, 
        s=100, 
        alpha=0.8,
        edgecolor='w',
        linewidth=1,
        ax=ax
    )
    
    # Target gridlines
    ax.grid(True, linestyle='--', alpha=0.5, color=COLOR_PALETTE['grid'])
    
    # 45-degree diagonal helper line
    lims = [0, 25]
    ax.plot(lims, lims, color='#94A3B8', linestyle=':', alpha=0.7, label='Equal Scores')
    
    # Threshold marks (marks = 12.5)
    ax.axhline(y=12.5, color=COLOR_PALETTE['low'], linestyle='--', alpha=0.4, label='Slow Learner Threshold (12.5)')
    ax.axvline(x=12.5, color=COLOR_PALETTE['low'], linestyle='--', alpha=0.4)

    ax.set_xlim(-0.5, 26)
    ax.set_ylim(-0.5, 26)
    
    ax.set_xlabel("Mid 1 Marks", fontsize=11, weight="bold", labelpad=10, color="#1E293B")
    ax.set_ylabel("Mid 2 Marks", fontsize=11, weight="bold", labelpad=10, color="#1E293B")
    
    # Style Legend
    legend = ax.legend(frameon=True, facecolor='white', edgecolor=COLOR_PALETTE['grid'], loc='upper left')
    legend.get_frame().set_alpha(0.9)
    plt.setp(legend.get_texts(), fontsize=9, color="#1E293B")
    
    ax.set_title("Mid 1 vs Mid 2 Marks Comparison", fontsize=13, weight="bold", pad=15, color="#0F172A")
    
    # Clean spines
    sns.despine(ax=ax, top=True, right=True, left=False, bottom=False)
    ax.spines['left'].set_color('#CBD5E1')
    ax.spines['bottom'].set_color('#CBD5E1')
    
    return fig

def plot_branch_wise_averages(df):
    """
    Plots a beautiful bar chart displaying the average Mid1, Mid2, and Overall scores 
    grouped by Academic Branch (CSE, ECE, IT, etc.).
    """
    df_eval = get_evaluated_dataframe(df)
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='none')
    
    if df_eval.empty:
        ax.text(0.5, 0.5, "No Graded Student Data Available", ha='center', va='center', fontsize=12, color='#94A3B8', weight='bold')
        ax.axis('off')
        return fig

    branch_stats = df_eval.groupby('Branch')[['Mid1', 'Mid2', 'Average']].mean().reset_index()
    
    # Melt dataframe for Seaborn grouping
    df_melted = pd.melt(
        branch_stats, 
        id_vars=['Branch'], 
        value_vars=['Mid1', 'Mid2', 'Average'], 
        var_name='ExamType', 
        value_name='AverageScore'
    )
    
    custom_palette = {
        'Mid1': COLOR_PALETTE['secondary'],
        'Mid2': COLOR_PALETTE['primary'],
        'Average': COLOR_PALETTE['high']
    }
    
    sns.barplot(
        data=df_melted, 
        x='Branch', 
        y='AverageScore', 
        hue='ExamType', 
        palette=custom_palette, 
        alpha=0.9,
        edgecolor='w',
        linewidth=1.2,
        ax=ax
    )
    
    # Add values on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', padding=3, fontsize=8, color='#334155', weight='bold')

    ax.grid(True, axis='y', linestyle='--', alpha=0.5, color=COLOR_PALETTE['grid'])
    ax.set_xlabel("Academic Branch", fontsize=11, weight="bold", labelpad=10, color="#1E293B")
    ax.set_ylabel("Average Score", fontsize=11, weight="bold", labelpad=10, color="#1E293B")
    ax.set_ylim(0, 28)
    
    legend = ax.legend(title="Assessment", frameon=True, facecolor='white', edgecolor=COLOR_PALETTE['grid'])
    plt.setp(legend.get_texts(), fontsize=9, color="#1E293B")
    
    ax.set_title("Branch-Wise Performance Summary", fontsize=13, weight="bold", pad=15, color="#0F172A")
    
    sns.despine(ax=ax, top=True, right=True, left=True, bottom=False)
    ax.spines['bottom'].set_color('#CBD5E1')
    
    return fig

def plot_slow_learner_metrics(df):
    """
    Generates a visual comparison between the number of Slow Learners 
    in Mid 1 vs Mid 2 vs Overall (Average).
    """
    df_eval = get_evaluated_dataframe(df)
    fig, ax = plt.subplots(figsize=(6, 5), facecolor='none')
    
    if df_eval.empty:
        ax.text(0.5, 0.5, "No Graded Student Data Available", ha='center', va='center', fontsize=12, color='#94A3B8', weight='bold')
        ax.axis('off')
        return fig

    mid1_slow = len(df_eval[df_eval['Mid1'] < 12.5])
    mid2_slow = len(df_eval[df_eval['Mid2'] < 12.5])
    avg_slow = len(df_eval[df_eval['Average'] < 12.5])
    
    categories = ['Mid 1 (<12.5)', 'Mid 2 (<12.5)', 'Overall Average (<12.5)']
    counts = [mid1_slow, mid2_slow, avg_slow]
    
    # Custom colored bars
    bar_colors = [COLOR_PALETTE['secondary'], COLOR_PALETTE['primary'], COLOR_PALETTE['low']]
    
    bars = ax.bar(categories, counts, color=bar_colors, edgecolor='w', linewidth=1.5, width=0.5, alpha=0.95)
    
    # Bar Labels
    ax.bar_label(bars, fmt='%d', padding=5, fontsize=10, color='#1E293B', weight='bold')
    
    ax.set_ylabel("Number of Students", fontsize=11, weight="bold", labelpad=10, color="#1E293B")
    ax.grid(True, axis='y', linestyle='--', alpha=0.5, color=COLOR_PALETTE['grid'])
    ax.set_ylim(0, max(counts) + (max(counts) * 0.2) if max(counts) > 0 else 5)
    
    ax.set_title("Slow Learners Threshold Analytics", fontsize=13, weight="bold", pad=15, color="#0F172A")
    
    sns.despine(ax=ax, top=True, right=True, left=True, bottom=False)
    ax.spines['bottom'].set_color('#CBD5E1')
    
    return fig
