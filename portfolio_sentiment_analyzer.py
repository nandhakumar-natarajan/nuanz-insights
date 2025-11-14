"""
Portfolio Sentiment Analyzer using FinBERT
Reads portfolio data from Excel and analyzes sentiment for each stock
"""
import pandas as pd
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime
import requests
import os

class PortfolioSentimentAnalyzer:
    def __init__(self):
        print("Initializing FinBERT model...")
        # Load FinBERT model for financial sentiment analysis
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        print("FinBERT model loaded successfully!")
        
    def load_portfolio_data(self, excel_file):
        """Load portfolio data from Excel file"""
        try:
            # Try different sheet names
            df = None
            for sheet_name in [None, 0, 'Sheet1', 'Portfolio', 'Holdings']:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    print(f"Loaded data from sheet: {sheet_name}")
                    break
                except:
                    continue
            
            if df is None:
                raise Exception("Could not read Excel file")
                
            print(f"Portfolio data shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            return df
            
        except Exception as e:
            print(f"Error loading portfolio data: {e}")
            return None
    
    def get_sample_news(self, stock_symbol):
        """Generate sample financial news for demonstration"""
        sample_news = {
            'RELIANCE': "Reliance Industries reports strong quarterly earnings with 15% growth in digital services revenue",
            'TCS': "TCS wins major digital transformation deal worth $2.5 billion, stock rallies on positive outlook",
            'HDFCBANK': "HDFC Bank's Q3 results beat estimates with healthy loan growth and stable asset quality",
            'INFY': "Infosys raises revenue guidance for FY25, cites strong demand in AI and cloud services",
            'BHARTIARTL': "Bharti Airtel 5G rollout accelerates, subscriber base grows 8% quarter-on-quarter",
            'ITC': "ITC diversification strategy shows results with FMCG segment contributing 50% to revenue",
            'SBIN': "State Bank of India reports lowest bad loan ratio in 8 years, provisions decline significantly",
            'LT': "Larsen & Toubro bags Rs 15,000 crore infrastructure orders, order book reaches record high",
            'ASIANPAINT': "Asian Paints faces margin pressure due to raw material cost inflation, volumes remain steady",
            'MARUTI': "Maruti Suzuki electric vehicle strategy gains momentum with new model launches planned"
        }
        
        return sample_news.get(stock_symbol.upper(), f"{stock_symbol} shows stable performance with moderate market volatility")
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using FinBERT"""
        try:
            # Tokenize and get model predictions
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT labels: 0=negative, 1=neutral, 2=positive
            labels = ['negative', 'neutral', 'positive']
            scores = predictions[0].tolist()
            
            # Get the predicted sentiment
            predicted_class = torch.argmax(predictions, dim=-1).item()
            predicted_label = labels[predicted_class]
            confidence = scores[predicted_class]
            
            return {
                'sentiment': predicted_label,
                'confidence': confidence,
                'scores': {
                    'negative': scores[0],
                    'neutral': scores[1],
                    'positive': scores[2]
                }
            }
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'scores': {'negative': 0.3, 'neutral': 0.4, 'positive': 0.3}
            }
    
    def analyze_portfolio_sentiment(self, excel_file):
        """Analyze sentiment for entire portfolio"""
        # Load portfolio data
        df = self.load_portfolio_data(excel_file)
        if df is None:
            return None
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_summary': {
                'total_stocks': 0,
                'positive_sentiment': 0,
                'negative_sentiment': 0,
                'neutral_sentiment': 0,
                'overall_sentiment': 'neutral',
                'most_positive': None,
                'most_negative': None
            },
            'stock_sentiments': []
        }
        
        # Find stock symbol column (try different possible names)
        stock_column = None
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['symbol', 'stock', 'scrip', 'name', 'company']):
                stock_column = col
                break
        
        if stock_column is None:
            print("Could not find stock symbol column")
            stock_column = df.columns[0]  # Use first column as fallback
        
        print(f"Using column '{stock_column}' for stock symbols")
        
        # Analyze sentiment for each stock
        portfolio_sentiments = []
        
        for idx, row in df.iterrows():
            stock_symbol = str(row[stock_column]).strip()
            if pd.isna(stock_symbol) or stock_symbol == 'nan':
                continue
                
            # Get sample news for the stock
            news_text = self.get_sample_news(stock_symbol)
            
            # Analyze sentiment
            sentiment_result = self.analyze_sentiment(news_text)
            
            stock_data = {
                'symbol': stock_symbol,
                'news': news_text,
                'sentiment': sentiment_result['sentiment'],
                'confidence': round(sentiment_result['confidence'], 3),
                'scores': {k: round(v, 3) for k, v in sentiment_result['scores'].items()}
            }
            
            # Add weight/value if available
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['value', 'amount', 'weight', 'allocation']):
                    try:
                        stock_data['weight'] = float(row[col])
                        break
                    except:
                        pass
            
            portfolio_sentiments.append(stock_data)
            
            # Update counters
            if sentiment_result['sentiment'] == 'positive':
                results['portfolio_summary']['positive_sentiment'] += 1
            elif sentiment_result['sentiment'] == 'negative':
                results['portfolio_summary']['negative_sentiment'] += 1
            else:
                results['portfolio_summary']['neutral_sentiment'] += 1
        
        # Calculate overall portfolio sentiment
        results['portfolio_summary']['total_stocks'] = len(portfolio_sentiments)
        results['stock_sentiments'] = portfolio_sentiments
        
        # Find most positive and negative stocks
        if portfolio_sentiments:
            most_positive = max(portfolio_sentiments, key=lambda x: x['scores']['positive'])
            most_negative = max(portfolio_sentiments, key=lambda x: x['scores']['negative'])
            
            results['portfolio_summary']['most_positive'] = {
                'symbol': most_positive['symbol'],
                'news': most_positive['news'],
                'confidence': most_positive['scores']['positive']
            }
            
            results['portfolio_summary']['most_negative'] = {
                'symbol': most_negative['symbol'],
                'news': most_negative['news'],
                'confidence': most_negative['scores']['negative']
            }
            
            # Overall sentiment based on majority
            pos_count = results['portfolio_summary']['positive_sentiment']
            neg_count = results['portfolio_summary']['negative_sentiment']
            
            if pos_count > neg_count:
                results['portfolio_summary']['overall_sentiment'] = 'positive'
            elif neg_count > pos_count:
                results['portfolio_summary']['overall_sentiment'] = 'negative'
            else:
                results['portfolio_summary']['overall_sentiment'] = 'neutral'
        
        return results

def main():
    """Main function to analyze portfolio sentiment"""
    analyzer = PortfolioSentimentAnalyzer()
    
    # Analyze the hypothetical portfolio
    excel_file = "Portfolio Data_Hypothetical.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Portfolio file {excel_file} not found!")
        return None
    
    print(f"Analyzing portfolio sentiment from {excel_file}...")
    results = analyzer.analyze_portfolio_sentiment(excel_file)
    
    if results:
        # Save results to JSON file for the web dashboard
        output_file = "portfolio_sentiment_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Sentiment analysis complete! Results saved to {output_file}")
        print(f"Portfolio Summary:")
        print(f"- Total stocks: {results['portfolio_summary']['total_stocks']}")
        print(f"- Positive: {results['portfolio_summary']['positive_sentiment']}")
        print(f"- Negative: {results['portfolio_summary']['negative_sentiment']}")
        print(f"- Neutral: {results['portfolio_summary']['neutral_sentiment']}")
        print(f"- Overall sentiment: {results['portfolio_summary']['overall_sentiment']}")
        
        if results['portfolio_summary']['most_positive']:
            print(f"\nMost positive: {results['portfolio_summary']['most_positive']['symbol']}")
        if results['portfolio_summary']['most_negative']:
            print(f"Most negative: {results['portfolio_summary']['most_negative']['symbol']}")
        
        return results
    else:
        print("Failed to analyze portfolio sentiment")
        return None

if __name__ == "__main__":
    main()