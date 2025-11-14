"""
Local test version without PyTorch for Windows compatibility
"""
import json
from datetime import datetime

class LocalFinBERTAnalyzer:
    def __init__(self):
        # Enhanced financial keywords for better accuracy
        self.positive_words = [
            'growth', 'strong', 'beat', 'rally', 'positive', 'win', 'profit', 
            'gain', 'high', 'good', 'excellent', 'bullish', 'surge', 'rise',
            'outperform', 'exceed', 'robust', 'solid', 'healthy', 'optimistic',
            'momentum', 'breakthrough', 'success', 'recovery', 'expansion',
            'upward', 'promising', 'stellar', 'impressive', 'milestone'
        ]
        self.negative_words = [
            'decline', 'fall', 'loss', 'weak', 'pressure', 'drop', 'bad', 
            'poor', 'bearish', 'crash', 'volatility', 'concern', 'risk',
            'challenge', 'struggle', 'disappointing', 'uncertain', 'headwind',
            'deteriorate', 'sluggish', 'unfavorable', 'downturn', 'warning',
            'plunge', 'turbulent', 'cautious', 'shortfall', 'disruption'
        ]
    
    def get_financial_news(self, stock_symbol):
        """Get enhanced financial news"""
        financial_news = {
            'GOLD1': "Gold ETF experiences strong institutional inflows as central bank policies drive safe haven demand amid global economic uncertainty",
            'NATIONALUM': "National Aluminium Company reports record quarterly production with 12% YoY growth, benefiting from robust automotive and infrastructure demand", 
            'OIL': "Oil and Natural Gas Corporation announces major offshore discovery, expects production boost of 15% over next two years with improved margins",
            'MOTILAL': "Motilal Oswal Large and Midcap Fund delivers alpha with disciplined stock selection, outperforming benchmark by 280 basis points YTD"
        }
        
        clean_symbol = stock_symbol.upper().replace(' ', '').replace('.', '')
        return financial_news.get(clean_symbol, f"{stock_symbol} demonstrates operational resilience with steady fundamentals and positive medium-term growth outlook")
    
    def analyze_sentiment(self, text):
        """Enhanced rule-based sentiment analysis simulating FinBERT quality"""
        text_lower = text.lower()
        
        # Count keyword occurrences
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Weight important financial terms more heavily
        important_positive = ['strong', 'growth', 'beat', 'outperform', 'surge', 'stellar', 'robust']
        important_negative = ['crash', 'loss', 'decline', 'warning', 'risk', 'plunge', 'concern']
        
        pos_boost = sum(2 for word in important_positive if word in text_lower)
        neg_boost = sum(2 for word in important_negative if word in text_lower)
        
        # Calculate scores
        total_positive = positive_count + pos_boost
        total_negative = negative_count + neg_boost
        
        # Determine sentiment with higher confidence thresholds
        if total_positive > total_negative and total_positive > 0:
            sentiment = 'positive'
            confidence = min(0.75 + (total_positive - total_negative) * 0.05, 0.95)
        elif total_negative > total_positive and total_negative > 0:
            sentiment = 'negative'
            confidence = min(0.75 + (total_negative - total_positive) * 0.05, 0.95)
        else:
            sentiment = 'neutral'
            confidence = 0.65
        
        # Generate FinBERT-style probability distribution
        if sentiment == 'positive':
            pos_score = confidence
            neg_score = (1 - confidence) * 0.3
            neu_score = (1 - confidence) * 0.7
        elif sentiment == 'negative':
            neg_score = confidence
            pos_score = (1 - confidence) * 0.3
            neu_score = (1 - confidence) * 0.7
        else:
            neu_score = confidence
            pos_score = (1 - confidence) * 0.5
            neg_score = (1 - confidence) * 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 4),
            'scores': {
                'negative': round(neg_score, 4),
                'neutral': round(neu_score, 4),
                'positive': round(pos_score, 4)
            },
            'method': 'enhanced_rule_based'
        }
    
    def analyze_portfolio(self):
        """Analyze portfolio with enhanced accuracy"""
        sample_portfolio = ['GOLD1', 'NATIONALUM', 'OIL', 'MOTILAL']
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'finbert_loaded': False,
                'textblob_available': False,
                'primary_method': 'enhanced_rule_based'
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
        
        portfolio_sentiments = []
        total_confidence = 0
        
        for stock_symbol in sample_portfolio:
            news_text = self.get_financial_news(stock_symbol)
            sentiment_result = self.analyze_sentiment(news_text)
            
            stock_data = {
                'symbol': stock_symbol,
                'news': news_text,
                'sentiment': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence'],
                'scores': sentiment_result['scores'],
                'method': sentiment_result['method']
            }
            
            portfolio_sentiments.append(stock_data)
            total_confidence += sentiment_result['confidence']
            
            # Update counters
            if sentiment_result['sentiment'] == 'positive':
                results['portfolio_summary']['positive_sentiment'] += 1
            elif sentiment_result['sentiment'] == 'negative':
                results['portfolio_summary']['negative_sentiment'] += 1
            else:
                results['portfolio_summary']['neutral_sentiment'] += 1
        
        # Calculate summary
        total_stocks = len(portfolio_sentiments)
        results['portfolio_summary']['total_stocks'] = total_stocks
        results['portfolio_summary']['average_confidence'] = round(total_confidence / total_stocks, 4)
        results['stock_sentiments'] = portfolio_sentiments
        
        # Find extremes
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
        
        # Overall sentiment
        pos_count = results['portfolio_summary']['positive_sentiment']
        neg_count = results['portfolio_summary']['negative_sentiment']
        
        if pos_count > neg_count * 1.5:
            results['portfolio_summary']['overall_sentiment'] = 'positive'
        elif neg_count > pos_count * 1.5:
            results['portfolio_summary']['overall_sentiment'] = 'negative'
        else:
            results['portfolio_summary']['overall_sentiment'] = 'neutral'
        
        return results

if __name__ == "__main__":
    analyzer = LocalFinBERTAnalyzer()
    results = analyzer.analyze_portfolio()
    
    # Save to JSON file
    with open('portfolio_sentiment_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("📊 Enhanced Portfolio Sentiment Analysis Summary:")
    print(f"🔧 Method: {results['model_info']['primary_method'].upper()}")
    print(f"📈 Total Stocks: {results['portfolio_summary']['total_stocks']}")
    print(f"✅ Positive: {results['portfolio_summary']['positive_sentiment']}")
    print(f"⚠️  Neutral: {results['portfolio_summary']['neutral_sentiment']}")
    print(f"❌ Negative: {results['portfolio_summary']['negative_sentiment']}")
    print(f"🎯 Overall: {results['portfolio_summary']['overall_sentiment'].upper()}")
    print(f"🔍 Avg Confidence: {results['portfolio_summary']['average_confidence']:.1%}")
    
    if results['portfolio_summary']['most_positive']:
        print(f"\n📈 Most Positive: {results['portfolio_summary']['most_positive']['symbol']}")
        
    if results['portfolio_summary']['most_negative']:
        print(f"📉 Watch Alert: {results['portfolio_summary']['most_negative']['symbol']}")