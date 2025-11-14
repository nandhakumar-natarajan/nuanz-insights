"""
FastAPI endpoints for portfolio sentiment analysis
Add these routes to your existing FastAPI app
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import json
import os
from typing import Dict, Any

# Add these to your existing app/main.py or create new endpoints

@app.get("/api/portfolio/sentiment-analysis")
async def get_portfolio_sentiment():
    """Get complete portfolio sentiment analysis"""
    try:
        sentiment_file = "portfolio_sentiment_analysis.json"
        if os.path.exists(sentiment_file):
            with open(sentiment_file, 'r') as f:
                data = json.load(f)
            return JSONResponse(content=data)
        else:
            # Return mock data if analysis file doesn't exist
            mock_data = {
                "timestamp": "2025-11-11T10:00:00",
                "portfolio_summary": {
                    "total_stocks": 4,
                    "positive_sentiment": 3,
                    "negative_sentiment": 0,
                    "neutral_sentiment": 1,
                    "overall_sentiment": "positive",
                    "most_positive": {
                        "symbol": "GOLD1",
                        "news": "Gold ETF sees strong inflows as investors seek safe haven assets",
                        "confidence": 0.85
                    },
                    "most_negative": {
                        "symbol": "OIL",
                        "news": "Oil prices remain volatile amid global economic uncertainty",
                        "confidence": 0.65
                    }
                },
                "stock_sentiments": [
                    {
                        "symbol": "GOLD1",
                        "sentiment": "positive",
                        "confidence": 0.85,
                        "news": "Gold ETF sees strong inflows as investors seek safe haven assets"
                    }
                ]
            }
            return JSONResponse(content=mock_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/sentiment")
async def get_portfolio_sentiment_summary():
    """Get portfolio sentiment summary for the main cards"""
    try:
        sentiment_file = "portfolio_sentiment_analysis.json"
        if os.path.exists(sentiment_file):
            with open(sentiment_file, 'r') as f:
                data = json.load(f)
            
            summary = data.get('portfolio_summary', {})
            return {
                "summary": f"{summary.get('overall_sentiment', 'neutral').title()}",
                "score": f"+{summary.get('positive_sentiment', 0)} | -{summary.get('negative_sentiment', 0)}"
            }
        else:
            return {
                "summary": "Mostly Positive",
                "score": "+3 | -0"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/top-news")
async def get_portfolio_top_news():
    """Get the most important news for the portfolio"""
    try:
        sentiment_file = "portfolio_sentiment_analysis.json"
        if os.path.exists(sentiment_file):
            with open(sentiment_file, 'r') as f:
                data = json.load(f)
            
            most_positive = data.get('portfolio_summary', {}).get('most_positive')
            if most_positive:
                return {
                    "headline": f"{most_positive['symbol']}: {most_positive['news'][:100]}...",
                    "link": f"/portfolio/{most_positive['symbol']}"
                }
        
        return {
            "headline": "GOLD1: Strong inflows drive positive sentiment in precious metals sector",
            "link": "/portfolio/GOLD1"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))