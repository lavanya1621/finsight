# app.py
import streamlit as st
import yfinance as yf
from openai import OpenAI
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated, Literal
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Initialize OpenAI client safely
api_key = os.getenv("OPENAI_API_KEY")
try:
    if not api_key and hasattr(st, "secrets"):
        api_key = st.secrets.get("OPENAI_API_KEY")
except Exception:
    pass

if not api_key:
    st.error("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable or add it to your Streamlit secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# Define state types
class AgentState(TypedDict):
    company_name: str
    ticker: str
    financial_data: dict
    recommendation: str
    signal: Literal["GREEN", "YELLOW", "RED"]
    insights: list

# Agent 1: Company Name to Ticker
def company_to_ticker(state: AgentState) -> AgentState:
    company_name = state["company_name"]
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a financial assistant. Your task is to convert a company name to its stock ticker symbol. Respond with ONLY the ticker symbol in uppercase."},
            {"role": "user", "content": f"What is the stock ticker symbol for {company_name}?"}
        ]
    )
    
    ticker = response.choices[0].message.content.strip()
    st.session_state.ticker = ticker  # Store in session state for display
    
    return {"company_name": company_name, "ticker": ticker}

# Agent 2: Financial Analysis
def analyze_financials(state: AgentState) -> AgentState:
    ticker = state["ticker"]
    company_name = state["company_name"]
    
    try:
        # Fetch data from yfinance
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key financial metrics
        financial_data = {
            "currentPrice": info.get("currentPrice", 0),
            "targetMeanPrice": info.get("targetMeanPrice", 0),
            "recommendationMean": info.get("recommendationMean", 0),
            "returnOnEquity": info.get("returnOnEquity", 0),
            "debtToEquity": info.get("debtToEquity", 0),
            "revenueGrowth": info.get("revenueGrowth", 0),
            "earningsGrowth": info.get("earningsGrowth", 0),
            "profitMargins": info.get("profitMargins", 0)
        }
        
        # Generate insights and recommendation using OpenAI
        prompt = f"""
        Analyze {company_name} ({ticker}) based on these financial metrics:
        Current Price: ${financial_data['currentPrice']}
        Target Price: ${financial_data['targetMeanPrice']}
        Recommendation Mean (1-5, 1 is Strong Buy): {financial_data['recommendationMean']}
        Return on Equity: {financial_data['returnOnEquity']*100 if financial_data['returnOnEquity'] else 'N/A'}%
        Debt to Equity: {financial_data['debtToEquity'] if financial_data['debtToEquity'] else 'N/A'}
        Revenue Growth: {financial_data['revenueGrowth']*100 if financial_data['revenueGrowth'] else 'N/A'}%
        Earnings Growth: {financial_data['earningsGrowth']*100 if financial_data['earningsGrowth'] else 'N/A'}%
        Profit Margins: {financial_data['profitMargins']*100 if financial_data['profitMargins'] else 'N/A'}%
        
        Provide exactly 4 key insights about this company's financial health. Make the insights such that a beginner investor can understand them.
        Then give an investment recommendation as either GREEN (strong buy), YELLOW (cautious buy/hold), or RED (avoid).
        Format your response as a JSON with two fields: "insights" (an array of 4 strings) and "signal" (either "GREEN", "YELLOW", or "RED").
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a financial advisor providing precise investment recommendations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        analysis = eval(response.choices[0].message.content.strip())
        
        return {
            "company_name": company_name,
            "ticker": ticker,
            "financial_data": financial_data,
            "insights": analysis["insights"],
            "signal": analysis["signal"]
        }
    
    except Exception as e:
        return {
            "company_name": company_name,
            "ticker": ticker,
            "financial_data": {},
            "insights": ["Error fetching financial data."],
            "signal": "YELLOW"
        }

# Function to get stock price history and create visualizations
def get_stock_history(ticker):
    end_date = datetime.now()
    
    # 12-month data
    start_date_12m = end_date - timedelta(days=365)
    data_12m = yf.download(ticker, start=start_date_12m, end=end_date)
    
    # 3-month data
    start_date_3m = end_date - timedelta(days=90)
    data_3m = yf.download(ticker, start=start_date_3m, end=end_date)
    
    return data_12m, data_3m

# Function to plot stock prices
def plot_stock_charts(data_12m, data_3m, ticker):
    # Create 12-month chart
    fig_12m, ax_12m = plt.subplots(figsize=(10, 6))
    ax_12m.plot(data_12m['Close'])
    ax_12m.set_title(f'{ticker} - 12 Month Stock Price')
    ax_12m.set_ylabel('Price (USD)')
    ax_12m.grid(True)
    st.pyplot(fig_12m)
    
    # Create 3-month chart
    fig_3m, ax_3m = plt.subplots(figsize=(10, 6))
    ax_3m.plot(data_3m['Close'])
    ax_3m.set_title(f'{ticker} - 3 Month Stock Price')
    ax_3m.set_ylabel('Price (USD)')
    ax_3m.grid(True)
    st.pyplot(fig_3m)

# Build the graph
def build_graph():
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("company_to_ticker", company_to_ticker)
    graph.add_node("analyze_financials", analyze_financials)
    
    # Add edges
    graph.set_entry_point("company_to_ticker")
    graph.add_edge("company_to_ticker", "analyze_financials")
    graph.set_finish_point("analyze_financials")
    
    return graph.compile()

# Streamlit UI
st.title("FinSight - See the Trends. Make the Move.")

with st.form("company_form"):
    company_name = st.text_input("Enter a company name:")
    submitted = st.form_submit_button("Analyze")
    
    if submitted and company_name:
        # Initialize and run the graph
        workflow = build_graph()
        result = workflow.invoke({"company_name": company_name})
        
        # Display results
        st.subheader(f"{result['company_name']} ({result['ticker']})")
        
        # Display signal with appropriate color
        signal_color = {
            "GREEN": "green",
            "YELLOW": "orange",
            "RED": "red"
        }
        
        st.markdown(f"### Investment Signal: <span style='color:{signal_color[result['signal']]}'>{result['signal']}</span>", unsafe_allow_html=True)
        
        # Display insights
        st.subheader("Key Insights:")
        for i, insight in enumerate(result['insights'], 1):
            st.write(f"{i}. {insight}")
        
        # Display financial metrics
        if result['financial_data']:
            st.subheader("Financial Metrics:")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Current Price", f"${result['financial_data']['currentPrice']}")
                st.metric("Target Price", f"${result['financial_data']['targetMeanPrice']}")
                st.metric("ROE", f"{result['financial_data']['returnOnEquity']*100 if result['financial_data']['returnOnEquity'] else 'N/A'}%")
                st.metric("Profit Margin", f"{result['financial_data']['profitMargins']*100 if result['financial_data']['profitMargins'] else 'N/A'}%")
            
            with col2:
                st.metric("Debt to Equity", result['financial_data']['debtToEquity'])
                st.metric("Revenue Growth", f"{result['financial_data']['revenueGrowth']*100 if result['financial_data']['revenueGrowth'] else 'N/A'}%")
                st.metric("Earnings Growth", f"{result['financial_data']['earningsGrowth']*100 if result['financial_data']['earningsGrowth'] else 'N/A'}%")
                rec_mean = result['financial_data']['recommendationMean']
                st.metric("Analyst Rating", f"{rec_mean}/5 (1 is Strong Buy)")
        
        # Display stock price charts
        st.subheader("Stock Price History")
        
        with st.spinner("Loading stock price data..."):
            try:
                # Get stock price data
                data_12m, data_3m = get_stock_history(result['ticker'])
                
                # Plot the charts
                plot_stock_charts(data_12m, data_3m, result['ticker'])
                
            except Exception as e:
                st.error(f"Error loading stock data: {str(e)}")