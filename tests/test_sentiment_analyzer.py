from app.sentiment_analyzer import sentiment_label

def test_negative_sentiment():
    assert sentiment_label("This is frustrating and I am tired of waiting") in ["Negative", "Very Negative"]

def test_positive_sentiment():
    assert sentiment_label("Thanks for the quick help") == "Positive"
