import requests
from bs4 import BeautifulSoup
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Title of the app
st.title("Dollar to Pesos Exchange Rate")

# Input for the amount in dollars
dollars = st.number_input("Enter the amount of dollars you would like to exchange:", min_value=0.0, step=1.0)

# URL of the page to scrape
url = "https://bluedollar.net/informal-rate/"

# Function to fetch current exchange rates
def fetch_exchange_rates():
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        buy_rate_element = soup.find('div', class_='buy buy-sell-blue')
        sell_rate_element = soup.find('div', class_='sell buy-sell-blue')
        
        if buy_rate_element and sell_rate_element:
            buy_rate_str = buy_rate_element.get_text(strip=True).replace("Buy", "").strip()
            sell_rate_str = sell_rate_element.get_text(strip=True).replace("Sell", "").strip()
            buy_rate = float(buy_rate_str.replace(",", ""))
            sell_rate = float(sell_rate_str.replace(",", ""))
            return buy_rate, sell_rate
        else:
            st.error("Failed to find the buy or sell rate elements.")
            return None, None
    except Exception as e:
        st.error(f"Error fetching exchange rates: {e}")
        return None, None

# Function to fetch historical data
def fetch_historical_data():
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Use webdriver_manager to handle ChromeDriver installation
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)

        # Wait for chart to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "amcharts-chart-div"))
        )

        # Click the 1Y button
        button = driver.find_element(By.XPATH, "//input[@value='1Y']")
        button.click()
        time.sleep(3)  # Wait for the chart to update

        # Extract chart data
        chart_data = driver.execute_script("return AmCharts.charts[0].dataProvider || [];")

        if not chart_data:
            st.error("No chart data found.")
            return None

        # Process and return chart data
        return chart_data

    except Exception as e:
        st.error(f"Error in historical data extraction: {str(e)}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()

# Create two columns
col1, col2 = st.columns([1, 2])

# Button to fetch rates and calculate pesos
if st.button("Get Rates and Calculate Pesos"):
    with col1:
        buy_rate, sell_rate = fetch_exchange_rates()
        
        if buy_rate is not None and sell_rate is not None:
            pesos_received = dollars * buy_rate
            st.write(f"**Buy Rate:** {buy_rate}")
            st.write(f"**Sell Rate:** {sell_rate}")
            st.write(f"You will receive this many pesos: **{pesos_received:.2f}**")
    
    with col2:
        with st.spinner('Fetching historical data...'):
            historical_data = fetch_historical_data()
            
            if historical_data:
                try:
                    # Convert to DataFrame and show raw data
                    st.write("Raw data shape:", len(historical_data))
                    
                    df = pd.DataFrame(historical_data)
                    st.write("DataFrame head:", df.head())
                    st.write("DataFrame columns:", df.columns.tolist())
                    
                    # Try to create the chart
                    if 'date' in df.columns and 'value' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])  # Convert to datetime
                        st.line_chart(df.set_index('date')['value'])
                        st.caption("Historical Exchange Rate (Last 1 Year)")
                    else:
                        st.error("Data format incorrect. Expected 'date' and 'value' columns.")
                        st.write("Available columns:", df.columns.tolist())
                except Exception as e:
                    st.error(f"Error creating chart: {str(e)}")
                    st.write("Data type:", type(historical_data))
                    st.write("Data preview:", historical_data[:5])

# Add information about the data source
st.markdown("---")
st.markdown("Data source: [Blue Dollar](https://bluedollar.net/informal-rate/)")
