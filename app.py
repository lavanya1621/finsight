import os
from dotenv import load_dotenv
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import re
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Set up the page
st.set_page_config(page_title="FINSIGHT", layout="wide")
st.title("FINSIGHT:  See the Trends. Make the Move.")
st.write("Enter any company. Uncover its stock story.")

load_dotenv()

def get_api_key():
    # First try to get from Streamlit secrets (for deployed app)
    if "openai_api_key" in st.secrets:
        return st.secrets["openai_api_key"]
    # Then try to get from environment variables (for local development)
    elif os.environ.get("OPENAI_API_KEY"):
        return os.environ.get("OPENAI_API_KEY")
    else:
        st.error("OpenAI API key not found. Please set it in .env file or Streamlit secrets.")
        st.stop()
llm = ChatOpenAI(model="gpt-4o")

# Agent 1: Company to Ticker Resolver
def resolve_ticker(company_name):
    prompt = f"""Given the company name "{company_name}", identify the most likely 
    stock ticker symbol. Return ONLY the ticker symbol, nothing else. 
    For example, if given "Apple", return "AAPL".
    If you're unsure, make your best guess.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    ticker = response.content.strip().upper()
    
    # Extract ticker using regex (looking for 1-5 capital letters)
    ticker_match = re.search(r'\b[A-Z]{1,5}\b', ticker)
    if ticker_match:
        ticker = ticker_match.group(0)
    
    return ticker

# Agent 2: Stock Data Analyzer
def analyze_stock(ticker, company_name):
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        company_info = stock.info
        
        # Get historical data for the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        hist_data = stock.history(start=start_date, end=end_date)
        
        if hist_data.empty:
            return None, f"Could not find data for ticker {ticker}. This might not be a valid company"
        
        # Prepare data for our analysis
        recent_price = hist_data['Close'].iloc[-1]
        price_start = hist_data['Close'].iloc[0]
        percent_change = ((recent_price - price_start) / price_start) * 100
        
        # Get company name from info if available, otherwise use the input name
        company_full_name = company_info.get('longName', company_name)
        
        # Collect key metrics
        data = {
            "ticker": ticker,
            "company_name": company_full_name,
            "current_price": recent_price,
            "yearly_change_percent": percent_change,
            "historical_data": hist_data,
            "market_cap": company_info.get('marketCap', 'Not available'),
            "company_info": company_info
        }
        
        return data, None
    
    except Exception as e:
        return None, f"Error retrieving data: {str(e)}"

# Function to generate insights based on stock data
def generate_insights(data):
    company_name = data['company_name']
    ticker = data['ticker']
    current_price = data['current_price']
    yearly_change = data['yearly_change_percent']
    hist_data = data['historical_data']
    
    # Calculate some simple metrics
    recent_50day_avg = hist_data['Close'][-50:].mean()
    recent_200day_avg = hist_data['Close'][-200:].mean() if len(hist_data) >= 200 else hist_data['Close'].mean()
    
    # Monthly performance
    monthly_change = ((hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-30]) / hist_data['Close'].iloc[-30]) * 100 if len(hist_data) > 30 else 0
    
    # Prepare prompt for insights
    prompt = f"""
    I need simple, easy-to-understand insights about {company_name} ({ticker}) stock for a non-financial person.
    
    Here's the relevant data:
    - Current stock price: ${current_price:.2f}
    - 1-year change: {yearly_change:.2f}%
    - 1-month change: {monthly_change:.2f}%
    - 50-day average price: ${recent_50day_avg:.2f}
    - 200-day average price: ${recent_200day_avg:.2f}
    - Market cap: {data['market_cap']}
    
    Please provide 3-4 insights that would help someone understand if this stock might be a good investment.
    Focus on:

    1.How the stock has been performing recently
    2.The overall trend (going up or down)
    3.Any notable patterns
    4.A simple recommendation (consider buying, maybe wait, or avoid for now)
    

    Avoid financial jargon. Write like you're explaining to a friend with no financial background.
    Add a one-sentence summary that captures the overall investment potential in plain language. Is this closer to a strong opportunity, proceed with caution, or not recommended?. 
    Be formal with your language and make it engaging for users to read.
    End with a simple FACT about the company that might surprise people.

    
    IMPORTANT: Do not use any special formatting, markdown, or symbols that might cause rendering issues.
    Use simple text formatting only. Use regular spaces between words. Avoid using asterisks, underscores, or other markdown formatting.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

# Function to format figure axes for better date display
def format_date_axis(fig, ax):
    # Rotate date labels and set them to appear monthly
    fig.autofmt_xdate()
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.tight_layout()
    return fig, ax

# Define a function to apply FINSIGHT styling to charts
def apply_finsight_style(fig, ax, title, y_label):
    # Set background color
    ax.set_facecolor('#f0f2f6')
    fig.set_facecolor('#ffffff')
    
    # Set grid style
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Set title and labels with better styling
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_ylabel(y_label, fontsize=12)
    
    # Set spines (borders)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_alpha(0.5)
    ax.spines['bottom'].set_alpha(0.5)
    
    return fig, ax

# Custom CSS to improve the app appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
    }
    .stProgress > div > div > div > div {
        background-color: #1E3A8A;
    }
    .stock-price {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .insights-header {
        color: #1E3A8A;
        font-size: 1.8rem;
        margin-top: 2rem;
    }
    .disclaimer {
        font-size: 0.8rem;
        color: #888888;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)





# Streamlit interface
company_name = st.text_input("Enter a company name:", "")

if company_name:
    with st.spinner(f"Finding ticker for {company_name}..."):
        # Step 1: Resolve ticker using Agent 1
        ticker = resolve_ticker(company_name)
        
        if ticker:
            st.info(f"Found the ticker for your company :) {ticker}")
            
            # Step 2: Analyze stock data using Agent 2
            with st.spinner(f"Looking into {ticker}..."):
                data, error = analyze_stock(ticker, company_name)
                
                if error:
                    st.error(error)
                elif data:
                    # Display basic info
                    st.header(f"{data['company_name']} ({ticker})")
                    st.markdown(f'<p class="stock-price">Current price: ${data["current_price"]:.2f}</p>', unsafe_allow_html=True)
                    
                    yearly_change = data['yearly_change_percent']
                    change_color = "green" if yearly_change > 0 else "red"
                    st.markdown(f"<p style='color:{change_color};'>Year change: {yearly_change:.2f}%</p>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    #Chart 1
                    with col1:
                        st.subheader("The Big Picture")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(data['historical_data'].index, data['historical_data']['Close'], color='#1E3A8A', linewidth=2)
                        fig, ax = apply_finsight_style(fig, ax, f"{ticker} - Past 12 Months Journey", "Price ($)")
                        fig, ax = format_date_axis(fig, ax)
                        st.pyplot(fig)
                    
                    #Chart 2
                    with col2:
                        st.subheader("Recent Story")
                        recent_data = data['historical_data'].iloc[-90:]
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.plot(recent_data.index, recent_data['Close'], color='#4338CA', linewidth=2)
                        fig, ax = apply_finsight_style(fig, ax, f"{ticker} - Last 5 Months Trend", "Price ($)")
                        fig, ax = format_date_axis(fig, ax)
                        st.pyplot(fig)
                    
                    #Chart 3
                    st.subheader(" Trading Activity")
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.bar(data['historical_data'].index, data['historical_data']['Volume'], color='#3B82F6', alpha=0.7)
                    fig, ax = apply_finsight_style(fig, ax, f"{ticker} - Trading Activity", "Volume")
                    fig, ax = format_date_axis(fig, ax)
                    st.pyplot(fig)
                    
                    # Generate insights
                    st.markdown('<p class="insights-header">✨ Your Finsights</p>', unsafe_allow_html=True)
                    with st.spinner("getting you your finsights...."):
                        insights = generate_insights(data)
                        st.write(insights)
                    
                    
                   
        else:
            st.error("Could not determine a ticker symbol for that company name.")