# brainrot_predictor/predictor.py
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

class BrainrotPredictor:
    def __init__(self):
        self.spawn_model = None
        self.rarity_model = None
        self.trading_model = None
        self.server_activity_model = None
        self.load_data()
        self.train_models()

    def load_data(self):
        """Load and preprocess data from JSON files"""
        self.spawn_data = self._load_json('data/spawn_history.json')
        self.rarity_data = self._load_json('data/rarity_data.json')
        self.trading_data = self._load_json('data/trading_history.json')
        
    def _load_json(self, filepath):
        """Helper method to load JSON data"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def train_models(self):
        """Train prediction models for different aspects"""
        self._train_spawn_prediction()
        self._train_rarity_prediction()
        self._train_trading_prediction()
        self._train_server_activity_prediction()

    def _train_spawn_prediction(self):
        """Train model for spawn location prediction"""
        if not self.spawn_data:
            print("No spawn data available for training.")
            return
            
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(self.spawn_data)
        
        # Example features (modify based on actual data structure)
        X = df[['hour', 'day_of_week', 'map_id']]  # Example features
        y = df['location_id']  # Target variable
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Train model
        self.spawn_model = RandomForestRegressor()
        self.spawn_model.fit(X_train, y_train)
        print("Spawn prediction model trained successfully")

    def _train_rarity_prediction(self):
        """Train model for rarity drop prediction"""
        if not self.rarity_data:
            print("No rarity data available for training.")
            return
            
        # Implementation would go here
        pass

    def _train_trading_prediction(self):
        """Train model for trading value prediction"""
        if not self.trading_data:
            print("No trading data available for training.")
            return
            
        # Implementation would go here
        pass

    def _train_server_activity_prediction(self):
        """Train model for server activity prediction"""
        # Implementation would go here
        pass

    def predict_spawn_location(self, current_time=None):
        """Predict next spawn location"""
        if current_time is None:
            current_time = datetime.now()
            
        if not self.spawn_model:
            return "Model not trained. Not enough data."
            
        # Prepare input features
        features = np.array([[
            current_time.hour,
            current_time.weekday(),
            1  # Default map_id, adjust as needed
        ]])
        
        # Make prediction
        prediction = self.spawn_model.predict(features)
        return f"Predicted spawn location: {int(prediction[0])}"

    def predict_rarity_drop(self, brainrot_type):
        """Predict rarity of next drop"""
        if not self.rarity_model:
            return 0.5  # Default probability if model not trained
            
        # Implementation would go here
        return 0.5

    def predict_trading_value(self, brainrot_name):
        """Predict trading value of a brainrot"""
        if not self.trading_model:
            return 100  # Default value if model not trained
            
        # Implementation would go here
        return 100

    def predict_server_activity(self, time_window="1h"):
        """Predict server activity for the next time window"""
        # Implementation would go here
        return "medium"  # Example: low/medium/high

def main():
    print("Initializing Brainrot Predictor...")
    predictor = BrainrotPredictor()
    
    while True:
        print("\n" + "="*30)
        print("  BRAINROT PREDICTOR")
        print("="*30)
        print("1. Predict Next Spawn Location")
        print("2. Predict Rarity Drop")
        print("3. Predict Trading Value")
        print("4. Predict Server Activity")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            location = predictor.predict_spawn_location()
            print(f"\n{location}")
            
        elif choice == '2':
            brainrot = input("Enter brainrot type: ")
            rarity = predictor.predict_rarity_drop(brainrot)
            print(f"\nPredicted rarity drop chance: {rarity*100:.2f}%")
            
        elif choice == '3':
            brainrot = input("Enter brainrot name: ")
            value = predictor.predict_trading_value(brainrot)
            print(f"\nPredicted trading value: {value} coins")
            
        elif choice == '4':
            activity = predictor.predict_server_activity()
            print(f"\nPredicted server activity: {activity}")
            
        elif choice == '5':
            print("\nExiting Brainrot Predictor. Goodbye!")
            break
            
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()