# **FinSight: Get Your Financial Insights**  

## **Overview**  
**FinSight** is a user-friendly stock analysis app that simplifies market insights. Just enter a company name, and **FinSight** will fetch its stock data, analyze past trends using AI, and present easy-to-understand insights. With engaging visuals, even beginners can navigate the stock market and make informed investment decisions.  

```mermaid
graph TD;
    A[User Inputs Company Name] --> B[Convert to Ticker Symbol];
    B --> C[Fetch Financial Data from Yahoo Finance];
    C --> D[Analyze Financial Metrics using OpenAI];
    D --> E[Generate Insights & Investment Signal];
    E --> F[Display Data & Charts on Streamlit];

## **Features**  

- **📊 Stock Data Analysis** – Fetches real-time stock data from **Yahoo Finance**, including current price, yearly change, and moving averages.  
- **🤖 AI-Powered Insights** – Uses **OpenAI's GPT-4o** to generate clear, actionable stock insights.  
- **📈 Dynamic Stock Charts** – Visualizes historical and recent stock performance with interactive charts.  
- **🎨 Clean & Intuitive UI** – Designed for readability and user engagement.  

## **Tech Stack**  

- **🛠 Programming Language:** Python  
- **💻 Frontend:** Streamlit  
- **⚙️ Backend:** LangChain, LangGraph, yFinance  
- **📊 Data Processing & Visualization:** Matplotlib  


