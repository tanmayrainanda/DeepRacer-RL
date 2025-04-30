import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# 1. Data Loading and Preprocessing
def load_data(file_path):
    """Load taxi trip data from parquet or CSV file"""
    print(f"Loading data from {file_path}")
    
    try:
        # Try parquet first
        df = pd.read_parquet(file_path)
        print(f"Loaded parquet with {len(df)} rows")
    except:
        # Fall back to CSV
        df = pd.read_csv(file_path, parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime'])
        print(f"Loaded CSV with {len(df)} rows")
    
    # Convert datetime columns if needed
    for col in ['tpep_pickup_datetime', 'tpep_dropoff_datetime']:
        if col in df.columns and not pd.api.types.is_datetime64_dtype(df[col]):
            df[col] = pd.to_datetime(df[col])
    
    # Add week column for aggregation
    df['pickup_week'] = df['tpep_pickup_datetime'].dt.to_period('W').dt.start_time
    
    return df

def aggregate_weekly(df):
    """Aggregate taxi data to weekly demand"""
    print("Aggregating data by week")
    
    # Group by week and count trips
    weekly_df = df.groupby('pickup_week').size().reset_index(name='demand')
    
    # Add time features
    weekly_df['week'] = weekly_df['pickup_week'].dt.isocalendar().week
    weekly_df['month'] = weekly_df['pickup_week'].dt.month
    weekly_df['year'] = weekly_df['pickup_week'].dt.year
    
    # Add cyclical encoding for weeks of the year (for seasonality)
    weekly_df['week_sin'] = np.sin(2 * np.pi * weekly_df['week'] / 52)
    weekly_df['week_cos'] = np.cos(2 * np.pi * weekly_df['week'] / 52)
    
    # Add cyclical encoding for month
    weekly_df['month_sin'] = np.sin(2 * np.pi * weekly_df['month'] / 12)
    weekly_df['month_cos'] = np.cos(2 * np.pi * weekly_df['month'] / 12)
    
    # Check if we have more than one year
    years = weekly_df['year'].unique()
    print(f"Data spans {len(years)} years: {years}")
    
    print(f"Created weekly dataset with {len(weekly_df)} points")
    print(f"Weekly demand range: {weekly_df['demand'].min()} to {weekly_df['demand'].max()}")
    
    return weekly_df

# 2. Sequence Creation and Dataset
def prepare_sequences(data, seq_length=8, target_col='demand'):
    """Create sequences for training with sequence length of 8 weeks"""
    print(f"Creating sequences with length {seq_length}")
    
    # Select features
    features = ['demand', 'week_sin', 'week_cos', 'month_sin', 'month_cos']
    model_data = data[features].copy()
    
    # Scale the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(model_data)
    
    # Get index of target column
    target_idx = model_data.columns.get_loc(target_col)
    
    # Create sequences (X) and targets (y)
    X, y = [], []
    for i in range(len(scaled_data) - seq_length):
        X.append(scaled_data[i:i+seq_length])
        y.append(scaled_data[i+seq_length, target_idx])
    
    # Convert to numpy arrays
    X = np.array(X)
    y = np.array(y)
    
    print(f"Created {len(X)} sequences")
    
    return X, y, scaler, target_idx

class TaxiDataset(Dataset):
    """PyTorch Dataset for LSTM"""
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# 3. LSTM Model
class SimpleLSTM(nn.Module):
    """Simple LSTM model for time series forecasting"""
    def __init__(self, input_size, hidden_size=64, num_layers=1):
        super(SimpleLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )
        
        # Output layer
        self.fc = nn.Linear(hidden_size, 1)
    
    def forward(self, x):
        # Initialize hidden states
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Get the output from the last time step
        out = out[:, -1, :]
        
        # Pass through linear layer
        out = self.fc(out)
        
        return out

# 4. Training and Evaluation
def train_lstm(model, train_loader, val_loader, epochs=20, learning_rate=0.001):
    """Train the LSTM model"""
    print("Training LSTM model")
    
    # Use CPU for simplicity and consistent behavior
    device = torch.device('cpu')
    model.to(device)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training history
    history = {'train_loss': [], 'val_loss': []}
    
    # Best model tracking
    best_val_loss = float('inf')
    best_model_state = None
    
    # Training loop
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        
        for inputs, targets in train_loader:
            inputs = inputs.to(device)
            targets = targets.to(device).unsqueeze(1)  # Add dimension for output
            
            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        history['train_loss'].append(train_loss)
        
        # Validation
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs = inputs.to(device)
                targets = targets.to(device).unsqueeze(1)
                
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        history['val_loss'].append(val_loss)
        
        print(f'Epoch {epoch+1}/{epochs}: train_loss = {train_loss:.6f}, val_loss = {val_loss:.6f}')
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
    
    # Load best model
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    return model, history

def evaluate_model(model, test_loader, scaler, target_idx, num_features):
    """Evaluate the model on test data"""
    print("Evaluating model")
    
    device = torch.device('cpu')
    model.to(device)
    model.eval()
    
    predictions = []
    actual = []
    
    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            outputs = model(inputs)
            
            # Store predictions and targets
            predictions.extend(outputs.squeeze().cpu().numpy())
            actual.extend(targets.cpu().numpy())
    
    # Convert to arrays
    predictions = np.array(predictions).reshape(-1, 1)
    actual = np.array(actual).reshape(-1, 1)
    
    # Inverse transform to original scale
    inv_predictions = invert_scaling(predictions, scaler, target_idx, num_features)
    inv_actual = invert_scaling(actual, scaler, target_idx, num_features)
    
    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(inv_actual, inv_predictions))
    mae = mean_absolute_error(inv_actual, inv_predictions)
    
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE: {mae:.2f}")
    
    return inv_predictions, inv_actual, rmse, mae

def invert_scaling(data, scaler, target_idx, num_features):
    """Invert scaling to get original values"""
    # Create dummy array with zeros
    dummy = np.zeros((len(data), num_features))
    
    # Put the predictions in the right column
    dummy[:, target_idx] = data.flatten()
    
    # Invert scaling
    inverted = scaler.inverse_transform(dummy)
    
    # Return just the target column
    return inverted[:, target_idx]

def plot_results(history, predictions, actual):
    """Plot training history and results"""
    plt.figure(figsize=(12, 10))
    
    # Plot loss
    plt.subplot(2, 1, 1)
    plt.plot(history['train_loss'], label='Training Loss')
    plt.plot(history['val_loss'], label='Validation Loss')
    plt.title('Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    # Plot predictions vs actual
    plt.subplot(2, 1, 2)
    plt.plot(actual, label='Actual')
    plt.plot(predictions, label='Predicted')
    plt.title('Weekly Taxi Demand Forecast')
    plt.xlabel('Week')
    plt.ylabel('Demand')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

# 5. Forecasting
def forecast_future_weeks(model, last_sequence, scaler, target_idx, num_features, num_weeks=4):
    """Forecast future weeks based on the last sequence"""
    print(f"Forecasting {num_weeks} weeks ahead")
    
    device = torch.device('cpu')
    model.to(device)
    model.eval()
    
    # Convert last sequence to tensor
    current_seq = torch.tensor(last_sequence, dtype=torch.float32).unsqueeze(0).to(device)
    
    # Store predictions
    predictions = []
    
    with torch.no_grad():
        for _ in range(num_weeks):
            # Get prediction for next week
            output = model(current_seq).item()
            predictions.append(output)
            
            # Update sequence for next prediction (rolling window)
            # Remove oldest week, add new prediction
            new_seq = current_seq.clone()
            # Shift data, dropping oldest time step
            new_seq[0, :-1, :] = current_seq[0, 1:, :]
            # Update target variable in the newest time step
            new_seq[0, -1, target_idx] = output
            
            current_seq = new_seq
    
    # Convert to array and invert scaling
    predictions = np.array(predictions).reshape(-1, 1)
    inverted_predictions = invert_scaling(predictions, scaler, target_idx, num_features)
    
    return inverted_predictions

# 6. Main function
def main():
    """Main function to run the entire pipeline"""
    # 1. Load and preprocess data
    df = load_data("taxi-dataset.parquet")  # Replace with your file path
    weekly_df = aggregate_weekly(df)
    
    # 2. Create sequences
    seq_length = 8  # Use 8 weeks of history to predict the next week
    X, y, scaler, target_idx = prepare_sequences(weekly_df, seq_length=seq_length)
    
    # Check if we have enough data
    if len(X) < 30:  # Arbitrary threshold
        print("WARNING: Very little data for training. Results may not be reliable.")
    
    # 3. Split data (70% train, 15% validation, 15% test)
    total_samples = len(X)
    train_size = int(0.7 * total_samples)
    val_size = int(0.15 * total_samples)
    
    X_train, y_train = X[:train_size], y[:train_size]
    X_val, y_val = X[train_size:train_size+val_size], y[train_size:train_size+val_size]
    X_test, y_test = X[train_size+val_size:], y[train_size+val_size:]
    
    print(f"Train: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    # 4. Create datasets and dataloaders
    train_dataset = TaxiDataset(X_train, y_train)
    val_dataset = TaxiDataset(X_val, y_val)
    test_dataset = TaxiDataset(X_test, y_test)
    
    batch_size = min(16, len(train_dataset))  # Avoid batch size > dataset size
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)
    
    # 5. Create and train model
    input_size = X.shape[2]  # Number of features
    model = SimpleLSTM(input_size=input_size)
    
    print(f"Model input size: {input_size}")
    trained_model, history = train_lstm(model, train_loader, val_loader, epochs=30)
    
    # 6. Evaluate model
    predictions, actual, rmse, mae = evaluate_model(
        trained_model, test_loader, scaler, target_idx, num_features=X.shape[2]
    )
    
    # 7. Plot results
    plot_results(history, predictions, actual)
    
    # 8. Forecast future weeks
    if len(X_test) > 0:
        last_sequence = X_test[-1]  # Use last test sequence for forecasting
        future_predictions = forecast_future_weeks(
            trained_model, last_sequence, scaler, target_idx, 
            num_features=X.shape[2], num_weeks=8
        )
        
        print("Forecasted demand for next 8 weeks:")
        for i, demand in enumerate(future_predictions):
            print(f"Week {i+1}: {demand:.0f}")
    
    return trained_model, predictions, actual, future_predictions

if __name__ == "__main__":
    main()