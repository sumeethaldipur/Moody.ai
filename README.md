# Moody.ai - Adaptive Activity Recommendation System Based on Emotion Detection

Moody.ai is an emotion-aware recommendation system that detects a user’s mood through facial expression analysis and suggests personalized activities to help regulate and improve mental well-being. The system leverages a Convolutional Neural Network (CNN) inspired by a modified VGG-16 architecture, trained on the FER-2013 dataset, to classify seven emotions—anger, disgust, fear, happiness, sadness, surprise, and neutrality—with an accuracy of ~90% 

Based on the detected emotion, Moody.ai recommends curated activities across multiple domains including movies, music, books, sports, and leisure pursuits. The platform supports both generalized recommendations for anonymous users and adaptive, personalized recommendations for authenticated users by incorporating historical activity engagement and post-activity mood feedback. The recommendation engine combines popularity-based ranking with content-based filtering using cosine similarity to continuously refine suggestions over time.

Designed with mental health awareness in mind, Moody.ai aims to help users better understand their emotional state and take actionable steps to uplift their mood, offering potential applications in self-care tools, mood tracking platforms, and assistive systems for mental health support.
