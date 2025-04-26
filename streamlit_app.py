import streamlit as st
import numpy as np
from scipy.optimize import fsolve
import plotly.graph_objects as go
from datetime import datetime, date
import pandas as pd

st.title('Migration Capacity Calculator')

st.write('Calculate the required monthly migration rate based on total capacity and timeframe.')

def evaluate_formula(formula, x):
    """Evaluate the formula with the given x value"""
    try:
        # Create a safe local environment with basic math functions
        safe_dict = {
            'x': x,
            'abs': abs,
            'pow': pow,
            'round': round,
            'min': min,
            'max': max,
            'np.sin': np.sin,
            'np.cos': np.cos,
            'np.tan': np.tan,
            'np.exp': np.exp,
            'np.log': np.log,
            'np.sqrt': np.sqrt
        }
        return eval(formula, {"__builtins__": {}}, safe_dict)
    except Exception as e:
        st.error(f'Error evaluating formula: {str(e)}')
        return None

def goal_seek(formula, target):
    """Find x value that makes formula equal target"""
    def objective(x):
        return evaluate_formula(formula, x) - target
    
    try:
        result = fsolve(objective, 0)[0]
        return result
    except Exception as e:
        st.error(f'Error in goal seek calculation: {str(e)}')
        return None

# UI Components
# Create one tab
tab1, = st.tabs(["Migration Calculator"])

with tab1:
    # Migration Calculator Inputs
    col1, col2 = st.columns([4, 1])
    with col1:
        with st.sidebar:
            # Date input for month/year selection
            current_date = date.today()
            min_date = date(current_date.year, current_date.month, 2)  # 2 years back
            max_date = date(2030, 3, 1)  # Extend to March 2030
            start_date = st.date_input('MIGRATION: Select start month:', min_value=min_date, max_value=max_date, value=date(2025, 7, 1))
            start_date = start_date.replace(day=1)  # Always use first day of the month
            
            # Date input for end month selection
            end_date = st.date_input('MIGRATION: Select end month:', min_value=min_date, max_value=max_date, value=date(2026, 6, 1))
            end_date = end_date.replace(day=1)  # Always use first day of the month

             # Date input for end of simulation
            end_simulation_date = st.slider('SIMULATION: Select end of simulation:', min_value=min_date, max_value=date(2030, 3, 15), value=date(2030, 3, 15), format='MMM YYYY')
            end_simulation_date = end_simulation_date.replace(day=1)  # Always use first day of the month

           
            
            # Calculate number of months
            num_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1

            # Number input for total capacity and target values
            total_capacity = st.number_input('Total capacity to migrate (TB):', min_value=0.0, value=3100.0, help='Para un mejor entendimiento rellena con el valor de un único CPD. El plan de migración será el mismo para el segundo CPD')
            target_value = st.number_input('Target remaining capacity (TB):', min_value=0.0, value=0.0)

            # Number input for added TB per month
            added_tb_per_month = st.number_input('Added TB per month:', min_value=0.0, value=60.0)

            if st.button('Reset Inputs', key='reset_inputs'):
                st.session_state['start_date'] = date.today()
                st.session_state['num_months'] = 12
                st.session_state['total_capacity'] = 100.0
                st.session_state['target_value'] = 0.0
                st.rerun()

    # Set up the formula for monthly migration rate
    formula = f'{total_capacity} - {num_months}*x'
    st.write(f'Formula: {formula}')

 #   added_tb_per_month = st.number_input('Added TB per month:', min_value=0.0, value=0.0)
    if st.button('Calculate Monthly Rate'):
        if num_months > 0 and total_capacity >= 0:
            result = goal_seek(formula, target_value)
            if result is not None:
                st.info(f'Required monthly migration rate: {result:.2f} TB/month')
                #st.write(f'Total capacity: {total_capacity} TB')
                #st.write(f'Target remaining capacity: {target_value} TB')
                st.info(f'Number of months to finish migration: {num_months}')
                #st.write(f'Monthly rate × months = {result * num_months:.2f} TB')
                
                # Generate data for the line chart with actual months
                months = []
                current_month = start_date
                while current_month <= end_simulation_date:
                    months.append(current_month)
                    next_month = current_month.month % 12 + 1
                    next_year = current_month.year + (current_month.month // 12)
                    current_month = current_month.replace(month=next_month, year=next_year)
                month_labels = [month.strftime('%b %Y') for month in months]
                remaining_capacity = [max(total_capacity - (result * i), 0) for i in range(1, len(months) + 1)]
                
                # Create the bar chart using Plotly
                fig = go.Figure()
                
                # Existing trace for Remaining Capacity
                fig.add_trace(go.Bar(
                    x=month_labels, 
                    y=remaining_capacity, 
                    name='Remaining Capacity',
                    marker_color=['blue' if datetime.strptime(label, '%b %Y') <= datetime(2026, 6, 30) else 'red' for label in month_labels]
                ))
                
                # New trace for Total Capacity - Remaining Capacity
                migrated_capacity = [total_capacity - cap for cap in remaining_capacity]
                fig.add_trace(go.Bar(
                    x=month_labels, 
                    y=migrated_capacity, 
                    name='Migrated Capacity',
                    marker_color='orange'
                ))
                
                # New trace for Added TB per month
                added_capacity = [added_tb_per_month * i for i in range(1, len(migrated_capacity) + 1)]
                fig.add_trace(go.Bar(
                    x=month_labels,
                    y=added_capacity,
                    name='Added Capacity',
                    marker_color='green'
                ))
                
                fig.add_trace(go.Scatter(
                    x=month_labels,
                    y=[migrated_capacity[i] + added_capacity[i] for i in range(len(month_labels))],
                    mode='lines+markers',
                    name='Total Capacity',
                    line=dict(color='purple')
                ))
                
                fig.update_layout(
                    title='Capacity Migration Over Time',
                    xaxis_title='Month',
                    yaxis_title='Capacity (TB)',
                    showlegend=True,
                    barmode='group'
                )
                
                st.plotly_chart(fig)
                
                # Create a data table with the monthly values
                data = {
                    'End of Month': month_labels,
                    'Remaining Capacity (TB)': [f'{cap:.2f}' for cap in remaining_capacity],
                    'Migrated Capacity (TB)': [f'{cap:.2f}' for cap in migrated_capacity],
                    'Added Capacity (TB)': [f'{cap:.2f}' for cap in added_capacity],
                    'Total Capacity (TB)': [f'{migrated_capacity[i] + added_capacity[i]:.2f}' for i in range(len(month_labels))]
                }
                # Enhance the table display with Streamlit's DataFrame styling
                styled_data = pd.DataFrame(data).style
                styled_data = styled_data.set_table_styles(
                    [
                        {'selector': 'thead th', 'props': [('font-weight', 'bold'), ('background-color', '#f0f0f0')]},
                        {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]},
                        {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]}
                    ]
                )
                
                # Display the styled table
                st.write('Monthly Capacity Values:')
                st.dataframe(styled_data)
        else:
            st.error('Please enter valid values for months and capacity')