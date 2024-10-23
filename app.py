import pandas as pd
import streamlit as st
import os

# Load the data from Excel files
inflation_data = pd.read_excel('Inflation_event_stock_analysis_resultsOct.xlsx')
income_data = pd.read_excel('Inflation_IncomeStatement_correlation_results.xlsx')
interest_rate_data = pd.read_excel('interestrate_event_stock_analysis_resultsOct.xlsx')
interest_rate_income_data = pd.read_excel('interestrate_IncomeStatement_correlation_results.xlsx')

# Set up Streamlit app
st.title('Stock Analysis Based on Economic Events')

# Create a sidebar for user input
st.sidebar.header('Search for a Stock')
event_type = st.sidebar.selectbox('Select Event Type:', ['Inflation', 'Interest Rate'])
stock_name = st.sidebar.text_input('Enter Stock Symbol:', '')
expected_rate = st.sidebar.number_input('Enter Expected Upcoming Rate (%):', value=3.65, step=0.01)
calculation_method = st.sidebar.selectbox('Select Calculation Method:', ['Dynamic', 'Simple'])

# Function to fetch details for a specific stock based on the event type
def get_stock_details(stock_symbol, event_type, method):
    if event_type == 'Inflation':
        event_row = inflation_data[inflation_data['Symbol'] == stock_symbol]
        income_row = income_data[income_data['Stock Name'] == stock_symbol]
    else:  # Interest Rate
        event_row = interest_rate_data[interest_rate_data['Symbol'] == stock_symbol]
        income_row = interest_rate_income_data[interest_rate_income_data['Stock Name'] == stock_symbol]
    
    if not event_row.empty and not income_row.empty:
        event_details = event_row.iloc[0]
        income_details = income_row.iloc[0]
        
        st.subheader(f'Details for {stock_symbol}')
        
        # Display event data
        st.write(f"### {event_type} Event Data")
        st.write(event_row)
        
        # Display income statement data
        st.write("### Income Statement Data")
        st.write(income_row)
        
        # Load and display additional income statement data
        display_income_statement(stock_symbol)

        # Generate projections based on expected rate
        projections = generate_projections(event_details, income_details, expected_rate, event_type, method)

        # Display projections
        st.write(f"### Projected Changes Based on Expected {event_type}")
        st.dataframe(projections)

        # Additional interpretations based on conditions
        if event_type == 'Inflation':
            interpret_inflation_data(event_details)
        else:
            interpret_interest_rate_data(event_details)

        interpret_income_data(income_details)
    else:
        st.warning('Stock symbol not found in the data. Please check the symbol and try again.')

# Function to display income statement data from the incomestatement folder
def display_income_statement(stock_symbol):
    file_path = f'incomestatement/{stock_symbol}.csv'
    if os.path.exists(file_path):
        income_statement_data = pd.read_csv(file_path)
        st.write("### Detailed Income Statement")
        st.dataframe(income_statement_data)
    else:
        st.warning(f'Income statement data for {stock_symbol} not found.')

# Function to interpret inflation data
def interpret_inflation_data(details):
    st.write("### Interpretation of Inflation Event Data")
    if 'Event Coefficient' in details.index:
        if details['Event Coefficient'] < -1:
            st.write("**1% Increase in Inflation:** Stock price decreases significantly. Increase portfolio risk.")
        elif details['Event Coefficient'] > 1:
            st.write("**1% Increase in Inflation:** Stock price increases, benefiting from inflation.")
    else:
        st.warning("Event Coefficient not found in inflation details.")

# Function to interpret interest rate data
def interpret_interest_rate_data(details):
    st.write("### Interpretation of Interest Rate Event Data")
    if 'Event Coefficient' in details.index:
        if details['Event Coefficient'] < -1:
            st.write("**1% Increase in Interest Rate:** Stock price decreases significantly. Increase portfolio risk.")
        elif details['Event Coefficient'] > 1:
            st.write("**1% Increase in Interest Rate:** Stock price increases, benefiting from interest hikes.")
    else:
        st.warning("Event Coefficient not found in interest rate details.")

# Function to interpret income data
def interpret_income_data(details):
    st.write("### Interpretation of Income Statement Data")
    if 'Average Operating Margin' in details.index:
        average_operating_margin = details['Average Operating Margin']
        if average_operating_margin > 0.2:
            st.write("**High Operating Margin:** Indicates strong management effectiveness.")
        elif average_operating_margin < 0.1:
            st.write("**Low Operating Margin:** Reflects risk in profitability.")

# Function to generate projections based on expected rate and calculation method
def generate_projections(event_details, income_details, expected_rate, event_type, method):
    latest_event_value = pd.to_numeric(income_details.get('Latest Event Value', 0), errors='coerce')
    projections = pd.DataFrame(columns=['Parameter', 'Current Value', 'Projected Value', 'Change'])

    if 'Latest Close Price' in event_details.index:
        latest_close_price = pd.to_numeric(event_details['Latest Close Price'], errors='coerce')

        if method == 'Dynamic':
            rate_change = expected_rate - latest_event_value
            price_change = event_details['Event Coefficient'] * rate_change
            projected_price = latest_close_price + price_change
            change = price_change
            explanation = "Dynamic calculation considers the event coefficient and rate change."
        else:  # Simple
            price_change = latest_close_price * (expected_rate / 100)
            projected_price = latest_close_price + price_change
            change = expected_rate
            explanation = "Simple calculation uses the expected rate directly."

        new_row = pd.DataFrame([{
            'Parameter': 'Projected Stock Price',
            'Current Value': latest_close_price,
            'Projected Value': projected_price,
            'Change': change
        }])
        projections = pd.concat([projections, new_row], ignore_index=True)
    else:
        st.warning("Stock Price data not available in event details.")

    # Project changes in new income statement items
    for column in income_details.index:
        if column != 'Stock Name':
            current_value = pd.to_numeric(income_details[column], errors='coerce')
            if pd.notna(current_value):
                if method == 'Dynamic':
                    if column in event_details.index:
                        correlation_factor = event_details[column] if column in event_details.index else 0
                        projected_value = current_value + (current_value * correlation_factor * (expected_rate - latest_event_value) / 100)
                    else:
                        projected_value = current_value * (1 + (expected_rate - latest_event_value) / 100)
                    change = projected_value - current_value
                else:  # Simple
                    projected_value = current_value * (1 + expected_rate / 100)
                    change = expected_rate

                new_row = pd.DataFrame([{
                    'Parameter': column,
                    'Current Value': current_value,
                    'Projected Value': projected_value,
                    'Change': change
                }])
                projections = pd.concat([projections, new_row], ignore_index=True)

    # Include the new columns for June 2024 in the projections
    new_columns = [
        'June 2024 Total Revenue/Income',
        'June 2024 Total Operating Expense',
        'June 2024 Operating Income/Profit',
        'June 2024 EBITDA',
        'June 2024 EBIT',
        'June 2024 Income/Profit Before Tax',
        'June 2024 Net Income From Continuing Operation',
        'June 2024 Net Income',
        'June 2024 Net Income Applicable to Common Share',
        'June 2024 EPS (Earning Per Share)'
    ]

    for col in new_columns:
        if col in income_details.index:
            current_value = pd.to_numeric(income_details[col], errors='coerce')
            if pd.notna(current_value):
                if method == 'Dynamic':
                    projected_value = current_value * (1 + (expected_rate - latest_event_value) / 100)
                else:  # Simple
                    projected_value = current_value * (1 + expected_rate / 100)

                new_row = pd.DataFrame([{
                    'Parameter': col,
                    'Current Value': current_value,
                    'Projected Value': projected_value,
                    'Change': expected_rate
                }])
                projections = pd.concat([projections, new_row], ignore_index=True)

    # Display the explanation for the chosen calculation method
    st.write(f"**Explanation of Calculation Method:** {explanation}")

    return projections

# Check if user has entered a stock symbol and selected an event
if stock_name and event_type:
    get_stock_details(stock_name, event_type, calculation_method)
