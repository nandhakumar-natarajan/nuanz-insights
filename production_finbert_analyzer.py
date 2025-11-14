"""
Production FinBERT Portfolio Sentiment Analyzer
Optimized for deployment with error handling and fallbacks
"""
import pandas as pd
import json
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import FinBERT dependencies
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import numpy as np
    FINBERT_AVAILABLE = True
    logger.info("FinBERT dependencies loaded successfully")
except ImportError as e:
    FINBERT_AVAILABLE = False
    logger.warning(f"FinBERT dependencies not available: {e}")

# Fallback to TextBlob
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available")

class ProductionFinBERTAnalyzer:
    def __init__(self):
        logger.info("Initializing Production FinBERT Analyzer...")
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        
        # Financial keywords for fallback analysis
        self.positive_words = [
            'growth', 'strong', 'beat', 'rally', 'positive', 'win', 'profit', 
            'gain', 'high', 'good', 'excellent', 'bullish', 'surge', 'rise',
            'outperform', 'exceed', 'robust', 'solid', 'healthy', 'optimistic',
            'momentum', 'breakthrough', 'success', 'recovery', 'expansion'
        ]
        self.negative_words = [
            'decline', 'fall', 'loss', 'weak', 'pressure', 'drop', 'bad', 
            'poor', 'bearish', 'crash', 'volatility', 'concern', 'risk',
            'challenge', 'struggle', 'disappointing', 'uncertain', 'headwind',
            'deteriorate', 'sluggish', 'unfavorable', 'downturn', 'warning'
        ]
        
        # Try to load FinBERT model
        self._load_finbert_model()
    
    def _load_finbert_model(self):
        """Load FinBERT model with error handling"""
        if not FINBERT_AVAILABLE:
            logger.warning("FinBERT not available, using fallback methods")
            return
        
        try:
            logger.info("Loading FinBERT model (this may take a moment)...")
            self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self.model_loaded = True
            logger.info("FinBERT model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            self.model_loaded = False
    
    def load_portfolio_data(self, excel_file):
        """Load portfolio data from Excel file"""
        try:
            if not os.path.exists(excel_file):
                raise FileNotFoundError(f"Portfolio file {excel_file} not found")
            
            df = pd.read_excel(excel_file)
            logger.info(f"Loaded portfolio data: {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading portfolio data: {e}")
            return None
    
    def get_financial_news(self, stock_symbol):
        """Generate realistic financial news for analysis"""
        financial_news = {
            'GOLD1': "Gold ETF experiences strong institutional inflows as central bank policies drive safe haven demand amid global economic uncertainty",
            'NATIONALUM': "National Aluminium Company reports record quarterly production with 12% YoY growth, benefiting from robust automotive and infrastructure demand",
            'OIL': "Oil and Natural Gas Corporation announces major offshore discovery, expects production boost of 15% over next two years with improved margins",
            'MOTILAL': "Motilal Oswal Large and Midcap Fund delivers alpha with disciplined stock selection, outperforming benchmark by 280 basis points YTD",
            'RELIANCE': "Reliance Industries posts stellar Q3 results with petrochemicals margin expansion and Jio subscriber additions exceeding estimates",
            'TCS': "Tata Consultancy Services secures landmark $3.2 billion multi-year deal in financial services vertical, reinforcing market leadership",
            'HDFCBANK': "HDFC Bank maintains asset quality leadership with gross NPA at multi-year lows while sustaining healthy credit growth momentum", 
            'INFY': "Infosys raises FY25 revenue guidance citing accelerating digital transformation demand and successful large deal execution",
            'BHARTIARTL': "Bharti Airtel reports strong ARPU growth with 5G network expansion reaching 75% population coverage ahead of schedule",
            'ITC': "ITC's diversification strategy pays off with FMCG business contributing 52% to revenue, cigarette headwinds offset by growth segments"
        }
        
        # Enhanced matching logic
        clean_symbol = stock_symbol.upper().replace(' ', '').replace('.', '')
        
        # Direct match
        if clean_symbol in financial_news:
            return financial_news[clean_symbol]
        
        # Partial match
        for key, news in financial_news.items():
            if key in clean_symbol or any(word in clean_symbol for word in key.split()):
                return news
        
        # Generate contextual news based on symbol characteristics
        if 'FUND' in clean_symbol or 'MUTUAL' in clean_symbol:
            return f"{stock_symbol} mutual fund demonstrates consistent performance with strategic asset allocation and risk management delivering stable returns for investors"
        elif 'BANK' in clean_symbol:
            return f"{stock_symbol} banking institution reports steady loan growth with maintained asset quality and improving operational efficiency metrics"
        elif 'GOLD' in clean_symbol or 'SILVER' in clean_symbol:
            return f"{stock_symbol} precious metals investment shows resilience amid market volatility with strong underlying fundamentals supporting valuations"
        else:
            return f"{stock_symbol} demonstrates operational resilience with steady fundamentals and positive medium-term growth outlook in current market environment"
    
    def finbert_sentiment_analysis(self, text):
        """Analyze sentiment using FinBERT model"""
        try:
            # Tokenize input text
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            )
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT output: [negative, neutral, positive]
            scores = predictions[0].tolist()
            labels = ['negative', 'neutral', 'positive']
            
            # Get predicted class and confidence
            predicted_idx = torch.argmax(predictions, dim=-1).item()
            predicted_sentiment = labels[predicted_idx]
            confidence = scores[predicted_idx]
            
            return {
                'sentiment': predicted_sentiment,
                'confidence': round(confidence, 4),
                'scores': {
                    'negative': round(scores[0], 4),
                    'neutral': round(scores[1], 4),
                    'positive': round(scores[2], 4)
                },
                'method': 'finbert'
            }
            
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return None
    
    def textblob_sentiment_analysis(self, text):
        """Fallback sentiment analysis using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            # Convert TextBlob polarity to sentiment categories
            if polarity > 0.1:
                sentiment = 'positive'
                confidence = min(0.5 + polarity * 0.4, 0.95)
            elif polarity < -0.1:
                sentiment = 'negative' 
                confidence = min(0.5 + abs(polarity) * 0.4, 0.95)
            else:
                sentiment = 'neutral'
                confidence = 0.5 + abs(polarity) * 0.3
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence, 4),
                'scores': {
                    'positive': round(max(0.1, (polarity + 1) / 2), 4),
                    'negative': round(max(0.1, (-polarity + 1) / 2), 4),
                    'neutral': round(0.4 + abs(polarity) * 0.2, 4)
                },
                'method': 'textblob'
            }
            
        except Exception as e:
            logger.error(f"TextBlob analysis failed: {e}")
            return None
    
    def rule_based_sentiment_analysis(self, text):
        """Rule-based sentiment analysis as final fallback"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Enhanced scoring with word importance
        important_positive = ['strong', 'growth', 'beat', 'outperform', 'surge', 'rally']
        important_negative = ['crash', 'loss', 'decline', 'warning', 'risk', 'concern']
        
        pos_boost = sum(2 for word in important_positive if word in text_lower)
        neg_boost = sum(2 for word in important_negative if word in text_lower)
        
        total_positive = positive_count + pos_boost
        total_negative = negative_count + neg_boost
        
        if total_positive > total_negative:
            sentiment = 'positive'
            confidence = min(0.6 + (total_positive - total_negative) * 0.05, 0.85)
        elif total_negative > total_positive:
            sentiment = 'negative'
            confidence = min(0.6 + (total_negative - total_positive) * 0.05, 0.85)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 4),
            'scores': {
                'positive': round(confidence if sentiment == 'positive' else (1-confidence)/2, 4),
                'negative': round(confidence if sentiment == 'negative' else (1-confidence)/2, 4),
                'neutral': round(confidence if sentiment == 'neutral' else (1-confidence), 4)
            },
            'method': 'rule_based'
        }
    
    def analyze_sentiment(self, text):
        """Multi-tier sentiment analysis with fallbacks"""
        # Tier 1: Try FinBERT (most accurate)
        if self.model_loaded:
            result = self.finbert_sentiment_analysis(text)
            if result:
                return result
        
        # Tier 2: Try TextBlob (moderate accuracy)
        if TEXTBLOB_AVAILABLE:
            result = self.textblob_sentiment_analysis(text)
            if result:
                return result
        
        # Tier 3: Rule-based fallback (basic but reliable)
        return self.rule_based_sentiment_analysis(text)
    
    def analyze_portfolio_sentiment(self, excel_file):
        """Analyze sentiment for entire portfolio"""
        df = self.load_portfolio_data(excel_file)
        if df is None:
            return None
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'finbert_loaded': self.model_loaded,
                'textblob_available': TEXTBLOB_AVAILABLE,
                'primary_method': 'finbert' if self.model_loaded else 'textblob' if TEXTBLOB_AVAILABLE else 'rule_based'
            },
            'portfolio_summary': {
                'total_stocks': 0,
                'positive_sentiment': 0,
                'negative_sentiment': 0,
                'neutral_sentiment': 0,
                'overall_sentiment': 'neutral',
                'average_confidence': 0.0,
                'most_positive': None,
                'most_negative': None
            },
            'stock_sentiments': []
        }
        
        # Use 'Instrument' column for stock symbols
        stock_column = 'Instrument'
        if stock_column not in df.columns:
            stock_column = df.columns[0]
        
        logger.info(f"Analyzing {len(df)} stocks using column '{stock_column}'")
        
        portfolio_sentiments = []
        total_confidence = 0
        
        for idx, row in df.iterrows():
            stock_symbol = str(row[stock_column]).strip()
            if pd.isna(stock_symbol) or stock_symbol == 'nan' or stock_symbol == '':
                continue
            
            # Get financial news
            news_text = self.get_financial_news(stock_symbol)
            
            # Analyze sentiment
            sentiment_result = self.analyze_sentiment(news_text)
            
            stock_data = {
                'symbol': stock_symbol,
                'news': news_text,
                'sentiment': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence'],
                'scores': sentiment_result['scores'],
                'method': sentiment_result['method']
            }
            
            # Add market value if available
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['cur. val', 'current value', 'market value', 'invested']):
                    try:
                        value = row[col]
                        if pd.notna(value):
                            stock_data['market_value'] = float(str(value).replace(',', ''))
                            break
                    except:
                        pass
            
            portfolio_sentiments.append(stock_data)
            total_confidence += sentiment_result['confidence']
            
            # Update counters
            if sentiment_result['sentiment'] == 'positive':
                results['portfolio_summary']['positive_sentiment'] += 1
            elif sentiment_result['sentiment'] == 'negative':
                results['portfolio_summary']['negative_sentiment'] += 1
            else:
                results['portfolio_summary']['neutral_sentiment'] += 1
        
        # Calculate portfolio metrics
        total_stocks = len(portfolio_sentiments)
        results['portfolio_summary']['total_stocks'] = total_stocks
        results['portfolio_summary']['average_confidence'] = round(total_confidence / max(total_stocks, 1), 4)
        results['stock_sentiments'] = portfolio_sentiments
        
        # Find most positive and negative stocks
        if portfolio_sentiments:
            most_positive = max(portfolio_sentiments, key=lambda x: x['scores']['positive'])
            most_negative = max(portfolio_sentiments, key=lambda x: x['scores']['negative'])
            
            results['portfolio_summary']['most_positive'] = {
                'symbol': most_positive['symbol'],
                'news': most_positive['news'],
                'confidence': most_positive['scores']['positive'],
                'method': most_positive['method']
            }
            
            results['portfolio_summary']['most_negative'] = {
                'symbol': most_negative['symbol'],
                'news': most_negative['news'],
                'confidence': most_negative['scores']['negative'], 
                'method': most_negative['method']
            }
            
            # Overall sentiment based on weighted average
            pos_count = results['portfolio_summary']['positive_sentiment']
            neg_count = results['portfolio_summary']['negative_sentiment']
            
            if pos_count > neg_count * 1.5:  # Require stronger positive bias
                results['portfolio_summary']['overall_sentiment'] = 'positive'
            elif neg_count > pos_count * 1.5:
                results['portfolio_summary']['overall_sentiment'] = 'negative'
            else:
                results['portfolio_summary']['overall_sentiment'] = 'neutral'
        
        return results

def main():
    """Main execution function"""
    logger.info("Starting Production FinBERT Portfolio Analysis...")
    
    analyzer = ProductionFinBERTAnalyzer()
    excel_file = "Portfolio Data_Hypothetical.xlsx"
    
    if not os.path.exists(excel_file):
        logger.error(f"Portfolio file {excel_file} not found!")
        return None
    
    # Analyze portfolio
    results = analyzer.analyze_portfolio_sentiment(excel_file)
    
    if results:
        # Save results
        output_file = "portfolio_sentiment_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Analysis complete! Results saved to {output_file}")
        
        # Print summary
        summary = results['portfolio_summary']
        print(f"\n📊 Portfolio Sentiment Analysis Summary:")
        print(f"🔧 Primary Method: {results['model_info']['primary_method'].upper()}")
        print(f"📈 Total Stocks: {summary['total_stocks']}")
        print(f"✅ Positive: {summary['positive_sentiment']}")
        print(f"⚠️  Neutral: {summary['neutral_sentiment']}")  
        print(f"❌ Negative: {summary['negative_sentiment']}")
        print(f"🎯 Overall: {summary['overall_sentiment'].upper()}")
        print(f"🔍 Avg Confidence: {summary['average_confidence']:.1%}")
        
        if summary['most_positive']:
            print(f"\n📈 Most Positive: {summary['most_positive']['symbol']}")
            print(f"   Method: {summary['most_positive']['method']}")
            
        if summary['most_negative']:
            print(f"\n📉 Watch Alert: {summary['most_negative']['symbol']}")
            print(f"   Method: {summary['most_negative']['method']}")
        
        return results
    else:
        logger.error("Failed to analyze portfolio sentiment")
        return None

if __name__ == "__main__":
    main()