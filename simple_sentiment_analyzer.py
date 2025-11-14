"""
Simplified Portfolio Sentiment Analyzer 
Uses TextBlob for basic sentiment analysis as a fallback when FinBERT is not available
"""
import pandas as pd
import json
import os
from datetime import datetime

# Try to import textblob, install if not available
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    print("TextBlob not available, using rule-based sentiment analysis")

class SimplePortfolioSentimentAnalyzer:
    def __init__(self):
        print("Initializing Simple Sentiment Analyzer...")
        self.positive_words = ['growth', 'strong', 'beat', 'rally', 'positive', 'win', 'profit', 'gain', 'high', 'good', 'excellent', 'bullish', 'surge', 'rise']
        self.negative_words = ['decline', 'fall', 'loss', 'weak', 'pressure', 'drop', 'bad', 'poor', 'bearish', 'crash', 'volatility', 'concern']
        
    def load_portfolio_data(self, excel_file):
        """Load portfolio data from Excel file"""
        try:
            # Read the Excel file
            df = pd.read_excel(excel_file)
            print(f"Loaded data from Excel file")
            print(f"Portfolio data shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            return df
            
        except Exception as e:
            print(f"Error loading portfolio data: {e}")
            return None
    
    def get_sample_news(self, stock_symbol):
        """Generate sample financial news for demonstration"""
        sample_news = {
            'GOLD1': "Gold ETF sees strong inflows as investors seek safe haven assets amid market uncertainty",
            'NATIONALUM': "National Aluminium Company reports record production levels, strong demand from automotive sector",
            'OIL': "Oil and Natural Gas Corporation discovers new reserves, production outlook remains positive",
            'MOTILAL': "Motilal Oswal Large and Midcap Fund outperforms benchmark with strong stock selection strategy",
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
        
        # Clean the stock symbol and try to match
        clean_symbol = stock_symbol.upper().replace(' ', '').replace('.', '')
        for key in sample_news:
            if key in clean_symbol or clean_symbol in key:
                return sample_news[key]
        
        return f"{stock_symbol} shows stable performance with moderate market volatility and steady investor interest"
    
    def simple_sentiment_analysis(self, text):
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.6 + (positive_count - negative_count) * 0.1, 0.95)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(0.6 + (negative_count - positive_count) * 0.1, 0.95)
        else:
            sentiment = 'neutral'
            confidence = 0.5
            
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'scores': {
                'positive': confidence if sentiment == 'positive' else 1 - confidence,
                'negative': confidence if sentiment == 'negative' else (1 - confidence) / 2,
                'neutral': confidence if sentiment == 'neutral' else (1 - confidence) / 2
            }
        }
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using available method"""
        if HAS_TEXTBLOB:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # -1 to 1
                
                if polarity > 0.1:
                    sentiment = 'positive'
                    confidence = min(0.5 + polarity * 0.5, 0.95)
                elif polarity < -0.1:
                    sentiment = 'negative'
                    confidence = min(0.5 + abs(polarity) * 0.5, 0.95)
                else:
                    sentiment = 'neutral'
                    confidence = 0.5 + abs(polarity) * 0.3
                
                return {
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'scores': {
                        'positive': max(0, polarity + 0.5) if sentiment != 'negative' else 0.2,
                        'negative': max(0, -polarity + 0.5) if sentiment != 'positive' else 0.2,
                        'neutral': 0.6 if sentiment == 'neutral' else 0.3
                    }
                }
            except:
                pass
        
        # Fallback to simple rule-based analysis
        return self.simple_sentiment_analysis(text)
    
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
        
        # Find stock symbol column - use "Instrument" column from the portfolio
        stock_column = 'Instrument'
        if stock_column not in df.columns:
            # Fallback to first column
            stock_column = df.columns[0]
        
        print(f"Using column '{stock_column}' for stock symbols")
        
        # Analyze sentiment for each stock
        portfolio_sentiments = []
        
        for idx, row in df.iterrows():
            if idx >= 20:  # Limit to first 20 stocks for demo
                break
                
            stock_symbol = str(row[stock_column]).strip()
            if pd.isna(stock_symbol) or stock_symbol == 'nan' or stock_symbol == '':
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
                if any(keyword in col.lower() for keyword in ['value', 'amount', 'weight', 'allocation', 'market']):
                    try:
                        value = row[col]
                        if pd.notna(value) and str(value).replace('.', '').replace(',', '').isdigit():
                            stock_data['weight'] = float(str(value).replace(',', ''))
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
    analyzer = SimplePortfolioSentimentAnalyzer()
    
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